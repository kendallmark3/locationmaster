# Skill — Location Story Builder

## Purpose
Reusable organizational knowledge for turning a user's business story into a map composition without fabricating geography.

## Inputs
- raw user intent
- subject location query/result
- current story-point set
- available approved symbol catalog
- current viewport

## Behavior
1. Preserve the user's original intent.
2. Extract a short set of story goals.
3. Suggest categories only when useful.
4. Translate category suggestions into search/tool requests, never coordinates.
5. Prefer a small useful story over visual clutter.
6. Keep subject location visually primary.
7. Explain proposed additions as suggestions, not facts, until tool-confirmed.
8. Return structured output matching the LocationStoryIntent contract.

## Never
- invent lat/lon,
- claim a place exists without provider evidence,
- mutate persisted state directly,
- bypass export validation,
- infer private/sensitive facts about occupants from location alone.
