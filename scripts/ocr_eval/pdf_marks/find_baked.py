"""Search every glyph of every NOORI* font saved by dump_fonts.py for the pesh and zer outlines (by contour size and area).
Prints the glyph keys that are not in marks_table.KNOWN. Run: py -3 -X utf8 scripts/ocr_eval/pdf_marks/find_baked.py"""
import json
import sys
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import marks_table as MT

W = MT.WORK
n2x = {k.split("|")[1]: v for k, v in json.load(open(W / "fonts/map_all.json")).items()}


def contours(tt, gname):
    gs = tt.getGlyphSet()
    pen = DecomposingRecordingPen(gs)
    gs[gname].draw(pen)
    out, cur = [], []
    for op, args in pen.value:
        if op == "moveTo":
            cur = [args[0]]
        elif op == "lineTo":
            cur.append(args[0])
        elif op in ("qCurveTo", "curveTo"):
            cur.extend(args)
        elif op in ("closePath", "endPath") and cur:
            out.append(cur)
            cur = []
    return out


def fp(c):
    xs = [p[0] for p in c]
    ys = [p[1] for p in c]
    a = sum(c[i][0] * c[(i + 1) % len(c)][1] - c[(i + 1) % len(c)][0] * c[i][1] for i in range(len(c)))
    return len(c), max(xs) - min(xs), max(ys) - min(ys), abs(a) / 2, min(ys), max(ys)


found = {"pesh": {}, "zer": {}}
for name, x in sorted(n2x.items()):
    if not name.startswith("NOORI"):
        continue
    tt = TTFont(W / f"fonts/x{x}.ttf")
    order = tt.getGlyphOrder()
    for gid, gname in enumerate(order):
        if (name, gid) in MT.KNOWN:
            continue
        try:
            cs = [fp(c) for c in contours(tt, gname) if len(c) > 3]
        except Exception:
            continue
        tail = any(52 <= f[1] <= 62 and 70 <= f[2] <= 80 and 2700 <= f[3] <= 2950 for f in cs)
        loop = any(13500 <= f[3] <= 15300 and 175 <= f[1] <= 195 and 190 <= f[2] <= 210 for f in cs)
        zer = any(5750 <= f[3] <= 6650 and 14 <= f[0] <= 18 and f[5] < 40 and f[1] < 260 and f[2] < 190 for f in cs)
        if tail and loop:
            found["pesh"][f"{name}:{gid}"] = 1
        if zer:
            found["zer"][f"{name}:{gid}"] = 1
for k, v in found.items():
    print(k, len(v), sorted(v)[:40])
