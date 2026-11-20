"""OCR of single-column Nastaliq pages (prose and poetry) with UTRNet-Large, with component-clean line crops.

Why this exists: a plain horizontal cut of a Nastaliq page leaves tails and dots of the line above or below inside
each crop (descenders reach into the next line). Here the page ink is split into connected components, and each
component goes to exactly one text line. A crop keeps only the ink of its own line; ink of other lines inside the
crop box is painted white.
  - A component that lies inside one line band, or mostly in the gap next to one line (dots and marks), goes to that
    line (the nearest band by edge distance when it lies only in the gap).
  - A component that spreads over two or more bands (two lines touch) is cut pixel by pixel at the middle of the gap
    between the bands, and both lines get the flag "touch": the crop may lack a piece of a letter.
Reading: a line is cut into segments at white gaps wider than 1.8 line heights (the two halves of a verse line);
each segment is cut into chunks no wider than 11 line heights (UTRNet limit) and read right to left. Segments are
joined with a TAB.
Word mode (--words auto|on|off): where the print has clear word gaps, each segment is cut at white gaps wider than
WORD_GAP x the median line height and every piece is read alone, so the spaces come from the print and not from the
reader (the whole-line reader joins words even where the print shows a wide gap). "auto" turns it on for a page when
at least 15% of its gaps are wide (>= 0.2 line heights) and at most 15% are in the unclear zone (0.12 to 0.2).
Tight pages (most gaps under 0.12) keep the whole-line reader. The decision and the gap shares are written to the json.
UTRNet shrinks every chunk to 32 px high (ocrlib.IMG_H), so a higher render DPI only changes how the chunk is
shrunk. Several DPIs can be run in one go (--dpis) to measure this.

Output in <out>/<tag>/dpi<DPI>/: page_NNN.txt (one line per row) and page_NNN.json (box, flags, per-row text),
and <out>/<tag>/crops/pNNN/Lkk.png (the cleaned crop, from the first DPI).
Run: py -3 -X utf8 scripts/ocr_eval/ocr_prose_pages.py --repo D:/ocr-tools/utrnet --weights D:/ocr-tools/weights/large.pth
        --pdf pdfs/anjumshanasi/Banjara.pdf --pages 60 150 --dpis 300 --out data/ocr/prose-test
UTRNet code and weights are third party (non-commercial: CC BY-NC 4.0 in its LICENSE file, CC BY-NC-SA 4.0 in its README).
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "pdf_marks"))
import ocrlib as O  # noqa: E402


def render(doc, n, dpi):
    pix = doc[n - 1].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), colorspace=fitz.csGRAY, alpha=False)
    g = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy()
    return g, g < O.otsu(g)


LAYOUT_DPI = 300
WORD_GAP = 0.2  # fraction of the median line height: a white gap at least this wide is a word gap (word mode)
VERSE_MARK = "؎"  # U+060E, the poetic verse sign printed at the start of a verse line in these books


def gap_shares(todo, med):
    """Shares of the white gaps of all read rows (in line heights): wide (>= 0.2), unclear (0.12 to 0.2), and the count.
    Verse-line gaps (> 1.8 line heights) and 1 px noise (< 0.03) are left out."""
    g = []
    for _row, _crop, mine, _cuts in todo:
        cols = mine.sum(axis=0) > 0
        xs = np.where(cols)[0]
        for p, q in O.runs_of(~cols[xs[0]:xs[-1] + 1]):
            w = (q - p) / med
            if 0.03 <= w <= 1.8:
                g.append(w)
    g = np.array(g)
    if len(g) == 0:
        return 0.0, 0.0, 0
    return float((g >= 0.2).mean()), float(((g >= 0.12) & (g < 0.2)).mean()), len(g)


def merge_small_bands(bands, ink, max_gap=0.6, min_overlap=0.5):
    """Join thin bands to the real line next to them.
    A thin band is usually the top bar of a kaf or gaf, a dot group, or a mark: it belongs to the line right above or
    below it. A band is thin if it is lower than half of the typical line (60th percentile of band heights). It is merged
    into the nearest real band when the vertical gap is at most max_gap x the typical height and the two overlap sideways
    (at least min_overlap of the thin band's width). A thin band with no such neighbour stays alone (stars, dashes)."""
    if len(bands) < 2:
        return bands
    ref = float(np.percentile([b - a for a, b in bands], 60))
    big = [list(b) for b in bands if b[1] - b[0] >= 0.5 * ref]
    small = [b for b in bands if b[1] - b[0] < 0.5 * ref]
    if not big:
        return bands
    left_over = []
    for a, b in small:
        xs = np.where(ink[a:b].any(axis=0))[0]
        if len(xs) == 0:
            continue
        s0, s1 = xs.min(), xs.max() + 1
        best, bd = None, None
        for bb in big:
            d = max(bb[0] - b, a - bb[1], 0)
            if d > max_gap * ref:
                continue
            cx = np.where(ink[bb[0]:bb[1]].any(axis=0))[0]
            if len(cx) == 0:
                continue
            ov = min(s1, cx.max() + 1) - max(s0, cx.min())
            if ov >= min_overlap * (s1 - s0) and (bd is None or d < bd):
                best, bd = bb, d
        if best is None:
            left_over.append((a, b))
        else:
            best[0], best[1] = min(best[0], a), max(best[1], b)
    return sorted([tuple(x) for x in big] + left_over)


def owner_by_y(H, bands):
    """For every pixel row y: the index of the band it belongs to (gap rows go to the nearer band edge)."""
    own = np.full(H, -1, dtype=np.int32)
    for k, (a, b) in enumerate(bands):
        own[a:b] = k
    ys = np.arange(H)
    for y in np.where(own < 0)[0]:
        d = [min(abs(y - a), abs(y - (b - 1))) for a, b in bands]
        own[y] = int(np.argmin(d))
    return own


def assign_components(ink, bands, touch_share=0.10):
    """Label map A: A[y, x] = row index of the line that owns this ink pixel, -1 for paper.
    Returns (A, set of row indices that contain cut (touching) components)."""
    H, W = ink.shape
    lab, n = ndimage.label(ink, structure=np.ones((3, 3)))
    objs = ndimage.find_objects(lab)
    band_of_y = np.full(H, -1, dtype=np.int32)
    for k, (a, b) in enumerate(bands):
        band_of_y[a:b] = k
    own_y = owner_by_y(H, bands)
    to_row = np.full(n + 1, -1, dtype=np.int32)
    touch_ids, touch_rows = [], set()
    for i, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        ys, xs = sl
        cnt = (lab[sl] == i).sum(axis=1)  # ink pixels per y
        yy = np.arange(ys.start, ys.stop)
        bo = band_of_y[yy]
        total = cnt.sum()
        shares = {}
        for k in np.unique(bo[bo >= 0]):
            shares[int(k)] = cnt[bo == k].sum() / total
        big = [k for k, s in shares.items() if s >= touch_share]
        if len(big) >= 2:
            touch_ids.append(i)
            touch_rows.update(big)
        elif big:
            to_row[i] = big[0]
        elif shares:
            to_row[i] = max(shares, key=shares.get)
        else:  # only in gaps: nearest band by the ink-weighted centre
            cy = int((cnt * yy).sum() / total)
            to_row[i] = own_y[min(max(cy, 0), H - 1)]
    A = to_row[lab]
    if touch_ids:
        tmask = np.isin(lab, touch_ids)
        ty, tx = np.nonzero(tmask)
        A[ty, tx] = own_y[ty]
    A[~ink] = -1
    return A, touch_rows


def read_segment(utr, gray_seg, ink_seg):
    h = gray_seg.shape[0]
    chunks = O.split_chunks(ink_seg, int(11 * h))
    parts = [(c0, utr.read(Image.fromarray(gray_seg[:, max(0, c0 - 2):c1 + 2]))) for c0, c1 in chunks]
    return " ".join(t for _, t in sorted(parts, key=lambda p: -p[0]))


def punct_space(s):
    """A space after ۔ and ، (the speaker's rule: ۔ ends a sentence, ، is a break). Same rule as score_prose_review.punct_rule."""
    return re.sub(r"([۔،])(?=[^\s۔،])", r"\1 ", s)


def pdf_marks_of_page(doc, n, dpi):
    """PDF mark glyphs of page n (1-based): [(type, x px, y px)]. Needs the NOORIN mark table (pdf_marks/marks_table.py)."""
    import marks_table as MT  # noqa: E402 (lazy: the mark modules load heavy helpers)
    import prose_marks as PM  # noqa: E402 (lazy: it imports this module)
    seed = json.loads(MT.SEED.read_text(encoding="utf-8"))
    return PM.page_marks(doc, n - 1, dpi, seed)


def ocr_page(utr, doc, n, dpi, crop_dir=None, words="off", pdf_marks=False):
    if pdf_marks:
        import marks_align as MA  # noqa: E402
        import marks_insert as MI  # noqa: E402
    gray, ink = render(doc, n, dpi)
    H, W = gray.shape
    # The row layout is always found on a 300 DPI render (split_rows works in pixels) and scaled to this DPI.
    _g3, ink3 = (gray, ink) if dpi == LAYOUT_DPI else render(doc, n, LAYOUT_DPI)
    bands3 = merge_small_bands([(a, b) for a, b in O.split_rows(ink3)], ink3)
    f = dpi / LAYOUT_DPI
    bands = [(max(0, int(round(a * f))), min(H, int(round(b * f)))) for a, b in bands3]
    med = float(np.median([b - a for a, b in bands])) if bands else 0.0
    A, touch_rows = assign_components(ink, bands)
    pad = max(3, round(0.02 * dpi))
    rows, todo = [], []
    for k, (a, b) in enumerate(bands):
        mine = A == k
        ys, xs = np.nonzero(mine)
        if len(ys) == 0:
            continue
        y0, y1, x0, x1 = max(0, ys.min() - pad), min(H, ys.max() + 1 + pad), max(0, xs.min() - pad), min(W, xs.max() + 1 + pad)
        sub_mine = mine[y0:y1, x0:x1]
        foreign = (A[y0:y1, x0:x1] >= 0) & ~sub_mine
        cl = ndimage.binary_dilation(foreign, iterations=max(1, dpi // 150)) & ~sub_mine
        crop = gray[y0:y1, x0:x1].copy()
        crop[cl] = 255
        row = {"row": k, "x0": int(x0), "x1": int(x1), "y0": int(y0), "y1": int(y1), "h": int(y1 - y0),
               "foreign_px": int(foreign.sum()), "own_px": int(sub_mine.sum()), "flags": [], "text": ""}
        if k in touch_rows:
            row["flags"].append("touch")
        if y0 < 0.09 * H:
            row["flags"].append("header")
        if (y1 - y0) < 0.45 * med or (x1 - x0) < 0.6 * med:
            row["flags"].append("small")  # star, dash, dot: not read
            rows.append(row)
            continue
        if crop_dir is not None:
            crop_dir.mkdir(parents=True, exist_ok=True)
            Image.fromarray(crop).save(crop_dir / f"L{k:02d}.png")
        cols = sub_mine.sum(axis=0) > 0
        xs_on = np.where(cols)[0]
        gaps = [(p + xs_on[0], q + xs_on[0]) for p, q in O.runs_of(~cols[xs_on[0]:xs_on[-1] + 1]) if q - p > 1.8 * med]
        cuts, start = [], xs_on[0]
        for gp, gq in gaps:
            cuts.append((start, gp))
            start = gq
        cuts.append((start, xs_on[-1] + 1))
        todo.append((row, crop, sub_mine, cuts))
        rows.append(row)
    wide, amb, ng = gap_shares(todo, med) if todo else (0.0, 0.0, 0)
    word_mode = words == "on" or (words == "auto" and wide >= 0.15 and amb <= 0.15)
    pm_page = pdf_marks_of_page(doc, n, dpi) if pdf_marks else []
    for row, crop, sub_mine, cuts in todo:
        row_pm = [(t, x, 0) for t, x, y in pm_page if row["x0"] - 4 <= x <= row["x1"] + 4
                  and min(range(len(bands)), key=lambda j: abs(y - (bands[j][0] + bands[j][1]) / 2)) == row["row"]]

        def rd(a0, a1):
            """(text, chars) of one piece. chars = [(letter, x in page px, 0)], right to left; only with pdf_marks."""
            text = read_segment(utr, crop[:, a0:a1], sub_mine[:, a0:a1])
            if not pdf_marks or not row_pm:  # the aligned reading (letter x) is only needed on a row that has PDF marks
                return text, None
            # the aligned reading only gives the x of each letter; the text (letters, spaces) stays the normal reading
            ch = [(c, row["x0"] + a0 + x, 0) for c, x in MA.read_row_aligned(utr, Image.fromarray(crop[:, a0:a1]), sub_mine[:, a0:a1])]
            return text, ch

        segs = []
        for c0, c1 in cuts:
            if word_mode:
                cols = sub_mine[:, c0:c1].sum(axis=0) > 0
                xs = np.where(cols)[0]
                pieces, start = [], xs[0] + c0
                for p, q in O.runs_of(~cols[xs[0]:xs[-1] + 1]):
                    if q - p >= WORD_GAP * med:
                        pieces.append((start, p + xs[0] + c0))
                        start = q + xs[0] + c0
                pieces.append((start, xs[-1] + 1 + c0))
                keep, marker = [], []
                for a0, a1 in pieces:  # an isolated flat dash is not a word: the reader would call it a letter
                    ys = np.where(sub_mine[:, a0:a1].any(axis=1))[0]
                    if len(ys) and (ys.max() - ys.min() + 1) < 0.25 * med and (a1 - a0) < 0.8 * med:
                        if c1 == cuts[-1][1] and a1 == pieces[-1][1]:
                            marker.append((a0, VERSE_MARK, [(VERSE_MARK, row["x0"] + a0, 0)] if pdf_marks else None))  # right end of the line: the verse-start mark
                        else:
                            row["dropped_marks"] = row.get("dropped_marks", 0) + 1
                    else:
                        keep.append((a0, a1))
                txt = [(a0, *rd(a0, a1)) for a0, a1 in keep] + marker
                txt.sort(key=lambda x: -x[0])
                chars = []
                for _, _t, ch in txt:
                    if pdf_marks and ch:
                        chars += ([(" ", chars[-1][1] - 1, 0)] if chars else []) + ch
                segs.append((c0, " ".join(t for _, t, _ in txt), chars))
            else:
                t, ch = rd(c0, c1)
                segs.append((c0, t, ch or []))
        segs.sort(key=lambda s: -s[0])
        row["text"] = "\t".join(t for _, t, _ in segs)
        row["segments"] = len(segs)
        if pdf_marks:
            chars = []
            for k_, (_, _t, ch) in enumerate(segs):
                if k_ and chars:
                    chars.append(("\t", chars[-1][1] - 1, 0))
                chars += ch or []
            raw = row["text"]
            idx = [i for i, (c, _, _) in enumerate(chars) if MI.is_letter(c) and c != " "]
            row["text"], _left = MI.insert_marks(raw, chars, idx, row_pm, False)
            row["raw"], row["pdf_marks"] = raw, len(row_pm)
    for row in rows:  # speaker's rule (2026-11-16): a space follows ۔ and ، even where the print has none
        row["text"] = punct_space(row["text"])
    return {"page": n, "dpi": dpi, "size": [W, H], "median_band": med, "word_mode": word_mode,
            "gaps": {"wide": round(wide, 3), "unclear": round(amb, 3), "n": ng}, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--pages", type=int, nargs="+", required=True)
    ap.add_argument("--dpis", type=int, nargs="+", default=[300])
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="")
    ap.add_argument("--words", choices=["auto", "on", "off"], default="auto")
    ap.add_argument("--pdf-marks", action="store_true", help="put pesh and zer in from the PDF's own mark glyphs (NOORIN books)")
    args = ap.parse_args()
    utr = O.UTRNet(args.repo, args.weights)
    doc = fitz.open(args.pdf)
    tag = args.tag or Path(args.pdf).stem
    base = Path(args.out) / tag
    t0 = time.time()
    for dpi_i, dpi in enumerate(args.dpis):
        out = base / f"dpi{dpi}"
        out.mkdir(parents=True, exist_ok=True)
        for n in args.pages:
            res = ocr_page(utr, doc, n, dpi, base / "crops" / f"p{n:03d}" if dpi_i == 0 else None, args.words, args.pdf_marks)
            (out / f"page_{n:03d}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            (out / f"page_{n:03d}.txt").write_text("\n".join(r["text"] for r in res["rows"] if r["text"]) + "\n", encoding="utf-8")
            fl = sum("touch" in r["flags"] for r in res["rows"])
            print(f"{tag} dpi {dpi} page {n}: {len(res['rows'])} rows, {fl} touch, word mode {res['word_mode']} {res['gaps']}, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
