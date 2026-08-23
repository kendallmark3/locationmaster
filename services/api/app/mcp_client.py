"""Minimal async MCP client that spawns mcp-server-fetch and calls the fetch tool."""

import json
import sys
from typing import Any

from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from mcp.client.session import ClientSession

# Only the joke-API domain is allowed; the MCP fetch server can reach web URLs, so we
# restrict here to prevent the demo from becoming a generic open proxy.
ALLOWED_FETCH_URL = "https://official-joke-api.appspot.com/random_joke"

_MCP_SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "mcp_server_fetch"],
)


async def fetch_via_mcp(url: str = ALLOWED_FETCH_URL) -> dict[str, Any]:
    """
    Connect to mcp-server-fetch, discover tools, call 'fetch', and return the
    normalized joke result plus MCP evidence.

    Raises ValueError if the URL is not on the allowlist.
    Raises RuntimeError if the MCP server is unavailable or the fetch tool is missing.
    """
    if url != ALLOWED_FETCH_URL:
        raise ValueError(f"URL not allowlisted: {url}")

    async with stdio_client(_MCP_SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            if "fetch" not in tool_names:
                raise RuntimeError(f"fetch tool not found; available: {tool_names}")

            call_result = await session.call_tool("fetch", {"url": url})

            # Extract text content from MCP CallToolResult
            raw_text = ""
            for block in call_result.content:
                if hasattr(block, "text"):
                    raw_text += block.text

            joke = _parse_joke(raw_text)
            return {
                "joke": joke,
                "mcp_tools_discovered": tool_names,
                "raw": raw_text,
            }


def _parse_joke(text: str) -> dict[str, str]:
    """Parse the joke API response, which may be wrapped in markdown by mcp-server-fetch."""
    # mcp-server-fetch may return markdown; find the first JSON object in the text.
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            data = json.loads(text[start:end])
            return {
                "setup": data.get("setup", ""),
                "punchline": data.get("punchline", ""),
                "source": "official-joke-api",
                "transport": "mcp",
                "tool": "fetch",
            }
        except json.JSONDecodeError:
            pass
    return {
        "setup": text[:200] if text else "unavailable",
        "punchline": "",
        "source": "official-joke-api",
        "transport": "mcp",
        "tool": "fetch",
    }
