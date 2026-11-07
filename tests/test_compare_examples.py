"""Tests for scripts/compare_examples.py (what stays the same across example documents).

Run from the repo root:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "skillforge" / "scripts" / "compare_examples.py"
FIX = ROOT / "tests" / "e2e" / "fixtures"

spec = importlib.util.spec_from_file_location("compare_examples", SCRIPT)
ce = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(ce)


def field(result: dict, name: str, section: str = "") -> dict:
    for f in result["fields"]:
        if f["field"] == name and f["section"] == section:
            return f
    raise AssertionError(f"no field {section!r} › {name!r}: {[f['field'] for f in result['fields']]}")


def write(folder: Path, files: dict[str, str]) -> list[Path]:
    out = []
    for name, text in files.items():
        p = folder / name
        p.write_text(text, encoding="utf-8")
        out.append(p)
    return out


class Classify(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(ce.classify(["이영희"] * 3), ("same", "이영희"))
        self.assertEqual(ce.classify(["2026-10-02", "2026.10.09", "2026년 10월 16일"])[0], "date")
        self.assertEqual(ce.classify(["2026-03-02 ~ 2026-03-15", "2026-06-15 ~ 2026-06-30"])[0], "date")
        self.assertEqual(ce.classify(["W41 보고", "W42 보고", "W43 보고"]), ("sequence", "W44 보고"))
        self.assertEqual(ce.classify(["promo-01", "promo-02", "promo-03"]), ("sequence", "promo-04"))
        self.assertEqual(ce.classify(["커피", "선풍기", "선물"])[0], "varies")

    def test_uneven_gaps_take_next_free_number(self):
        self.assertEqual(ce.classify(["PRD-26-011", "PRD-26-014", "PRD-26-020"], "문서 ID"),
                         ("sequence", "PRD-26-021"))

    def test_rising_amounts_are_not_a_counter(self):
        self.assertEqual(ce.classify(["49,000원", "59,000원"], "판매가")[0], "shape")
        self.assertEqual(ce.classify(["1억", "2억", "3억"], "목표")[0], "shape")
        # two values are a counter only when the field is named like one
        self.assertEqual(ce.classify(["A-031", "A-058"], "문서번호")[0], "sequence")
        self.assertEqual(ce.classify(["31개", "58개"], "수량")[0], "shape")


class Fixtures(unittest.TestCase):
    def test_weekly_reports(self):
        r = ce.compare(sorted((FIX / "pm").glob("weekly-report-W4*.md")))
        self.assertEqual(field(r, "프로젝트")["kind"], "same")
        self.assertEqual(field(r, "PM")["new"], "이영희")
        self.assertEqual(field(r, "보고일")["kind"], "date")
        self.assertEqual(field(r, "제목 (# 첫 줄)")["new"], "주간 보고 (2026년 W44)")
        self.assertEqual(field(r, "파일 이름")["new"], "weekly-report-W44")
        self.assertIn({"heading": "다음 주 계획", "in": 3, "label": "required"}, r["sections"])
        self.assertEqual([i["next"] for i in r["ids"] if i["prefix"] == "R"], ["R-04"])

    def test_promo_plans(self):
        r = ce.compare(sorted((FIX / "ecommerce").glob("*.md")))
        self.assertEqual(field(r, "작성자")["new"], "홍길동")
        self.assertEqual(field(r, "기간", "행사 개요")["kind"], "date")
        self.assertEqual(field(r, "혜택", "행사 개요")["kind"], "varies")
        self.assertEqual(r["numbered_headings"], 3)
        self.assertIn("목표 (KPI)", [s["heading"] for s in r["sections"]])  # numbering stripped
        self.assertFalse([i for i in r["ids"] if i["prefix"] == "D"])  # D-14 is a day count

    def test_office_files_and_mixed_ids(self):
        r = ce.compare(sorted(p for p in (FIX / "pos-specs-messy").iterdir()))
        self.assertEqual(len(r["documents"]), 5)  # .md, .docx and .hwpx all read
        fs = [i for i in r["ids"] if i["prefix"] == "FS-POS"][0]
        self.assertGreater(len(fs["digits"]), 1)  # 0018 / 007 / 12: mixed widths are reported
        self.assertTrue(any(i.get("per_document") for i in r["ids"]))  # FS-POS-0018-05 style rows

    def test_id_keyed_rows_are_content_not_fields(self):
        r = ce.compare(sorted((FIX / "pm-prd").glob("*.md")))
        self.assertFalse([f for f in r["fields"] if f["field"].startswith("REQ-0")])
        self.assertEqual(field(r, "문서 ID")["kind"], "sequence")


class Cli(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                              encoding="utf-8")

    def test_markdown_and_json(self):
        res = self.run_cli(str(FIX / "ecommerce"))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("## 2. 값 채우기 규칙 후보", res.stdout)
        self.assertIn("기본값으로 그대로: 홍길동", res.stdout)
        data = json.loads(self.run_cli(str(FIX / "ecommerce"), "--json").stdout)
        self.assertEqual(len(data["documents"]), 3)

    def test_needs_two_documents_and_skips_trial_and_unknown_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            write(d, {"a.md": "# A\n\n**담당:** 김\n", "notes.csv": "x,y\n"})
            res = self.run_cli(str(d))
            self.assertEqual(res.returncode, 2)
            self.assertIn("2개 이상", res.stderr)
            (d / "skillforge-trial").mkdir()
            write(d / "skillforge-trial", {"t.md": "# T\n"})
            write(d, {"b.md": "# B\n\n**담당:** 김\n"})
            res = self.run_cli(str(d), str(d / "skillforge-trial" / "t.md"))
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertNotIn("t.md", res.stdout)

    def test_code_blocks_and_pipes_in_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            files = write(d, {
                "1.md": "# R 1\n\n| 항목 | 내용 |\n| --- | --- |\n| 채널 | 앱 \\| 웹 |\n\n```\nkey: ignored\n```\n",
                "2.md": "# R 2\n\n| 항목 | 내용 |\n| --- | --- |\n| 채널 | 앱 \\| 웹 |\n",
            })
            r = ce.compare(files)
            self.assertNotIn("key", [f["field"] for f in r["fields"]])
            self.assertEqual(field(r, "채널")["new"], "앱 | 웹")
            md = ce.to_markdown(r, [])
            rows = [line for line in md.splitlines() if line.startswith("| 머리말 | 채널")]
            self.assertEqual(len(rows), 1)
            self.assertIn("앱 \\| 웹", rows[0])  # escaped again so the table keeps 6 columns


if __name__ == "__main__":
    unittest.main()
