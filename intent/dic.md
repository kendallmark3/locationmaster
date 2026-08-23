# DIC — Skills, Hooks, and Automation Commands

This document explains **what to run, when to run it, and who should run it**.

## 1) Skills (`/skills`)

Skills are reusable guidance for AI-assisted work.

| Skill | Purpose | Who uses it | When to use it |
|---|---|---|---|
| `skills/geocoding/SKILL.md` | Coordinate provenance and geocoding rules | Developers + AI agents | Any place search, coordinate creation, or point updates |
| `skills/map-composition/SKILL.md` | Map readability defaults | Developers + AI agents | Story-point/category/symbol composition |
| `skills/location-story-builder/SKILL.md` | Intent-to-story workflow guardrails | Developers + AI agents | Building or updating narrative/story logic |
| `skills/aws-deployment/SKILL.md` | Phase-1 AWS deployment defaults | Developers + platform engineers | Infra/deployment planning and implementation |

## 2) Hooks (`/hooks`)

Hooks are deterministic checks and should be treated as required.

| Hook | Command | Who runs it | When to run |
|---|---|---|---|
| Contract validation | `python hooks/validate_contracts.py` | Devs, CI, Claude Stop hook | Before commit/PR and after contract changes |
| Secret scan | `python hooks/forbid_secrets.py` | Devs, CI, Claude Stop hook | Before commit/PR and after config/env edits |
| Coordinate provenance check | `python hooks/enforce_coordinate_provenance.py path/to/project.json` | Devs/QA/API owners | Before export flow testing and when point payload logic changes |
| Export boundary guard logic | Used by API via `hooks/pre_export.py` (`validate_exportable_project`) | Backend/API runtime | Automatically during `POST /projects/{id}/export` |

## 3) Automation currently wired

### Claude Code Stop hook (`.claude/settings.json`)

Runs automatically at stop:

```bash
python hooks/validate_contracts.py && python hooks/forbid_secrets.py
```

### API export automation

`services/api/app/main.py` calls `validate_exportable_project(...)` before image rendering in:

- `POST /projects/{project_id}/export`

This blocks invalid payloads at runtime.

## 4) Key commands (run from repo root unless noted)

### Start local backend

```bash
docker compose up -d
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../..
PYTHONPATH=. uvicorn services.api.app.main:app --reload
```

### Run backend tests

```bash
pytest services/api/tests/
pytest services/api/tests/test_export_guard.py
pytest services/api/tests/test_export_guard.py::test_rejects_missing_coordinates
```

### Start frontend

```bash
cd apps/web
npm install
npm run dev
```

### Build frontend

```bash
cd apps/web
npm run build
```

## 5) Recommended run order (developer workflow)

1. Make changes.
2. Run targeted tests for changed behavior.
3. Run `python hooks/validate_contracts.py`.
4. Run `python hooks/forbid_secrets.py`.
5. If export/points changed, run `python hooks/enforce_coordinate_provenance.py <payload.json>`.
6. Open/update PR.
