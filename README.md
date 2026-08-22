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
