#!/usr/bin/env python3
"""Build and check the README images (assets/*.svg).

Why this exists
---------------
GitHub shows README SVGs inside <img>. Any <text> in them is drawn with the
fonts installed on the *viewer's* machine, so a layout measured with one font
overflows its boxes when the viewer gets a wider Korean or monospace fallback
(2026-11-05: the install command ran out of the code box in start.svg).

How it works
------------
  assets/src/*.svg  editable sources with real <text>.  EDIT THESE.
  assets/*.svg      built files.  Every <text> is replaced by glyph outlines
                    taken from pinned fonts (Pretendard, JetBrains Mono), so
                    the image looks identical on every machine and browser.

Checks (``check``) fail on any of these:
  * a built file still contains <text>, or is out of date with its source;
  * text ink leaves its container (rect/circle/ellipse it sits in) or comes
    closer than the required padding, or leaves the canvas;
  * text touches another text or a shape drawn on top of its container;
  * the same in the *source* when laid out with deliberately wide fallback
    fonts (DejaVu Sans / DejaVu Sans Mono, Hangul forced to a full 1 em),
    so the layout stays safe even if someone ships the sources un-outlined.

Commands
--------
  python3 scripts/readme_assets.py fonts            # download pinned fonts
  python3 scripts/readme_assets.py build            # src -> assets (outlined)
  python3 scripts/readme_assets.py check            # all checks, exit 1 on failure
  python3 scripts/readme_assets.py check --offline  # built-file geometry only (stdlib)
  python3 scripts/readme_assets.py render OUTDIR    # PNG previews, light + dark

Dependencies: Python 3.10+. ``build``/full ``check`` need ``fonttools`` and
``uharfbuzz``; ``render`` needs ``resvg-py``
(pip install -r scripts/requirements-readme-assets.txt).
Fonts (SIL OFL 1.1) are downloaded once into $SF_FONT_DIR or
~/.cache/skillforge-readme-fonts and verified by SHA-256; they are not
committed to the repo.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import math
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "assets" / "src"
OUT_DIR = ROOT / "assets"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# --------------------------------------------------------------------------
# Pinned fonts (all SIL Open Font License 1.1)
# --------------------------------------------------------------------------
FONT_ARCHIVES = {
    "pretendard": {
        "url": "https://github.com/orioncactus/pretendard/releases/download/v1.3.9/Pretendard-1.3.9.zip",
        "sha256": "04be351a74d6bf7d60c480a3087e51d185485d35a52023142af1df19eb8c428a",
        "members": {f"public/static/Pretendard-{w}.otf": f"Pretendard-{w}.otf"
                    for w in ("Regular", "Medium", "SemiBold", "Bold", "ExtraBold")},
    },
    "jetbrains-mono": {
        "url": "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip",
        "sha256": "6f6376c6ed2960ea8a963cd7387ec9d76e3f629125bc33d1fdcd7eb7012f7bbf",
        "members": {f"fonts/ttf/JetBrainsMono-{w}.ttf": f"JetBrainsMono-{w}.ttf"
                    for w in ("Regular", "Medium", "SemiBold", "Bold", "ExtraBold")},
    },
    "dejavu": {
        "url": "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip",
        "sha256": "7576310b219e04159d35ff61dd4a4ec4cdba4f35c00e002a136f00e96a908b0a",
        "members": {f"dejavu-fonts-ttf-2.37/ttf/{n}": n for n in (
            "DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf")},
    },
}

WEIGHT_NAMES = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold"}


def font_dir() -> Path:
    return Path(os.environ.get("SF_FONT_DIR", Path.home() / ".cache" / "skillforge-readme-fonts"))


def fonts_present() -> bool:
    d = font_dir()
    return all((d / name).exists() for a in FONT_ARCHIVES.values() for name in a["members"].values())


def download_fonts(quiet: bool = False) -> None:
    d = font_dir()
    d.mkdir(parents=True, exist_ok=True)
    for key, spec in FONT_ARCHIVES.items():
        if all((d / n).exists() for n in spec["members"].values()):
            continue
        if not quiet:
            print(f"downloading {key} ...", file=sys.stderr)
        with urllib.request.urlopen(spec["url"], timeout=300) as r:
            data = r.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != spec["sha256"]:
            raise SystemExit(f"{key}: SHA-256 mismatch ({digest}); refusing to use it")
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for member, name in spec["members"].items():
                (d / name).write_bytes(z.read(member))


# --------------------------------------------------------------------------
# Small geometry helpers (stdlib only; used by every check)
# --------------------------------------------------------------------------
Matrix = tuple  # (a, b, c, d, e, f) like SVG matrix()
IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mat_mul(m: Matrix, n: Matrix) -> Matrix:
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D,
            a * E + c * F + e, b * E + d * F + f)


def apply(m: Matrix, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


def parse_transform(s: str | None) -> Matrix:
    m = IDENTITY
    if not s:
        return m
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s):
        v = [float(t) for t in re.split(r"[\s,]+", args.strip()) if t]
        if name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            r = math.radians(v[0])
            cx, cy = (v[1], v[2]) if len(v) == 3 else (0, 0)
            t = mat_mul(mat_mul((1, 0, 0, 1, cx, cy), (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)),
                        (1, 0, 0, 1, -cx, -cy))
        elif name == "matrix":
            t = tuple(v)
        else:
            raise ValueError(f"unsupported transform {name}")
        m = mat_mul(m, t)
    return m


def bbox_of_points(pts) -> tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def transform_bbox(m: Matrix, bb) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = bb
    return bbox_of_points([apply(m, x0, y0), apply(m, x1, y0), apply(m, x0, y1), apply(m, x1, y1)])


def union(a, b):
    if a is None:
        return b
    return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])


def intersects(a, b, gap: float = 0.0) -> bool:
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def path_points(d: str) -> list[tuple[float, float]]:
    """Points that bound a path: vertices, control points, sampled arcs."""
    toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|" + _NUM, d)
    pts: list[tuple[float, float]] = []
    i = 0
    cmd = None
    x = y = sx = sy = 0.0

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                x, y = sx, sy
                continue
        rel = cmd.islower()
        c = cmd.upper()
        ox, oy = (x, y) if rel else (0.0, 0.0)
        if c == "M":
            x, y = ox + num(), oy + num()
            sx, sy = x, y
            pts.append((x, y))
            cmd = "l" if rel else "L"
        elif c == "L" or c == "T":
            x, y = ox + num(), oy + num()
            pts.append((x, y))
        elif c == "H":
            x = ox + num()
            pts.append((x, y))
        elif c == "V":
            y = oy + num()
            pts.append((x, y))
        elif c in "CSQ":
            n = {"C": 3, "S": 2, "Q": 2}[c]
            for _ in range(n):
                px, py = ox + num(), oy + num()
                pts.append((px, py))
            x, y = px, py
        elif c == "A":
            rx, ry, rot, large, sweep = num(), num(), num(), num(), num()
            ex, ey = ox + num(), oy + num()
            pts.extend(_arc_points(x, y, rx, ry, rot, int(large), int(sweep), ex, ey))
            x, y = ex, ey
        else:
            raise ValueError(f"bad path command {cmd}")
    return pts


def _arc_points(x1, y1, rx, ry, phi_deg, fa, fs, x2, y2, n=48):
    if rx == 0 or ry == 0:
        return [(x2, y2)]
    phi = math.radians(phi_deg)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = (x1p ** 2) / (rx ** 2) + (y1p ** 2) / (ry ** 2)
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    coef = math.sqrt(max(0.0, num / den)) if den else 0.0
    if fa == fs:
        coef = -coef
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dt > 0:
        dt -= 2 * math.pi
    elif fs and dt < 0:
        dt += 2 * math.pi
    out = []
    for k in range(n + 1):
        t = t1 + dt * k / n
        out.append((cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp,
                    cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp))
    return out


# --------------------------------------------------------------------------
# Scene model shared by the source check and the built-file check
# --------------------------------------------------------------------------
@dataclass
class Shape:
    order: int
    kind: str                # rect | circle | ellipse | line | path | polygon
    bbox: tuple              # absolute bbox incl. stroke
    geom: tuple | None       # exact container geometry (rect or ellipse) or None
    filled: bool
    desc: str
    tip: tuple | None = None  # absolute end point of an arrow (marker-end)


@dataclass
class TextItem:
    order: int
    label: str
    anchor: tuple            # absolute (x, y) of the text's x/y attributes
    size: float              # font size in px (absolute)
    ink: tuple | None        # absolute ink bbox
    glyphs: list = field(default_factory=list)  # build only


@dataclass
class Scene:
    name: str
    width: float
    height: float
    shapes: list
    texts: list


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _num(v, default=0.0) -> float:
    if v is None:
        return default
    return float(str(v).replace("px", ""))


INHERITED = ("fill", "stroke", "stroke-width", "font-size", "font-weight", "letter-spacing",
             "text-anchor", "class", "font-family")


def _inherit(parent: dict, el: ET.Element) -> dict:
    st = dict(parent)
    for k in INHERITED:
        if el.get(k) is not None:
            st[k] = el.get(k)
    style = el.get("style")
    if style:
        for part in style.split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                if k.strip() in INHERITED:
                    st[k.strip()] = v.strip()
    return st


def _shape_from(el, name, st, m, order) -> Shape | None:
    stroke = st.get("stroke") not in (None, "none")
    sw = _num(st.get("stroke-width"), 1.0) if stroke else 0.0
    filled = st.get("fill", "#000") != "none"
    geom = None
    tip = None
    if name == "rect":
        x, y = _num(el.get("x")), _num(el.get("y"))
        w, h = _num(el.get("width")), _num(el.get("height"))
        rx = el.get("rx")
        ry = el.get("ry")
        rx = _num(rx if rx is not None else ry)
        ry = _num(ry if ry is not None else rx)
        bb = transform_bbox(m, (x, y, x + w, y + h))
        if abs(m[1]) < 1e-9 and abs(m[2]) < 1e-9:
            sx, sy = abs(m[0]), abs(m[3])
            geom = ("rect", *bb, rx * sx, ry * sy)
    elif name in ("circle", "ellipse"):
        cx, cy = _num(el.get("cx")), _num(el.get("cy"))
        rx = _num(el.get("r")) if name == "circle" else _num(el.get("rx"))
        ry = _num(el.get("r")) if name == "circle" else _num(el.get("ry"))
        bb = transform_bbox(m, (cx - rx, cy - ry, cx + rx, cy + ry))
        if abs(m[1]) < 1e-9 and abs(m[2]) < 1e-9:
            ccx, ccy = apply(m, cx, cy)
            geom = ("ellipse", ccx, ccy, rx * abs(m[0]), ry * abs(m[3]))
    elif name == "line":
        p = [apply(m, _num(el.get("x1")), _num(el.get("y1"))), apply(m, _num(el.get("x2")), _num(el.get("y2")))]
        bb = bbox_of_points(p)
        if el.get("marker-end"):
            tip = p[1]
        if el.get("marker-end") or el.get("marker-start"):
            sw += 8  # arrowhead
        filled = False
    elif name in ("polygon", "polyline"):
        vals = [float(t) for t in re.findall(_NUM, el.get("points", ""))]
        bb = bbox_of_points([apply(m, vals[i], vals[i + 1]) for i in range(0, len(vals), 2)])
    elif name == "path":
        pts = path_points(el.get("d", ""))
        if not pts:
            return None
        bb = bbox_of_points([apply(m, *p) for p in pts])
        if el.get("marker-end"):
            tip = apply(m, *pts[-1])
        if el.get("marker-end") or el.get("marker-start"):
            sw += 8
    else:
        return None
    h = sw / 2
    bb = (bb[0] - h, bb[1] - h, bb[2] + h, bb[3] + h)
    desc = f"<{name}" + "".join(f' {k}="{el.get(k)}"' for k in ("x", "y", "width", "height", "cx", "cy", "r", "d")
                                 if el.get(k) is not None)[:70] + ">"
    return Shape(order, name, bb, geom, filled, desc, tip)


def walk(root: ET.Element, on_text, on_textgroup=None) -> tuple[list, list]:
    """Walk the SVG in document order, collecting shapes and text items.

    on_text(el, style, matrix, order) -> TextItem   for <text>
    on_textgroup(el, matrix, order) -> TextItem     for built <g data-sf-text>
    """
    shapes, texts = [], []
    counter = [0]

    def rec(el, st, m):
        name = _local(el.tag)
        if name in ("defs", "title", "desc", "style", "marker", "linearGradient", "radialGradient", "symbol"):
            return
        st = _inherit(st, el)
        m = mat_mul(m, parse_transform(el.get("transform")))
        counter[0] += 1
        order = counter[0]
        if name == "text":
            texts.append(on_text(el, st, m, order))
            return
        if name == "g" and el.get("data-sf-text") is not None and on_textgroup:
            texts.append(on_textgroup(el, m, order))
            return
        sh = _shape_from(el, name, st, m, order)
        if sh:
            shapes.append(sh)
        for child in el:
            rec(child, st, m)

    rec(root, {}, IDENTITY)
    return shapes, texts


def svg_size(root: ET.Element) -> tuple[float, float]:
    vb = root.get("viewBox")
    if vb:
        _, _, w, h = [float(v) for v in vb.split()]
        return w, h
    return _num(root.get("width")), _num(root.get("height"))


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------
@dataclass
class Rules:
    name: str
    pad_x: callable          # (font_size) -> required horizontal padding inside a rect
    pad_y: callable
    pad_round: float         # padding inside a circle/ellipse
    gap: float               # min gap between text and other text / shapes on top
    canvas: float            # min distance from canvas edge


STRICT = Rules("bundled fonts", lambda fs: max(10.0, 0.6 * fs), lambda fs: max(4.0, 0.25 * fs), 3.0, 4.0, 12.0)
STRESS = Rules("wide fallback fonts", lambda fs: 3.0, lambda fs: 2.0, 1.0, 1.0, 4.0)


def _inside_container(ink, geom, pad_x, pad_y, pad_round) -> float:
    """Return the smallest slack (>= 0 means OK) of ink inside geom with padding."""
    if geom[0] == "rect":
        _, x0, y0, x1, y1, rx, ry = geom
        ix0, iy0, ix1, iy1 = x0 + pad_x, y0 + pad_y, x1 - pad_x, y1 - pad_y
        slack = min(ink[0] - ix0, ink[1] - iy0, ix1 - ink[2], iy1 - ink[3])
        # rounded corners: the inset rectangle keeps the remaining corner radius
        r_x, r_y = max(rx - pad_x, 0.0), max(ry - pad_y, 0.0)
        if r_x > 0 and r_y > 0 and slack >= 0:
            for px, py in ((ink[0], ink[1]), (ink[2], ink[1]), (ink[0], ink[3]), (ink[2], ink[3])):
                ccx = ix0 + r_x if px < ix0 + r_x else (ix1 - r_x if px > ix1 - r_x else None)
                ccy = iy0 + r_y if py < iy0 + r_y else (iy1 - r_y if py > iy1 - r_y else None)
                if ccx is not None and ccy is not None:
                    k = math.hypot((px - ccx) / r_x, (py - ccy) / r_y)
                    if k > 1:
                        slack = min(slack, -(k - 1) * min(r_x, r_y))
        return slack
    _, cx, cy, rx, ry = geom
    rx, ry = rx - pad_round, ry - pad_round
    worst = 0.0
    for px, py in ((ink[0], ink[1]), (ink[2], ink[1]), (ink[0], ink[3]), (ink[2], ink[3])):
        k = math.hypot((px - cx) / rx, (py - cy) / ry)
        worst = max(worst, k)
    return (1 - worst) * min(rx, ry)


def _contains_point(geom, x, y) -> bool:
    if geom[0] == "rect":
        return geom[1] <= x <= geom[3] and geom[2] <= y <= geom[4]
    _, cx, cy, rx, ry = geom
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def _area(geom) -> float:
    if geom[0] == "rect":
        return (geom[3] - geom[1]) * (geom[4] - geom[2])
    return math.pi * geom[3] * geom[4]


def check_scene(scene: Scene, rules: Rules) -> list[str]:
    problems = []
    W, H = scene.width, scene.height
    for t in scene.texts:
        where = f"{scene.name}: \"{t.label}\""
        if t.ink is None:
            continue
        # anchor point: x/y of the text; for centred text this is the centre
        cands = [s for s in scene.shapes
                 if s.order < t.order and s.filled and s.geom and _contains_point(s.geom, *t.anchor)]
        if not cands:
            problems.append(f"{where}: no container shape around the text")
            continue
        box = min(cands, key=lambda s: (_area(s.geom), -s.order))
        slack = _inside_container(t.ink, box.geom, rules.pad_x(t.size), rules.pad_y(t.size), rules.pad_round)
        if slack < -1e-6:
            problems.append(f"{where}: {'overflows' if slack < -rules.pad_x(t.size) else 'too close to the edge of'} "
                            f"its box {box.desc} by {-slack:.1f}px ({rules.name})")
        if (t.ink[0] < rules.canvas or t.ink[1] < rules.canvas or
                t.ink[2] > W - rules.canvas or t.ink[3] > H - rules.canvas):
            problems.append(f"{where}: too close to the image edge ({rules.name})")
        for s in scene.shapes:
            if s is box or s.order <= box.order:
                continue  # behind the container: hidden by it
            if s.geom and _contains_point(s.geom, *t.anchor):
                continue  # a nested container (e.g. pill inside card)
            if intersects(t.ink, s.bbox, rules.gap):
                problems.append(f"{where}: collides with {s.desc} ({rules.name})")
        for u in scene.texts:
            if u.order > t.order and u.ink and intersects(t.ink, u.ink, rules.gap):
                problems.append(f"{where}: collides with text \"{u.label}\" ({rules.name})")
    return problems


def check_arrows(scene: Scene) -> list[str]:
    """An arrowhead must not end under a filled shape drawn on top of it."""
    problems = []
    for a in scene.shapes:
        if a.tip is None:
            continue
        for s in scene.shapes:
            if s.order > a.order and s.filled and s.geom and _contains_point(s.geom, *a.tip):
                problems.append(f"{scene.name}: arrowhead of {a.desc} is hidden under {s.desc}")
                break
    return problems


# --------------------------------------------------------------------------
# Built files (outlined): geometry from glyph outlines, stdlib only
# --------------------------------------------------------------------------
def scene_from_built(path: Path) -> Scene:
    root = ET.parse(path).getroot()
    glyph_bb = {}
    for p in root.iter(f"{{{SVG_NS}}}path"):
        gid = p.get("id")
        if gid and gid.startswith("g-"):
            pts = path_points(p.get("d", ""))
            glyph_bb[gid] = bbox_of_points(pts) if pts else None

    def on_text(el, st, m, order):
        raise AssertionError("built file still contains <text>")

    def on_group(el, m, order):
        ink = None
        for u in el.iter(f"{{{SVG_NS}}}use"):
            ref = (u.get("href") or u.get(f"{{{XLINK_NS}}}href") or "").lstrip("#")
            bb = glyph_bb.get(ref)
            if bb is None:
                continue
            um = mat_mul(m, parse_transform(u.get("transform")))
            ink = union(ink, transform_bbox(um, bb))
        ax, ay = apply(m, float(el.get("data-sf-x")), float(el.get("data-sf-y")))
        size = float(el.get("data-sf-size")) * math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))
        return TextItem(order, el.get("data-sf-text"), (ax, ay), size, ink)

    shapes, texts = walk(root, on_text, on_group)
    w, h = svg_size(root)
    return Scene(path.name, w, h, shapes, texts)


def check_built_file(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    if re.search(r"<text\b", raw):
        return [f"{path.name}: still contains <text>; GitHub would draw it with the viewer's fonts. "
                f"Edit assets/src/{path.name} and run scripts/readme_assets.py build"]
    scene = scene_from_built(path)
    return check_scene(scene, STRICT) + check_arrows(scene)


# --------------------------------------------------------------------------
# Source files: lay text out with real fonts (fonttools + harfbuzz)
# --------------------------------------------------------------------------
HANGUL = re.compile(r"[ᄀ-ᇿ㄰-㆏가-힣]")


class Font:
    _cache: dict = {}

    def __init__(self, path: Path, key: str, min_hangul_em: float | None = None):
        from fontTools.ttLib import TTFont
        import uharfbuzz as hb
        self.path, self.key, self.min_hangul_em = path, key, min_hangul_em
        self.tt = TTFont(str(path), lazy=True)
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.order = self.tt.getGlyphOrder()
        self.gs = self.tt.getGlyphSet()
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        self._outline, self._bounds = {}, {}

    @classmethod
    def get(cls, path: Path, key: str, min_hangul_em=None) -> "Font":
        k = (str(path), min_hangul_em)
        if k not in cls._cache:
            cls._cache[k] = Font(path, key, min_hangul_em)
        return cls._cache[k]

    def has(self, ch: str) -> bool:
        return ord(ch) in self.cmap

    def shape(self, text: str, mono: bool):
        import uharfbuzz as hb
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        feats = {"liga": False, "calt": False, "dlig": False} if mono else {}
        hb.shape(self.hb, buf, feats)
        return list(zip(buf.glyph_infos, buf.glyph_positions))

    def outline(self, gid: int) -> str:
        if gid not in self._outline:
            from fontTools.pens.svgPathPen import SVGPathPen
            from fontTools.pens.transformPen import TransformPen
            pen = SVGPathPen(self.gs, ntos=lambda v: ("%d" % round(v)))
            self.gs[self.order[gid]].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
            self._outline[gid] = pen.getCommands()
        return self._outline[gid]

    def bounds(self, gid: int):
        if gid not in self._bounds:
            from fontTools.pens.boundsPen import ControlBoundsPen
            pen = ControlBoundsPen(self.gs)
            self.gs[self.order[gid]].draw(pen)
            b = pen.bounds
            self._bounds[gid] = None if b is None else (b[0], -b[3], b[2], -b[1])  # y-down
        return self._bounds[gid]


def _snap_weight(w: int, available) -> int:
    return min(available, key=lambda a: (abs(a - w), -a))


def font_chain(profile: str, mono: bool, weight: int) -> list[Font]:
    d = font_dir()
    pw = _snap_weight(weight, WEIGHT_NAMES)
    pretendard = Font.get(d / f"Pretendard-{WEIGHT_NAMES[pw]}.otf", f"pr{pw}")
    if profile == "bundled":
        if mono:
            return [Font.get(d / f"JetBrainsMono-{WEIGHT_NAMES[pw]}.ttf", f"jb{pw}"), pretendard]
        return [pretendard]
    # stress: wide Latin (DejaVu), Hangul forced to a full em
    bold = weight >= 600
    wide_ko = Font.get(d / f"Pretendard-{WEIGHT_NAMES[pw]}.otf", f"prw{pw}", min_hangul_em=1.0)
    if mono:
        return [Font.get(d / ("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"), "djm"), wide_ko]
    return [Font.get(d / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), "djs"), wide_ko]


def _family_is_mono(st: dict, class_fonts: dict) -> bool:
    fam = st.get("font-family") or ""
    for c in (st.get("class") or "").split():
        fam = class_fonts.get(c, fam)
    return "monospace" in fam or "Mono" in fam or "Consolas" in fam


def _class_fonts(root) -> dict:
    out = {}
    for s in root.iter(f"{{{SVG_NS}}}style"):
        for cls, body in re.findall(r"\.([\w-]+)\s*\{([^}]*)\}", s.text or ""):
            m = re.search(r"font-family\s*:\s*([^;]+)", body)
            if m:
                out[cls] = m.group(1)
    return out


def _spans(el: ET.Element, st: dict):
    """(text, style) runs of a <text>, honouring <tspan> fill/weight."""
    out = []
    if el.text:
        out.append((el.text, st))
    for child in el:
        if _local(child.tag) != "tspan":
            raise ValueError("only <tspan> is supported inside <text>")
        for bad in ("x", "y", "dx", "dy", "rotate"):
            if child.get(bad) is not None:
                raise ValueError(f"<tspan {bad}=...> is not supported; use separate <text> lines")
        cst = _inherit(st, child)
        if child.text:
            out.append((child.text, cst))
        if child.tail:
            out.append((child.tail, st))
    return out


def layout_text(el, st, m, order, profile, class_fonts) -> TextItem:
    x, y = _num(el.get("x")), _num(el.get("y"))
    pen = 0.0
    placed = []  # (font, gid, px, py, scale, fill)
    for text, sst in _spans(el, st):
        text = re.sub(r"\s+", " ", text)
        fs = _num(sst.get("font-size"), 16.0)
        ls = _num(sst.get("letter-spacing"), 0.0)
        weight = int(sst.get("font-weight", "400").replace("bold", "700").replace("normal", "400"))
        mono = _family_is_mono(sst, class_fonts)
        chain = font_chain(profile, mono, weight)
        # split into runs by the first font that has each character
        runs = []
        for ch in text:
            f = next((f for f in chain if f.has(ch)), chain[-1])
            if runs and runs[-1][0] is f:
                runs[-1][1] += ch
            else:
                runs.append([f, ch])
        for f, run in runs:
            scale = fs / f.upm
            shaped = f.shape(run, mono)
            for idx, (info, pos) in enumerate(shaped):
                adv = pos.x_advance
                ch = run[info.cluster] if info.cluster < len(run) else ""
                if f.min_hangul_em and HANGUL.match(ch):
                    adv = max(adv, f.min_hangul_em * f.upm)
                placed.append((f, info.codepoint, pen + pos.x_offset * scale, -pos.y_offset * scale,
                               scale, sst.get("fill", "#000")))
                pen += adv * scale
                last_in_cluster = idx + 1 == len(shaped) or shaped[idx + 1][0].cluster != info.cluster
                if last_in_cluster:
                    pen += ls
    anchor = st.get("text-anchor", "start")
    x0 = x - pen if anchor == "end" else (x - pen / 2 if anchor == "middle" else x)
    glyphs, ink = [], None
    for f, gid, gx, gy, scale, fill in placed:
        gx, gy = x0 + gx, y + gy
        glyphs.append((f, gid, gx, gy, scale, fill))
        b = f.bounds(gid)
        if b is not None:
            ink = union(ink, transform_bbox(m, (gx + b[0] * scale, gy + b[1] * scale,
                                                gx + b[2] * scale, gy + b[3] * scale)))
    label = "".join(t for t, _ in _spans(el, st)).strip()
    ax, ay = apply(m, x, y)
    size = _num(st.get("font-size"), 16.0) * math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))
    item = TextItem(order, label, (ax, ay), size, ink, glyphs)
    item.local = (x, y, _num(st.get("font-size"), 16.0))
    return item


def scene_from_source(path: Path, profile: str) -> Scene:
    root = ET.parse(path).getroot()
    cf = _class_fonts(root)
    shapes, texts = walk(root, lambda el, st, m, o: layout_text(el, st, m, o, profile, cf))
    w, h = svg_size(root)
    return Scene(f"{path.name} [{profile}]", w, h, shapes, texts)


def _fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def build_svg(src: Path) -> str:
    raw = src.read_text(encoding="utf-8")
    scene = scene_from_source(src, "bundled")
    glyph_defs: dict[str, str] = {}
    groups = []
    for t in scene.texts:
        x, y, fs = t.local
        parts = [f'<g data-sf-text="{html.escape(t.label, quote=True)}" data-sf-x="{_fmt(x)}" '
                 f'data-sf-y="{_fmt(y)}" data-sf-size="{_fmt(fs)}">']
        cur_fill = None
        for f, gid, gx, gy, scale, fill in t.glyphs:
            d = f.outline(gid)
            if not d:
                continue  # space
            gref = f"g-{f.key}-{gid}"
            glyph_defs.setdefault(gref, d)
            if fill != cur_fill:
                if cur_fill is not None:
                    parts.append("</g>")
                parts.append(f'<g fill="{fill}">')
                cur_fill = fill
            sc = f"{scale:.6f}".rstrip("0")
            parts.append(f'<use href="#{gref}" xlink:href="#{gref}" '
                         f'transform="translate({_fmt(gx)} {_fmt(gy)}) scale({sc})"/>')
        if cur_fill is not None:
            parts.append("</g>")
        parts.append("</g>")
        groups.append("".join(parts))

    pieces = re.split(r"(<text\b.*?</text>)", raw, flags=re.S)
    text_slots = [i for i, p in enumerate(pieces) if p.startswith("<text")]
    if len(text_slots) != len(groups):
        raise RuntimeError(f"{src.name}: found {len(text_slots)} <text> but laid out {len(groups)}")
    for i, g in zip(text_slots, groups):
        pieces[i] = g
    out = "".join(pieces)
    defs = "".join(f'<path id="{k}" d="{v}"/>' for k, v in glyph_defs.items())
    note = ("<!-- Built by scripts/readme_assets.py from assets/src/" + src.name +
            ". Do not edit: text is outlined so it renders the same on every machine. -->")
    if "</defs>" in out:
        out = out.replace("</defs>", f"<g id=\"sf-glyphs\">{defs}</g></defs>", 1)
    else:
        out = re.sub(r"(<svg\b[^>]*>)", r"\1<defs><g id=\"sf-glyphs\">" + defs.replace("\\", "\\\\") + "</g></defs>",
                     out, count=1)
    out = re.sub(r"<svg\b", f'{note}\n<svg xmlns:xlink="{XLINK_NS}"', out, count=1) \
        if "xmlns:xlink" not in out else re.sub(r"<svg\b", f"{note}\n<svg", out, count=1)
    # the font-family classes are no longer needed once nothing is text
    out = re.sub(r"<style>[^<]*font-family[^<]*</style>", "", out)
    out = re.sub(r'\s+class="[fm]"', "", out)
    return out


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------
def sources() -> list[Path]:
    return sorted(SRC_DIR.glob("*.svg"))


def cmd_build(args) -> int:
    download_fonts()
    for src in sources():
        out = OUT_DIR / src.name
        out.write_text(build_svg(src), encoding="utf-8")
        print(f"built {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
    return 0


def cmd_check(args) -> int:
    problems: list[str] = []
    srcs = sources()
    if not srcs:
        problems.append("assets/src/ has no SVG sources")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    used = re.findall(r'src="(assets/[^"]+\.svg)"', readme)
    for rel in used:
        name = Path(rel).name
        if not (SRC_DIR / name).exists():
            problems.append(f"README uses {rel} but assets/src/{name} does not exist")
    for src in srcs:
        built = OUT_DIR / src.name
        if not built.exists():
            problems.append(f"{built.name}: not built")
            continue
        problems += check_built_file(built)
    full = not args.offline
    if full:
        try:
            import fontTools  # noqa: F401
            import uharfbuzz  # noqa: F401
        except ImportError:
            print("fonttools/uharfbuzz missing: pip install -r scripts/requirements-readme-assets.txt",
                  file=sys.stderr)
            return 2
        download_fonts(quiet=True)
        for src in srcs:
            for profile, rules in (("bundled", STRICT), ("stress", STRESS)):
                problems += check_scene(scene_from_source(src, profile), rules)
            built = OUT_DIR / src.name
            if built.exists() and built.read_text(encoding="utf-8") != build_svg(src):
                problems.append(f"{built.name}: out of date with assets/src/{src.name}; run build")
    n_texts = sum(len(scene_from_built(OUT_DIR / s.name).texts) for s in srcs if (OUT_DIR / s.name).exists()
                  and not re.search(r"<text\b", (OUT_DIR / s.name).read_text(encoding="utf-8")))
    if problems:
        print(f"README images: {len(problems)} problem(s)")
        for p in problems:
            print("  - " + p)
        return 1
    mode = "built files only (offline)" if args.offline else "built files + sources with bundled and wide fonts"
    print(f"README images OK: {len(srcs)} images, {n_texts} text lines, checked {mode}")
    return 0


def cmd_render(args) -> int:
    import resvg_py
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    files = [Path(f) for f in args.files] or [OUT_DIR / s.name for s in sources()]
    font_files = [str(p) for p in font_dir().glob("*.[ot]tf")] if args.fonts == "bundled" else None
    for f in files:
        svg = f.read_text(encoding="utf-8")
        for bg_name, bg in (("light", "#ffffff"), ("dark", "#0d1117")):
            png = resvg_py.svg_to_bytes(svg_string=svg, background=bg, zoom=args.zoom,
                                        font_files=font_files, skip_system_fonts=args.fonts == "bundled")
            out = outdir / f"{f.stem}-{bg_name}.png"
            out.write_bytes(bytes(png))
            print(out)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fonts", help="download pinned fonts")
    sub.add_parser("build", help="outline assets/src/*.svg into assets/*.svg")
    c = sub.add_parser("check", help="fail on any text overflow or stale build")
    c.add_argument("--offline", action="store_true", help="only check built files (no fonts, stdlib only)")
    r = sub.add_parser("render", help="PNG previews on light and dark backgrounds (needs resvg-py)")
    r.add_argument("outdir")
    r.add_argument("files", nargs="*")
    r.add_argument("--zoom", type=float, default=1.0)
    r.add_argument("--fonts", choices=("system", "bundled"), default="system")
    args = ap.parse_args(argv)
    if args.cmd == "fonts":
        download_fonts()
        print(font_dir())
        return 0
    return {"build": cmd_build, "check": cmd_check, "render": cmd_render}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
