"""Table of the mark glyphs (pesh, zer) of the Noori Nastaleeq fonts, keyed by the hash of the glyph outline.

The glyph ids of a font subset can differ between books; the outline of a glyph does not. So a PDF is read like this:
hash the outline of every glyph of every NOORI* font it uses, look the hash up in data/decode/noori_marks_seed.json.

  py -3 -X utf8 scripts/ocr_eval/pdf_marks/marks_table.py build      # (re)write the seed from the Kahawat-Kosh fonts
  py -3 -X utf8 scripts/ocr_eval/pdf_marks/marks_table.py add <pdf> <page 0-based> <font> <gid> <type> <kind> [letter]
  py -3 -X utf8 scripts/ocr_eval/pdf_marks/marks_table.py scan <pdf> [pages ...]   # which of the table's glyphs does a PDF use?

The seed was found in Kahawat-Kosh.pdf (2026-11-11, see LOG.md): standalone `NOORIC,Bold` gid 49 (pesh) and 47 (zer), and
letter+mark glyphs of `NOORIN01,Bold` (pesh: 47 105 106 111 159 171, zer: 49 92 100 101 131 134 147 153).
The "v" over ن (type nun, `NOORIC02,Bold` 27) is written as ݨ (U+0768) by marks_insert.py.
Added from other books with the `add` command: NOORIN01,Bold 48 = alef with zabar (Gojri-Ghazal p. 40, the word اَج).
"""
import hashlib
import io
import json
import sys
from pathlib import Path

import fitz
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[3]
SEED = ROOT / "data/decode/noori_marks_seed.json"
WORK = ROOT / "data/ocr/pdfmarks-work"
KNOWN = {  # (font name, gid): (type, kind)
    **{("NOORIC,Bold", 49): ("pesh", "standalone"), ("NOORIC,Bold", 47): ("zer", "standalone")},
    **{("NOORIN01,Bold", g): ("pesh", "baked") for g in (47, 105, 106, 111, 159, 171)},
    **{("NOORIN01,Bold", g): ("zer", "baked") for g in (49, 92, 100, 101, 131, 134, 147, 153)},
    ("NOORIC02,Bold", 27): ("nun", "standalone"),  # the small "v" over ن: the retroflex nun ݨ (speaker's ruling 2026-11-15)
}


def glyph_hash(tt, gid):
    """md5 of the outline (coordinates and contour ends) of one glyph; None for an empty glyph."""
    glyf = tt["glyf"]
    g = glyf[tt.getGlyphOrder()[gid]]
    if g.numberOfContours == 0:
        return None
    coords, ends, _ = g.getCoordinates(glyf)
    return hashlib.md5((repr(list(coords)) + repr(list(ends))).encode()).hexdigest()[:16]


def ink_x(tt, gid):
    """(xmin, xmax) of the outline in em units."""
    g = tt["glyf"][tt.getGlyphOrder()[gid]]
    upm = tt["head"].unitsPerEm
    return g.xMin / upm, g.xMax / upm


def build():
    fm = json.loads((WORK / "fonts/map_all.json").read_text())
    n2x = {k.split("|")[1]: v for k, v in fm.items()}
    seed = json.loads(SEED.read_text(encoding="utf-8")) if SEED.exists() else {}  # keep glyphs added from other books
    for (name, gid), (typ, kind) in KNOWN.items():
        tt = TTFont(WORK / f"fonts/x{n2x[name]}.ttf")
        h = glyph_hash(tt, gid)
        xmin, xmax = ink_x(tt, gid)
        seed[h] = {"type": typ, "kind": kind, "src": f"Kahawat-Kosh.pdf {name}:{gid}", "xmin": round(xmin, 4), "xmax": round(xmax, 4)}
    SEED.parent.mkdir(parents=True, exist_ok=True)
    SEED.write_text(json.dumps(seed, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", SEED, len(seed), "glyphs")


def add(pdf, pno, font, gid, typ, kind, letter=None):
    """Put one glyph of a PDF (font name, gid on page pno, 0-based) into the seed, by outline hash."""
    doc = fitz.open(pdf)
    for f in doc[pno].get_fonts(full=True):
        if f[3].split("+")[-1] == font:
            tt = TTFont(io.BytesIO(doc.extract_font(f[0])[3]))
            h = glyph_hash(tt, gid)
            xmin, xmax = ink_x(tt, gid)
            seed = json.loads(SEED.read_text(encoding="utf-8"))
            seed[h] = {"type": typ, "kind": kind, "src": f"{Path(pdf).name} {font}:{gid}", "xmin": round(xmin, 4), "xmax": round(xmax, 4)}
            if letter:
                seed[h]["letter"] = letter
            SEED.write_text(json.dumps(seed, indent=1, ensure_ascii=False), encoding="utf-8")
            print("added", typ, h, "->", len(seed), "glyphs")
            return
    raise SystemExit("font not on that page")


def host_letter(chars, table, vx, vy):
    """The letter under a small "v" mark (type nun) at (vx, vy) in pt: "ن" or "ل", or None if the glyph under it is not in the table.
    chars: (font, gid, ox, oy, size) of the page; table: {(font, gid): seed entry}; entries of type vhost carry the letter."""
    for fn, gid, ox, oy, size in chars:
        e = table.get((fn, gid))
        if e and e["type"] == "vhost" and abs(oy - vy) < 14 and ox + e["xmin"] * size - 2 <= vx <= ox + e["xmax"] * size + 2:
            return e["letter"]
    return None


def pdf_mark_glyphs(doc, pno, seed=None):
    """{(font name, gid): seed entry} for the mark glyphs of the fonts used on page pno (0-based)."""
    seed = seed or json.loads(SEED.read_text(encoding="utf-8"))
    out = {}
    for f in doc[pno].get_fonts(full=True):
        name = f[3].split("+")[-1]
        if not name.startswith("NOORI"):
            continue
        try:
            tt = TTFont(io.BytesIO(doc.extract_font(f[0])[3]))
        except Exception:
            continue
        for gid in range(len(tt.getGlyphOrder())):
            try:
                h = glyph_hash(tt, gid)
            except Exception:
                continue
            if h in seed:
                out[(name, gid)] = seed[h]
    return out


def scan(pdf, pages):
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    doc = fitz.open(pdf)
    pages = pages or sorted({int(len(doc) * q) for q in (0.1, 0.3, 0.5, 0.7, 0.9)})
    found, uses = {}, {"pesh": 0, "zer": 0, "zabar": 0, "nun": 0}
    for p in pages:
        gl = pdf_mark_glyphs(doc, p, seed)
        found.update(gl)
        if not gl:
            continue
        for s in doc[p].get_texttrace():
            e = gl.get((s["font"].split("+")[-1], s["chars"][0][1])) if len(s["chars"]) == 1 else None
            for ch in s["chars"]:
                e = gl.get((s["font"].split("+")[-1], ch[1]))
                if e:
                    uses[e["type"]] += 1
    print(Path(pdf).name, "pages", pages, "mark glyphs found", len(found), "uses (doubled)", uses)
    return found, uses


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build()
    elif sys.argv[1] == "add":  # add <pdf> <page 0-based> <font> <gid> <type> <kind>
        add(sys.argv[2], int(sys.argv[3]), sys.argv[4], int(sys.argv[5]), sys.argv[6], sys.argv[7], sys.argv[8] if len(sys.argv) > 8 else None)
    elif sys.argv[1] == "scan":
        scan(sys.argv[2], [int(a) for a in sys.argv[3:]])
