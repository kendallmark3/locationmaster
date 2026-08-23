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
- **Export Image**: downloads a real PNG of the live map — actual basemap tiles plus your story points — after the backend's export-boundary validation passes.
- **Run Capability Check**: a small "System Capabilities" panel that proves out the Skill → Tool → MCP → Hook chain live (calls the official Fetch MCP server to pull a joke from a public API), not a canned demo.
- **Map basemap**: defaults to a free OpenFreeMap dev style; set `VITE_MAPBOX_TOKEN` in `apps/web/.env` for real Mapbox raster tiles instead (see `apps/web/.env.example`).

## Getting the best results

- Set a clear project intent (ideally at least one full sentence).
- Keep a real **subject** location in the story (via geocode or current location).
- Add at least 2 meaningful points or add notes to key points before generating narrative.
- Use point notes to explain *why* each place matters; narrative quality depends on this detail.
- Save before generating narrative or exporting so you use the latest project version.

## Export image (PNG)

Click **Export Image** in the sidebar after saving. Under the hood:

1. The frontend calls `POST /projects/{id}/export` with the saved `projectVersion` — this is purely an export-boundary validation call (contracts + coordinate provenance via `hooks/pre_export.py`); a stale or invalid version is rejected here.
2. On success, the frontend captures the *live* MapLibre canvas (`map.getCanvas()`, requires `canvasContextAttributes.preserveDrawingBuffer`) and composites your story points on top client-side, so the downloaded file shows the real basemap tiles you're looking at rather than a schematic diagram.
3. A PNG downloads automatically, named after the project.

The backend endpoint also independently renders a basic PIL-drawn PNG (`services/api/app/exporter.py`) — a flat schematic with plotted dots, no basemap imagery. That's what you get calling the endpoint directly (e.g. via `curl`) without the frontend's canvas-capture step; the UI button is the one that produces a real map image.

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
- Map: MapLibre GL JS (OpenFreeMap dev style by default; optional Mapbox raster basemap)
- Backend: FastAPI + Python
- AI: Anthropic Claude (relocation narrative generation, capability-check demo)
- External tool protocol: MCP (Model Context Protocol) — official `mcp-server-fetch` reference server
- Persistence: PostgreSQL/PostGIS (Phase 1 currently uses in-memory storage; DB wiring is future work)
- Auth: Amazon Cognito (not yet wired — future work)
- Maps/Geocoding/Places: Amazon Location Service (`geo-places`: Geocode, SearchText, ReverseGeocode)
- Artifact storage: Amazon S3 (not yet wired — exports currently download directly to the browser)
- Deployment: AWS CDK starter
- Local development: Docker Compose

## Repo layout

- `intent/` — product and phase intent files (`INTENT.md` is Phase 1; `v1intent.md` and `PHASE-05-EXPERIENCE.md` are later intents — see status notes in each)
- `contracts/` — structured handoff schemas
- `skills/` — reusable AI/process knowledge, including `capability-check/SKILL.md` for the MCP demo
- `hooks/` — deterministic guardrails, including `validate_capability_result.py` (capability-check hook)
- `agents/` — narrowly justified subagent definitions
- `apps/web/` — React app
- `services/api/` — FastAPI service; notable modules beyond the core CRUD/geocoding: `narrative.py` (Claude relocation narrative), `exporter.py` (PIL schematic export), `capability_workflow.py` + `mcp_client.py` + `tools.py` (Skill → Tool → MCP → Hook demo)
- `infra/` — AWS deployment scaffolding
- `.claude/` — Claude Code project guidance/hooks wiring
- `docs/` — architecture notes and ADRs
- `dic.md` — index of skills/hooks/commands: what to run, when, and who runs it

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

Copy `.env.example` files as needed (`services/api/.env.example`, `apps/web/.env.example`).

### Required credentials for live features

- **`services/api/.env` → `ANTHROPIC_API_KEY`** — required for "Give me a reason to move here" and the capability-check joke result.
- **AWS credentials** (standard credential chain — `~/.aws/credentials`, env vars, etc.) for the IAM identity used by `boto3`, with an inline policy granting at minimum:
  ```json
  {
    "Effect": "Allow",
    "Action": ["geo-places:Geocode", "geo-places:SearchText", "geo-places:ReverseGeocode"],
    "Resource": "arn:aws:geo-places:us-east-1::provider/default"
  }
  ```
  Without this, `/geocode`, `/places/nearby`, and `/reverse-geocode` return a clean 502 with the real AWS error rather than crashing — but none of the location features work.
- **`apps/web/.env` → `VITE_MAPBOX_TOKEN`** — optional. Without it, the map falls back to a free OpenFreeMap dev style (works fine, just less detailed/no key needed).

## Definition of done for Phase 1

A signed-in user can create a story project, enter intent, geocode a location, add/edit/remove story points with symbols and labels, save/reload the project, and export a basic image/preview without bypassing contract validation.
