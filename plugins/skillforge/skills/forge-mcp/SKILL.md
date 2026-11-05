---
name: forge-mcp
description: Generates a minimal, working MCP (Model Context Protocol) server skeleton that connects Claude to an external system such as an API, database or internal tool, with a README and the registration command, validated before handing over. Use when a confirmed SkillForge spec has type mcp, or someone asks to connect Claude to a system, e.g. "connect Claude to our system", "make an MCP server", "MCP 만들어 줘", "우리 DB랑 연결하고 싶어".
---

# Forge an MCP server

## Inputs

A confirmed `forge-spec.md` with `Type: mcp`, covering: the system, the operations (read vs
write), the auth method (environment variable names only) and the language. Default to
Python unless the person asks for another language.

## Steps

1. **Create the folder** `<name>/` where the person wants it (default: current directory).
2. **Copy the Python template** from [templates/python/](templates/python/):
   - `server.py` → `<name>/server.py`
   - `requirements.txt` → `<name>/requirements.txt`
   Replace every `{{...}}` placeholder and the example tool with one tool per operation in the spec.
   The template targets the official Python SDK 2.x (`from mcp.server.mcpserver import MCPServer`).
   If the person must stay on `mcp<2`, use `from mcp.server.fastmcp import FastMCP` instead.
3. **Design the tools:**
   - One clear verb per tool (`get_order`, `search_products`), typed parameters, and a
     docstring that says when to use it; Claude reads the docstring to choose tools.
   - Start **read-only**. Add write tools only if the spec asks, and make each write tool's
     docstring say it changes data.
   - Read secrets from environment variables (`os.environ["..."]`) and fail with a clear message
     if they are missing. Never hard-code a secret.
   - Return small, structured results (dicts/lists of strings and numbers), not huge dumps.
4. **Write `<name>/README.md`** with: what it connects to, the tools, the environment variables,
   install (`python3 -m pip install -r requirements.txt`) and registration:

   ```bash
   claude mcp add <name> -e API_TOKEN=... -- python3 /absolute/path/to/<name>/server.py
   ```

   If the server will ship inside a plugin, add it to that plugin's `.mcp.json` instead:

   ```json
   {
     "mcpServers": {
       "<name>": {
         "command": "python3",
         "args": ["${CLAUDE_PLUGIN_ROOT}/servers/<name>/server.py"]
       }
     }
   }
   ```

5. **Validate:**

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" mcp <name>
   ```

   This compiles the server and checks it defines an MCP server with at least one tool. If the
   `mcp` package is installed, also start the server once with a quick import check
   (`python3 -c "import runpy; runpy.run_path('<name>/server.py', run_name='check')"`).
   Say plainly which checks ran and which did not.

## Hand-over

Tell the person: the tools it exposes, the environment variables to set, the one command to
register it, and what was validated. Remind them that write tools act on real data.

## Rules

- No secrets, tokens or customer personal data in any generated file.
- Don't call the real system during validation unless the person asks.
