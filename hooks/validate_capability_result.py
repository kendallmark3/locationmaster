"""Deterministic validation hook for the capability-check workflow.

Checks that the workflow produced the required execution evidence.
No LLM is involved; all checks are pure Python.
"""


def validate_capability_result(evidence: dict) -> dict:
    """
    Validate the execution evidence from run_capability_check.

    Parameters
    ----------
    evidence : dict
        Keys set by the workflow:
        - skill_loaded (bool)
        - local_tool_executed (bool)
        - mcp_connected (bool)
        - mcp_fetch_called (bool)
        - external_result (dict, non-empty means at least one non-empty string value)

    Returns
    -------
    dict with ``passed`` (bool) and ``checks`` (list of {name, passed}).
    """
    checks = [
        {
            "name": "local-tool",
            "passed": bool(evidence.get("local_tool_executed")),
        },
        {
            "name": "mcp-connected",
            "passed": bool(evidence.get("mcp_connected")),
        },
        {
            "name": "mcp-fetch",
            "passed": bool(evidence.get("mcp_fetch_called")),
        },
        {
            "name": "external-result",
            "passed": _has_content(evidence.get("external_result")),
        },
    ]
    return {
        "passed": all(c["passed"] for c in checks),
        "checks": checks,
    }


def _has_content(value) -> bool:
    if not value:
        return False
    if isinstance(value, dict):
        return any(str(v).strip() for v in value.values())
    return bool(str(value).strip())
