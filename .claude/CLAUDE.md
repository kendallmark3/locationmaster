# Claude Code Project Instructions

Read `intent/INTENT.md` first.

## Operating rules

- Implement the smallest safe change that advances the current intent.
- Goal-oriented execution is the default.
- Do not create subagents unless a reason matches `agents/`.
- Treat `contracts/` as authoritative handoff schemas.
- Treat `skills/` as reusable organizational guidance.
- Treat runtime validation as mandatory even if Claude Code hooks also check it.
- Never invent geographic coordinates.
- Never place credentials in source.
- Do not broaden Phase 1 into demographics, billing, or advanced analytics.
- Before finishing a task:
  1. run contract validation,
  2. run tests for changed behavior,
  3. summarize changed files,
  4. state acceptance criteria satisfied,
  5. state remaining gaps.

## Context passing

Pass minimum sufficient context.
Prefer structured findings/deltas over raw chat history.
When passing external findings, retain source/provider identifiers needed for verification.
