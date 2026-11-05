#!/usr/bin/env python3
"""Validate artifacts produced by SkillForge before handing them over.

Usage:
    python3 forge_validate.py skill <skill-dir>
    python3 forge_validate.py plugin <plugin-dir>
    python3 forge_validate.py marketplace <repo-dir>
    python3 forge_validate.py mcp <server-dir-or-file>

Exit code 0 when there are no errors (warnings are allowed), 1 otherwise.
Standard library only (PyYAML is used when installed), Python 3.9+.

When the `claude` CLI is available, also run `claude plugin validate <dir>`;
it is the authority on what Claude Code accepts. This script adds checks the
CLI does not do: unfilled SkillForge placeholders, broken links, missing hook
and server files, hard-coded secrets and weak trigger descriptions.
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
# SkillForge templates mark every blank as {{SF: ...}}; other {{...}} (merge fields) are allowed.
PLACEHOLDER_RE = re.compile(r"\{\{\s*SF\s*:[^}]*\}\}")
# Trigger clauses that tell Claude when to load a skill, in English or Korean.
TRIGGER_HINTS = ("use when", "use after", "use for", "use this when", "use it when", "할 때", "때 사용", "경우", "사용하세요", "사용합니다")
SECRET_RE = re.compile(
    r"(api[_-]?key|token|secret|password|passwd)\s*[=:]\s*['\"][^'\"\s$]{8,}['\"]"
    r"|['\"]Bearer\s+[A-Za-z0-9._\-]{12,}['\"]"
    r"|['\"](sk|pk|ghp|xox[bp])[-_][A-Za-z0-9_\-]{12,}['\"]",
    re.I,
)
PLUGIN_ROOT_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"'`]+)")


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

class Frontmatter:
    """Parsed frontmatter: data (dict or None when unusable), body, and parser notes."""

    def __init__(self, data: dict | None, body: str, notes: list[str] | None = None) -> None:
        self.data = data
        self.body = body
        self.notes = notes or []


def parse_frontmatter(text: str) -> Frontmatter:
    """Split a Markdown file into frontmatter and body.

    data is None when the file does not start with '---', the block is not
    closed, or the YAML is unusable. Strict PyYAML errors that a lenient
    parser can still read (e.g. an unquoted colon inside a description) are
    reported as notes, not as a missing frontmatter.
    """
    text = text.lstrip("﻿")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return Frontmatter(None, text)
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return Frontmatter(None, text, ["frontmatter has no closing '---'"])
    raw = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:])
    flat, flat_problem = _parse_flat_yaml(raw)
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None
    if yaml is not None:
        try:
            data = yaml.safe_load(raw) or {}
        except Exception as exc:  # yaml.YAMLError
            if flat_problem or not flat:
                return Frontmatter(None, body, [f"YAML does not parse: {str(exc).splitlines()[0]}"])
            return Frontmatter(flat, body, ["strict YAML parsers reject this frontmatter; "
                                            "wrap the description in double quotes"])
        if not isinstance(data, dict):
            return Frontmatter(None, body, ["frontmatter is not a mapping"])
        return Frontmatter(data, body)
    if flat_problem:
        return Frontmatter(None, body, [flat_problem])
    return Frontmatter(flat, body)


def _parse_flat_yaml(raw: str) -> tuple[dict, str]:
    """Lenient parser for flat 'key: value' frontmatter.

    Supports quoted values, '>' / '|' block scalars and simple '- item' lists.
    Returns (data, problem); problem is non-empty when a value cannot be valid YAML,
    e.g. it starts with a quote that closes before the end of the value.
    """
    data: dict = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+):(?:\s+(.*)|\s*)$", line)
        if not m:
            i += 1
            continue
        key, value = m.group(1), (m.group(2) or "").strip()
        if value in (">", ">-", "|", "|-", ""):
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            items = [b for b in block if b]
            if value == "" and items and all(b.startswith("- ") for b in items):
                data[key] = [b[2:].strip() for b in items]
            else:
                joiner = "\n" if value.startswith("|") else " "
                data[key] = joiner.join(items).strip()
            continue
        if value[:1] in ("'", '"'):
            q = value[0]
            if len(value) < 2 or not value.endswith(q):
                return data, f"'{key}' starts with a quote that does not close at the end of the line"
            value = value[1:-1]
        else:
            value = re.sub(r"\s+#.*$", "", value)  # YAML comment
        data[key] = value
        i += 1
    return data, ""


def _strip_code(md: str) -> str:
    """Remove fenced code blocks and inline code so their contents are not checked as links."""
    md = re.sub(r"^(```|~~~).*?^\1\s*$", "", md, flags=re.S | re.M)
    return re.sub(r"`[^`\n]*`", "", md)


def _check_links(md: str, base: Path, where: Path, rep: Report) -> None:
    for target in re.findall(r"\]\(\s*<?([^)>\s]+)>?(?:\s+\"[^\"]*\")?\s*\)", _strip_code(md)):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith(("#", "${")):
            continue  # URL, mailto:, in-page anchor, or a runtime variable
        path = target.split("#", 1)[0]
        if path and not (base / path).exists():
            rep.error(where, f"linked file '{path}' does not exist")


# ---------------------------------------------------------------- checkers

def check_skill(skill_dir: Path, rep: Report) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        rep.error(skill_dir, "missing SKILL.md")
        return
    text = skill_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    for note in fm.notes:
        (rep.warn if fm.data is not None else rep.error)(skill_md, note)
    if fm.data is None:
        if not fm.notes:
            rep.error(skill_md, "frontmatter must start on line 1 with '---'")
        return
    data, body = fm.data, fm.body
    name = str(data.get("name") or skill_dir.name)
    if not NAME_RE.match(name):
        rep.error(skill_md, f"name '{name}' must be lowercase letters, digits and hyphens")
    if len(name) > SKILL_NAME_MAX:
        rep.error(skill_md, f"name is longer than {SKILL_NAME_MAX} characters")
    if data.get("name") and data["name"] != skill_dir.name:
        rep.warn(skill_md, f"name '{data['name']}' differs from folder '{skill_dir.name}'")
    desc = data.get("description")
    if desc is None or (isinstance(desc, str) and not desc.strip()):
        rep.error(skill_md, "description is missing; Claude uses it to decide when to load the skill")
    elif not isinstance(desc, str):
        rep.error(skill_md, f"description must be a string, not {type(desc).__name__}")
    else:
        if len(desc) > SKILL_DESC_MAX:
            rep.error(skill_md, f"description is {len(desc)} characters (max {SKILL_DESC_MAX})")
        if "<" in desc or ">" in desc:
            rep.error(skill_md, "description must not contain '<' or '>'")
        if not any(h in desc.lower() for h in TRIGGER_HINTS):
            rep.warn(skill_md, "description says what the skill does but not when to use it "
                               "('Use when ...' / '... 할 때 사용'); natural-language triggering may be weak")
    # Placeholders quoted inside code are documentation, not blanks.
    if PLACEHOLDER_RE.search(_strip_code(text)):
        rep.error(skill_md, "unfilled {{SF: ...}} placeholder left in SKILL.md")
    n_lines = len(body.splitlines())
    if n_lines > SKILL_BODY_MAX_LINES:
        rep.warn(skill_md, f"body has {n_lines} lines; move detail into supporting files (aim < {SKILL_BODY_MAX_LINES})")
    if not body.strip():
        rep.error(skill_md, "body is empty")
    _check_links(body, skill_dir, skill_md, rep)
    for f in skill_dir.rglob("*"):
        # Files named *.template.* are SkillForge's own blanks and are expected to hold placeholders.
        if f.is_file() and f.suffix in {".md", ".py", ".json", ".txt", ".html"} and f != skill_md \
                and ".template." not in f.name:
            try:
                if PLACEHOLDER_RE.search(f.read_text(encoding="utf-8")):
                    rep.error(f, "unfilled {{SF: ...}} placeholder")
            except UnicodeDecodeError:
                pass


def check_agent(agent_md: Path, rep: Report) -> None:
    text = agent_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    for note in fm.notes:
        (rep.warn if fm.data is not None else rep.error)(agent_md, note)
    if fm.data is None:
        if not fm.notes:
            rep.error(agent_md, "frontmatter must start on line 1 with '---'")
        return
    name = str(fm.data.get("name") or "")
    if not name:
        rep.error(agent_md, "agent 'name' is required")
    elif ":" in name or len(name) > 256:
        rep.error(agent_md, "agent 'name' must not contain ':' and must be at most 256 characters")
    desc = fm.data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        rep.error(agent_md, "agent 'description' is required and must be a string")
    for ignored in ("hooks", "mcpServers", "permissionMode"):
        if ignored in fm.data:
            rep.warn(agent_md, f"'{ignored}' is ignored for plugin subagents")
    if not fm.body.strip():
        rep.error(agent_md, "agent body (system prompt) is empty")
    if PLACEHOLDER_RE.search(text):
        rep.error(agent_md, "unfilled {{SF: ...}} placeholder left in agent file")


def _check_plugin_paths(values: list[str], plugin_dir: Path | None, where: Path, rep: Report) -> None:
    """Every ${CLAUDE_PLUGIN_ROOT}/... referenced by a hook or server must exist in the plugin."""
    if plugin_dir is None:
        return
    for v in values:
        for rel in PLUGIN_ROOT_RE.findall(str(v)):
            if not (plugin_dir / rel).exists():
                rep.error(where, f"'${{CLAUDE_PLUGIN_ROOT}}/{rel}' does not exist in the plugin")


def check_hooks(hooks_json: Path, rep: Report, plugin_dir: Path | None = None) -> None:
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
                    continue
                if htype != "command":
                    continue
                cmd, args = h.get("command"), h.get("args") or []
                if not cmd:
                    rep.error(hooks_json, f"'{event}' command handler needs 'command'")
                    continue
                if "${user_config." in str(cmd) and not args:
                    rep.error(hooks_json, f"'{event}': shell-form commands can't use ${{user_config.*}}; "
                                          "use exec form (command + args) or $CLAUDE_PLUGIN_OPTION_<KEY>")
                _check_plugin_paths([cmd, *args], plugin_dir, hooks_json, rep)


def check_mcp_json(mcp_json: Path, rep: Report, plugin_dir: Path | None = None) -> None:
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
            continue
        _check_plugin_paths([cfg.get("command", ""), *(cfg.get("args") or [])], plugin_dir, mcp_json, rep)
        for k, v in (cfg.get("env") or {}).items():
            if isinstance(v, str) and v and "${" not in v and re.search(r"token|key|secret|password", k, re.I):
                rep.error(mcp_json, f"server '{name}' env '{k}' looks like a hard-coded secret; "
                                    "use ${user_config.<key>} with a sensitive userConfig entry")


def check_plugin(plugin_dir: Path, rep: Report) -> None:
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    data = None
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
                rep.error(manifest, "unfilled {{SF: ...}} placeholder left in plugin.json")
            _check_user_config(data.get("userConfig"), manifest, rep)
            inline = data.get("mcpServers")
            if isinstance(inline, dict):
                tmp = Report()
                fake = plugin_dir / ".claude-plugin" / "plugin.json#mcpServers"
                for n, cfg in inline.items():
                    if isinstance(cfg, dict):
                        _check_plugin_paths([cfg.get("command", ""), *(cfg.get("args") or [])],
                                            plugin_dir, fake, tmp)
                rep.errors += tmp.errors
    else:
        rep.warn(plugin_dir, "no .claude-plugin/plugin.json; name will come from the folder or marketplace")
    mdir = plugin_dir / ".claude-plugin"
    for p in (mdir.iterdir() if mdir.is_dir() else []):
        if p.name not in ("plugin.json", "marketplace.json", "icon.png"):
            rep.error(mdir, f"'{p.name}' should be at the plugin root, not in .claude-plugin/")
    if (plugin_dir / "CLAUDE.md").exists():
        rep.warn(plugin_dir / "CLAUDE.md", "a plugin-root CLAUDE.md is not loaded; put instructions in a skill")

    skills_dir = plugin_dir / "skills"
    for sd in sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []:
        if (sd / "SKILL.md").is_file():
            check_skill(sd, rep)
        else:
            rep.warn(sd, "folder under skills/ has no SKILL.md and will be ignored")
    agents_dir = plugin_dir / "agents"
    for agent_md in sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []:
        check_agent(agent_md, rep)
    if (plugin_dir / "hooks" / "hooks.json").is_file():
        check_hooks(plugin_dir / "hooks" / "hooks.json", rep, plugin_dir)
    if (plugin_dir / ".mcp.json").is_file():
        check_mcp_json(plugin_dir / ".mcp.json", rep, plugin_dir)
    components = [skills_dir, agents_dir, plugin_dir / "commands", plugin_dir / "hooks", plugin_dir / ".mcp.json"]
    has_inline = isinstance(data, dict) and any(k in data for k in ("mcpServers", "hooks", "skills", "agents", "commands"))
    if not any(c.exists() for c in components) and not has_inline:
        rep.error(plugin_dir, "plugin has no components (skills/, agents/, commands/, hooks/ or .mcp.json)")


def _check_user_config(cfg, where: Path, rep: Report) -> None:
    if cfg is None:
        return
    if not isinstance(cfg, dict):
        rep.error(where, "'userConfig' must be an object")
        return
    allowed = {"type", "title", "description", "required", "default", "options", "multiple", "sensitive", "min", "max"}
    for key, spec in cfg.items():
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            rep.error(where, f"userConfig key '{key}' must be letters, digits and '_' and not start with a digit")
        if not isinstance(spec, dict):
            rep.error(where, f"userConfig '{key}' must be an object")
            continue
        for req in ("type", "title", "description"):
            if req not in spec:
                rep.error(where, f"userConfig '{key}' needs '{req}'")
        if spec.get("type") not in (None, "string", "number", "boolean", "directory", "file"):
            rep.error(where, f"userConfig '{key}' has invalid type '{spec.get('type')}'")
        for extra in set(spec) - allowed:
            rep.error(where, f"userConfig '{key}' has unknown field '{extra}'")


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
    if PLACEHOLDER_RE.search(mp.read_text(encoding="utf-8")):
        rep.error(mp, "unfilled {{SF: ...}} placeholder left in marketplace.json")
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
        rep.error(server, "unfilled {{SF: ...}} placeholder left in server.py")
    if not ("mcp.server" in text and ("MCPServer" in text or "FastMCP" in text)):
        rep.error(server, "does not create an MCP server (expected mcp.server.mcpserver.MCPServer, or FastMCP on mcp<2)")
    tools = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any("tool" in ast.unparse(d) for d in node.decorator_list)
    ]
    if not tools:
        rep.error(server, "defines no tools (expected functions decorated with @mcp.tool())")
    for node in tools:
        if not ast.get_docstring(node):
            rep.warn(server, f"tool '{node.name}' has no docstring; Claude uses it to choose tools")
    has_run = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
        for n in ast.walk(tree)
    )
    if not has_run:
        rep.error(server, "never calls .run(); the server would exit immediately (add mcp.run() under __main__)")
    if SECRET_RE.search(text):
        rep.error(server, "looks like a hard-coded secret; read it from an environment variable")
    req = server.parent / "requirements.txt"
    if not req.is_file():
        rep.warn(server.parent, "no requirements.txt (expected 'mcp>=2,<3')")
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
        return json.loads(path.read_text(encoding="utf-8-sig"))
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
