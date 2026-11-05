---
name: forge-mcp
description: "Generates a minimal, working MCP (Model Context Protocol) server that connects Claude to an external system such as an API, database or internal tool: Python server, requirements, README and registration, validated and started once before hand-over. Use after forge-intake has a confirmed spec of type mcp, or when the person has already agreed which system and operations to connect and says to build it. If the need is still vague, start forge-intake instead."
---

# Forge an MCP server

## Inputs

A confirmed `forge-spec.md` with type mcp: the system, the operations (read vs write), the auth
method (environment variable names only) and where it will run. Default to Python.

## Requirements to state up front

- Python **3.10 or newer** (the official MCP SDK 2.x needs it). Check with `python3 --version`;
  if it is older, say so and stop before generating.
- The `mcp` package is installed in a virtual environment next to the server, not globally.

## Steps

1. **Folder** `<name>/` where the person wants it (default: current folder; inside a plugin:
   `<plugin>/servers/<name>/`).
2. **Copy the template** [templates/python/server.template.py](templates/python/server.template.py)
   to `<name>/server.py` and [templates/python/requirements.txt](templates/python/requirements.txt)
   to `<name>/requirements.txt`. Replace every `{{SF: ...}}` blank; use one env prefix everywhere
   (e.g. `INVENTORY` → `INVENTORY_TOKEN`). Replace the example tool with one tool per operation.
   The template uses SDK 2.x (`from mcp.server.mcpserver import MCPServer`); keep `mcp.run()`.
3. **Design the tools:**
   - One clear verb per tool (`get_order`, `search_products`), typed parameters, and a docstring
     that says when to use it; Claude reads the docstring to choose tools.
   - Start **read-only**. Add write tools only if the spec asks; their docstring must say they change data.
   - Read secrets from environment variables and fail with a clear message if missing. Never hard-code one.
   - Raise `ToolError` (`from mcp.server.mcpserver.exceptions import ToolError`) for every failure you
     expect (missing env var, bad input, refused query, system not reachable). SDK 2.x hides the text of
     any other exception, so Claude would only see `Error executing tool <name>`.
   - Return small, structured results.
4. **Install and start it once** (you run these, don't hand them over):

   ```bash
   cd <name> && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
   .venv/bin/python -c "import runpy, asyncio; ns = runpy.run_path('server.py', run_name='check'); print([t.name for t in asyncio.run(ns['mcp'].list_tools())])"
   ```

   This lists the tools without touching the real system. If install fails (no network, old Python),
   say exactly what failed.
5. **Register it.** Standalone, for all of this person's projects:

   ```bash
   claude mcp add <name> -s user -e <PREFIX>_TOKEN=<value> -- /abs/path/<name>/.venv/bin/python /abs/path/<name>/server.py
   ```

   Run this only with the person's go-ahead, and let them type the token value themselves.
   Inside a plugin, use `.mcp.json` plus a sensitive `userConfig` entry so Claude Code asks each
   teammate for the token when they enable the plugin and stores it securely:

   ```jsonc
   // .claude-plugin/plugin.json (excerpt)
   "userConfig": {
     "inventory_token": { "type": "string", "title": "Inventory API token",
                          "description": "Read-only token", "sensitive": true, "required": true }
   }
   // .mcp.json
   { "mcpServers": { "inventory": {
       "command": "python3",
       "args": ["${CLAUDE_PLUGIN_ROOT}/servers/inventory/server.py"],
       "env": { "INVENTORY_TOKEN": "${user_config.inventory_token}" } } } }
   ```

   Tell teammates in the plugin README that the server needs Python 3.10+ and `pip install mcp`.
6. **README.md** in `<name>/`: what it connects to, the tools, the env vars, install and registration.
7. **Validate** and fix until it passes:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" mcp <name>
   ```

## Hand-over (in the person's language, short)

The tools it exposes, the one thing they must do (set the token), whether it's registered, and what
was checked. Remind them that write tools act on real data.

## Rules

- No secrets, tokens or customer personal data in any generated file.
- Don't call the real system during validation unless the person asks.
- Don't delete files unless the person asks. Git and SkillForge files: run `git commit`, `git push` or create a repository only when the person's own words ask for it ("확인까지 해 주세요" or "마무리해 주세요" is not that). Never edit, commit or push SkillForge's own files (this plugin's folder or the SkillForge repository); if SkillForge itself has a problem, say so in the hand-over.
