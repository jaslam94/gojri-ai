"""Gojri page OCR: rows -> SegNet script runs -> UTRNet (Arabic) + Tesseract (English). Writes <page>_<tag>_original.txt.

Rows come from the page image only (ocrlib.split_rows). The page mode is chosen first: SegNet marks English runs, Tesseract
confirms them (>= 6 letters); if they cover >= 15% of the text width the page is "mixed" (LineReader: SegNet runs, UTRNet for
Arabic, Tesseract for English, run text left to right), otherwise "arabic" (UTRNet alone, whole row right to left). Pages named in --columns have two columns (right column first, rows
paired by vertical overlap, as in utrnet_gold.py).

Run: py -3 -X utf8 scripts/ocr_eval/ocr_page.py --repo local/ocr-tools/utrnet --weights local/ocr-tools/weights/large.pth
        --segnet <segnet.pt> [--pages dict_alif ...] [--tag pipe_v1] [--columns kahawat_kosh]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True)
ap.add_argument("--weights", required=True)
ap.add_argument("--segnet", required=True)
ap.add_argument("--pages", nargs="*", default=[])
ap.add_argument("--tag", default="pipe_v1")
ap.add_argument("--columns", nargs="*", default=[])
ap.add_argument("--mixed-share", type=float, default=0.15, help="page is read as mixed-script if confirmed English covers at least this share of its text width")
args = ap.parse_args()
reader = O.LineReader(O.UTRNet(args.repo, args.weights), args.segnet, Path(__file__).resolve().parent / "sm_seg")


def page_mode(img):
    """'mixed' if confirmed English covers >= --mixed-share of the text width of the page, else 'arabic'."""
    gray = np.asarray(img.convert("L"))
    ink = gray < O.otsu(gray)
    eng = tot = 0
    for a, b in O.split_rows(ink):
        e, t = O.english_width(reader, img.crop((0, max(0, a - 3), img.width, min(img.height, b + 3))))
        eng, tot = eng + e, tot + t
    share = eng / tot if tot else 0.0
    return ("mixed" if share >= args.mixed_share else "arabic"), share


def read_region(img, mode):
    gray = np.asarray(img.convert("L"))
    ink = gray < O.otsu(gray)
    res = []
    for a, b in O.split_rows(ink):
        row = img.crop((0, max(0, a - 3), img.width, min(gray.shape[0], b + 3)))
        if mode == "mixed":
            text = " ".join(t for _, _, _, t in reader.read(row))
        else:
            text = O.read_arabic_only(reader, row)
        res.append((a, b, text))
    return res


pages = args.pages or sorted(p.stem for p in (ROOT / "data/gold/images_cropped").glob("*.png"))
for page in pages:
    img = Image.open(ROOT / "data/gold/images_cropped" / f"{page}.png").convert("RGB")
    mode, share = page_mode(img)
    print(f"{page}: confirmed English share {100 * share:.1f}% -> {mode} mode", flush=True)
    if page in args.columns:
        gray = np.asarray(img.convert("L"))
        ink = gray < O.otsu(gray)
        lo, hi = int(img.width * 0.35), int(img.width * 0.65)
        cut = lo + int(np.argmin(ink[:, lo:hi].sum(axis=0)))
        right, left = read_region(img.crop((cut, 0, img.width, img.height)), mode), read_region(img.crop((0, 0, cut, img.height)), mode)
        lines, used = [], set()
        for ra, rb, rt in right:
            best, bo = None, 0
            for k, (la, lb, _lt) in enumerate(left):
                o = min(rb, lb) - max(ra, la)
                if o > bo and k not in used:
                    best, bo = k, o
            if best is not None and bo > 0.3 * (rb - ra):
                used.add(best)
                lines.append(rt + " " + left[best][2])
            else:
                lines.append(rt)
        lines += [lt for k, (_, _, lt) in enumerate(left) if k not in used]
    else:
        lines = [t for _, _, t in read_region(img, mode)]
    out = ROOT / "data/gold/transcriptions" / page / f"{page}_{args.tag}_original.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(page, len(lines), "lines ->", out.name, flush=True)
