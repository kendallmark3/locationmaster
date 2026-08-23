# Location Story Engine — Intent-Driven Starter

A focused enterprise-ready starter for building location stories from intent.

## First-pass user journey

1. User signs in.
2. User creates a project and enters a plain-language intent.
3. User searches/geocodes a subject location.
4. User adds as many story points as needed.
5. User changes symbol, label, category, size, and visibility.
6. User saves the project.
7. User exports a first-pass image artifact.
8. Project, intent, points, and output remain retrievable.

## Current implemented workflow (UI + API)

- **Use my location — fill in everything**: auto-fills project name/intent, adds a subject point, and pulls nearby coffee/restaurants/schools/parks.
- **Find**: geocodes your typed location and adds it as a subject point.
- **Map click**: click anywhere on the map to add a custom point.
- **Add real nearby places** chips: appends real nearby places by category.
- **Story Points** editor: rename points, change symbol, add notes, remove points.
- **Save Story**: persists project name, intent, points, and viewport.
- **Give me a reason to move here**: generates a grounded relocation narrative from saved points/intent.
- **Export image**: currently available through the API endpoint (`POST /projects/{id}/export`).

## Getting the best results

- Set a clear project intent (ideally at least one full sentence).
- Keep a real **subject** location in the story (via geocode or current location).
- Add at least 2 meaningful points or add notes to key points before generating narrative.
- Use point notes to explain *why* each place matters; narrative quality depends on this detail.
- Save before generating narrative or exporting so you use the latest project version.

## Export image (PNG/JPEG)

There is no dedicated Export button in the web UI yet; use the export API after saving:

1. Save your story in the UI.
2. Copy the project ID from the URL query string (`?project=<id>`).
3. Use the latest saved version shown in the UI (`Saved (version X)`).
4. Call export:

```bash
curl -X POST "http://127.0.0.1:8000/projects/<PROJECT_ID>/export" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "<PROJECT_ID>",
    "projectVersion": <VERSION>,
    "format": "png",
    "width": 1280,
    "height": 720
  }' \
  --output story.png
```

Notes:
- `projectId` in body must match the URL project id.
- `projectVersion` must match the latest saved version (stale versions are rejected).

## Architecture posture

- Goal-oriented by default.
- Procedural orchestration only around external calls and publish/export boundaries.
- AI interprets intent; deterministic services own coordinates, persistence, auth, validation, and rendering.
- Minimum-sufficient context is passed between boundaries.
- Structured contracts are required for every automated handoff.
- Skills contain reusable organizational knowledge.
- Hooks enforce non-optional rules.
- Subagents are used only when specialization or isolation is justified.

## Technology choices

- Frontend: React + TypeScript + Vite
- Map: MapLibre GL JS
- Backend: FastAPI + Python
- Persistence: PostgreSQL/PostGIS
- Auth: Amazon Cognito
- Maps/Geocoding/Places: Amazon Location Service
- Artifact storage: Amazon S3
- Deployment: AWS CDK starter
- Local development: Docker Compose

## Repo layout

- `intent/` — product and phase intent files
- `contracts/` — structured handoff schemas
- `skills/` — reusable AI/process knowledge
- `hooks/` — deterministic guardrails
- `agents/` — narrowly justified subagent definitions
- `apps/web/` — React app
- `services/api/` — FastAPI service
- `infra/` — AWS deployment scaffolding
- `.claude/` — Claude Code project guidance/hooks wiring
- `docs/` — architecture notes and ADRs

## MVP definition

This starter intentionally does **not** implement demographic intelligence, billing, high-resolution production rendering, or broad commercial data integrations. It establishes the governed platform these capabilities can later plug into.

## Local start

```bash
docker compose up -d
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../..
# Run from the repo root (not services/api) so the app can import hooks/,
# which lives at the repo root as a sibling of services/api.
PYTHONPATH=. uvicorn services.api.app.main:app --reload
```

Run tests from the repo root the same way — `pyproject.toml` sets `pythonpath = ["."]` so `pytest` resolves `hooks/` automatically:

```bash
pytest services/api/tests/
```

In another shell:

```bash
cd apps/web
npm install
npm run dev
```

Copy `.env.example` files as needed.

## Definition of done for Phase 1

A signed-in user can create a story project, enter intent, geocode a location, add/edit/remove story points with symbols and labels, save/reload the project, and export a basic image/preview without bypassing contract validation.
