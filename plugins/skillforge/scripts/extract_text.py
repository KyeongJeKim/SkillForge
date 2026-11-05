#!/usr/bin/env python3
"""Extract readable text from Office files so SkillForge can learn from them.

Usage:
    python3 extract_text.py <file.docx|.xlsx|.pptx|.hwpx|.hwp> [more files...]
    (on Windows: python or py -3 instead of python3)

Prints plain text (Markdown-like) to stdout: Word paragraphs with heading
levels and tables as '|' rows, Excel sheets as '|' rows, PowerPoint slides
as '## Slide N' sections, Hangul (.hwpx, and .hwp 5.0) paragraphs with
.hwpx tables as '|' rows. Standard library only.

Not supported: .doc, .xls, .ppt (old binary Office), password-protected or
distribution-locked .hwp, and .hwp older than 5.0. Ask for a PDF export or
pasted text instead; Claude can read PDFs directly.
"""

from __future__ import annotations

import re
import struct
import sys
import zipfile
import zlib
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


# ---------------------------------------------------------------- Hangul .hwpx (OWPML, zipped XML)

def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _hwpx_text_of(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.iter() if _local(t.tag) == "t")


def _hwpx_emit(el: ET.Element, out: list[str]) -> None:
    name = _local(el.tag)
    if name == "tbl":
        rows = [[_cell(_hwpx_text_of(tc)) for tc in tr if _local(tc.tag) == "tc"]
                for tr in el if _local(tr.tag) == "tr"]
        rows = [r for r in rows if any(r)]
        if rows:
            width = max(len(r) for r in rows)
            out.append("")
            for i, r in enumerate(rows):
                out.append("| " + " | ".join(r + [""] * (width - len(r))) + " |")
                if i == 0:
                    out.append("|" + " --- |" * width)
            out.append("")
        return
    if name == "p":
        # Text of this paragraph, excluding tables nested in its runs (emitted separately).
        parts: list[str] = []
        nested: list[ET.Element] = []
        stack = list(el)[::-1]
        while stack:
            node = stack.pop()
            n = _local(node.tag)
            if n == "tbl":
                nested.append(node)
                continue
            if n == "t":
                parts.append("".join(node.itertext()))
                continue
            if n in ("lineBreak",):
                parts.append("\n")
            stack.extend(list(node)[::-1])
        line = "".join(parts).strip()
        if line:
            out.append(line)
        for t in nested:
            _hwpx_emit(t, out)
        return
    for child in el:
        _hwpx_emit(child, out)


def hwpx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        sections = sorted((n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)),
                          key=lambda n: int(re.findall(r"\d+", n)[-1]))
        if not sections:
            raise KeyError("no Contents/section*.xml (not an .hwpx file?)")
        out: list[str] = []
        for name in sections:
            _hwpx_emit(ET.fromstring(z.read(name)), out)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


# ---------------------------------------------------------------- Hangul .hwp 5.0 (OLE compound file)

class _Cfb:
    """Minimal read-only reader for OLE2 compound files (the container used by .hwp 5.0)."""

    FREE, END = 0xFFFFFFFF, 0xFFFFFFFE

    def __init__(self, data: bytes):
        if data[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            raise ValueError("not an OLE compound file")
        self.data = data
        self.ssize = 1 << struct.unpack_from("<H", data, 0x1E)[0]
        self.msize = 1 << struct.unpack_from("<H", data, 0x20)[0]
        n_fat, first_dir = struct.unpack_from("<II", data, 0x2C)
        self.cutoff, first_mini, n_mini, first_difat, n_difat = struct.unpack_from("<IIIII", data, 0x38)
        difat = list(struct.unpack_from("<109I", data, 0x4C))
        sid = first_difat
        for _ in range(n_difat):
            vals = struct.unpack_from(f"<{self.ssize // 4}I", self._sector(sid))
            difat.extend(vals[:-1])
            sid = vals[-1]
        self.fat: list[int] = []
        for fsid in difat[:n_fat]:
            self.fat.extend(struct.unpack_from(f"<{self.ssize // 4}I", self._sector(fsid)))
        dirs = self._chain(first_dir)
        self.entries = [self._entry(dirs[i:i + 128]) for i in range(0, len(dirs), 128)]
        root = self.entries[0]
        self.ministream = self._chain(root["start"])[: root["size"]]
        self.minifat = list(struct.unpack(f"<{len(m) // 4}I", m)) if (m := self._chain(first_mini) if n_mini else b"") else []
        self.paths: dict[str, dict] = {}
        self._walk(root["child"], "")

    def _sector(self, sid: int) -> bytes:
        off = (sid + 1) * self.ssize
        return self.data[off:off + self.ssize]

    def _chain(self, sid: int) -> bytes:
        out, seen = bytearray(), set()
        while sid not in (self.END, self.FREE) and sid < len(self.fat) + 1 and sid not in seen:
            seen.add(sid)
            out += self._sector(sid)
            sid = self.fat[sid] if sid < len(self.fat) else self.END
        return bytes(out)

    @staticmethod
    def _entry(raw: bytes) -> dict:
        nlen = struct.unpack_from("<H", raw, 64)[0]
        name = raw[: max(nlen - 2, 0)].decode("utf-16-le", "replace")
        left, right, child = struct.unpack_from("<III", raw, 68)
        start, size = struct.unpack_from("<IQ", raw, 116)
        return {"name": name, "type": raw[66], "left": left, "right": right, "child": child,
                "start": start, "size": size & 0xFFFFFFFF}

    def _walk(self, idx: int, prefix: str, seen: set | None = None) -> None:
        seen = set() if seen is None else seen
        if idx >= len(self.entries) or idx in seen:
            return
        seen.add(idx)
        e = self.entries[idx]
        path = prefix + e["name"]
        self.paths[path] = e
        self._walk(e["left"], prefix, seen)
        self._walk(e["right"], prefix, seen)
        if e["type"] == 1:  # storage
            self._walk(e["child"], path + "/", seen)

    def read(self, path: str) -> bytes:
        e = self.paths[path]
        if e["size"] < self.cutoff:
            out, sid, seen = bytearray(), e["start"], set()
            while sid not in (self.END, self.FREE) and sid < len(self.minifat) and sid not in seen:
                seen.add(sid)
                off = sid * self.msize
                out += self.ministream[off:off + self.msize]
                sid = self.minifat[sid]
            return bytes(out[: e["size"]])
        return self._chain(e["start"])[: e["size"]]


# Control characters inside HWP paragraph text (HWP 5.0 spec, section 4.2.10).
_HWP_ONE = {0, 10, 13} | set(range(24, 32))        # occupy 1 code unit
_HWP_EIGHT = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}  # 8 units


def _hwp_para_text(raw: bytes) -> str:
    units = struct.unpack(f"<{len(raw) // 2}H", raw[: len(raw) // 2 * 2])
    out, i = [], 0
    while i < len(units):
        ch = units[i]
        if ch >= 32:
            out.append(chr(ch))
            i += 1
        elif ch in _HWP_EIGHT:
            if ch == 9:
                out.append("\t")
            i += 8
        else:
            if ch == 10:
                out.append("\n")
            elif ch in (30, 31):
                out.append(" ")
            i += 1
    return "".join(out)


def hwp_text(path: Path) -> str:
    cfb = _Cfb(path.read_bytes())
    header = cfb.read("FileHeader")
    if not header.startswith(b"HWP Document File"):
        raise ValueError("not an HWP 5.0 file (older .hwp formats are not supported)")
    flags = struct.unpack_from("<I", header, 36)[0]
    if flags & 0x2:
        raise ValueError("the file is password-protected")
    if flags & 0x4:
        raise ValueError("the file is distribution-locked (배포용 문서)")
    compressed = bool(flags & 0x1)
    sections = sorted((p for p in cfb.paths if re.fullmatch(r"BodyText/Section\d+", p)),
                      key=lambda p: int(p[len("BodyText/Section"):]))
    out: list[str] = []
    for sec in sections:
        data = cfb.read(sec)
        if compressed:
            data = zlib.decompress(data, -15)
        pos = 0
        while pos + 4 <= len(data):
            head = struct.unpack_from("<I", data, pos)[0]
            tag, size = head & 0x3FF, head >> 20
            pos += 4
            if size == 0xFFF:
                size = struct.unpack_from("<I", data, pos)[0]
                pos += 4
            if tag == 67:  # HWPTAG_PARA_TEXT
                line = _hwp_para_text(data[pos:pos + size]).strip()
                if line:
                    out.append(line)
            pos += size
    if not out and "PrvText" in cfb.paths:  # preview text kept by Hangul itself
        out.append(cfb.read("PrvText").decode("utf-16-le", "replace").strip())
    return "\n".join(out)


HANDLERS = {".docx": docx_text, ".xlsx": xlsx_text, ".xlsm": xlsx_text, ".pptx": pptx_text,
            ".hwpx": hwpx_text, ".hwp": hwp_text}


def main(argv: list[str]) -> int:
    # Windows consoles often default to a legacy code page; never crash on Korean or symbols.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
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
        except (zipfile.BadZipFile, KeyError, ET.ParseError, ValueError, struct.error, zlib.error) as exc:
            print(f"Could not read {path.name}: {exc}. Export to PDF or paste the text instead.")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
