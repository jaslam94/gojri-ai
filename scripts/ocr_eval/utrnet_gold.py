"""UTRNet-Large on the 12 gold pages with a simple line splitter (no PDF glyph boxes).

Why: the 200-line dictionary test cut Arabic runs with glyph boxes from the PDF. A scanned page has no such
boxes, so this test cuts text lines from the page image alone.

Steps for each page image in data/gold/images_cropped/:
  1. grey -> Otsu threshold -> ink mask.
  2. Rows: horizontal ink profile, gaps below a small threshold split the page into text lines.
  3. Chunks: UTRNet squeezes any input into 32 x 400 px, so a line wider than ~12 x its height loses detail.
     Each row is cut at its widest vertical gaps into chunks of width <= MAX_ASPECT x row height.
  4. Each chunk is read by UTRNet-Large (grey, mirrored, 32 px high; same as scripts/utrnet_arabic_eval.py).
     Chunks are joined right to left (Urdu reading order), rows top to bottom.
  5. Output goes to data/gold/transcriptions/<page>/<page>_utrnet_v1_original.txt, which
     scripts/score_gold.py scores like the other systems. Row crops are saved under --debug-dir if given.

English/Latin text and pictures are not handled (UTRNet fails on them); this test shows how much that costs.

Run: py -3 -X utf8 scripts/ocr_eval/utrnet_gold.py --repo local/ocr-tools/utrnet --weights local/ocr-tools/weights/large.pth
"""
import argparse
import math
import sys
from argparse import Namespace
from pathlib import Path

import numpy as np
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True)
ap.add_argument("--weights", required=True)
ap.add_argument("--pages", nargs="*", default=[])
ap.add_argument("--tag", default="utrnet_v1")
ap.add_argument("--max-aspect", type=float, default=11.0)
ap.add_argument("--debug-dir", default="")
ap.add_argument("--valley", action="store_true", help="split rows taller than 1.6 x median at the ink valley")
ap.add_argument("--columns", nargs="*", default=[], help="pages to split into 2 columns at the central gutter")
args = ap.parse_args()
sys.path.insert(0, args.repo)
from model import Model  # noqa: E402  (UTRNet; only model.py and modules/ are imported)

IMG_H, IMG_W = 32, 400
glyphs = "".join(s.strip("\n") for s in open(Path(args.repo) / "UrduGlyphs.txt", encoding="utf-8")) + " "
chars = ["[CTCblank]"] + list(glyphs)
opt = Namespace(FeatureExtraction="HRNet", SequenceModeling="DBiLSTM", Prediction="CTC", imgH=IMG_H, imgW=IMG_W,
                num_fiducial=20, input_channel=1, output_channel=32, hidden_size=256, batch_max_length=100,
                rgb=False, device=torch.device("cpu"), character=glyphs, num_class=len(chars))
net = Model(opt)
state = torch.load(args.weights, map_location="cpu", weights_only=True)
net.load_state_dict({k.removeprefix("module."): v for k, v in state.items()})
net.eval()


def utrnet_read(img):
    img = img.convert("L").transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    w, h = img.size
    rw = IMG_W if math.ceil(IMG_H * w / h) > IMG_W else math.ceil(IMG_H * w / h)
    a = np.asarray(img.resize((rw, IMG_H), Image.Resampling.BICUBIC), dtype="float32") / 255.0
    t = torch.from_numpy((a - 0.5) / 0.5).unsqueeze(0)
    x = torch.zeros(1, IMG_H, IMG_W)
    x[:, :, :rw] = t
    if rw < IMG_W:
        x[:, :, rw:] = t[:, :, rw - 1].unsqueeze(2).expand(1, IMG_H, IMG_W - rw)
    with torch.no_grad():
        idx = net(x.unsqueeze(0)).argmax(2)[0].tolist()
    out, prev = [], 0
    for k in idx:
        if k != 0 and k != prev:
            out.append(chars[k])
        prev = k
    return "".join(out)


def otsu(g):
    hist = np.bincount(g.ravel(), minlength=256).astype("float64")
    total, sum_all = g.size, (np.arange(256) * hist).sum()
    best, thr, wb, sb = 0.0, 128, 0.0, 0.0
    for t in range(256):
        wb += hist[t]
        if wb == 0 or wb == total:
            continue
        sb += t * hist[t]
        mb, mf = sb / wb, (sum_all - sb) / (total - wb)
        v = wb * (total - wb) * (mb - mf) ** 2
        if v > best:
            best, thr = v, t
    return thr


def runs_of(mask):
    """(start, end) of consecutive True values."""
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(mask)))
    return out


def split_rows(ink):
    prof = ink.sum(axis=1).astype("float32")
    thr = max(2.0, 0.02 * prof.max())
    rows = runs_of(prof > thr)
    merged = []
    for a, b in rows:  # merge rows split by a dot or diacritic gap smaller than 3 px
        if merged and a - merged[-1][1] < 3:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    rows = [(a, b) for a, b in merged if b - a >= 8]
    if args.valley and len(rows) >= 4:
        med = float(np.median([b - a for a, b in rows]))
        smooth = np.convolve(prof, np.ones(5) / 5, mode="same")
        out = []
        stack = list(reversed(rows))
        while stack:
            a, b = stack.pop()
            if b - a > 1.6 * med and b - a >= 2 * 8:
                lo, hi = a + int(0.35 * (b - a)), a + int(0.65 * (b - a))  # cut near the middle, at the lowest ink
                cut = lo + int(np.argmin(smooth[lo:hi]))
                stack += [(cut, b), (a, cut)]
            else:
                out.append((a, b))
        rows = out
    return rows


def split_chunks(ink_row, max_w):
    """Cut a row (ink mask) into x-ranges no wider than max_w, cutting at the widest white gaps."""
    cols = ink_row.sum(axis=0) > 0
    xs = np.where(cols)[0]
    if len(xs) == 0:
        return []
    x0, x1 = xs[0], xs[-1] + 1
    gaps = [(a, b) for a, b in runs_of(~cols[x0:x1])]
    gaps = [(a + x0, b + x0) for a, b in gaps]
    chunks, start = [], x0
    while x1 - start > max_w:
        lim = start + max_w
        cand = [g for g in gaps if g[0] > start + max_w * 0.4 and g[1] <= lim + 2]
        if not cand:  # no gap: cut at the narrowest-ink column inside the window
            cand = [(lim - 1, lim)]
        g = max(cand, key=lambda t: t[1] - t[0])
        chunks.append((start, g[0]))
        start = g[1]
    chunks.append((start, x1))
    return [c for c in chunks if c[1] - c[0] >= 6]


def read_region(gray, ink, dbg, tag):
    lines = []
    for ri, (a, b) in enumerate(split_rows(ink)):
        pad = 3
        a2, b2 = max(0, a - pad), min(gray.shape[0], b + pad)
        h = b2 - a2
        parts = []
        for ci, (c0, c1) in enumerate(split_chunks(ink[a2:b2], int(args.max_aspect * h))):
            crop = Image.fromarray(gray[a2:b2, max(0, c0 - 2):c1 + 2])
            if dbg is not None:
                crop.save(dbg / f"{tag}_r{ri:02d}_c{ci}.png")
            parts.append((c0, utrnet_read(crop)))
        parts.sort(key=lambda t: -t[0])  # right to left
        lines.append((a, b, " ".join(p for _, p in parts)))
    return lines


pages = args.pages or sorted(p.stem for p in (ROOT / "data/gold/images_cropped").glob("*.png"))
for page in pages:
    gray = np.asarray(Image.open(ROOT / "data/gold/images_cropped" / f"{page}.png").convert("L"))
    ink = gray < otsu(gray)
    dbg = None
    if args.debug_dir:
        dbg = Path(args.debug_dir) / page
        dbg.mkdir(parents=True, exist_ok=True)
    if page in args.columns:
        mid = gray.shape[1] // 2
        win = ink[:, int(gray.shape[1] * 0.35):int(gray.shape[1] * 0.65)].sum(axis=0)
        cut = int(gray.shape[1] * 0.35) + int(np.argmin(win))
        right = read_region(gray[:, cut:], ink[:, cut:], dbg, "R")
        left = read_region(gray[:, :cut], ink[:, :cut], dbg, "L")
        # gold pairs each right-column row with the left-column row at the same height: pair by vertical overlap
        lines, used = [], set()
        for ra, rb, rt in right:
            best, bo = None, 0
            for k, (la, lb, lt) in enumerate(left):
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
        lines = [t for _, _, t in read_region(gray, ink, dbg, "p")]
    out = ROOT / "data/gold/transcriptions" / page / f"{page}_{args.tag}_original.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(page, len(lines), "lines ->", out.name, flush=True)
