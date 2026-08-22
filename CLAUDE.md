# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Read `intent/INTENT.md` first — it is the source of truth for scope, acceptance criteria, and stop conditions for the current phase (Phase 1, see `intent/PHASE-01-MAP-STORY.md`).

## Commands

Backend (run from repo root, not `services/api` — `hooks/` is a sibling of `services/api` and is imported by `main.py`; `pyproject.toml` sets `pythonpath = ["."]` and `conftest.py` reinforces this):

```bash
docker compose up -d                 # PostGIS on localhost:5432
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ../..
PYTHONPATH=. uvicorn services.api.app.main:app --reload
```

Tests:

```bash
pytest services/api/tests/                       # all backend tests
pytest services/api/tests/test_export_guard.py   # single file
pytest services/api/tests/test_export_guard.py::test_rejects_missing_coordinates  # single test
```

Frontend:

```bash
cd apps/web
npm install
npm run dev     # vite dev server
npm run build    # tsc -b && vite build
```

Deterministic guardrails (also wired as a Claude Code `Stop` hook in `.claude/settings.json`, but must be runnable standalone since runtime safety cannot depend only on Claude Code hooks):

```bash
python hooks/validate_contracts.py    # sanity-checks contracts/*.schema.json themselves
python hooks/forbid_secrets.py        # scans repo for committed keys/tokens
python hooks/enforce_coordinate_provenance.py path/to/project.json  # checks a project payload
```

## Architecture

This is an intent-driven starter for a "Location Story Engine": a signed-in user states a plain-language intent, geocodes a subject location, composes additional story points on a map, saves the project, and exports an image artifact.

### The governing rule: AI interprets intent, it never owns geographic truth (ADR-001)

This is the one architectural decision that shapes everything else. AI (Claude, or any LLM) may normalize free-text intent, suggest categories, and propose places to search for — but it must never fabricate or silently alter a coordinate. Every `StoryPoint` carries a `coordinateSource` (`geocoder` | `map_click` | `import`); geocoded points must additionally carry a `providerPlaceId` for provenance. Coordinates, persistence, auth, schema validation, and artifact storage are deterministic-code concerns, not AI concerns. See `docs/ADR-001-ai-boundary.md` and `docs/ARCHITECTURE.md`.

### Contracts are the handoff boundary

`contracts/*.schema.json` (JSON Schema) define the structured payloads that cross system/agent boundaries: `LocationStoryIntent`, `StoryPoint`, `ExportRequest`. Any automated handoff — frontend↔backend, subagent↔main flow, export payload — must conform to these. `hooks/validate_contracts.py` validates the schema files themselves; `hooks/enforce_coordinate_provenance.py` and `hooks/pre_export.py` (`validate_exportable_project`) validate actual payloads against the provenance/export rules. `services/api/app/main.py`'s `/projects/{id}/export` endpoint calls `validate_exportable_project` before allowing export — this is the pattern to follow for any new boundary: validate with the same logic the hooks use, don't reimplement checks ad hoc.

### Repo layout

- `intent/` — product/phase intent (read `INTENT.md` first)
- `contracts/` — JSON Schema handoff contracts (authoritative)
- `hooks/` — deterministic guardrails (non-optional; not just Claude Code hooks)
- `skills/` — reusable organizational knowledge for AI-assisted work (geocoding provenance rules, map composition defaults, AWS deployment posture, location-story-builder behavior)
- `agents/` — narrowly-scoped subagent definitions; only two exist (`architecture-reviewer`, `intent-normalizer`), each with a stated reason and an explicit context-passing policy — don't create new ones without a comparable justification
- `apps/web/` — React + TypeScript + Vite frontend (MapLibre GL for mapping); `src/main.tsx` is a single-file app (no component split yet) covering intent capture, geocode search, map-click point add, and story-point edit/remove; the dev server proxies `/api` to the FastAPI backend at `127.0.0.1:8000` (`vite.config.ts`)
- `services/api/` — FastAPI backend; `app/main.py` has in-memory dict storage (`projects: dict[UUID, Project]`) as a Phase 1 placeholder for PostgreSQL/PostGIS — `POST /projects` creates, `PUT /projects/{id}` replaces the full saved state (points/center/zoom/name/intent) and bumps `version`, `GET /projects/{id}` reloads; `app/geocoding.py` wraps Amazon Location Service (`geo-places`) via boto3, `app/models.py` holds the Pydantic models mirroring the JSON Schema contracts
- `infra/` — AWS CDK deployment scaffold (not yet built out)
- `docs/` — architecture notes and ADRs

### Target stack (see `docs/ARCHITECTURE.md`, `skills/aws-deployment/SKILL.md`)

React/TypeScript/Vite + MapLibre GL → FastAPI → PostgreSQL/PostGIS, with Cognito auth, Amazon Location Service for geocoding, S3 for exported artifacts, deployed via CDK (S3+CloudFront for the frontend, ECS Fargate for the API). Much of this (auth, real persistence, the renderer/S3 export pipeline) is not implemented yet — `main.py`'s export endpoint explicitly stops at "project is exportable" and notes the renderer is the next vertical slice.

## Operating rules

- Implement the smallest safe change that advances the current intent phase; don't broaden Phase 1 into demographics, billing, or advanced analytics (see Non-goals in `intent/PHASE-01-MAP-STORY.md`).
- Never invent geographic coordinates. Coordinates only come from the configured geocoder or an explicit map click/import.
- Treat `contracts/` as authoritative — validate against them, don't hand-roll equivalent checks.
- Don't create subagents beyond `agents/` unless a new case matches that bar (specialization or isolation genuinely required).
- Pass minimum sufficient context between boundaries (e.g. to the `intent-normalizer` subagent); prefer structured findings over raw chat history, and retain source/provider identifiers needed for verification when passing external findings along.
- Before finishing a task: run contract validation (`hooks/validate_contracts.py`), run tests for the changed behavior, summarize changed files, state which acceptance criteria (from `intent/INTENT.md`) are satisfied, and state remaining gaps.
