#!/usr/bin/env python3
"""Package a generated skill as a ZIP for the Claude app (claude.ai / Claude Desktop chat).

Usage:
    python3 package_skill.py <skill-dir> [output.zip]

What it does:
  1. Validates the skill with forge_validate.py and stops on errors.
  2. Copies the folder into a ZIP whose top level is the skill folder (<name>/SKILL.md ...),
     the layout the app's Skills upload expects.
  3. Rewrites ${CLAUDE_SKILL_DIR} (a Claude Code-only placeholder) to "<skill-folder>" and adds
     one line telling Claude what that means, so bundled scripts still resolve in the app.
  4. Leaves out trial output, caches, git data and OS clutter.

It refuses skills that use ${CLAUDE_PLUGIN_ROOT} or !`command` injection, which only work in
Claude Code. Standard library only. Prints the ZIP path and size.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKIP_DIRS = {".git", "__pycache__", "skillforge-trial", ".venv", "venv", "node_modules"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".sh", ".csv", ".html"}
PLACEHOLDER = "<skill-folder>"
NOTE = (f"> In this app, `{PLACEHOLDER}` means the folder this SKILL.md was loaded from. "
        "If that folder can't be written, skip any step that writes into it.\n\n")


def _validator():
    spec = importlib.util.spec_from_file_location("forge_validate", HERE / "forge_validate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _with_note(skill_md: str) -> str:
    """Insert NOTE right after the frontmatter block."""
    m = re.match(r"^---\r?\n.*?\r?\n---\r?\n", skill_md, flags=re.DOTALL)
    if not m:
        return NOTE + skill_md
    return skill_md[: m.end()] + "\n" + NOTE + skill_md[m.end():].lstrip("\n")


def package(skill_dir: Path, out: Path | None = None) -> Path:
    skill_dir = skill_dir.resolve()
    fv = _validator()
    rep = fv.Report()
    fv.check_skill(skill_dir, rep)
    if not rep.ok:
        rep.print()
        raise SystemExit("Fix the errors above before packaging.")

    problems = []
    files = []
    uses_dir = False
    for path in sorted(skill_dir.rglob("*")):
        rel = path.relative_to(skill_dir)
        if any(part in SKIP_DIRS for part in rel.parts) or path.name in SKIP_FILES or path.is_dir():
            continue
        files.append((path, rel))
        if path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="replace")
            uses_dir = uses_dir or "${CLAUDE_SKILL_DIR}" in text
            if "${CLAUDE_PLUGIN_ROOT}" in text:
                problems.append(f"{rel}: uses ${{CLAUDE_PLUGIN_ROOT}}, which exists only in Claude Code plugins")
            if path.suffix.lower() == ".md" and re.search(r"!`[^`]+`", fv._strip_code(text)):
                problems.append(f"{rel}: uses !`command` injection, which runs only in Claude Code")
    if problems:
        raise SystemExit("Can't package for the Claude app:\n  " + "\n  ".join(problems))

    out = (out or Path.cwd() / f"{skill_dir.name}.zip").resolve()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path, rel in files:
            arc = f"{skill_dir.name}/{rel.as_posix()}"
            if path.suffix.lower() in TEXT_SUFFIXES:
                text = path.read_text(encoding="utf-8", errors="replace")
                text = text.replace("${CLAUDE_SKILL_DIR}", PLACEHOLDER)
                if rel.as_posix() == "SKILL.md" and uses_dir:
                    text = _with_note(text)
                z.writestr(arc, text)
            else:
                z.write(path, arc)
    return out


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) not in (2, 3):
        print(__doc__)
        return 1
    out = package(Path(argv[1]).expanduser(), Path(argv[2]).expanduser() if len(argv) == 3 else None)
    print(f"Packaged {out} ({out.stat().st_size / 1024:.1f} KB)")
    print("Upload it in the Claude app: Settings > Capabilities > Skills (code execution must be on).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
