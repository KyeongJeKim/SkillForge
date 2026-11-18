"""{{SF: server-name}}: MCP server that connects Claude to {{SF: system}}.

Requires Python 3.10+ and the official MCP SDK 2.x:
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

Register with Claude Code (all projects for this user):
    claude mcp add {{SF: server-name}} -s user -e {{SF: ENV_PREFIX}}_TOKEN=... -- /absolute/path/.venv/bin/python /absolute/path/server.py
"""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

# The person's standing rules for this server ("다음부터 ~"). Claude Code reads the server's
# instructions when the server starts, so a rule saved here applies in every later session.
CORRECTIONS = Path(__file__).resolve().parent / "corrections.md"


def _instructions() -> str:
    """How Claude should use this server, plus every rule the person added to corrections.md."""
    text = (
        "{{SF: one or two sentences: what this server is for and which tool to call for which question}}\n"
        "When the person corrects how results from this server are shown and says it should hold next "
        "time (다음부터, 항상, 앞으로), apply it now and add one line '- YYYY-MM-DD: <the rule in their "
        f"words>' under '## 규칙' in {CORRECTIONS} (replace '(아직 없음)'). Write the rule only, never "
        "tokens, passwords or customer data. If that file can't be written, say in one line that "
        "SkillForge can make the rule permanent (이 MCP 개선해 줘)."
    )
    try:
        rules = CORRECTIONS.read_text(encoding="utf-8").split("## 규칙", 1)[1].strip()
    except (OSError, IndexError):
        rules = ""
    if rules and rules != "(아직 없음)":
        text += "\nRules the person gave earlier (follow every one):\n" + rules
    return text


mcp = MCPServer("{{SF: server-name}}", instructions=_instructions())

TOKEN_ENV = "{{SF: ENV_PREFIX}}_TOKEN"


def _token() -> str:
    """Read the API token from the environment; never hard-code it."""
    token = os.environ.get(TOKEN_ENV)
    if not token:
        # ToolError: Claude sees this message. Any other exception reaches Claude only as
        # "Error executing tool <name>", so it can't tell the person what to fix.
        raise ToolError(f"Set the {TOKEN_ENV} environment variable first.")
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
