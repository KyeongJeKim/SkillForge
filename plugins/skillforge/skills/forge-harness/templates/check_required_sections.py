#!/usr/bin/env python3
"""PostToolUse hook: warn when a written Markdown file lacks required sections.

Reads the hook event JSON from stdin. If the tool wrote a .md file whose name matches
TARGET_GLOB and the file is missing any REQUIRED_SECTIONS heading, prints a warning
on stderr and exits with code 2 so Claude sees the message and can fix the file.
Exits 0 (silently) in every other case, so it never blocks unrelated work.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys

# Edit these two values for your workflow.
TARGET_GLOB = "*spec*.md"
REQUIRED_SECTIONS = ["Overview", "Requirements", "Acceptance criteria"]


def missing_sections(text: str, required: list[str]) -> list[str]:
    """Return required headings that do not appear as Markdown headings in text."""
    headings = {
        m.group(1).strip().lower()
        for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, flags=re.MULTILINE)
    }
    return [s for s in required if s.lower() not in headings]


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not path or not fnmatch.fnmatch(os.path.basename(path), TARGET_GLOB):
        return 0
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return 0
    missing = missing_sections(text, REQUIRED_SECTIONS)
    if not missing:
        return 0
    print(
        f"{os.path.basename(path)} is missing required sections: {', '.join(missing)}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
