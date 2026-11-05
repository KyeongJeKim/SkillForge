"""{{server-name}}: MCP server that connects Claude to {{system}}.

Run directly for local testing:
    python3 server.py

Register with Claude Code:
    claude mcp add {{server-name}} -e {{SYSTEM}}_TOKEN=... -- python3 /absolute/path/server.py
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("{{server-name}}")


def _token() -> str:
    """Read the API token from the environment; never hard-code it."""
    token = os.environ.get("{{SYSTEM}}_TOKEN")
    if not token:
        raise RuntimeError("Set the {{SYSTEM}}_TOKEN environment variable first.")
    return token


@mcp.tool()
def get_item(item_id: str) -> dict:
    """Look up one item in {{system}} by its ID. Read-only.

    Use when the user asks about a specific item and gives its ID.
    """
    _token()  # Replace with a real API call that uses the token.
    return {"item_id": item_id, "status": "example", "source": "{{system}}"}


if __name__ == "__main__":
    mcp.run()
