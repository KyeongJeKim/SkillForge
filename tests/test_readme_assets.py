"""Tests for the README images (assets/*.svg) and their checker.

GitHub draws README SVGs inside <img> with the viewer's own fonts, so text can
overflow its boxes on some machines. scripts/readme_assets.py outlines all text
and checks every image. These tests keep that from regressing.

Run from the repo root:
    python3 -m unittest discover -s tests -v

The first three test classes use only the standard library. The full check
(sources laid out with the bundled and with deliberately wide fonts, plus
"built file is up to date") runs when fonttools and uharfbuzz are installed:
    pip install -r scripts/requirements-readme-assets.txt
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "readme_assets.py"


def load():
    spec = importlib.util.spec_from_file_location("readme_assets", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["readme_assets"] = mod  # dataclasses need the module registered
    spec.loader.exec_module(mod)
    return mod


ra = load()

# One "glyph": a 10 x 10 unit square sitting on the baseline (y-down units).
GLYPH = '<path id="g-t-1" d="M0 0L10 0L10 -10L0 -10Z"/>'


def built_svg(body: str, extra_defs: str = "") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="400" height="200" viewBox="0 0 400 200"><defs>{GLYPH}{extra_defs}</defs>'
            f'<rect x="1" y="1" width="398" height="198" fill="#fff"/>{body}</svg>')


def text_group(x: float, y: float, n: int, size: float = 10) -> str:
    """n glyphs of `size` px laid out from (x, y), like the build writes them."""
    uses = "".join(f'<use href="#g-t-1" transform="translate({x + i * size} {y}) scale({size / 10})"/>'
                   for i in range(n))
    return (f'<g data-sf-text="t" data-sf-x="{x}" data-sf-y="{y}" data-sf-size="{size}">'
            f'<g fill="#000">{uses}</g></g>')


class CheckerCatchesProblems(unittest.TestCase):
    def check(self, svg: str) -> list[str]:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.svg"
            p.write_text(svg, encoding="utf-8")
            return ra.check_built_file(p)

    def test_text_inside_box_passes(self):
        svg = built_svg('<rect x="40" y="40" width="200" height="60" fill="#eee"/>' + text_group(60, 76, 5))
        self.assertEqual(self.check(svg), [])

    def test_overflow_past_box_edge_fails(self):
        # 20 glyphs x 10px = 200px starting at 60 -> ends at 260, box ends at 240
        svg = built_svg('<rect x="40" y="40" width="200" height="60" fill="#eee"/>' + text_group(60, 76, 20))
        problems = self.check(svg)
        self.assertTrue(any("overflows" in p for p in problems), problems)

    def test_too_little_padding_fails(self):
        # ends at 235 with a 240 edge: inside, but under the 10px padding
        svg = built_svg('<rect x="40" y="40" width="200" height="60" fill="#eee"/>' + text_group(85, 76, 15))
        problems = self.check(svg)
        self.assertTrue(any("too close" in p for p in problems), problems)

    def test_rounded_corner_counts(self):
        # a pill: the text clears the straight edges' padding, but its corner
        # pokes into the rounded end
        pill = '<rect x="40" y="40" width="200" height="40" rx="20" fill="#eee"/>'
        self.assertTrue(self.check(built_svg(pill + text_group(51, 75, 3, size=14))))
        # same pill, square corners: the same text passes
        square = '<rect x="40" y="40" width="200" height="40" fill="#eee"/>'
        self.assertEqual(self.check(built_svg(square + text_group(51, 75, 3, size=14))), [])

    def test_collision_with_shape_on_top_fails(self):
        svg = built_svg('<rect x="40" y="40" width="300" height="60" fill="#eee"/>'
                        '<rect x="150" y="50" width="80" height="30" fill="#ccc"/>' + text_group(60, 76, 12))
        problems = self.check(svg)
        self.assertTrue(any("collides" in p for p in problems), problems)

    def test_text_left_as_text_fails(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">'
               '<text x="10" y="30">hello</text></svg>')
        problems = self.check(svg)
        self.assertTrue(any("still contains <text>" in p for p in problems), problems)

    def test_hidden_arrowhead_fails(self):
        svg = built_svg('<line x1="20" y1="150" x2="120" y2="150" stroke="#000" marker-end="url(#a)"/>'
                        '<rect x="100" y="120" width="100" height="60" fill="#eee"/>')
        problems = self.check(svg)
        self.assertTrue(any("arrowhead" in p for p in problems), problems)

    def test_transformed_group_is_followed(self):
        svg = built_svg('<g transform="translate(0 50)"><rect x="40" y="40" width="200" height="60" fill="#eee"/>'
                        + text_group(60, 76, 20) + "</g>")
        problems = self.check(svg)
        self.assertTrue(any("overflows" in p for p in problems), problems)


class ArcGeometry(unittest.TestCase):
    def test_arc_bbox_matches_circle(self):
        # a half circle of radius 50 around (100, 100), top half
        pts = ra.path_points("M50 100 A50 50 0 0 1 150 100")
        x0, y0, x1, y1 = ra.bbox_of_points(pts)
        self.assertAlmostEqual(y0, 50, delta=0.5)
        self.assertAlmostEqual(x0, 50, delta=0.01)
        self.assertAlmostEqual(x1, 150, delta=0.01)


class ReadmeImages(unittest.TestCase):
    def test_every_readme_image_passes(self):
        sources = ra.sources()
        self.assertTrue(sources, "assets/src/ has no SVG sources")
        for src in sources:
            built = ra.OUT_DIR / src.name
            with self.subTest(image=src.name):
                self.assertTrue(built.exists(), f"{built} missing; run scripts/readme_assets.py build")
                self.assertEqual(ra.check_built_file(built), [])

    def test_readme_only_uses_built_images(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        import re
        used = re.findall(r'src="(assets/[^"]+\.svg)"', readme)
        self.assertTrue(used)
        for rel in used:
            self.assertTrue((ROOT / "assets" / "src" / Path(rel).name).exists(), rel)
            self.assertNotIn("<text", (ROOT / rel).read_text(encoding="utf-8"), rel)


def _font_tools_available() -> bool:
    try:
        import fontTools  # noqa: F401
        import uharfbuzz  # noqa: F401
    except ImportError:
        return False
    return True


@unittest.skipUnless(_font_tools_available(),
                     "fonttools/uharfbuzz not installed: pip install -r scripts/requirements-readme-assets.txt")
class SourcesWithRealFonts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ra.download_fonts(quiet=True)

    def test_sources_fit_with_bundled_and_wide_fonts(self):
        for src in ra.sources():
            for profile, rules in (("bundled", ra.STRICT), ("stress", ra.STRESS)):
                with self.subTest(image=src.name, fonts=profile):
                    self.assertEqual(ra.check_scene(ra.scene_from_source(src, profile), rules), [])

    def test_built_files_are_up_to_date(self):
        for src in ra.sources():
            with self.subTest(image=src.name):
                built = (ra.OUT_DIR / src.name).read_text(encoding="utf-8")
                self.assertTrue(built == ra.build_svg(src),
                                f"assets/{src.name} is stale: run python3 scripts/readme_assets.py build")


if __name__ == "__main__":
    unittest.main()
