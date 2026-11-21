---
name: forge-mcp
description: "Generates a minimal, working MCP (Model Context Protocol) server that connects Claude to an external system such as an API, database or internal tool: Python server, requirements, README and registration, validated and started once before hand-over. Use after forge-intake has a confirmed spec of type mcp, or when the person has already agreed which system and operations to connect and says to build it. If the need is still vague, start forge-intake instead."
---

# Forge an MCP server

## Inputs

A confirmed `forge-spec.md` with type mcp: the system, the operations (read vs write), the auth
method (environment variable names only) and where it will run. Default to Python.

**Before you build:** if this conversation has no confirmed `forge-spec.md` (the person said yes to a
played-back summary), start `skillforge:forge-intake` first, even when the request looks complete.
It can be short when the examples answer most questions, but it still confirms what they settle,
asks about the hard parts and plays back the summary before anything is built.

## Requirements to state up front

- Python **3.10 or newer** (the official MCP SDK 2.x needs it). Check with `python3 --version`;
  if it is older, say so and stop before generating.
- The `mcp` package is installed in a virtual environment next to the server, not globally.
- **Windows:** the Python command may be `python` or `py -3` instead of `python3` (the Microsoft
  Store `python3` alias only opens the Store), and the virtual environment's Python is
  `.venv\Scripts\python.exe` (`.venv/Scripts/python.exe` in Git Bash) instead of `.venv/bin/python`.
  Use whichever answers `--version` with 3.10+, and use the Windows paths in every command below.

## Steps

1. **Folder** `<name>/` where the person wants it (default: current folder; inside a plugin:
   `<plugin>/servers/<name>/`).
2. **Copy the template** [templates/python/server.template.py](templates/python/server.template.py)
   to `<name>/server.py` and [templates/python/requirements.txt](templates/python/requirements.txt)
   to `<name>/requirements.txt`. Replace every `{{SF: ...}}` blank; use one env prefix everywhere
   (e.g. `INVENTORY` → `INVENTORY_TOKEN`). Replace the example tool with one tool per operation.
   The template uses SDK 2.x (`from mcp.server.mcpserver import MCPServer`); keep `mcp.run()`.
   Also copy [templates/python/corrections.md](templates/python/corrections.md) unchanged to
   `<name>/corrections.md`, and keep `_instructions()`: Claude Code reads the server's instructions
   at start, so the person's "다음부터 ~" rules saved there hold in every later session (the
   validator fails a server that uses corrections.md without the file). Fill its first sentence with
   what the server is for and which tool answers which question.
   If you also make a skill that uses this server (a how-to-ask or report skill), build it with
   `skillforge:forge-skill` so it gets its own `corrections.md` and correction step.
3. **Design the tools:**
   - One clear verb per tool (`get_order`, `search_products`), typed parameters, and a docstring
     that says when to use it; Claude reads the docstring to choose tools.
   - Start **read-only**. Add write tools only if the spec asks; their docstring must say they change data.
   - Read secrets from environment variables and fail with a clear message if missing. Never hard-code one.
   - Raise `ToolError` (`from mcp.server.mcpserver.exceptions import ToolError`) for every failure you
     expect (missing env var, bad input, refused query, system not reachable). SDK 2.x hides the text of
     any other exception, so Claude would only see `Error executing tool <name>`.
   - Return small, structured results.
   - **When the real response shape isn't known yet** (no API doc or sample), don't wait: keep every
     endpoint path and field name in one `ENDPOINTS` / `FIELDS` block at the top of `server.py`, mark
     each guessed value `# [확인 필요]`, and test the tools against a small local fake response. The
     hand-over lists exactly which lines to check once a real sample comes.
   - Cover the spec's 예외 처리 cases (no result, too many rows, system down) with a clear `ToolError`
     or an empty result that says why, and keep every 금지 item (e.g. no customer phone numbers) out
     of what the tools return.
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

   In the README, write it so it works wherever the folder sits: `cd` into `<name>/` first, then
   `-- "$(pwd)/.venv/bin/python" "$(pwd)/server.py"` (PowerShell: `"$PWD\.venv\Scripts\python.exe"`).
   Don't paste the build session's absolute path (it may be a temporary folder, and the person may
   move the folder), and never `/abs/path`.
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
   `.mcp.json` runs `python3` directly, so on Windows it works only if `python3 --version` works in a
   terminal (python.org installer with "Add python.exe to PATH", Store alias turned off). Say this
   in the README's Windows section, with `claude mcp add` and the `.venv\Scripts\python.exe` path as
   the fallback.
6. **README.md** in `<name>/`, in the person's language, written for the person first and the
   developer second (the person may not know what a terminal is):
   - **바로 쓰기** at the top: one line on what it connects to; what you already did (installed in
     this folder, registered or not, checked with sample data or not); the **one** thing left and who
     does it in plain words (e.g. "개발팀에서 API 주소와 토큰을 받아 오시면 됩니다"), with no command
     unless the person runs it themselves; and two or three example questions to ask Claude
     ("품절 임박 상품 보여 줘").
   - **개발 담당용** below it: the tools, the env vars (names only), the values marked `# [확인 필요]`
     in `server.py` and what to check, install and registration commands, and the Windows notes.
   - Commands must run as written: `cd` into the folder, then `"$(pwd)/..."` paths. Never leave
     `/abs/path`, `/절대경로/`, `<이 폴더 경로>` or `<owner>/<repo>` for the reader to fill; the
     validator fails them. A secret the person types themselves is the env var name in words
     ("`INVENTORY_TOKEN` 에 개발팀에서 받은 키"), not a value in the command. A value nobody knows yet is one
     `[확인 필요: 무엇 - 누가 가진 값]` line.
   - One line that corrections said with 다음부터/항상 are kept in `corrections.md` and apply from the
     next session.
7. **Validate** and fix until it passes:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" mcp <name>
   ```

## Hand-over (in the person's language, short)

What they can ask Claude now, the one thing left and who does it (e.g. the dev team sends the
address and token), whether it's registered, and what was checked, in the same plain words as the
README's 바로 쓰기 part; no commands for a person who doesn't use a terminal. Remind them that write tools act on real data. Add one line that if they say
"다음부터는 ~" about how results are shown, the server remembers it (`corrections.md`).

## Rules

- No secrets, tokens or customer personal data in any generated file.
- Don't call the real system during validation unless the person asks.
- Don't delete files unless the person asks. Git and SkillForge files: run `git commit`, `git push` or create a repository only when the person's own words ask for it ("확인까지 해 주세요" or "마무리해 주세요" is not that). Never edit, commit or push SkillForge's own files (this plugin's folder or the SkillForge repository); if SkillForge itself has a problem, say so in the hand-over.
