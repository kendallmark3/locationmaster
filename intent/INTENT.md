# Intent — Location Story Engine

## Intent / Goal

Build the smallest enterprise-ready Location Story Engine that turns a user's plain-language location intent into an editable map-based story.

The system must let a signed-in user:
- state what story they want to tell,
- identify and geocode a subject location,
- add any number of additional locations,
- assign/change labels, categories, and symbols,
- visually compose the story on a map,
- save and retrieve the story,
- generate a first-pass image artifact.

The application is intent-driven, but AI must not own deterministic geographic truth.

## Inputs / Context

Primary inputs:
- authenticated user identity,
- project name,
- free-text story intent,
- subject address/place search,
- manually added story points,
- selected symbols/categories,
- labels and presentation preferences.

External capabilities:
- Amazon Location Service for map/geocode/place lookup,
- PostgreSQL/PostGIS for structured/spatial persistence,
- S3 for exported artifacts,
- Cognito for authentication.

## Outputs

Required outputs:
1. persisted Location Story project,
2. normalized intent contract,
3. geocoded subject location,
4. editable story-point collection,
5. saved map viewport/style state,
6. first-pass image/preview artifact,
7. validation evidence for export/publish operations.

## Success Criteria

- User can sign in.
- User can create a Location Story from plain-language intent.
- Subject address resolves to verifiable coordinates.
- User can add unlimited practical story points for MVP purposes.
- Every point has coordinates, label, category, and symbol.
- User can edit/remove/hide points and change symbols/labels.
- Project reload recreates the saved composition.
- Export creates and stores an artifact linked to the project/user.
- Invalid or ungeocoded points cannot cross the export boundary.
- No LLM may fabricate coordinates or silently replace geocoder results.

## Constraints

- React/TypeScript frontend.
- FastAPI/Python backend.
- AWS deployment target.
- MapLibre for interactive mapping.
- Amazon Location Service is the default map/geocode provider.
- PostgreSQL/PostGIS is the system of record.
- Keep Phase 1 intentionally small.
- No demographic, employment, traffic, footfall, parcel, or paid third-party intelligence yet.
- No production billing engine yet.
- No autonomous multi-agent workflow unless a concrete need appears.

## Current State / Repo Assumptions

Greenfield repository.
Use this repo as the source of truth.
Prefer the smallest safe implementation.
Do not introduce frameworks or infrastructure that are not required by this intent.

## Architecture Rules

1. Goal-oriented implementation is the default.
2. Procedural orchestration is allowed for:
   - geocode calls,
   - persistence transactions,
   - export/publish validation,
   - external side effects,
   - retries and failure recovery.
3. Skills contain reusable "how we do this" knowledge.
4. Hooks enforce non-bypassable constraints.
5. Tools perform external actions.
6. Contracts are mandatory at system/agent boundaries.
7. Subagents require a stated reason.
8. Pass minimum sufficient context; never pass raw conversation history by default.
9. Deterministic code owns:
   - coordinates,
   - distance/math,
   - authorization,
   - persistence,
   - schema validation,
   - artifact storage.
10. AI may interpret intent, suggest categories, summarize story choices, and propose points to search for. AI may not invent geographic truth.

## Acceptance Criteria

### Authentication
- Cognito-backed identity supported in deployment architecture.
- API rejects unauthenticated protected requests.
- Projects are user-owned.

### Intent
- User can enter/edit free-text intent.
- Backend produces/stores a normalized `LocationStoryIntent`.
- Original user text is preserved.

### Map
- MapLibre renders a base map.
- Subject location can be found by place/address.
- Search result coordinates come from the configured geocoder.
- Clicking or searching can add story points.

### Story Points
- Add/edit/delete/hide points.
- Change:
  - label,
  - category,
  - symbol,
  - size,
  - notes.
- Coordinates are read-only unless explicitly replaced through a map/geocode action.
- User may place a custom point by clicking the map; reverse geocoding is optional but recommended.

### Persistence
- Create/read/update project.
- Save viewport, zoom, center, points, intent, and style.
- Reload is deterministic.

### Export
- Basic PNG/JPEG or static preview is sufficient for MVP.
- Export validates contracts first.
- Artifact is stored under project/user ownership.
- Export record includes timestamp and source project version.

## Validation / Evidence

Before marking Phase 1 complete, provide:
- unit tests for contract validation,
- API tests for project ownership,
- geocode adapter tests with mocked provider,
- CRUD tests for story points,
- export-boundary test proving invalid points are rejected,
- frontend smoke test for creating/editing a point,
- README run instructions,
- architecture diff summary.

## Stop Conditions

Stop and report instead of guessing when:
- required AWS credentials/configuration are absent for a live deployment,
- a provider response cannot be legally or technically stored,
- authentication cannot be verified,
- coordinate provenance is missing,
- the implementation would require broad architecture not justified by this phase.

## Delivery Expectations

Implement by vertical slice:
1. auth shell,
2. intent/project model,
3. map + geocode,
4. story points,
5. save/reload,
6. basic export,
7. deployment scaffold.

Do not build future intelligence features during Phase 1.
