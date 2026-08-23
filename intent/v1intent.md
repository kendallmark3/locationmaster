Yes. For V1, I’d use the official Fetch MCP reference server. It’s MIT-licensed, free, requires no API key, and can run locally with uvx mcp-server-fetch. That gives us a genuine MCP tool call without introducing another SaaS dependency. 

The important distinction I put into the intent: don’t merely configure MCP for Claude Code. Make the application demonstrate the capability so you can actually see Skill → workflow/tool orchestration → MCP call → Hook validation → UI evidence. For a visible demo, Fetch MCP can retrieve a random joke from the free Official Joke API, which requires no signup or key. 

INTENT.md

Intent / Goal

Extend the existing application with a small, working agentic capability demonstration that proves the remaining architecture concepts without turning the application into an overengineered multi-agent system.

V1 must demonstrate:

Intent → Skill → Tool Workflow → MCP Tool → Hook → Visible Result

The implementation should reuse the existing application architecture and make the smallest safe change necessary.

Do not redesign the application.

Do not introduce unnecessary infrastructure.

Do not create agent theater.

⸻

Primary Outcome

Add a small System / AI Capabilities panel to the existing UI that lets the user run a demonstration workflow.

Example:

Run Capability Check

When executed, the application performs a simple workflow and visibly reports something similar to:

✓ Skill loaded: capability-check
✓ Local tool executed
✓ MCP server connected: fetch
✓ MCP tool executed: fetch
✓ External data received
✓ Validation hook passed
Joke of the Day:
Why did the developer go broke?
Because he used up all his cache.

The exact UI presentation may follow the existing design system.

The important requirement is that these are real executions, not hard-coded status messages.

⸻

Required Architecture

Use the minimum sufficient architecture.

Preferred pattern:

User
  ↓
React UI
  ↓
Application API / Backend
  ↓
Capability Workflow
  ↓
Skill
  ↓
Tool(s)
  ↓
MCP Client
  ↓
Fetch MCP Server
  ↓
Public Joke API
  ↓
Result
  ↓
Validation Hook
  ↓
UI

The workflow/orchestrator should remain extremely small.

A full workflow engine is NOT required.

A simple routine/function/class is acceptable.

⸻

1. Add One Skill

Create one reusable application Skill.

Suggested name:

capability-check

Purpose:

Define how this application performs a basic external capability check.

The Skill should describe:

* what the workflow is trying to accomplish
* what tools are available
* what MCP capability is available
* expected output
* validation requirements
* failure behavior

Example conceptual responsibility:

Capability Check Skill
Goal:
Prove that the application can invoke local tools and MCP tools
and return validated results to the UI.

Follow any Skill structure already present in the repository.

If the repository already has a Skills directory or convention, reuse it.

Do NOT invent a second skill framework.

⸻

2. Add One Tool

Add one very small local tool.

Example:

get_application_status

Possible result:

{
  "application": "locationmaster",
  "status": "ok",
  "timestamp": "...",
  "version": "..."
}

The purpose is simply to prove that the workflow can invoke an application-owned tool.

Do not call an LLM to determine application status.

This should be deterministic code.

⸻

3. Add One MCP Server

Use the official Model Context Protocol Fetch MCP Server.

Preferred implementation:

mcp-server-fetch

Preferred local launch:

uvx mcp-server-fetch

Alternative if the existing environment makes this easier:

pip install mcp-server-fetch
python -m mcp_server_fetch

Do not introduce a paid MCP provider.

No API key should be required for V1.

⸻

4. MCP Client Integration

The APPLICATION must act as an MCP client.

This requirement is important.

Do NOT satisfy this intent merely by adding MCP configuration for Claude Code.

Claude Code may use MCP during development, but the purpose of this feature is to demonstrate MCP capability inside the running application.

Implement the smallest MCP client appropriate for the existing backend technology.

The application should:

connect
   ↓
discover/list MCP tools
   ↓
find "fetch"
   ↓
call "fetch"
   ↓
receive response
   ↓
normalize result

Use the official MCP SDK appropriate for the repository language where practical.

Do not manually reinvent the MCP protocol unless absolutely necessary.

⸻

5. External Demo

Use Fetch MCP to retrieve a free public resource.

For V1 use:

https://official-joke-api.appspot.com/random_joke

No API key is required.

The MCP server must perform the external fetch.

Do NOT bypass MCP by having application code directly call the Joke API.

The purpose is to prove:

Application
→ MCP Client
→ MCP Server
→ External Resource

Normalize the result into a simple structure such as:

{
  "setup": "...",
  "punchline": "...",
  "source": "official-joke-api",
  "transport": "mcp",
  "tool": "fetch"
}

If parsing this specific endpoint proves unreliable through Fetch MCP, another free, no-key public endpoint may be substituted.

Preserve the architectural requirement that the external request goes through MCP.

⸻

6. Add One Hook

Create one deterministic validation Hook.

Suggested name:

validate-capability-result

Run it after the workflow has completed and before the final response is returned to the UI.

The Hook should validate that the workflow produced the required evidence.

Minimum checks:

local tool executed
MCP connection succeeded
MCP fetch tool executed
external result returned
result is non-empty

Example conceptual result:

{
  "passed": true,
  "checks": [
    {
      "name": "local-tool",
      "passed": true
    },
    {
      "name": "mcp-connected",
      "passed": true
    },
    {
      "name": "mcp-fetch",
      "passed": true
    },
    {
      "name": "external-result",
      "passed": true
    }
  ]
}

The Hook must be deterministic.

Do NOT use an LLM to decide whether these checks passed.

⸻

7. Workflow / Orchestrator

Create the smallest reasonable workflow.

Suggested conceptual implementation:

runCapabilityCheck()

Sequence:

1. Load capability-check Skill
2. Execute get_application_status tool
3. Connect to Fetch MCP server
4. Discover MCP tools
5. Execute MCP "fetch"
6. Retrieve joke/external content
7. Normalize results
8. Execute validation Hook
9. Return structured result

This workflow may be implemented as a normal service/function.

Do NOT introduce:

* Temporal
* Airflow
* Kafka
* LangGraph
* CrewAI
* multi-agent frameworks
* workflow databases
* distributed orchestration

unless the repository already depends on one and reuse is clearly simpler.

⸻

8. Structured Workflow Result

Return one structured contract from the backend.

Example:

{
  "success": true,
  "workflow": "capability-check",
  "steps": [
    {
      "name": "skill",
      "status": "passed",
      "detail": "capability-check"
    },
    {
      "name": "local-tool",
      "status": "passed",
      "detail": "get_application_status"
    },
    {
      "name": "mcp",
      "status": "passed",
      "detail": "fetch"
    },
    {
      "name": "external-data",
      "status": "passed"
    },
    {
      "name": "validation-hook",
      "status": "passed"
    }
  ],
  "result": {
    "setup": "...",
    "punchline": "..."
  }
}

Use the repository’s existing API response conventions when available.

This is an information contract between backend and UI.

Keep it small.

⸻

9. UI

Add a small capability demonstration section to the existing application.

Do not make it the primary purpose of the application.

Suggested location:

System Capabilities
or
AI / Integration Status

Include a button:

Run Capability Check

While running:

Running capability workflow...

Then display the actual workflow steps.

Example:

✓ Skill: capability-check
✓ Tool: application status
✓ MCP server: fetch
✓ MCP tool: fetch
✓ External request
✓ Validation hook

Then display the resulting joke or external message.

Example:

Joke of the Day
[setup]
[punchline]

Include failure states.

Example:

✕ MCP server unavailable
Capability check completed with errors.

Do not fake successful checks.

⸻

10. Optional LLM Orchestration

An LLM is NOT required for this V1 workflow.

Prefer deterministic orchestration.

If the repository already has Anthropic integration and using it materially improves the demonstration, an LLM may decide WHICH available tool to call.

However:

LLM reasoning is optional.
Tool execution is required.
MCP execution is required.
Hook validation is required.

Do not add an LLM merely so the architecture can be called “agentic.”

⸻

Context Engineering

Each component receives only the context it needs.

Skill receives

workflow goal
available tool names
available MCP capability
expected output

Local tool receives

Only its required parameters.

MCP call receives

URL
fetch arguments

Validation Hook receives

workflow execution evidence
normalized result

Do not pass entire conversation histories or giant application state objects between components.

⸻

Failure Behavior

Individual failures should be visible.

Examples:

Skill loaded
Local tool passed
MCP connection failed
Validation failed

Do not crash the entire React application because the MCP process is unavailable.

Return a useful structured error.

Example:

{
  "success": false,
  "failedStep": "mcp-connect",
  "message": "Fetch MCP server unavailable."
}

⸻

Development Experience

Provide a simple way to start the MCP dependency locally.

Prefer an existing development script if one exists.

Potential examples:

npm run mcp

or:

make mcp

or documented:

uvx mcp-server-fetch

If practical, have the backend manage the MCP child process itself.

Choose whichever solution results in the least complexity for this repository.

⸻

Security Constraints

The Fetch MCP server can retrieve web resources.

Do not expose a generic unrestricted arbitrary-URL endpoint directly to public users.

For this V1 capability check, restrict the workflow to an allowlisted endpoint/domain.

Example:

official-joke-api.appspot.com

Do not allow the browser to submit arbitrary internal/private URLs to the MCP fetch tool.

Do not expose:

localhost
127.0.0.1
private network ranges
cloud metadata endpoints
internal service addresses

through the demo feature.

⸻

Repository Rules

Before implementing:

1. Inspect the repository.
2. Identify the existing frontend/backend architecture.
3. Identify existing Skill and Hook conventions.
4. Identify existing API/service patterns.
5. Reuse them.
6. Make the smallest safe change.

Do NOT replace working architecture.

Do NOT restructure unrelated code.

Do NOT create duplicate frameworks.

Do NOT rename unrelated components.

⸻

Expected Files

Exact paths should follow the repository’s existing conventions.

Conceptually this may result in something similar to:

skills/
  capability-check.md
hooks/
  validate-capability-result.*
services/
  capabilityWorkflow.*
  mcpClient.*
tools/
  applicationStatus.*
frontend/
  components/
    CapabilityCheck.*
tests/
  capabilityWorkflow.*

These paths are examples only.

Claude must inspect the repository before determining actual placement.

⸻

Testing

Add focused tests.

At minimum test:

local tool returns structured status
workflow handles successful MCP execution
workflow handles MCP connection failure
hook passes valid execution evidence
hook rejects incomplete execution evidence
backend returns structured contract
UI handles running state
UI handles success
UI handles failure

Mock the external MCP call for normal automated tests where appropriate.

Also provide one real integration test or manual verification command demonstrating the actual MCP server.

⸻

Acceptance Criteria

The feature is complete when:

* Existing application still works.
* Existing Skill remains functional.
* Existing Hook remains functional.
* One new capability Skill exists.
* One deterministic local tool can execute.
* Fetch MCP server is configured.
* Running application connects to MCP.
* Application discovers or invokes the MCP fetch tool.
* External data is retrieved through MCP.
* Application does not bypass MCP for the external demo.
* Validation Hook executes.
* Hook results are visible.
* Workflow steps are visible in the UI.
* Joke/external result is visible in the UI.
* MCP failures are handled gracefully.
* No paid service is required.
* Tests pass.
* Existing map/location functionality is unaffected.

⸻

Validation Evidence

Before declaring completion, provide:

FILES CHANGED
ARCHITECTURE USED
SKILL CREATED/USED
HOOK CREATED/USED
LOCAL TOOL EXECUTED
MCP SERVER
- name
- startup method
MCP TOOL DISCOVERED
MCP TOOL EXECUTED
EXTERNAL RESOURCE CALLED
TEST RESULTS
MANUAL VERIFICATION
KNOWN LIMITATIONS

Include actual command output or test evidence where practical.

Do not report a capability as working without executing it.

⸻

Stop Conditions

Stop and report rather than expanding architecture if:

* the repository already contains an equivalent implementation
* MCP integration requires replacing the current backend
* the proposed change would materially destabilize the mapping features
* a paid service becomes necessary
* credentials other than optional existing project credentials become mandatory

Do not compensate by creating a larger architecture.

⸻

Explicit Non-Goals

V1 does NOT require:

* autonomous multi-agent execution
* persistent agent memory
* multiple MCP servers
* production MCP registry
* dynamic MCP discovery
* arbitrary external URL access
* distributed workflow orchestration
* workflow persistence
* Kafka
* vector database
* authentication redesign
* another LLM provider
* paid APIs

⸻

Architectural Principle

Use:

Skill
    = reusable knowledge about how this capability works
Tool
    = deterministic application action
MCP
    = governed external capability
Workflow
    = minimal ordering of required actions
Hook
    = deterministic non-bypassable validation
UI
    = visible evidence that the architecture actually ran

The purpose of this V1 is not architecture for architecture’s sake.

The purpose is to make these concepts real, executable, and visible inside the application.

Build the smallest version that proves the pattern.

That gives you the whole chain without contaminating the app with a big framework. One nuance I deliberately locked down: Fetch MCP can reach web URLs, and its own documentation warns about access to local/internal addresses, so the demo should allowlist the joke endpoint rather than expose arbitrary URL fetching from the browser. 

I also like this because once Claude gets it running, you’ve essentially completed the architecture showcase: intent, skill, hook, deterministic tool, workflow/orchestration, structured contract, MCP, and UI evidence—each doing a different job instead of just being folders with names.
