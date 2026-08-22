from fastapi import FastAPI, HTTPException
from uuid import UUID
from .models import Project, ProjectCreate, StoryPoint
from .geocoding import AwsLocationGeocoder
from hooks.pre_export import validate_exportable_project

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

@app.get("/geocode")
def geocode(q: str):
    # Live AWS call. Replace with dependency-injected adapter in tests.
    return AwsLocationGeocoder().geocode(q)

@app.post("/projects/{project_id}/export")
def export(project_id: UUID):
    project = get_project(project_id)
    errors = validate_exportable_project({
        "intent": project.rawIntent,
        "points": [p.model_dump(mode="json") for p in project.points],
    })
    if errors:
        raise HTTPException(422, {"errors": errors})
    # Phase 1 scaffold: runtime renderer/S3 implementation plugs in here.
    return {
        "status": "validated",
        "projectId": str(project.id),
        "projectVersion": project.version,
        "message": "Project is exportable; renderer is the next vertical slice."
    }
