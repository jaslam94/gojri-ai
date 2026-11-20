"""Per-column script labels for real dictionary line images (training data for a script segmenter).

For every line image the PDF glyph boxes give runs of Arabic-script (Batool/PUA fonts) and Latin characters.
Each pixel column of the image gets a class: 0 gap, 1 Arabic script, 2 Latin. Images are resized to a height of
64 px (labels are resized to match). Output is a pickle (own data, trusted) with two splits:
  test  = the 200 reviewed lines (labels_review_test.jsonl)
  train = all other non-folio lines whose PAGE has no reviewed line (so no page appears in both splits)

Run: py -3 -X utf8 scripts/ocr_eval/build_segmenter_data.py <out.pkl> [--limit N]
"""
import argparse
import json
import gzip
import pickle
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(1, str(ROOT / "scripts" / "synth"))
import fitz  # noqa: E402
from PIL import Image  # noqa: E402

import dump_batool_lines as D  # noqa: E402
import merge_decode_letters as M  # noqa: E402
import mine_batool_pairs as MB  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--base", default="", help="existing pickle to extend instead of rebuilding the real lines")
ap.add_argument("--synth", type=int, default=0, help="add N pure-Arabic synthetic story lines (data/synth/line_full, source fli)")
args = ap.parse_args()
H = 64
base = ROOT / "data" / "synth" / "real_pairs"
review = [json.loads(l) for l in (ROOT / "data" / "reviews" / "dictionary-200-lines" / "labels_review_test.jsonl").open(encoding="utf-8")]
rev_keys = {r["page_line"] for r in review}
rev_pages = {int(k[5:9]) for k in rev_keys}
allrows = [json.loads(l) for l in (base / "labels_merged_clean.jsonl").open(encoding="utf-8")]
train_rows = [r for r in allrows if not r["folio"] and int(r["page_line"][5:9]) not in rev_pages]
if args.limit:
    train_rows = train_rows[: args.limit]

doc = fitz.open(M.PDF); pua = D.load_map()
cache = {}


def line_boxes(page):
    labels = M.pass2_labels(page)
    rws = MB.cluster_rows_full(MB.page_chars_full(doc[page - 1]))
    texts = [re.sub(r"\s+", " ", D.fmt_line(bb["chars"], pua, wrap_batool=False)).strip() for _y, bb in rws]
    keep = str(page) in labels
    return [bb for (_y, bb), t in zip(rws, texts) if t and (keep or t != str(page))]


def column_labels(bb, width):
    rx0 = max(0, int((bb["x0"] - MB.PAD_PT) * MB.ZOOM))
    lab = np.zeros(width, dtype=np.uint8)
    for x0, x1, font, c, o in bb["chars"]:
        if not c.strip():
            continue  # spaces stay gap
        cls = 1 if ("Batool" in font or 0xE000 <= o <= 0xF8FF) else 2
        a, b = max(0, int(x0 * MB.ZOOM - rx0)), min(width, int(x1 * MB.ZOOM - rx0) + 1)
        lab[a:b] = cls
    # fill gaps between same-class neighbours inside a word (letters of one script with no space char)
    out = lab.copy()
    runs = []
    i = 0
    while i < width:
        if lab[i] == 0:
            i += 1
            continue
        j = i
        while j < width and lab[j] == lab[i]:
            j += 1
        runs.append((i, j, lab[i]))
        i = j
    return out, runs


def make(rows, split):
    items = []
    for k, r in enumerate(rows):
        page, line = int(r["page_line"][5:9]), int(r["page_line"].split(":L")[1])
        try:
            bb = cache.setdefault(page, line_boxes(page))[line - 1]
        except IndexError:
            continue
        img = Image.open(base / r["image"]).convert("L")
        lab, _ = column_labels(bb, img.width)
        s = H / img.height
        w2 = max(8, round(img.width * s))
        im2 = np.asarray(img.resize((w2, H), Image.Resampling.BICUBIC), dtype=np.uint8)
        lab2 = np.asarray(Image.fromarray(lab[None, :]).resize((w2, 1), Image.Resampling.NEAREST), dtype=np.uint8)[0]
        items.append({"key": r["page_line"], "split": split, "img": im2, "lab": lab2, "scale": s})
        if (k + 1) % 1000 == 0:
            print(split, k + 1, "of", len(rows), flush=True)
    return items


def synth_items(n):
    """Pure-Arabic rendered story lines. Labels come from the ink columns of the CLEAN image (gaps >= 0.10 x height
    are class 0, the rest of the text span is Arabic); the image used is the clean one or one of its 3 degraded copies."""
    import random
    random.seed(0)
    sdir = ROOT / "data" / "synth" / "line_full"
    rows_ = [json.loads(l) for l in (sdir / "labels.jsonl").open(encoding="utf-8")]
    rows_ = [r for r in rows_ if r["source_tag"] != "dictionary" and not re.search(r"[A-Za-z]", r["text"])]
    random.shuffle(rows_)
    items = []
    for r in rows_[:n]:
        clean = Image.open(sdir / r["image"]).convert("L")
        g = np.asarray(clean)
        ink = g < 128
        cols = ink.sum(axis=0) > 0
        xs = np.where(cols)[0]
        if len(xs) == 0:
            continue
        lab = np.zeros(g.shape[1], dtype=np.uint8)
        lab[xs[0]: xs[-1] + 1] = 1
        gapmin = max(4, int(0.10 * g.shape[0]))
        i = xs[0]
        while i <= xs[-1]:
            if not cols[i]:
                j = i
                while j <= xs[-1] and not cols[j]:
                    j += 1
                if j - i >= gapmin:
                    lab[i:j] = 0
                i = j
            else:
                i += 1
        name = r["image"] if random.random() < 0.25 else r["image"].replace(".png", f"_v{random.randint(1, 3)}.png")
        img = Image.open(sdir / name).convert("L")
        s = H / img.height
        w2 = max(8, round(img.width * s))
        im2 = np.asarray(img.resize((w2, H), Image.Resampling.BICUBIC), dtype=np.uint8)
        lab2 = np.asarray(Image.fromarray(lab[None, :]).resize((w2, 1), Image.Resampling.NEAREST), dtype=np.uint8)[0]
        items.append({"key": "synth:" + name, "split": "train", "img": im2, "lab": lab2, "scale": s})
    return items


if args.base:
    data = pickle.load(gzip.open(args.base, "rb"))
else:
    data = make(train_rows, "train") + make(review, "test")
if args.synth:
    extra = synth_items(args.synth)
    print("added", len(extra), "synthetic pure-Arabic lines")
    data += extra
pickle.dump(data, gzip.open(args.out, "wb", compresslevel=3))
cls = np.concatenate([d["lab"] for d in data if d["split"] == "train"])
print(len(data), "items;", sum(d["split"] == "train" for d in data), "train,", sum(d["split"] == "test" for d in data), "test")
print("train column share: gap %.2f arabic %.2f latin %.2f" % tuple(np.bincount(cls, minlength=3) / len(cls)))
