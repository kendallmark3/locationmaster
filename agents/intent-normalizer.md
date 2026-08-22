# Subagent — Intent Normalizer

## Why this subagent exists
Isolation: normalize free-text intent into a small structured contract without carrying the full main conversation.

## Input contract
- rawIntent
- projectName
- subject query if already known
- approved category vocabulary

## Output contract
`LocationStoryIntent`

## Context policy
Pass only the current intent text and approved vocabulary.
Do not pass repo history, unrelated conversation, credentials, or map-provider responses.

## Stop
Return validation failure rather than inventing missing subject coordinates.
