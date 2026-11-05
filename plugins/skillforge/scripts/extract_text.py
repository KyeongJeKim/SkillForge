#!/usr/bin/env python3
"""Extract readable text from Office files so SkillForge can learn from them.

Usage:
    python3 extract_text.py <file.docx|file.xlsx|file.pptx> [more files...]

Prints plain text (Markdown-like) to stdout: Word paragraphs with heading
levels and tables as '|' rows, Excel sheets as '|' rows, PowerPoint slides
as '## Slide N' sections. Standard library only.

Not supported: .hwp, .doc, .xls, .ppt (old binary formats). Ask for a PDF
export or pasted text instead; Claude can read PDFs directly.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(f"{W}body")
    out: list[str] = []
    for el in list(body) if body is not None else []:
        if el.tag == f"{W}p":
            text = "".join(t.text or "" for t in el.iter(f"{W}t"))
            if not text.strip():
                continue
            style = el.find(f"{W}pPr/{W}pStyle")
            sid = style.get(f"{W}val", "") if style is not None else ""
            m = re.search(r"(?:Heading|제목)\s*(\d)", sid, re.I)
            if m:
                out.append("#" * int(m.group(1)) + " " + text.strip())
            elif sid.lower() == "title":
                out.append("# " + text.strip())
            elif el.find(f"{W}pPr/{W}numPr") is not None:
                out.append("- " + text.strip())
            else:
                out.append(text.strip())
        elif el.tag == f"{W}tbl":
            rows = []
            for tr in el.iter(f"{W}tr"):
                cells = ["".join(t.text or "" for t in tc.iter(f"{W}t")) for tc in tr.iter(f"{W}tc")]
                rows.append("| " + " | ".join(_cell(c) for c in cells) + " |")
            if rows:
                ncols = rows[0].count("|") - 1
                rows.insert(1, "|" + " --- |" * max(ncols, 1))
                out.append("\n".join(rows))
    return "\n\n".join(out)


def xlsx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{S}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{S}t")))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels}
        out: list[str] = []
        for sheet in wb.iter(f"{S}sheet"):
            target = targets.get(sheet.get(f"{R}id"), "")
            target = target.lstrip("/")
            part = target if target.startswith("xl/") else "xl/" + target
            if part not in names:
                continue
            rows = []
            for row in ET.fromstring(z.read(part)).iter(f"{S}row"):
                vals = []
                for c in row.iter(f"{S}c"):
                    v = c.find(f"{S}v")
                    if c.get("t") == "s" and v is not None:
                        vals.append(shared[int(v.text)])
                    elif c.get("t") == "inlineStr":
                        vals.append("".join(t.text or "" for t in c.iter(f"{S}t")))
                    else:
                        vals.append(v.text if v is not None and v.text else "")
                if any(x.strip() for x in vals):
                    rows.append("| " + " | ".join(_cell(x) for x in vals) + " |")
            out.append(f"## Sheet: {sheet.get('name')}\n\n" + "\n".join(rows))
    return "\n\n".join(out)


def pptx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        slides = sorted(
            (n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
            key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)),
        )
        out = []
        for i, name in enumerate(slides, 1):
            root = ET.fromstring(z.read(name))
            paras = ["".join(t.text or "" for t in p.iter(f"{A}t")) for p in root.iter(f"{A}p")]
            out.append(f"## Slide {i}\n\n" + "\n".join(p for p in paras if p.strip()))
    return "\n\n".join(out)


HANDLERS = {".docx": docx_text, ".xlsx": xlsx_text, ".xlsm": xlsx_text, ".pptx": pptx_text}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    status = 0
    for arg in argv[1:]:
        path = Path(arg).expanduser()
        handler = HANDLERS.get(path.suffix.lower())
        print(f"===== {path.name}")
        if handler is None:
            print(f"Unsupported format '{path.suffix}'. Export to PDF or paste the text instead.")
            status = 1
            continue
        try:
            print(handler(path))
        except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
            print(f"Could not read {path.name}: {exc}. Export to PDF or paste the text instead.")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
