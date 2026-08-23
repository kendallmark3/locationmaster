"""Tests for the capability-check feature.

MCP calls are mocked for normal unit/integration tests. A real integration test that
actually spawns mcp-server-fetch is provided at the bottom and skipped by default unless
CAPABILITY_INTEGRATION=1 is set.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from hooks.validate_capability_result import validate_capability_result
from services.api.app.tools import get_application_status
from services.api.app.capability_workflow import run_capability_check


# ---------------------------------------------------------------------------
# Local tool
# ---------------------------------------------------------------------------

def test_get_application_status_returns_structure():
    result = get_application_status()
    assert result["application"] == "locationmaster"
    assert result["status"] == "ok"
    assert "timestamp" in result
    assert "version" in result


# ---------------------------------------------------------------------------
# Hook
# ---------------------------------------------------------------------------

def _good_evidence():
    return {
        "skill_loaded": True,
        "local_tool_executed": True,
        "mcp_connected": True,
        "mcp_fetch_called": True,
        "external_result": {"setup": "Why?", "punchline": "Because."},
    }


def test_hook_passes_valid_evidence():
    result = validate_capability_result(_good_evidence())
    assert result["passed"] is True
    assert all(c["passed"] for c in result["checks"])


def test_hook_rejects_missing_mcp():
    ev = _good_evidence()
    ev["mcp_connected"] = False
    result = validate_capability_result(ev)
    assert result["passed"] is False
    failed = [c for c in result["checks"] if not c["passed"]]
    assert any(c["name"] == "mcp-connected" for c in failed)


def test_hook_rejects_empty_external_result():
    ev = _good_evidence()
    ev["external_result"] = {}
    result = validate_capability_result(ev)
    assert result["passed"] is False


def test_hook_rejects_missing_local_tool():
    ev = _good_evidence()
    ev["local_tool_executed"] = False
    result = validate_capability_result(ev)
    assert result["passed"] is False


# ---------------------------------------------------------------------------
# Workflow — mocked MCP
# ---------------------------------------------------------------------------

_MOCK_JOKE = {
    "joke": {
        "setup": "Why did the developer go broke?",
        "punchline": "Because he used up all his cache.",
        "source": "official-joke-api",
        "transport": "mcp",
        "tool": "fetch",
    },
    "mcp_tools_discovered": ["fetch"],
    "raw": '{"setup":"Why did the developer go broke?","punchline":"Because he used up all his cache."}',
}


@pytest.mark.asyncio
async def test_workflow_success_with_mocked_mcp():
    with patch(
        "services.api.app.capability_workflow.fetch_via_mcp",
        new_callable=AsyncMock,
        return_value=_MOCK_JOKE,
    ):
        result = await run_capability_check()
    assert result["success"] is True
    assert result["workflow"] == "capability-check"
    statuses = {s["name"]: s["status"] for s in result["steps"]}
    assert statuses["skill"] == "passed"
    assert statuses["local-tool"] == "passed"
    assert statuses["mcp"] == "passed"
    assert statuses["external-data"] == "passed"
    assert statuses["validation-hook"] == "passed"
    assert result["result"]["setup"]
    assert result["hook"]["passed"] is True


@pytest.mark.asyncio
async def test_workflow_handles_mcp_failure():
    with patch(
        "services.api.app.capability_workflow.fetch_via_mcp",
        new_callable=AsyncMock,
        side_effect=RuntimeError("MCP server unavailable"),
    ):
        result = await run_capability_check()
    assert result["success"] is False
    assert result["failedStep"] == "mcp-connect"
    assert "MCP server unavailable" in result["message"]


# ---------------------------------------------------------------------------
# API endpoint
# ---------------------------------------------------------------------------

def test_capability_check_endpoint_success():
    from services.api.app.main import app
    client = TestClient(app)
    with patch(
        "services.api.app.capability_workflow.fetch_via_mcp",
        new_callable=AsyncMock,
        return_value=_MOCK_JOKE,
    ):
        r = client.post("/capability-check")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["result"]["setup"]


def test_capability_check_endpoint_mcp_failure():
    from services.api.app.main import app
    client = TestClient(app)
    with patch(
        "services.api.app.capability_workflow.fetch_via_mcp",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Fetch MCP server unavailable"),
    ):
        r = client.post("/capability-check")
    assert r.status_code == 200  # always 200; failure encoded in body
    body = r.json()
    assert body["success"] is False
    assert body["failedStep"] == "mcp-connect"


# ---------------------------------------------------------------------------
# Real integration test (skipped unless CAPABILITY_INTEGRATION=1)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    os.environ.get("CAPABILITY_INTEGRATION") != "1",
    reason="Set CAPABILITY_INTEGRATION=1 to run live MCP integration test",
)
@pytest.mark.asyncio
async def test_real_mcp_integration():
    """Spawn the real mcp-server-fetch subprocess and call the live joke API."""
    result = await run_capability_check()
    print("\n--- Real MCP integration result ---")
    for step in result.get("steps", []):
        marker = "✓" if step["status"] == "passed" else "✕"
        print(f"  {marker} {step['name']}: {step.get('detail', '')}")
    if result.get("result"):
        print(f"  Joke: {result['result']['setup']} / {result['result']['punchline']}")
    assert result["success"] is True, result.get("message")
