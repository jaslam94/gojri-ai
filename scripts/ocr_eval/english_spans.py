"""Find the printed English notes in the rows of Kahawat-Kosh.pdf with Tesseract (English).

Many entries carry a short English gloss on its own row or beside the Gojri meaning ("Faith moves mountains.").
UTRNet reads only Arabic script, so it turns these notes into junk letters. This script finds the English runs in
every row; ocr_kahawat.py then whitens them out before UTRNet reads the row and puts the Tesseract text back.

Same page geometry and row cut as ocr_kahawat.py (page_setup, region_rows). Output: <out>/eng_NNN.json per page,
{"r": {row top: [[x0, x1, text], ...]}, "l": {...}} (x in column-crop pixels; r = idiom column, l = meaning column),
and <out>/english_runs.tsv (page, column, row top, text) for a human check.

A Tesseract word counts as English if its confidence is at least 80 with 4 or more ASCII letters, or at least 88 with
2 or more. Arabic-script rows give lower scores and short junk (measured on 992 rows of 21 pages, 2026-11-09: every
real note scored 90 or more per word; every junk word with 2 or more letters scored 82 or less). A run needs 4 or more
ASCII letters in all.

Run (CPU, about 0.2 s per row): py -3 -X utf8 scripts/ocr_eval/english_spans.py --out data/ocr/kahawat-eng [--pages 54 64]
"""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402
import ocr_kahawat as K  # noqa: E402


def letters(t):
    return sum(ch.isascii() and ch.isalpha() for ch in t)


def is_english_word(conf, text):
    n = letters(text)
    return (conf >= 80 and n >= 4) or (conf >= 88 and n >= 2)


def english_runs(words):
    """[(x0, x1, text)] runs of consecutive English words (one weak word with 2+ letters may sit between two good ones)."""
    flags = [is_english_word(w[2], w[3]) for w in words]
    runs, cur = [], None
    for k, (w, f) in enumerate(zip(words, flags)):
        # one weak ASCII word between two good words belongs to the run ("Pride hath a fall.")
        bridge = (not f and cur is not None and k + 1 < len(words) and flags[k + 1] and w[3].isascii() and letters(w[3]) >= 1)
        # one weak word right after a good word is the tail of the note ("Pros and cons.", "Old is gold")
        # (its confidence is low because the printed dash or the Arabic after it touches it)
        tail = (not f and cur is not None and flags[k - 1] and w[2] >= 10 and letters(w[3][:3]) == 3)
        if f or bridge or tail:
            cur = (cur or [w[0], w[1], [], False, 0])
            cur[1] = w[1]
            cur[2].append(w[3])
            cur[4] += f and w[2] >= 90
            # a real note holds a good word of 4+ letters, or two very good words ("Old is" + the weak tail "gold")
            cur[3] = cur[3] or (f and letters(w[3]) >= 4) or cur[4] >= 2
        elif cur is not None:
            runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)
    out = []
    for a, b, t, strong, _n in runs:
        if not strong:
            continue  # "SU ees" and "bos pools" came out of Arabic rows: short words with a high score by chance
        text = re.sub(r"(?:[-_]+[()]*|\(\))\s*$", "", " ".join(t)).rstrip()  # a trailing dash or bracket is the printed separator, not text
        if letters(text) >= 4:
            out.append((a, b, text))
    return out


def left_note(img, ink_cols):
    """An English note at the left end of a row that also holds Arabic script. Tesseract reads the whole row badly there
    (the Arabic touches the note), so try shorter and shorter left parts of the row, cut at the gaps between ink groups,
    and keep the longest one that reads as English only. Returns (x1, text) or None. Row-crop pixels."""
    groups = O.runs_of(ink_cols)
    cuts = [groups[i][1] for i in range(len(groups) - 1) if groups[i + 1][0] - groups[i][1] >= 3]
    best = None
    for x in cuts:
        words = O.tesseract_words(img.crop((0, 0, x + 4, img.height)))
        if not words or not all(is_english_word(w[2], w[3]) for w in words):
            continue
        text = " ".join(w[3] for w in words)
        if letters(text) >= 6 and any(letters(w[3]) >= 4 for w in words):
            best = (x, text)  # cuts grow, so the last good one is the longest
    return best


def row_runs(gray_crop, a, b):
    """English runs of the row (a, b) of a column crop, x in column-crop pixels."""
    a2, b2 = max(0, a - 3), min(gray_crop.shape[0], b + 3)
    row = gray_crop[a2:b2]
    ink_cols = (row < O.otsu(row)).any(axis=0)
    cols = np.where(ink_cols)[0]
    if len(cols) == 0:
        return []
    off = max(0, int(cols[0]) - 6)
    img = Image.fromarray(row[:, off:int(cols[-1]) + 7])
    words = O.tesseract_words(img)
    runs = [(x0 + off, x1 + off, t) for x0, x1, t in english_runs([(w[0], w[1], w[2], w[3]) for w in words])]
    # a note at the left end that the whole-row pass missed: the first word still looks like English letters
    if not any(r[0] - off < 30 for r in runs) and words and words[0][0] < 30 and re.search(r"[A-Za-z]{5,}", words[0][3]):
        got = left_note(img, ink_cols[off:int(cols[-1]) + 7])
        if got:
            runs.append((off, got[0] + off, got[1]))
    return runs


def page_spans(doc, n, dpi, fallback):
    gray, ln, info, crops = K.page_setup(doc, n, dpi, fallback)
    if crops is None:
        return n, None, 0
    out, nrows = {"r": {}, "l": {}}, 0
    for side, crop in (("r", crops[0]), ("l", crops[1])):
        for a, b in K.region_rows(crop):
            nrows += 1
            runs = row_runs(crop, a, b)
            if runs:
                out[side][str(a)] = [list(r) for r in runs]
    return n, out, nrows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", nargs="*", type=int, default=[])
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--pdf", default=str(K.PDF))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(args.pdf)
    pages = args.pages or list(range(1, len(doc) + 1))
    fallback = K.book_line(doc, args.dpi, range(20, min(len(doc), 60), 4))

    def work(n):
        # one document handle per thread call: PyMuPDF objects are not thread safe
        return page_spans(fitz.open(args.pdf), n, args.dpi, fallback)

    tsv = ["page\tcolumn\trow_top\ttext"]
    rows_total = runs_total = 0
    with ThreadPoolExecutor(args.workers) as ex:
        for n, spans, nrows in ex.map(work, pages):
            if spans is None:
                continue
            (out / f"eng_{n:03d}.json").write_text(json.dumps(spans, ensure_ascii=False), encoding="utf-8")
            rows_total += nrows
            for side in ("r", "l"):
                for a, runs in spans[side].items():
                    runs_total += len(runs)
                    tsv += [f"{n}\t{side}\t{a}\t{t}" for _x0, _x1, t in runs]
            print(n, nrows, "rows", sum(len(v) for v in spans["r"].values()) + sum(len(v) for v in spans["l"].values()), "runs", flush=True)
    (out / "english_runs.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    print("total", rows_total, "rows,", runs_total, "English runs")


if __name__ == "__main__":
    main()
