# ADR-001 — AI Interprets Intent; It Does Not Own Geographic Truth

## Decision
Use AI to normalize/summarize story intent and suggest searches/categories. Use deterministic provider-backed code for coordinates and place facts.

## Consequences
- Every geocoded point retains provenance.
- AI-generated coordinates are rejected.
- Reproducibility improves.
- Provider changes remain isolated behind an adapter.
