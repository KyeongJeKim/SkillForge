"""Checks that the Markdown docs render cleanly on GitHub.

- every relative link and image (Markdown or HTML) points to a file that exists;
- every #anchor points to a heading that exists (GitHub's heading slugs);
- code blocks in the docs people read on GitHub (README.md, docs/) have no line
  so long that a phone has to scroll sideways a lot (CJK counts double).

Run from the repo root:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unicodedata
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "fixtures"}          # fixtures are synthetic team documents
READER_DOCS = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
MAX_CODE_COLS = 100

FENCE = re.compile(r"^(```|~~~)[^\n]*\n(.*?)^\1", re.S | re.M)


def md_files() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.md") if not SKIP_DIRS & set(p.relative_to(ROOT).parts))


def strip_code(text: str) -> str:
    text = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return re.sub(r"`[^`\n]*`", "", text)


def github_slug(heading: str) -> str:
    h = re.sub(r"<[^>]+>", "", heading)
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", h).replace("`", "")
    h = h.strip().lower()
    h = "".join(c for c in h if c in " -_" or unicodedata.category(c)[0] in "LN")
    return h.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    out, seen = set(), {}
    for line in strip_code(text).splitlines():
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            s = github_slug(m.group(2))
            n = seen.get(s, 0)
            out.add(s if n == 0 else f"{s}-{n}")
            seen[s] = n + 1
    out.update(re.findall(r'<a\s+(?:name|id)="([^"]+)"', text))
    return out


def links(text: str) -> list[str]:
    body = strip_code(text)
    found = re.findall(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)", body)
    found += re.findall(r'(?:href|src)="([^"]+)"', body)
    return found


def display_width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


class Links(unittest.TestCase):
    def test_relative_links_and_anchors_resolve(self):
        problems = []
        for md in md_files():
            for link in links(md.read_text(encoding="utf-8")):
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", link):
                    continue  # http:, https:, mailto: ...
                path, _, frag = link.partition("#")
                target = (md.parent / unquote(path)).resolve() if path else md
                rel = md.relative_to(ROOT)
                if path and not target.exists():
                    problems.append(f"{rel}: link to missing file {link}")
                    continue
                if frag and target.suffix == ".md" and unquote(frag) not in anchors(target):
                    problems.append(f"{rel}: link to missing heading {link}")
        self.assertEqual(problems, [])

    def test_slug_matches_github(self):
        self.assertEqual(github_slug("🚀 시작하기"), "-시작하기")
        self.assertEqual(github_slug("🔁 스스로 더 좋아집니다 (RSI)"), "-스스로-더-좋아집니다-rsi")
        self.assertEqual(github_slug("Step 2: Run `check`"), "step-2-run-check")


class CodeBlocks(unittest.TestCase):
    def test_no_very_long_code_lines_in_reader_docs(self):
        problems = []
        for md in READER_DOCS:
            for m in FENCE.finditer(md.read_text(encoding="utf-8")):
                for line in m.group(2).splitlines():
                    if display_width(line) > MAX_CODE_COLS:
                        problems.append(f"{md.relative_to(ROOT)}: {display_width(line)} cols: {line[:60]}")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
