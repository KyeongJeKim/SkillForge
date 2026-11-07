#!/usr/bin/env python3
"""Compare 2 or more example documents of the same kind and print what stays the same.

Usage:
    python3 compare_examples.py <file-or-folder> [more ...] [--json]
    (on Windows: python or py -3 instead of python3)

For each section heading, header field ("**PM:** 이영희", "작성자: 홍길동", a two-column
"| 항목 | 내용 |" table row), title line and file name it reports whether the value is:

  same      identical in every example        -> the new document can use it as a default
  sequence  same shape, one number counts up  -> the new document takes the next number
  date      a date or date range              -> today / the request, never copied
  shape     same shape, numbers differ        -> keep the shape, fill the numbers
  varies    different every time              -> comes from the request, else [확인 필요]

It also lists ID schemes (R-01, FR-001, FS-POS-018) and sentences that appear word for word in
every example (fixed wording candidates). The output is a text comparison: a value that is the
same only by coincidence (last week's tasks copied forward) still needs a person's OK.

Reads .md, .markdown and .txt directly, and .docx, .xlsx, .pptx, .hwpx and .hwp through the bundled
extract_text.py. Folders are read one level deep; `skillforge-trial/` and hidden files are skipped.
Standard library only. The idea of learning fixed text and blanks from several examples
("reverse templating") follows templatemaker/templater; no code was taken from them.
"""

from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

TEXT = {".md", ".markdown", ".txt"}
OFFICE = {".docx", ".xlsx", ".pptx", ".hwpx", ".hwp"}

DATE = re.compile(
    r"^\s*(\d{4}[-./]\s?\d{1,2}[-./]\s?\d{1,2}\.?|\d{4}년\s*\d{1,2}월(\s*\d{1,2}일)?|\d{1,2}월\s*\d{1,2}일)"
    r"(\s*\(.\))?(\s*\d{1,2}:\d{2})?"
    r"(\s*[~∼–-]\s*(\d{4}[-./]\s?)?\d{1,2}[-./]\s?\d{1,2}\.?(\s*\(.\))?|\s*[~∼–-]\s*(\d{1,2}월\s*)?\d{1,2}일)?\s*$"
)
ID = re.compile(r"(?<![A-Za-z0-9-])([A-Z][A-Z0-9]{0,7}(?:-(?:[A-Z][A-Z0-9]{0,7}|\d{2,4}(?=-\d)))*)-(\d{1,5})(?![0-9])")
BOLD_FIELD = re.compile(r"\*\*([^*:：\n]{1,30}?)\s*[:：]\s*\*\*\s*([^·|*\n]+)|\*\*([^*:：\n]{1,30}?)\*\*\s*[:：]\s*([^·|*\n]+)")
PLAIN_FIELD = re.compile(r"^(?:[-*]\s+)?([^\s:：|#>`*][^:：|`]{0,24}?)\s*[:：]\s+(\S.*)$")
NUMBERING = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]?|[IVX]+\.|[가-하][.)])\s+")
SEP = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$")


def read(path: Path) -> str:
    if path.suffix.lower() in TEXT:
        return path.read_text(encoding="utf-8", errors="replace")
    import subprocess

    script = Path(__file__).resolve().parent / "extract_text.py"
    res = subprocess.run([sys.executable, str(script), str(path)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return res.stdout


def collect(args: list[str]) -> tuple[list[Path], list[str]]:
    files, skipped = [], []
    for a in args:
        p = Path(a)
        items = sorted(p.iterdir()) if p.is_dir() else [p]
        for f in items:
            if f.name.startswith(".") or f.is_dir() or "skillforge-trial" in f.parts:
                continue
            ext = f.suffix.lower()
            if ext in TEXT or ext in OFFICE:
                files.append(f)
            elif p.is_file() or ext in {".pdf", ".png", ".jpg", ".jpeg", ".hwp", ".doc", ".xls", ".ppt"}:
                skipped.append(f.name)
    return files, skipped


def norm_heading(text: str) -> str:
    text = text.strip().strip("#").strip()
    text = re.sub(r"\*\*|__|`", "", text)
    return NUMBERING.sub("", text).strip()


def cells(line: str) -> list[str]:
    parts = re.split(r"(?<!\\)\|", line.strip().strip("|"))
    return [c.strip().replace("**", "").replace("\\|", "|") for c in parts]


def parse(text: str) -> dict:
    """Headings, fields (section, key) -> value, title, sentences and IDs of one document."""
    lines = text.splitlines()
    headings: list[str] = []
    numbered = 0
    fields: "OrderedDict[tuple[str, str], str]" = OrderedDict()
    sentences: list[str] = []
    title = ""
    section = ""
    in_code = False

    def put(key: str, value: str) -> None:
        key = key.strip().strip("*").strip()
        value = value.strip().strip("*").strip()
        # A row keyed by an ID (| REQ-02 | ... |) is a content unit, not a header field.
        if key and value and len(key) <= 30 and not key.startswith("<") and not ID.fullmatch(key):
            k = (section, key)
            if k not in fields:
                fields[k] = value

    for i, raw in enumerate(lines):
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line.strip():
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level, htext = len(m.group(1)), m.group(2)
            if level == 1 and not title:
                title = re.sub(r"\*\*", "", htext).strip()
                continue
            name = norm_heading(htext)
            if NUMBERING.match(htext.strip()):
                numbered += 1
            if name:
                headings.append(name)
                if level <= 3:
                    section = name
            continue
        s = line.strip()
        if s.startswith("|"):
            if SEP.match(s):
                continue
            row = cells(s)
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if SEP.match(nxt):  # header row
                continue
            if len(row) == 2:
                put(row[0], row[1])
            continue
        found = False
        for bm in BOLD_FIELD.finditer(s):
            k, v = (bm.group(1), bm.group(2)) if bm.group(1) else (bm.group(3), bm.group(4))
            put(k, v)
            found = True
        if not found:
            pm = PLAIN_FIELD.match(s)
            if pm and not re.search(r"[.?!。]\s*$", pm.group(1)) and len(pm.group(1).split()) <= 4:
                put(pm.group(1), pm.group(2))
        sent = re.sub(r"\s+", " ", re.sub(r"^[-*>]\s+|^\d+[.)]\s+", "", s)).strip()
        if len(sent) >= 8:
            sentences.append(sent)
    ids: dict[str, set[str]] = {}
    for prefix, num in ID.findall(text):
        if prefix == "D":  # D-14, D-7: days before an event, not an ID
            continue
        ids.setdefault(prefix, set()).add(num)
    return {"title": title, "headings": headings, "numbered": numbered, "fields": fields,
            "sentences": sentences, "ids": ids}


def shape(value: str) -> str:
    return re.sub(r"\d+", "#", value)


COUNTER_KEY = re.compile(r"번호|ID|No\.?$|코드|차수|주차|제목|파일", re.I)
AMOUNT = re.compile(r"[원%억만]|\$|KRW|USD")


def classify(values: list[str], key: str = "") -> tuple[str, str]:
    """Return (kind, what to do in a new document) for one field across the examples."""
    if len(set(values)) == 1:
        return "same", values[0]
    if all(DATE.match(v) for v in values):
        return "date", ""
    shapes = {shape(v) for v in values}
    if len(shapes) == 1:
        runs = [re.findall(r"\d+", v) for v in values]
        differ = [j for j in range(len(runs[0])) if len({r[j] for r in runs}) > 1]
        if len(differ) == 1:
            j = differ[0]
            nums = [int(r[j]) for r in runs]
            steps = [b - a for a, b in zip(nums, nums[1:])]
            # A counter, not two prices that happen to rise: 3+ examples or a field named like an ID.
            counter = (len(values) >= 3 or COUNTER_KEY.search(key)) and not AMOUNT.search(values[-1])
            if counter and all(st > 0 for st in steps):
                step = steps[0] if len(set(steps)) == 1 else 1  # uneven gaps: next free number
                width = len(runs[-1][j])
                nxt = str(nums[-1] + step).zfill(width) if runs[-1][j].startswith("0") else str(nums[-1] + step)
                parts = re.split(r"(\d+)", values[-1])
                parts[2 * j + 1] = nxt
                return "sequence", "".join(parts)
        return "shape", next(iter(shapes))
    return "varies", ""


def compare(paths: list[Path]) -> dict:
    docs = [(p.name, parse(read(p))) for p in paths]
    n = len(docs)
    out: dict = {"documents": [name for name, _ in docs], "sections": [], "fields": [], "ids": [],
                 "fixed_sentences": []}

    longest = max((d["headings"] for _, d in docs), key=len, default=[])
    order = list(dict.fromkeys(longest + [h for _, d in docs for h in d["headings"]]))
    for h in order:
        k = sum(h in d["headings"] for _, d in docs)
        label = "required" if k == n else ("common" if k * 2 > n else "varies")
        out["sections"].append({"heading": h, "in": k, "label": label})
    out["numbered_headings"] = sum(1 for _, d in docs if d["numbered"])

    rows: "OrderedDict[tuple[str, str], list[str]]" = OrderedDict()
    rows[("", "제목 (# 첫 줄)")] = [d["title"] for _, d in docs if d["title"]]
    rows[("", "파일 이름")] = [Path(name).stem for name, _ in docs]
    for _, d in docs:
        for key in d["fields"]:
            rows.setdefault(key, [])
    for key in list(rows):
        if key[1] in ("제목 (# 첫 줄)", "파일 이름"):
            continue
        rows[key] = [d["fields"][key] for _, d in docs if key in d["fields"]]
    out["hidden_once"] = 0
    for (sec, key), values in rows.items():
        if not values:
            continue
        if len(values) == 1 and n > 1 and sec:  # one-off body line (a quote in meeting notes)
            out["hidden_once"] += 1
            continue
        kind, hint = classify(values, key) if len(values) > 1 else ("once", "")
        out["fields"].append({"section": sec, "field": key, "in": len(values), "kind": kind,
                              "examples": list(dict.fromkeys(values))[:3], "new": hint})

    groups: dict[str, set[str]] = {}
    for prefix in {p for _, d in docs for p in d["ids"]}:
        groups.setdefault(shape(prefix), set()).add(prefix)
    for g in sorted(groups):
        prefixes = groups[g]
        k = sum(any(p in d["ids"] for p in prefixes) for _, d in docs)
        nums = [(p, x) for p in prefixes for _, d in docs for x in d["ids"].get(p, set())]
        widths = sorted({len(x) for _, x in nums})
        if k < 2 and len(nums) < 2:  # a one-off reference (EAN-13), not a numbering scheme
            continue
        if len(prefixes) > 1 and "#" in g:  # FS-POS-0018-05, FS-POS-007-06: numbered inside each document
            out["ids"].append({"prefix": g + "-" + "#" * max(widths), "in": k, "digits": widths,
                               "highest": "", "next": "문서마다 01부터", "per_document": True})
            continue
        p, top = max(nums, key=lambda t: int(t[1]))
        out["ids"].append({"prefix": p, "in": k, "digits": widths, "highest": f"{p}-{top}",
                           "next": f"{p}-{str(int(top) + 1).zfill(len(top))}"})

    if n > 1:
        common = set(docs[0][1]["sentences"])
        for _, d in docs[1:]:
            common &= set(d["sentences"])
        fieldish = {f"{k}: {v}" for _, d in docs for (_, k), v in d["fields"].items()}
        out["fixed_sentences"] = [s for s in dict.fromkeys(docs[0][1]["sentences"])
                                  if s in common and not s.startswith("|") and s not in fieldish][:15]
    return out


KIND_KO = {
    "same": ("모든 예시에서 같음", "기본값으로 그대로: {new}"),
    "sequence": ("순번 (하나씩 늘어남)", "가장 최근 문서 다음 값 (예시 기준: {new})"),
    "date": ("날짜", "요청한 날짜, 없으면 오늘. 예시에서 복사하지 않음"),
    "shape": ("모양은 같고 숫자만 다름", "모양 유지: {new}"),
    "varies": ("매번 다름", "요청에서 받음. 없으면 [확인 필요]"),
    "once": ("한 예시에만 있음", "선택 항목. 사람에게 확인"),
}
LABEL_KO = {"required": "필수", "common": "대부분", "varies": "가끔"}


def cell(text: str, limit: int = 40) -> str:
    text = text.replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def to_markdown(r: dict, skipped: list[str]) -> str:
    n = len(r["documents"])
    lines = [f"# 예시 비교 결과 ({n}개 문서)", "", "문서: " + ", ".join(r["documents"]), ""]
    if skipped:
        lines += ["읽지 않은 파일 (직접 읽어 주세요): " + ", ".join(skipped), ""]
    lines += ["## 1. 섹션", "", "| 제목 | 있는 문서 | 분류 |", "| --- | --- | --- |"]
    lines += [f"| {cell(s['heading'])} | {s['in']}/{n} | {LABEL_KO[s['label']]} |" for s in r["sections"]]
    if r["sections"]:
        lines += ["", f"제목 앞 번호(1. 2. …): {r['numbered_headings']}/{n}개 문서"]
    lines += ["", "## 2. 값 채우기 규칙 후보", "",
              "| 위치 | 항목 | 있는 문서 | 분류 | 예시 값 | 새 문서에서 |", "| --- | --- | --- | --- | --- | --- |"]
    for f in r["fields"]:
        kind, todo = KIND_KO[f["kind"]]
        lines.append(f"| {cell(f['section'] or '머리말', 20)} | {cell(f['field'], 24)} | {f['in']}/{n} | {kind} | "
                     f"{cell(' / '.join(f['examples']), 50)} | {cell(todo.format(new=f['new']), 60)} |")
    if r.get("hidden_once"):
        lines += ["", f"(본문에서 한 예시에만 있는 항목 {r['hidden_once']}개는 뺐습니다.)"]
    if r["ids"]:
        lines += ["", "## 3. 번호 체계", "", "| 접두어 | 있는 문서 | 자릿수 | 예시 최대 | 다음 번호 |",
                  "| --- | --- | --- | --- | --- |"]
        for i in r["ids"]:
            digits = "/".join(str(d) for d in i["digits"]) + ("자리 (섞여 있음: 사람에게 확인)" if len(i["digits"]) > 1 else "자리")
            lines.append(f"| {i['prefix']} | {i['in']}/{n} | {digits} | {i['highest']} | {i['next']} |")
    if r["fixed_sentences"]:
        lines += ["", "## 4. 모든 예시에 똑같이 있는 문장 (고정 문구 후보)", ""]
        lines += [f"- {cell(s, 90)}" for s in r["fixed_sentences"]]
    lines += ["", "> 글자 비교 결과입니다. 우연히 같은 값(지난번 할 일, 같은 담당자 등)은 고정값으로 쓰기 전에 사람에게 한 번 확인하세요."]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 2
    files, skipped = collect(args)
    if len(files) < 2:
        print(f"비교하려면 같은 종류의 문서가 2개 이상 필요합니다 (읽은 문서 {len(files)}개).", file=sys.stderr)
        return 2
    result = compare(files)
    if as_json:
        print(json.dumps({**result, "skipped": skipped}, ensure_ascii=False, indent=1))
    else:
        sys.stdout.write(to_markdown(result, skipped))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
