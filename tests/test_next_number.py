"""Tests for scripts/next_number.py (the next file name in a numbered document series).

Run from the repo root:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "skillforge" / "scripts" / "next_number.py"
FIX = ROOT / "tests" / "e2e" / "fixtures"


def run(*args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return p.returncode, p.stdout


def next_of(out: str) -> str:
    return out.splitlines()[0].removeprefix("next: ")


class NextNumber(unittest.TestCase):
    def test_empty_save_folder_continues_from_examples(self):
        # The 2026-11-17/19 failure: a fresh session saved promo-plan-01 next to examples 01-03.
        with tempfile.TemporaryDirectory() as out:
            code, text = run("promo-plan-{N}", out, str(FIX / "ecommerce"))
        self.assertEqual(code, 0)
        self.assertEqual(next_of(text), "promo-plan-04")

    def test_save_folder_ahead_of_examples_wins(self):
        with tempfile.TemporaryDirectory() as out:
            Path(out, "promo-plan-07_블랙프라이데이.md").write_text("x", encoding="utf-8")
            code, text = run("promo-plan-{N}", out, str(FIX / "ecommerce"))
        self.assertEqual(next_of(text), "promo-plan-08")
        self.assertIn("promo-plan-07", text)

    def test_padding_and_free_text_after_the_number(self):
        self.assertEqual(next_of(run("LST-2026-{N}", str(FIX / "ecommerce-listing"))[1]), "LST-2026-0459")
        self.assertEqual(next_of(run("PRD-26-{N}", str(FIX / "pm-prd"))[1]), "PRD-26-021")
        # Mixed padding (0018, 007, 021, 12): the highest number is 21, written like it.
        self.assertEqual(next_of(run("FS-POS-{N}", str(FIX / "pos-specs-messy"))[1]), "FS-POS-022")
        self.assertEqual(next_of(run("weekly-report-W{N}", str(FIX / "pm"))[1]), "weekly-report-W44")

    def test_trial_and_hidden_folders_do_not_move_the_counter(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "promo-plan-02.md").write_text("x", encoding="utf-8")
            for sub in ("skillforge-trial", ".git"):
                Path(d, sub).mkdir()
                Path(d, sub, "promo-plan-09.md").write_text("x", encoding="utf-8")
            self.assertEqual(next_of(run("promo-plan-{N}", d)[1]), "promo-plan-03")

    def test_whole_digit_run_and_text_after_N(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "W43.md").write_text("x", encoding="utf-8")
            Path(d, "W5-memo.md").write_text("x", encoding="utf-8")
            self.assertEqual(next_of(run("W{N}", d)[1]), "W44")
            self.assertEqual(next_of(run("W{N}-memo", d)[1]), "W6-memo")

    def test_no_match_exits_2_and_overflow_grows(self):
        with tempfile.TemporaryDirectory() as d:
            code, text = run("plan-{N}", d)
            self.assertEqual(code, 2)
            self.assertIn("no matching file", text)
            Path(d, "plan-99.md").write_text("x", encoding="utf-8")
            self.assertEqual(next_of(run("plan-{N}", d)[1]), "plan-100")

    def test_bad_pattern(self):
        code = subprocess.run([sys.executable, str(SCRIPT), "plan", "."], capture_output=True).returncode
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
