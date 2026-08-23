# Phase 01 — Interactive Location Story

## Status

Steps 2–7 (intent capture through save/reload) are complete. Step 8's export *boundary*
(validation) is complete and working; the *artifact record* half (persisted, linked to
project/user ownership with a timestamp) is not — exports currently just download to the
browser. Step 1 (project shell) has no auth shell, since Cognito isn't wired up yet — see
`intent/INTENT.md` status note for the full detail on both gaps.

## Goal
Deliver a working vertical slice from authenticated project creation through saved editable map story and basic export.

## Required sequence
1. Project shell
2. Intent capture
3. Subject geocode
4. Interactive map
5. Story-point CRUD
6. Symbol/label editing
7. Save/reload
8. Export boundary + artifact record

## Non-goals
- demographic analysis
- automated commercial-property scoring
- advanced billing
- 4K print renderer
- PDF/PowerPoint generation
- multi-tenant enterprise administration
- autonomous research agents

## Completion evidence
A developer can run the app locally and complete the entire user journey without manually editing database state.
