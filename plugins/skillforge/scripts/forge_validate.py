#!/usr/bin/env python3
"""Validate artifacts produced by SkillForge before handing them over.

Usage:
    python3 forge_validate.py skill <skill-dir>
    python3 forge_validate.py plugin <plugin-dir>
    python3 forge_validate.py marketplace <repo-dir>
    python3 forge_validate.py mcp <server-dir-or-file>

Exit code 0 when there are no errors (warnings are allowed), 1 otherwise.
Standard library only, so it runs on any machine with Python 3.9+.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_NAME_MAX = 64
SKILL_DESC_MAX = 1024
SKILL_BODY_MAX_LINES = 500
RESERVED_PLUGIN_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
RESERVED_PLUGIN_NAMES = {"claude", "anthropic", "claude-code", "claude-mods"}
HOOK_EVENTS = {
    "SessionStart", "Setup", "UserPromptSubmit", "UserPromptExpansion", "PreToolUse",
    "PermissionRequest", "PermissionDenied", "PostToolUse", "PostToolUseFailure",
    "PostToolBatch", "Notification", "MessageDisplay", "SubagentStart", "SubagentStop",
    "TaskCreated", "TaskCompleted", "Stop", "StopFailure", "TeammateIdle",
    "InstructionsLoaded", "ConfigChange", "CwdChanged", "DirectoryAdded", "FileChanged",
    "WorktreeCreate", "WorktreeRemove", "PreCompact", "PostCompact", "PreModelSwitch",
    "PostModelSwitch", "Elicitation", "ElicitationResult", "SessionEnd",
}
HOOK_TYPES = {"command", "http", "mcp_tool", "prompt", "agent"}
PLACEHOLDER_RE = re.compile(r"\{\{\s*[A-Za-z][^}]*\}\}")


class Report:
    """Collects errors and warnings with the file they refer to."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: Path | str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: Path | str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors

    def print(self) -> None:
        for e in self.errors:
            print(f"ERROR   {e}")
        for w in self.warnings:
            print(f"WARNING {w}")
        status = "passed" if self.ok else "failed"
        extra = " with warnings" if self.ok and self.warnings else ""
        print(f"Validation {status}{extra} ({len(self.errors)} errors, {len(self.warnings)} warnings)")


# ---------------------------------------------------------------- frontmatter

def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Split a Markdown file into (frontmatter dict, body).

    Returns (None, text) when the file does not start with a '---' line.
    Uses PyYAML when installed; otherwise a small parser for flat 'key: value'
    pairs, quoted strings and '>' / '|' block scalars.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text
    raw = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:])
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return None, body
        return data, body
    except ImportError:
        return _parse_flat_yaml(raw), body
    except Exception:  # yaml.YAMLError and friends
        return None, body


def _parse_flat_yaml(raw: str) -> dict:
    data: dict = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2).strip()
        if value in (">", ">-", "|", "|-"):
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            joiner = " " if value.startswith(">") else "\n"
            data[key] = joiner.join(b for b in block if b).strip()
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        data[key] = value
        i += 1
    return data


# ---------------------------------------------------------------- checkers

def check_skill(skill_dir: Path, rep: Report) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        rep.error(skill_dir, "missing SKILL.md")
        return
    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if fm is None:
        rep.error(skill_md, "frontmatter must start on line 1 with '---' and be valid YAML")
        return
    name = str(fm.get("name") or skill_dir.name)
    if not NAME_RE.match(name):
        rep.error(skill_md, f"name '{name}' must be lowercase letters, digits and hyphens")
    if len(name) > SKILL_NAME_MAX:
        rep.error(skill_md, f"name is longer than {SKILL_NAME_MAX} characters")
    if fm.get("name") and fm["name"] != skill_dir.name:
        rep.warn(skill_md, f"name '{fm['name']}' differs from folder '{skill_dir.name}'")
    desc = str(fm.get("description") or "").strip()
    if not desc:
        rep.error(skill_md, "description is missing; Claude uses it to decide when to load the skill")
    else:
        if len(desc) > SKILL_DESC_MAX:
            rep.error(skill_md, f"description is {len(desc)} characters (max {SKILL_DESC_MAX})")
        if "<" in desc or ">" in desc:
            rep.error(skill_md, "description must not contain '<' or '>'")
        if "use when" not in desc.lower() and "use for" not in desc.lower():
            rep.warn(skill_md, "description has no 'Use when ...' clause; natural-language triggering may be weak")
    if PLACEHOLDER_RE.search(text):
        rep.error(skill_md, "unfilled {{placeholder}} left in SKILL.md")
    n_lines = len(body.splitlines())
    if n_lines > SKILL_BODY_MAX_LINES:
        rep.warn(skill_md, f"body has {n_lines} lines; move detail into supporting files (aim < {SKILL_BODY_MAX_LINES})")
    if not body.strip():
        rep.error(skill_md, "body is empty")
    for target in re.findall(r"\]\(([^)#\s]+)\)", body):
        if "://" in target or target.startswith("${"):
            continue
        if not (skill_dir / target).exists():
            rep.error(skill_md, f"linked file '{target}' does not exist")


def check_agent(agent_md: Path, rep: Report) -> None:
    fm, body = parse_frontmatter(agent_md.read_text(encoding="utf-8"))
    if fm is None:
        rep.error(agent_md, "frontmatter must start on line 1 with '---' and be valid YAML")
        return
    name = str(fm.get("name") or "")
    if not name:
        rep.error(agent_md, "agent 'name' is required")
    elif ":" in name or len(name) > 256:
        rep.error(agent_md, "agent 'name' must not contain ':' and must be at most 256 characters")
    if not str(fm.get("description") or "").strip():
        rep.error(agent_md, "agent 'description' is required")
    for ignored in ("hooks", "mcpServers", "permissionMode"):
        if ignored in fm:
            rep.warn(agent_md, f"'{ignored}' is ignored for plugin subagents")
    if not body.strip():
        rep.error(agent_md, "agent body (system prompt) is empty")


def check_hooks(hooks_json: Path, rep: Report) -> None:
    data = _load_json(hooks_json, rep)
    if data is None:
        return
    events = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(events, dict):
        rep.error(hooks_json, "must have a top-level 'hooks' object mapping events to matcher groups")
        return
    for event, groups in events.items():
        if event not in HOOK_EVENTS:
            rep.error(hooks_json, f"unknown hook event '{event}'")
        if not isinstance(groups, list):
            rep.error(hooks_json, f"'{event}' must be a list of matcher groups")
            continue
        for g in groups:
            handlers = g.get("hooks") if isinstance(g, dict) else None
            if not isinstance(handlers, list) or not handlers:
                rep.error(hooks_json, f"'{event}' group needs a non-empty 'hooks' list")
                continue
            for h in handlers:
                htype = h.get("type") if isinstance(h, dict) else None
                if htype not in HOOK_TYPES:
                    rep.error(hooks_json, f"'{event}' handler has invalid type '{htype}'")
                elif htype == "command" and not h.get("command"):
                    rep.error(hooks_json, f"'{event}' command handler needs 'command'")


def check_mcp_json(mcp_json: Path, rep: Report) -> None:
    data = _load_json(mcp_json, rep)
    if data is None:
        return
    servers = data.get("mcpServers", data) if isinstance(data, dict) else None
    if not isinstance(servers, dict) or not servers:
        rep.error(mcp_json, "must map server names to configs (under 'mcpServers')")
        return
    for name, cfg in servers.items():
        if not isinstance(cfg, dict) or not (cfg.get("command") or cfg.get("url")):
            rep.error(mcp_json, f"server '{name}' needs 'command' (stdio) or 'url' (http)")


def check_plugin(plugin_dir: Path, rep: Report) -> None:
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    if manifest.is_file():
        data = _load_json(manifest, rep)
        if isinstance(data, dict):
            name = str(data.get("name") or "")
            if not name:
                rep.error(manifest, "'name' is required")
            else:
                _check_plugin_name(name, manifest, rep)
            for field in ("version", "description", "author"):
                if field not in data:
                    rep.warn(manifest, f"'{field}' is recommended")
            author = data.get("author")
            if author is not None and not (isinstance(author, dict) and author.get("name")):
                rep.error(manifest, "'author' must be an object with 'name'")
            homepage = data.get("homepage")
            if homepage and not re.match(r"^https?://", str(homepage)):
                rep.error(manifest, "'homepage' must be a URL")
            if PLACEHOLDER_RE.search(manifest.read_text(encoding="utf-8")):
                rep.error(manifest, "unfilled {{placeholder}} left in plugin.json")
    else:
        rep.warn(plugin_dir, "no .claude-plugin/plugin.json; name will come from the folder or marketplace")
    extra = [p.name for p in (plugin_dir / ".claude-plugin").glob("*") if p.name != "plugin.json"] \
        if (plugin_dir / ".claude-plugin").is_dir() else []
    for name in extra:
        if name != "marketplace.json":
            rep.error(plugin_dir / ".claude-plugin", f"'{name}' should be at the plugin root, not in .claude-plugin/")
    if (plugin_dir / "CLAUDE.md").exists():
        rep.warn(plugin_dir / "CLAUDE.md", "a plugin-root CLAUDE.md is not loaded; put instructions in a skill")

    skills_dir = plugin_dir / "skills"
    skill_dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []
    for sd in skill_dirs:
        check_skill(sd, rep)
    agents_dir = plugin_dir / "agents"
    for agent_md in sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []:
        check_agent(agent_md, rep)
    if (plugin_dir / "hooks" / "hooks.json").is_file():
        check_hooks(plugin_dir / "hooks" / "hooks.json", rep)
    if (plugin_dir / ".mcp.json").is_file():
        check_mcp_json(plugin_dir / ".mcp.json", rep)
    components = [skills_dir, agents_dir, plugin_dir / "commands", plugin_dir / "hooks", plugin_dir / ".mcp.json"]
    if not any(c.exists() for c in components):
        rep.error(plugin_dir, "plugin has no components (skills/, agents/, commands/, hooks/ or .mcp.json)")


def check_marketplace(repo_dir: Path, rep: Report) -> None:
    mp = repo_dir / ".claude-plugin" / "marketplace.json"
    if not mp.is_file():
        rep.error(repo_dir, "missing .claude-plugin/marketplace.json")
        return
    data = _load_json(mp, rep)
    if not isinstance(data, dict):
        return
    name = str(data.get("name") or "")
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", name) or ".." in name:
        rep.error(mp, "'name' must start with a letter or digit and use letters, digits, '.', '_' or '-'")
    owner = data.get("owner")
    if not (isinstance(owner, dict) and owner.get("name")):
        rep.error(mp, "'owner.name' is required")
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        rep.error(mp, "'plugins' must be a non-empty list")
        return
    seen: set[str] = set()
    for entry in plugins:
        pname = str(entry.get("name") or "") if isinstance(entry, dict) else ""
        if not pname:
            rep.error(mp, "each plugin entry needs 'name'")
            continue
        if pname in seen:
            rep.error(mp, f"duplicate plugin name '{pname}'")
        seen.add(pname)
        source = entry.get("source")
        if isinstance(source, str):
            if not source.startswith("./") or ".." in source:
                rep.error(mp, f"'{pname}' relative source must start with './' and not contain '..'")
                continue
            pdir = (repo_dir / source).resolve()
            if not pdir.is_dir():
                rep.error(mp, f"'{pname}' source '{source}' does not exist")
                continue
            check_plugin(pdir, rep)
            manifest = pdir / ".claude-plugin" / "plugin.json"
            if manifest.is_file():
                mdata = _load_json(manifest, Report())
                if isinstance(mdata, dict) and mdata.get("name") and mdata["name"] != pname:
                    rep.error(mp, f"entry '{pname}' does not match plugin.json name '{mdata['name']}'")
        elif isinstance(source, dict):
            if not source.get("source"):
                rep.error(mp, f"'{pname}' source object needs a 'source' type")
        else:
            rep.error(mp, f"'{pname}' needs a 'source'")


def check_mcp_server(target: Path, rep: Report) -> None:
    server = target / "server.py" if target.is_dir() else target
    if not server.is_file():
        rep.error(target, "no server.py found")
        return
    text = server.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(server))
    except SyntaxError as exc:
        rep.error(server, f"syntax error: {exc}")
        return
    if PLACEHOLDER_RE.search(text):
        rep.error(server, "unfilled {{placeholder}} left in server.py")
    uses_sdk = "mcp.server" in text and ("MCPServer" in text or "FastMCP" in text)
    if not uses_sdk:
        rep.error(server, "does not create an MCP server (expected mcp.server.mcpserver.MCPServer, or FastMCP on mcp<2)")
    tools = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any("tool" in ast.unparse(d) for d in node.decorator_list)
    ] if hasattr(ast, "unparse") else []
    if hasattr(ast, "unparse") and not tools:
        rep.error(server, "defines no tools (expected functions decorated with @mcp.tool())")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in tools:
            if not ast.get_docstring(node):
                rep.warn(server, f"tool '{node.name}' has no docstring; Claude uses it to choose tools")
    if re.search(r"(api[_-]?key|token|secret|password)\s*=\s*['\"][^'\"]{8,}['\"]", text, re.I):
        rep.error(server, "looks like a hard-coded secret; read it from an environment variable")
    readme = server.parent / "README.md"
    if not readme.is_file():
        rep.warn(server.parent, "no README.md with tools, env vars and the registration command")


# ---------------------------------------------------------------- helpers

def _check_plugin_name(name: str, where: Path, rep: Report) -> None:
    if not NAME_RE.match(name):
        rep.error(where, f"plugin name '{name}' must be kebab-case")
    if name in RESERVED_PLUGIN_NAMES or name.startswith(RESERVED_PLUGIN_PREFIXES):
        rep.error(where, f"plugin name '{name}' is reserved")


def _load_json(path: Path, rep: Report):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.error(path, f"invalid JSON: {exc}")
        return None


CHECKS = {
    "skill": check_skill,
    "plugin": check_plugin,
    "marketplace": check_marketplace,
    "mcp": check_mcp_server,
}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in CHECKS:
        print(__doc__)
        return 1
    target = Path(argv[2]).expanduser()
    if not target.exists():
        print(f"ERROR   {target}: does not exist")
        return 1
    rep = Report()
    CHECKS[argv[1]](target, rep)
    rep.print()
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
