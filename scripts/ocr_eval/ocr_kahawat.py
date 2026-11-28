"""OCR of Kahawat-Kosh.pdf (two columns around a vertical line: idiom on the right, meaning on the left).

Per page: render at --dpi, find the vertical line (longest thin ink run), cut the page into the right column
(idioms) and the left column (meanings) between the line's top and bottom (the page number above it is ignored),
split each column into text rows, read each row with UTRNet-Large (chunks of at most 11 x row height, joined right to
left), then pair rows across the columns by vertical overlap. An unpaired row continues the entry above it in its own
column. An entry whose idiom does not end with ":" and whose meaning does not end with a stop is merged with the next
one (a wrapped entry). Pages without two real columns are written as plain rows ("other" pages: front matter).
A row much thinner than the median (the tall strokes or tails of a line, cut off by the ink profile) is merged into the
closest row within 8 px (absorb_thin); without this each such piece was read as a junk row (89 of 151 pages had one).

Output in <out>: page_NNN.json (entries with confidences and flags), page_NNN.txt (one entry per line, idiom TAB meaning,
the layout of data/gold/transcriptions/kahawat_kosh), and kahawat_kosh_entries.tsv for the whole run.

Run: py -3 -X utf8 scripts/ocr_eval/ocr_kahawat.py --repo local/ocr-tools/utrnet --weights local/ocr-tools/weights/large.pth
        --out <dir> [--pages 50 51 | --first 1 --last 169] [--dpi 200]
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402

PDF = ROOT / "pdfs" / "anjumshanasi" / "Kahawat-Kosh.pdf"
STOPS = "۔.-ـ—–"


def longest_run(col):
    """(length, start, end) of the longest True run in a 1-D bool array."""
    d = np.diff(np.concatenate(([0], col.astype(np.int8), [0])))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    if len(st) == 0:
        return 0, 0, 0
    k = int(np.argmax(en - st))
    return int(en[k] - st[k]), int(st[k]), int(en[k])


def detect_line(ink):
    """The vertical rule: (xa, xb, y0, y1) or None. A thin column band with an ink run of at least 25% of the page height."""
    H, W = ink.shape
    lo, hi = int(0.15 * W), int(0.55 * W)
    runs = [longest_run(ink[:, x]) for x in range(lo, hi)]
    lens = np.array([r[0] for r in runs])
    k = int(np.argmax(lens))
    if lens[k] < 0.25 * H:
        return None
    band = [i for i in range(len(lens)) if lens[i] >= 0.8 * lens[k] and abs(i - k) <= 8]
    xa, xb = lo + min(band), lo + max(band) + 1
    if xb - xa > 12:  # a thick block, not a rule
        return None
    return xa, xb, runs[k][1], runs[k][2]


def read_row(utr, gray_row, h, max_aspect=11.0, eng=()):
    """Text and confidence of one row, plus a language tag: "" Arabic script only, "en" English only, "mixed" both.
    eng = [(x0, x1, text)] printed English runs of this row (found by english_spans.py with Tesseract). They are
    whitened out before UTRNet reads the rest, and put back into the text by x position (right to left)."""
    thr = O.otsu(gray_row)  # of the whole row, before the English runs are whitened out
    gray_row = gray_row.copy()
    for x0, x1, _t in eng:
        gray_row[:, max(0, x0 - 3):x1 + 3] = 255
    ink = gray_row < thr
    img = Image.fromarray(gray_row)
    parts = []
    for c0, c1 in O.split_chunks(ink, int(max_aspect * h)):
        t, c = utr.read_conf(img.crop((max(0, c0 - 2), 0, c1 + 2, h)))
        parts.append((c0, t, c))
    n_ar = len(parts)
    parts += [(x0, t, 0.95) for x0, _x1, t in eng]
    parts.sort(key=lambda p: -p[0])
    lang = "" if not eng else ("mixed" if n_ar else "en")
    return " ".join(p[1] for p in parts), (min(p[2] for p in parts) if parts else 0.0), lang


def absorb_thin(rows, max_frac=0.45, max_gap=8):
    """Merge a thin row (the tall strokes or the tails of a line that the profile cut off) into the closest row
    within max_gap px. Thin = shorter than max_frac x the median row height. A thin row with no near neighbour stays."""
    if len(rows) < 4:
        return rows
    med = float(np.median([b - a for a, b in rows]))
    rows = list(rows)
    k = 0
    while k < len(rows):
        a, b = rows[k]
        if b - a < max_frac * med:
            gp = rows[k - 1][1] if k > 0 else None
            gn = rows[k + 1][0] if k + 1 < len(rows) else None
            dp = a - gp if gp is not None else 10 ** 9
            dn = gn - b if gn is not None else 10 ** 9
            if min(dp, dn) <= max_gap:
                if dn <= dp:
                    rows[k + 1] = (a, rows[k + 1][1])
                else:
                    rows[k - 1] = (rows[k - 1][0], b)
                del rows[k]
                continue
        k += 1
    return rows


def region_rows(gray):
    """Text rows of one column region: [(a, b)] in region pixels (same cut for the OCR run and for english_spans.py)."""
    return absorb_thin(O.split_rows(gray < O.otsu(gray)))


def eng_for_row(eng, a):
    """English runs [(x0, x1, text)] of the row that starts at y = a, from {row_top: runs}; the nearest row top within 4 px."""
    if not eng:
        return ()
    k = min(eng, key=lambda t: abs(t - a))
    return eng[k] if abs(k - a) <= 4 else ()


def read_region(utr, gray, y_off, eng=None):
    """Rows of one column region: [(y0, y1, text, conf, lang)] with y in page coordinates. eng: {row top: English runs}."""
    out = []
    for a, b in region_rows(gray):
        a2, b2 = max(0, a - 3), min(gray.shape[0], b + 3)
        t, c, lang = read_row(utr, gray[a2:b2], b2 - a2, eng=eng_for_row(eng, a))
        out.append((y_off + a, y_off + b, t, c, lang))
    return out


def row_end(rows, idx):
    """Last character of the last row of an entry column. A row with English in it ends in the English note, which closes
    its entry like a full stop does: English only counts as ".", and for a mixed row the Arabic part before the note counts."""
    if not idx:
        return ""
    r = rows[idx[-1]]
    s = r[2].rstrip()
    if len(r) > 4 and r[4] in ("en", "mixed"):
        s = re.sub(r"[A-Za-z0-9 ]+$", "", s).rstrip()
        return s[-1:] if s else "."
    return s[-1:]


def pair(right, left):
    """Pair idiom rows (right) with meaning rows (left) by vertical overlap; unpaired rows continue the entry above."""
    cand = []
    for i, rr_ in enumerate(right):
        ra, rb = rr_[0], rr_[1]
        for j, ll_ in enumerate(left):
            la, lb = ll_[0], ll_[1]
            o = min(rb, lb) - max(ra, la)
            if o > 0.3 * min(rb - ra, lb - la):
                cand.append((o, i, j))
    cand.sort(reverse=True)
    pi, pj, mate = set(), set(), {}
    for o, i, j in cand:
        if i not in pi and j not in pj:
            pi.add(i); pj.add(j); mate[i] = j
    ents = []  # each: dict(r=[row idx], l=[row idx], y)
    pending_l = {}
    for j in range(len(left)):
        pending_l[j] = None
    items = [(right[i][0], "r", i) for i in range(len(right))] + [(left[j][0], "l", j) for j in range(len(left)) if j not in pj]
    items.sort()
    cur = None
    entry_of_right, entry_of_left = {}, {}
    for _y, side, k in items:
        if side == "r":
            if k in mate:
                cur = {"r": [k], "l": [mate[k]], "y": right[k][0]}
                ents.append(cur)
                entry_of_left[mate[k]] = cur
            else:
                # unpaired idiom row: continues the last entry that has an idiom
                tgt = next((e for e in reversed(ents) if e["r"]), None)
                if tgt is None:
                    tgt = {"r": [], "l": [], "y": right[k][0]}
                    ents.append(tgt)
                tgt["r"].append(k)
        else:
            tgt = next((e for e in reversed(ents) if e["l"]), None)
            if tgt is None:
                tgt = {"r": [], "l": [], "y": left[k][0]}
                ents.append(tgt)
            tgt["l"].append(k)
    ents.sort(key=lambda e: e["y"])
    res = []
    for e in ents:
        rr, ll = sorted(e["r"]), sorted(e["l"])
        res.append({"idiom": " ".join(right[i][2] for i in rr), "meaning": " ".join(left[j][2] for j in ll),
                    "idiom_conf": min([right[i][3] for i in rr], default=0.0),
                    "meaning_conf": min([left[j][3] for j in ll], default=0.0),
                    "y": e["y"], "rows": len(rr) + len(ll),
                    # page y-range of every row of this entry (review crops and checks use them)
                    "yr": [[right[i][0], right[i][1]] for i in rr], "yl": [[left[j][0], left[j][1]] for j in ll],
                    "i_end": row_end(right, rr), "m_end": row_end(left, ll)})
    # merge wrapped entries: idiom has no ":" ending and meaning has no stop ending -> continues in the next entry
    merged = []
    k = 0
    while k < len(res):
        e = dict(res[k])
        while k + 1 < len(res) and e["i_end"] != ":" and e["m_end"] not in STOPS:
            n = res[k + 1]
            e["i_end"], e["m_end"] = n["i_end"] or e["i_end"], n["m_end"] or e["m_end"]
            e["idiom"] = (e["idiom"] + " " + n["idiom"]).strip()
            e["meaning"] = (e["meaning"] + " " + n["meaning"]).strip()
            e["idiom_conf"], e["meaning_conf"] = min(e["idiom_conf"], n["idiom_conf"]), min(e["meaning_conf"], n["meaning_conf"])
            e["rows"] += n["rows"]
            e["yr"], e["yl"] = e["yr"] + n["yr"], e["yl"] + n["yl"]
            e["merged"] = True
            k += 1
        e.pop("i_end"), e.pop("m_end")
        merged.append(e)
        k += 1
    return merged


def find_headings(ink, xm, min_run=100, gap=(85, 135)):
    """Boxed section letters: a box drawn across the rule, one per letter of the alphabet (26 pages of this book).
    The top and bottom edges are ink runs of at least min_run px through the rule column xm, about 105 px apart.
    Returns [(y0, y1, x0, x1)] with a 3 px margin. The letter inside belongs to neither column."""
    groups = []  # [y_start, y_end, x_min, x_max] of consecutive rows with a long run through xm
    for y in np.where(ink[:, xm])[0]:
        row = ink[y]
        l = xm
        while l > 0 and row[l - 1]:
            l -= 1
        r = xm
        while r < len(row) - 1 and row[r + 1]:
            r += 1
        if r - l + 1 < min_run:
            continue
        if groups and y - groups[-1][1] <= 2:
            groups[-1][1] = int(y)
            groups[-1][2], groups[-1][3] = min(groups[-1][2], l), max(groups[-1][3], r)
        else:
            groups.append([int(y), int(y), l, r])
    out = []
    for a, b in zip(groups, groups[1:]):
        if gap[0] <= b[0] - a[1] <= gap[1]:
            out.append((a[0] - 3, b[1] + 3, min(a[2], b[2]) - 3, max(a[3], b[3]) + 3))
    return out


def book_line(doc, dpi, pages):
    """Typical rule of the book from a few pages: median x band and top, largest bottom. Used when a page has a broken rule."""
    found = []
    for n in pages:
        pix = doc[n - 1].get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
        gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
        ln = detect_line(gray < O.otsu(gray))
        if ln is not None:
            found.append(ln)
    if not found:
        return None
    a = np.array(found)
    return int(np.median(a[:, 0])), int(np.median(a[:, 1])), int(np.median(a[:, 2])), int(a[:, 3].max())


def assemble(right, left):
    """Entries from the rows of the two columns, or None when the page is not an idiom page (front matter in two columns
    of prose, a title page). Returns (entries, dropped junk entries)."""
    paired = sum(any(min(r[1], l[1]) - max(r[0], l[0]) > 0.3 * min(r[1] - r[0], l[1] - l[0]) for l in left) for r in right)
    if len(right) >= 4 and len(left) >= 3 and paired >= 0.5 * len(right):
        ents = pair(right, left)
        # a boxed letter heading, a stray folio or a lone mark is not an idiom: keep the count, drop the entry
        junk = [e for e in ents if len(e["idiom"].strip()) <= 3 and len(e["meaning"].strip()) <= 3]
        dropped = [{"y": e["y"], "idiom": e["idiom"], "meaning": e["meaning"]} for e in junk]
        ents = [e for e in ents if e not in junk]
        lens = sorted(len(e["idiom"]) for e in ents)
        # idiom pages hold many short idioms; front matter in two columns of prose holds few long ones
        if len(ents) >= 5 and lens[len(lens) // 2] <= 90:
            return ents, dropped
    return None


def page_setup(doc, n, dpi, fallback=None):
    """Render page n and find its layout. Returns (gray, ln, info, crops): gray has the section-letter boxes whitened;
    ln is the rule (xa, xb, y0, y1) or None; info holds page, line, headings, region; crops = (right, left, y0) are the
    two column images (right = idioms, left = meanings) or None when there is no rule."""
    pix = doc[n - 1].get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy()
    ink = gray < O.otsu(gray)
    ln = detect_line(ink)
    info = {"page": n, "line": ln}
    if ln is None and fallback is not None:
        # a rule drawn in short pieces fails the long-run test: try the book's usual rule, kept only if the page pairs well
        ln = fallback
        info["line"] = list(fallback)
        info["line_fallback"] = True
    crops = None
    if ln is not None:
        xa, xb, y0, y1 = ln
        heads = find_headings(ink, (xa + xb) // 2)
        if heads:  # whiten each section-letter box: its letter is not an idiom or a meaning (it was read as the start of one)
            info["headings"] = [list(h) for h in heads]
            for hy0, hy1, hx0, hx1 in heads:
                gray[max(0, hy0):hy1, max(0, hx0):hx1] = 255
        if fallback is not None:
            # the rule is often found in pieces (26 of 151 pages): the text region is the book's usual rule range, so
            # rows above or below the found piece are read too, and the last row is never cut at the end of the piece
            y0, y1 = min(y0, fallback[2]), max(y1, fallback[3])
        info["region"] = [y0, y1]
        crops = (gray[y0:y1, xb + 3:], gray[y0:y1, :max(1, xa - 3)], y0)
    return gray, ln, info, crops


def ocr_page(utr, doc, n, dpi, fallback=None, eng=None):
    """eng: {"r": {row top: [(x0, x1, text)]}, "l": {...}} printed English runs per column row (english_spans.py), or None."""
    gray, ln, info, crops = page_setup(doc, n, dpi, fallback)
    eng = eng or {}
    if crops is not None:
        y0 = crops[2]
        right = read_region(utr, crops[0], y0, eng.get("r"))
        left = read_region(utr, crops[1], y0, eng.get("l"))
        info["rows_r"], info["rows_l"] = [list(r) for r in right], [list(r) for r in left]  # the raw rows of both columns
        got = assemble(right, left)
        if got is not None:
            ents, junk = got
            if junk:
                info["dropped_junk"] = junk
            info.update(kind="entries", entries=ents, rows_right=len(right), rows_left=len(left))
            return info
        if info.get("line_fallback"):
            info["line"] = None
            ln = None
    # other page (front matter, title): the rule is whitened out, rows read across the page
    g2 = gray.copy()
    if ln is not None:
        g2[:, max(0, ln[0] - 2):ln[1] + 2] = 255
        top = max(0, ln[2] - 2)
        g2 = g2[top:, :]
    else:
        top = 0
    rows = read_region(utr, g2, top)
    info.update(kind="other", rows=[{"text": r[2], "conf": r[3], "y": r[0]} for r in rows])
    return info


def load_eng(folder, n):
    """English runs of page n from <folder>/eng_NNN.json: {"r": {row top: [(x0, x1, text)]}, "l": {...}} or None."""
    f = Path(folder) / f"eng_{n:03d}.json" if folder else None
    if f is None or not f.exists():
        return None
    d = json.loads(f.read_text(encoding="utf-8"))
    return {side: {int(a): [tuple(r) for r in runs] for a, runs in d.get(side, {}).items()} for side in ("r", "l")}


def write_page(out, info):
    """page_NNN.json (everything) and page_NNN.txt (one entry per line, idiom TAB meaning; other pages: one row per line)."""
    n = info["page"]
    (out / f"page_{n:03d}.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    if info["kind"] == "entries":
        lines = [e["idiom"] + "\t" + e["meaning"] for e in info["entries"]]
    else:
        lines = [r["text"] for r in info["rows"]]
    (out / f"page_{n:03d}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def write_tsv(out):
    """kahawat_kosh_entries.tsv rebuilt from all page files, so a re-run of single pages never duplicates rows."""
    with (out / "kahawat_kosh_entries.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["pdf_page", "entry", "idiom", "meaning", "idiom_conf", "meaning_conf", "rows", "merged"])
        for pf in sorted(out.glob("page_*.json")):
            info = json.loads(pf.read_text(encoding="utf-8"))
            if info["kind"] == "entries":
                for k, e in enumerate(info["entries"], 1):
                    w.writerow([info["page"], k, e["idiom"], e["meaning"], round(e["idiom_conf"], 3), round(e["meaning_conf"], 3),
                                e["rows"], int(e.get("merged", False))])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", nargs="*", type=int, default=[])
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=0)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--pdf", default=str(PDF), help="Kahawat-Kosh.pdf (default: pdfs/anjumshanasi/Kahawat-Kosh.pdf)")
    ap.add_argument("--eng-dir", default="", help="folder with eng_NNN.json from english_spans.py (printed English runs)")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    utr = O.UTRNet(args.repo, args.weights)
    doc = fitz.open(args.pdf)
    pages = args.pages or list(range(args.first, (args.last or len(doc)) + 1))
    fallback = book_line(doc, args.dpi, range(20, min(len(doc), 60), 4))
    for n in pages:
        info = ocr_page(utr, doc, n, args.dpi, fallback, load_eng(args.eng_dir, n))
        print(n, info["kind"], write_page(out, info), "lines", flush=True)
    write_tsv(out)
