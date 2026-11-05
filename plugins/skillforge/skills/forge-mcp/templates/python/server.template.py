"""{{SF: server-name}}: MCP server that connects Claude to {{SF: system}}.

Requires Python 3.10+ and the official MCP SDK 2.x:
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

Register with Claude Code (all projects for this user):
    claude mcp add {{SF: server-name}} -s user -e {{SF: ENV_PREFIX}}_TOKEN=... -- /absolute/path/.venv/bin/python /absolute/path/server.py
"""

from __future__ import annotations

import os

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("{{SF: server-name}}")

TOKEN_ENV = "{{SF: ENV_PREFIX}}_TOKEN"


def _token() -> str:
    """Read the API token from the environment; never hard-code it."""
    token = os.environ.get(TOKEN_ENV)
    if not token:
        raise RuntimeError(f"Set the {TOKEN_ENV} environment variable first.")
    return token


@mcp.tool()
def get_item(item_id: str) -> dict:
    """Look up one item in {{SF: system}} by its ID. Read-only.

    Use when the user asks about a specific item and gives its ID.
    """
    _token()  # Replace with a real API call that uses the token.
    return {"item_id": item_id, "status": "example", "source": "{{SF: system}}"}


if __name__ == "__main__":
    mcp.run()
