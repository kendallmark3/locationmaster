# Skill — Geocoding and Coordinate Provenance

## Purpose
Define how location text becomes trusted coordinates.

## Rules
- All searched addresses/places must resolve through the configured geocoder tool.
- Persist provider provenance with coordinates.
- A user map click may create coordinates directly with `coordinateSource=map_click`.
- LLM output is never a coordinate authority.
- Ambiguous results must be presented for user selection.
- If a provider's license restricts storage, follow provider storage rules and retain only permitted fields.
- Do not silently move an existing point because a label changed.
