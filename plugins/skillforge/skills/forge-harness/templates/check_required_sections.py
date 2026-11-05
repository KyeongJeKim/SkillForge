#!/usr/bin/env python3
"""PostToolUse hook: warn when a written Markdown document lacks required sections.

Reads the hook event JSON from stdin. If the tool wrote a .md file whose name
matches one of TARGET_GLOBS and the file lacks a heading for any entry in
REQUIRED_SECTIONS, prints the missing sections on stderr and exits with code 2
so Claude sees the message and fixes the file. Exits 0 silently otherwise, so
it never blocks unrelated work.

Matching is forgiving: heading numbers and punctuation are ignored
("## 4. 기능 상세" matches "기능 상세"), case is ignored, and a heading that
starts with the section name also matches ("Acceptance criteria (AC)").
An entry can list alternatives with "|", e.g. "요구사항|Requirements".

Fill both lists from the team's style guide when generating a harness.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys

# Edit these for your workflow (from the learned style guide).
TARGET_GLOBS = ["*spec*.md", "*명세*.md", "FS-*.md"]
REQUIRED_SECTIONS = ["개요|Overview", "요구사항|기능 상세|Requirements", "예외 처리|Exceptions"]

_NUMBERING = re.compile(r"^(?:(?:\d+|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+|[IVX]+(?=[.)]))[.)\]:\-]*\s*)+")


def normalize(heading: str) -> str:
    """Lowercase a heading and drop leading numbering such as '4.', '1)', '2.3', 'Ⅱ.'."""
    h = re.sub(r"\s+", " ", heading.strip().strip("#").strip())
    h = _NUMBERING.sub("", h)
    return h.strip(" .:-").lower()


def headings(text: str) -> list[str]:
    return [normalize(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, flags=re.MULTILINE)]


def missing_sections(text: str, required: list[str]) -> list[str]:
    """Return the required entries that no heading in text matches."""
    found = headings(text)
    missing = []
    for entry in required:
        options = [normalize(o) for o in entry.split("|") if o.strip()]
        if not any(h == o or h.startswith(o) for h in found for o in options):
            missing.append(entry.split("|")[0])
    return missing


def main() -> int:
    # Read bytes and decode as UTF-8 ourselves: on Windows the default console code page
    # (e.g. cp949) would garble Korean file names in the event JSON.
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(event, dict):
        return 0
    path = (event.get("tool_input") or {}).get("file_path") or ""
    name = os.path.basename(path)
    if not path.endswith(".md") or not any(fnmatch.fnmatch(name, g) for g in TARGET_GLOBS):
        return 0
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return 0
    missing = missing_sections(text, REQUIRED_SECTIONS)
    if not missing:
        return 0
    print(f"{name}: 필수 섹션이 빠졌습니다 / missing required sections: {', '.join(missing)}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
