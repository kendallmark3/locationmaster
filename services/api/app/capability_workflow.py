"""Minimal capability-check workflow.

Sequence:
  1. Load capability-check skill (resolved from filesystem).
  2. Execute get_application_status local tool.
  3. Connect to Fetch MCP server, discover tools, call fetch.
  4. Normalize external result.
  5. Run validate_capability_result hook.
  6. Return structured contract.
"""

from pathlib import Path
from typing import Any

from .tools import get_application_status
from .mcp_client import fetch_via_mcp, ALLOWED_FETCH_URL

_SKILL_PATH = (
    Path(__file__).resolve().parents[3] / "skills" / "capability-check" / "SKILL.md"
)


def _load_skill() -> str:
    """Return the raw skill definition text."""
    return _SKILL_PATH.read_text()


async def run_capability_check() -> dict[str, Any]:
    """Execute the full capability-check workflow and return a structured result."""
    steps: list[dict] = []
    evidence: dict[str, Any] = {}

    # Step 1 — skill
    try:
        _load_skill()
        steps.append({"name": "skill", "status": "passed", "detail": "capability-check"})
        evidence["skill_loaded"] = True
    except Exception as exc:
        steps.append({"name": "skill", "status": "failed", "detail": str(exc)})
        evidence["skill_loaded"] = False
        return _failure("skill-load", str(exc), steps)

    # Step 2 — local tool
    try:
        app_status = get_application_status()
        steps.append({"name": "local-tool", "status": "passed", "detail": "get_application_status"})
        evidence["local_tool_executed"] = True
        evidence["app_status"] = app_status
    except Exception as exc:
        steps.append({"name": "local-tool", "status": "failed", "detail": str(exc)})
        evidence["local_tool_executed"] = False
        return _failure("local-tool", str(exc), steps)

    # Step 3 + 4 — MCP connect, discover, fetch, normalize
    mcp_result: dict[str, Any] = {}
    try:
        mcp_result = await fetch_via_mcp(ALLOWED_FETCH_URL)
        steps.append({"name": "mcp", "status": "passed", "detail": "fetch"})
        evidence["mcp_connected"] = True
        evidence["mcp_fetch_called"] = True
        evidence["external_result"] = mcp_result.get("joke", {})
    except Exception as exc:
        steps.append({"name": "mcp", "status": "failed", "detail": str(exc)})
        evidence["mcp_connected"] = False
        evidence["mcp_fetch_called"] = False
        evidence["external_result"] = {}
        return _failure("mcp-connect", str(exc), steps)

    # Check external result non-empty
    joke = mcp_result.get("joke", {})
    if not joke.get("setup") and not joke.get("punchline"):
        steps.append({"name": "external-data", "status": "failed", "detail": "empty response"})
        evidence["external_result"] = {}
        return _failure("external-data", "MCP fetch returned empty content", steps)
    steps.append({"name": "external-data", "status": "passed"})

    # Step 5 — validation hook
    from hooks.validate_capability_result import validate_capability_result
    hook_result = validate_capability_result(evidence)
    if hook_result["passed"]:
        steps.append({"name": "validation-hook", "status": "passed"})
    else:
        steps.append({"name": "validation-hook", "status": "failed", "detail": hook_result})
        return _failure("validation-hook", "Hook validation failed", steps, hook_result)

    return {
        "success": True,
        "workflow": "capability-check",
        "steps": steps,
        "result": joke,
        "hook": hook_result,
    }


def _failure(failed_step: str, message: str, steps: list, hook: dict | None = None) -> dict:
    result: dict[str, Any] = {
        "success": False,
        "workflow": "capability-check",
        "failedStep": failed_step,
        "message": message,
        "steps": steps,
    }
    if hook is not None:
        result["hook"] = hook
    return result
