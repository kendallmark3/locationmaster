from pathlib import Path

import anthropic
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from uuid import UUID
from .models import ExportRequest, Project, ProjectCreate, ProjectSave, StoryPoint
from .geocoding import AwsLocationGeocoder
from .narrative import generate_relocation_narrative, has_enough_detail
from .exporter import render_project_image
from hooks.pre_export import validate_exportable_project

# Explicit path: uvicorn is run from the repo root per README, so the default
# load_dotenv() cwd-search would miss services/api/.env.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="Location Story Engine API")
projects: dict[UUID, Project] = {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/projects", response_model=Project)
def create_project(payload: ProjectCreate):
    project = Project(name=payload.name, rawIntent=payload.rawIntent)
    projects[project.id] = project
    return project

@app.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: UUID):
    if project_id not in projects:
        raise HTTPException(404, "Project not found")
    return projects[project_id]

@app.post("/projects/{project_id}/points", response_model=Project)
def add_point(project_id: UUID, point: StoryPoint):
    project = get_project(project_id)
    project.points.append(point)
    project.version += 1
    return project

@app.put("/projects/{project_id}", response_model=Project)
def save_project(project_id: UUID, payload: ProjectSave):
    project = get_project(project_id)
    project.name = payload.name
    project.rawIntent = payload.rawIntent
    project.points = payload.points
    project.center = payload.center
    project.zoom = payload.zoom
    project.version += 1
    return project

@app.get("/geocode")
def geocode(q: str):
    # Live AWS call. Replace with dependency-injected adapter in tests.
    try:
        return AwsLocationGeocoder().geocode(q)
    except ClientError as exc:
        raise HTTPException(502, f"Geocoding failed: {exc.response['Error']['Message']}")

@app.get("/reverse-geocode")
def reverse_geocode(lng: float, lat: float):
    # Live AWS call. Replace with dependency-injected adapter in tests.
    try:
        results = AwsLocationGeocoder().reverse_geocode(lng, lat)
    except ClientError as exc:
        raise HTTPException(502, f"Reverse geocoding failed: {exc.response['Error']['Message']}")
    if not results:
        raise HTTPException(404, "No address found for that location.")
    return results[0]

# Friendly category id -> free-text query sent to the geocoder's nearby-search. Free text
# (not AWS's IncludeCategories taxonomy) so results come from the same proven search path
# as /geocode, and a typo here just returns fewer/irrelevant results instead of silently
# matching nothing.
NEARBY_CATEGORY_QUERIES = {
    "coffee": "coffee shop",
    "restaurant": "restaurant",
    "school": "school",
    "park": "park",
    "transit": "public transit station",
    "hotel": "hotel",
    "grocery": "grocery store",
}

@app.get("/places/nearby")
def places_nearby(lng: float, lat: float, category: str):
    query = NEARBY_CATEGORY_QUERIES.get(category)
    if not query:
        raise HTTPException(422, f"Unknown category '{category}'. Known: {', '.join(NEARBY_CATEGORY_QUERIES)}")
    # Live AWS call. Replace with dependency-injected adapter in tests.
    try:
        return AwsLocationGeocoder().search_nearby(query, lng, lat)
    except ClientError as exc:
        raise HTTPException(502, f"Nearby search failed: {exc.response['Error']['Message']}")

@app.post("/projects/{project_id}/narrative")
def narrative(project_id: UUID):
    project = get_project(project_id)
    visible_points = [p for p in project.points if p.visible]
    if not visible_points:
        raise HTTPException(422, "Add at least one visible story point first.")
    if not has_enough_detail(project.rawIntent, [p.model_dump(mode="json") for p in visible_points]):
        raise HTTPException(
            422,
            "Not enough detail to write a grounded narrative yet — add notes to a story "
            "point, a second point, or expand the project intent.",
        )
    try:
        text = generate_relocation_narrative(
            project.rawIntent,
            [p.model_dump(mode="json") for p in visible_points],
        )
    except (anthropic.AuthenticationError, TypeError):
        # TypeError: the SDK raises this client-side (not AuthenticationError) when no
        # credential at all is resolvable, as opposed to an invalid one being rejected.
        raise HTTPException(502, "Narrative generation is not configured (missing or invalid API credentials).")
    except anthropic.RateLimitError:
        raise HTTPException(503, "Narrative generation is rate-limited; try again shortly.")
    except anthropic.APIStatusError as exc:
        raise HTTPException(502, f"Narrative generation failed: {exc.message}")
    except anthropic.APIConnectionError:
        raise HTTPException(503, "Could not reach the narrative generation service.")
    return {"narrative": text}

@app.post("/projects/{project_id}/export")
def export(project_id: UUID, payload: ExportRequest):
    project = get_project(project_id)
    if payload.projectId != str(project.id):
        raise HTTPException(409, "projectId does not match the requested project.")
    if payload.projectVersion != project.version:
        raise HTTPException(409, "projectVersion is stale; reload and retry export.")
    errors = validate_exportable_project({
        "intent": project.rawIntent,
        "points": [p.model_dump(mode="json") for p in project.points],
    })
    if errors:
        raise HTTPException(422, {"errors": errors})
    content = render_project_image(project, payload.format, payload.width, payload.height)
    media_type = "image/png" if payload.format == "png" else "image/jpeg"
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "X-Project-Id": str(project.id),
            "X-Project-Version": str(project.version),
            "Content-Disposition": f'inline; filename="{project.id}.{payload.format}"',
        },
    )
