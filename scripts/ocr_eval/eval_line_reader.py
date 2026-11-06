"""End-to-end mixed-script line reader, tested on the 200 reviewed dictionary lines WITHOUT the PDF glyph boxes.

For each line image:
  1. Tesseract (English) reads the whole line and returns word boxes.
  2. Words that look like real English (ocrlib.is_latin_word) form Latin spans (neighbours closer than 1.5 x line
     height are merged). Tesseract's text for these spans is the English reading.
  3. The rest of the line (between Latin spans) is the Arabic-script part. It is cut at white gaps into chunks of
     at most 11 x line height and each chunk is read by UTRNet-Large. Chunks inside one gap are joined right to left,
     gaps are joined left to right (same order as scripts/utrnet_arabic_eval.py).
Scores: Arabic-letter error against reference_arabic (the 2.1% baseline used PDF glyph boxes), and Latin character
error (non-Arabic, non-space characters of text_fix, in left-to-right span order).

Run: py -3 -X utf8 scripts/ocr_eval/eval_line_reader.py --repo D:/ocr-tools/utrnet --weights D:/ocr-tools/weights/large.pth
     [--limit 200] [--out data/utrnet-test/line_reader_results.tsv]
"""
import argparse
import csv
import json
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
ap.add_argument("--limit", type=int, default=200)
ap.add_argument("--out", default="")
ap.add_argument("--segnet", default="", help="segnet.pt: use the neural script segmenter instead of Tesseract word boxes")
ap.add_argument("--max-aspect", type=float, default=11.0)
args = ap.parse_args()

utr = O.UTRNet(args.repo, args.weights)
seg = None
if args.segnet:
    import torch
    sys.path.insert(0, str(Path(__file__).resolve().parent / "sm_seg"))
    from segnet import SegNet, spans_from_logits
    seg = SegNet()
    seg.load_state_dict(torch.load(args.segnet, map_location="cpu", weights_only=True))
    seg.eval()
base = ROOT / "data" / "synth" / "real_pairs"
review = [json.loads(l) for l in (base / "labels_review_test.jsonl").open(encoding="utf-8")][: args.limit]


def read_line_seg(img):
    """SegNet finds Arabic and Latin spans from the line image only; UTRNet reads Arabic, Tesseract reads Latin."""
    h, w = img.height, img.width
    s = 64 / h
    g64 = img.convert("L").resize((max(8, round(w * s)), 64), Image.Resampling.BICUBIC)
    x = (torch.from_numpy(np.asarray(g64, dtype="float32") / 255.0)[None, None] - 0.5) / 0.5
    with torch.no_grad():
        logits = seg(x)[0]
    spans = [(c, int(a / s), min(w, int(b / s) + 1)) for c, a, b in spans_from_logits(logits)]
    # consecutive spans of the same script (no other script between) are one run, as in the PDF:
    # a long Arabic sentence can have wide word gaps, but it still reads as one right-to-left unit
    runs = []
    for c, a, b in spans:
        if runs and runs[-1][0] == c:
            runs[-1] = (c, runs[-1][1], b)
        else:
            runs.append((c, a, b))
    spans = runs
    gray = np.asarray(img.convert("L"))
    ink = gray < O.otsu(gray)
    ar, la = [], []
    for c, a, b in spans:
        a, b = max(0, a - 2), min(w, b + 2)
        if c == 1:
            parts = []
            for c0, c1 in O.split_chunks(ink[:, a:b], int(args.max_aspect * h)):
                parts.append((c0, utr.read(img.crop((a + max(0, c0 - 2), 0, a + c1 + 2, h)))))
            ar.append(" ".join(t for _, t in sorted(parts, key=lambda p: -p[0])))
        else:
            la.append(O.tesseract_text(img.crop((a, 0, b, h))))
    return " ".join(ar), " ".join(la)


def read_line(img):
    if seg is not None:
        return read_line_seg(img)
    h, w = img.height, img.width
    gray = np.asarray(img.convert("L"))
    ink = gray < O.otsu(gray)
    words = [x for x in O.tesseract_words(img) if O.is_latin_word(x[2], x[3])]
    spans = []  # [x0, x1, [texts]]
    for x0, x1, _c, t in words:
        if spans and x0 - spans[-1][1] < 1.5 * h:
            spans[-1][1] = max(spans[-1][1], x1)
            spans[-1][2].append(t)
        else:
            spans.append([x0, x1, [t]])
    # Arabic intervals = complement of the Latin spans
    cuts, pos = [], 0
    for x0, x1, _t in spans:
        cuts.append((pos, max(pos, x0 - 2)))
        pos = min(w, x1 + 2)
    cuts.append((pos, w))
    arabic_txt = []
    for a, b in cuts:
        if b - a < 12:
            continue
        parts = []
        for c0, c1 in O.split_chunks(ink[:, a:b], int(args.max_aspect * h)):
            crop = img.crop((a + max(0, c0 - 2), 0, a + c1 + 2, h))
            parts.append((c0, utr.read(crop)))
        arabic_txt.append(" ".join(t for _, t in sorted(parts, key=lambda p: -p[0])))
    latin_txt = " ".join(" ".join(t) for _, _, t in spans)
    return " ".join(arabic_txt), latin_txt


rows, ea = [], [0, 0, 0]
el = [0, 0, 0]
for i, r in enumerate(review):
    img = Image.open(base / r["image"]).convert("RGB")
    a_out, l_out = read_line(img)
    ref_a, ref_l = O.arabic(r["text_fix"]), O.latin(r["text_fix"])
    da, dl = O.ed(ref_a, O.arabic(a_out)), O.ed(ref_l, O.latin(l_out))
    ea[0] += da; ea[1] += len(ref_a); ea[2] += da == 0
    el[0] += dl; el[1] += len(ref_l); el[2] += dl == 0
    rows.append([r["page_line"], r["text_fix"], a_out, l_out, da, len(ref_a), dl, len(ref_l)])
    if (i + 1) % 25 == 0:
        print(f"{i + 1} lines: Arabic {100 * ea[0] / max(1, ea[1]):.1f}%  Latin {100 * el[0] / max(1, el[1]):.1f}%", flush=True)

n = len(review)
print(f"\nLines: {n}")
print(f"Arabic-letter error: {ea[0]} of {ea[1]} = {100 * ea[0] / ea[1]:.1f}% ({ea[2]} lines exact)   [PDF-box baseline: 2.1%]")
print(f"Latin character error: {el[0]} of {el[1]} = {100 * el[0] / el[1]:.1f}% ({el[2]} lines exact)")
if args.out:
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["page_line", "reference", "arabic_out", "latin_out", "arabic_err", "arabic_len", "latin_err", "latin_len"])
        w.writerows(rows)
