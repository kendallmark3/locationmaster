# Skill — Capability Check

## Purpose
Prove that the application can invoke a local deterministic tool, connect to an MCP server,
call an MCP tool to reach an external resource, and validate the whole chain—without
fabricating any step or bypassing the hook.

## Inputs
- workflow goal: "capability-check"
- local tool available: `get_application_status`
- MCP server: `mcp-server-fetch` (stdio, `python -m mcp_server_fetch`)
- MCP tool available: `fetch`
- allowed external URL: `https://official-joke-api.appspot.com/random_joke`

## Workflow
1. Execute `get_application_status` (deterministic local tool).
2. Spawn `mcp-server-fetch` subprocess via MCP stdio transport.
3. Discover MCP tools; confirm `fetch` is present.
4. Call MCP `fetch` with the allowed joke-API URL.
5. Normalize the response into `{setup, punchline, source, transport, tool}`.
6. Run `validate_capability_result` hook on the execution evidence.
7. Return structured result to the caller.

## Expected Output
```json
{
  "success": true,
  "workflow": "capability-check",
  "steps": [...],
  "result": {"setup": "...", "punchline": "..."}
}
```

## Validation Requirements
The hook must confirm all of: local-tool executed, mcp-connected, mcp-fetch called,
external-result non-empty.

## Failure Behavior
Each step that fails is recorded individually. Return `success: false` with the first
`failedStep` name and a human-readable `message`. Do not crash—always return a structured
response.

## Never
- bypass MCP to call the external API directly,
- expose arbitrary-URL fetching to callers,
- use an LLM to decide whether steps passed.
