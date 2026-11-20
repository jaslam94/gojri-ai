"""PDF pesh/zer marks for single-column pages (prose, poetry) of a NOORIN book. Second-book test of the method.

Rows and clean line crops come from ocr_prose_pages.py; UTRNet reads each segment with the x of every letter
(marks_align.read_row_aligned); the mark glyphs come from the PDF itself, found by outline hash
(marks_table.pdf_mark_glyphs); marks_insert.insert_marks puts each mark after the nearest letter.

Run: py -3 -X utf8 scripts/ocr_eval/pdf_marks/prose_marks.py --pdf pdfs/anjumshanasi/Gojri-Ghazal.pdf --pages 40 --out data/ocr/ghazal-marks
Writes <out>/page_NNN.json: rows with "raw" (UTRNet text) and "text" (with the PDF marks), and page_NNN.txt (text).
"""
import argparse
import json
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import marks_align as A  # noqa: E402
import marks_insert as MI  # noqa: E402
import marks_table as MT  # noqa: E402
import ocr_prose_pages as P  # noqa: E402
import ocrlib as O  # noqa: E402


def page_marks(doc, pno, dpi, seed):
    """[(type, x px, y px)] of the mark glyphs of page pno (0-based) at dpi. The small "v" (type nun) becomes nun_n or nun_l
    by the letter glyph under it (type vhost in the table); a "v" over an unknown glyph is left out."""
    gl = MT.pdf_mark_glyphs(doc, pno, seed)
    chars = [(s["font"].split("+")[-1], ch[1], ch[2][0], ch[2][1], s["size"]) for s in doc[pno].get_texttrace() for ch in s["chars"]]
    out, seen = [], set()
    for fn, gid, ox, oy, size in chars:
        e = gl.get((fn, gid))
        key = (fn, gid, ox, oy)
        if not e or e["type"] == "vhost" or key in seen:
            continue
        seen.add(key)
        x_pt = ox + (e["xmin"] + e["xmax"]) / 2 * size
        t = e["type"]
        if t == "nun":
            h = MT.host_letter(chars, gl, x_pt, oy)
            if h is None:
                continue
            t = "nun_n" if h == "ن" else "nun_l"
        if e.get("kind") == "baked" and e.get("letter"):
            t = t + "|" + e["letter"]
        out.append((t, x_pt * dpi / 72, oy * dpi / 72))
    return out


def process_page(utr, doc, n, dpi, seed):
    gray, ink = P.render(doc, n, dpi)
    H, W = gray.shape
    _g3, ink3 = (gray, ink) if dpi == P.LAYOUT_DPI else P.render(doc, n, P.LAYOUT_DPI)
    bands3 = P.merge_small_bands([(a, b) for a, b in O.split_rows(ink3)], ink3)
    f = dpi / P.LAYOUT_DPI
    bands = [(max(0, int(round(a * f))), min(H, int(round(b * f)))) for a, b in bands3]
    med = float(np.median([b - a for a, b in bands])) if bands else 0.0
    Aown, touch_rows = P.assign_components(ink, bands)
    marks = page_marks(doc, n - 1, dpi, seed)
    from scipy import ndimage
    pad = max(3, round(0.02 * dpi))
    rows = []
    for k, (a, b) in enumerate(bands):
        mine = Aown == k
        ys, xs = np.nonzero(mine)
        if len(ys) == 0:
            continue
        y0, y1, x0, x1 = max(0, ys.min() - pad), min(H, ys.max() + 1 + pad), max(0, xs.min() - pad), min(W, xs.max() + 1 + pad)
        sub = mine[y0:y1, x0:x1]
        foreign = (Aown[y0:y1, x0:x1] >= 0) & ~sub
        cl = ndimage.binary_dilation(foreign, iterations=max(1, dpi // 150)) & ~sub
        crop = gray[y0:y1, x0:x1].copy()
        crop[cl] = 255
        row = {"row": k, "x0": int(x0), "x1": int(x1), "y0": int(y0), "y1": int(y1), "flags": [], "raw": "", "text": ""}
        if (y1 - y0) < 0.45 * med or (x1 - x0) < 0.6 * med:
            row["flags"].append("small")
            rows.append(row)
            continue
        cols = sub.sum(axis=0) > 0
        xs_on = np.where(cols)[0]
        gaps = [(p + xs_on[0], q + xs_on[0]) for p, q in O.runs_of(~cols[xs_on[0]:xs_on[-1] + 1]) if q - p > 1.8 * med]
        cuts, start = [], xs_on[0]
        for gp, gq in gaps:
            cuts.append((start, gp))
            start = gq
        cuts.append((start, xs_on[-1] + 1))
        chars = []   # logical order: segments right to left, letters right to left
        for c0, c1 in sorted(cuts, key=lambda c: -c[0]):
            seg = A.read_row_aligned(utr, Image.fromarray(crop[:, c0:c1]), sub[:, c0:c1])
            if chars:
                chars.append((" ", chars[-1][1] - 1, 0))
            chars += [(ch, x0 + c0 + x, 0) for ch, x in seg]
        # the marks of this row: each PDF mark belongs to the line whose band centre is nearest in y
        pm = [(t, x, 0) for t, x, y in marks if x0 - 4 <= x <= x1 + 4
              and min(range(len(bands)), key=lambda j: abs(y - (bands[j][0] + bands[j][1]) / 2)) == k]
        raw = "".join(ch for ch, _, _ in chars)
        idx = [i for i, (ch, _, _) in enumerate(chars) if MI.is_letter(ch) and ch != " "]
        new, left = MI.insert_marks(raw, chars, idx, pm, False)
        row.update(raw=raw, text=new, pdf_marks=len(pm))
        rows.append(row)
    return {"page": n, "dpi": dpi, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--pages", type=int, nargs="+", required=True)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--out", required=True)
    ap.add_argument("--threads", type=int, default=0)
    a = ap.parse_args()
    if a.threads:
        import torch
        torch.set_num_threads(a.threads)
    utr = O.UTRNet(O.UTRNET_REPO, O.UTRNET_WEIGHTS)
    doc = fitz.open(a.pdf)
    seed = json.loads(MT.SEED.read_text(encoding="utf-8"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for n in a.pages:
        res = process_page(utr, doc, n, a.dpi, seed)
        (out / f"page_{n:03d}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        (out / f"page_{n:03d}.txt").write_text("\n".join(r["text"] for r in res["rows"] if r["text"]) + "\n", encoding="utf-8")
        print("page", n, len(res["rows"]), "rows,", sum(r.get("pdf_marks", 0) for r in res["rows"]), "PDF marks placed", flush=True)


if __name__ == "__main__":
    main()
