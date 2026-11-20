#!/usr/bin/env python3
"""Print the next file name (or ID) in a numbered document series.

Usage:
  python3 next_number.py "<pattern>" <folder> [<folder> ...]

The pattern is a file name with {N} where the counter goes, e.g. "promo-plan-{N}",
"LST-2026-{N}", "FS-POS-{N}", "PRD-26-{N}". Every file under the folders (subfolders too) whose
name starts with the pattern counts, whatever follows the number ("LST-2026-0458_denim-pants.md"
matches "LST-2026-{N}"). Pass the folder where new documents are saved AND the examples folder:
the save folder is often empty on first use, and the series must go on from the examples
(promo-plan-03 -> promo-plan-04), never restart at 01.

Prints three lines and exits 0:
  next: promo-plan-04          (the highest number + 1, zero-padded like the highest one)
  after: examples/promo-plan-03.md
  width: 2
Exits 2 when no file matches (then the series starts at the pattern's first number; say so).
Skips skillforge-trial/ and hidden folders, so trial runs never move the counter.
Standard library only. Text in the files is never read, only their names.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP = {"skillforge-trial", "node_modules", "__pycache__"}


def matcher(pattern: str) -> re.Pattern[str]:
    if pattern.count("{N}") != 1:
        raise SystemExit('pattern needs exactly one {N}, e.g. "promo-plan-{N}"')
    before, after = pattern.split("{N}")
    # The number is the whole digit run, so "W{N}" reads W43 as 43, never as 4.
    tail = re.escape(after) if after else r"(?=$|[^0-9])"
    return re.compile(re.escape(before) + r"(\d+)" + tail, re.I)


def files(folders: list[str]) -> list[Path]:
    out: list[Path] = []
    for f in folders:
        root = Path(f)
        if root.is_file():
            out.append(root)
            continue
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            rel = p.relative_to(root).parts
            if any(part in SKIP or part.startswith(".") for part in rel[:-1]) or not p.is_file():
                continue
            out.append(p)
    return out


def next_name(pattern: str, folders: list[str]) -> tuple[str, Path | None, int]:
    rx = matcher(pattern)
    best: tuple[int, int, Path] | None = None
    for p in files(folders):
        m = rx.match(p.stem) or rx.match(p.name)
        if not m:
            continue
        n, width = int(m.group(1)), len(m.group(1))
        if best is None or n > best[0] or (n == best[0] and width > best[1]):
            best = (n, width, p)
    if best is None:
        return pattern.replace("{N}", "01"), None, 2
    n, width, p = best
    digits = str(n + 1).zfill(width) if width > len(str(n)) else str(n + 1)
    return pattern.replace("{N}", digits), p, width


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv[:1] in (["-h"], ["--help"]) else 1
    name, after, width = next_name(argv[0], argv[1:])
    if after is None:
        print(f"next: {name}")
        print("after: (no matching file in " + ", ".join(argv[1:]) + ")")
        return 2
    print(f"next: {name}")
    print(f"after: {after}")
    print(f"width: {width}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
