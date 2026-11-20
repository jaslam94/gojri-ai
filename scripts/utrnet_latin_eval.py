"""How well does UTRNet-Large read the ENGLISH (Latin) parts of the 200 held-out lines?

Companion to utrnet_arabic_eval.py (same setup, same 200 lines). The Latin runs
are cut with the glyph boxes in the PDF (every run of glyphs that is not in the
Arabic font Batool). The reference is the text the PDF itself stores for those
glyphs, so it is exact. Scored on letters and digits only (spaces and punctuation
ignored): Levenshtein distance divided by reference characters. UTRNet normally
gets mirrored images (it reads right to left), so both mirrored and not mirrored
input are scored.

Run: py -3 -X utf8 scripts/utrnet_latin_eval.py --repo <UTRNet clone> --weights <large.pth>
"""
import argparse
import json
import math
import re
import sys
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(1, str(ROOT / "scripts" / "synth"))

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True)
ap.add_argument("--weights", required=True)
args = ap.parse_args()
sys.path.insert(2, args.repo)

import fitz  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402

import dump_batool_lines as D  # noqa: E402
import merge_decode_letters as M  # noqa: E402
import mine_batool_pairs as MB  # noqa: E402
from model import Model  # noqa: E402

H, W = 32, 400
glyphs = "".join(s.strip("\n") for s in open(Path(args.repo) / "UrduGlyphs.txt", encoding="utf-8")) + " "
chars = ["[CTCblank]"] + list(glyphs)
opt = Namespace(FeatureExtraction="HRNet", SequenceModeling="DBiLSTM", Prediction="CTC", imgH=H, imgW=W,
                num_fiducial=20, input_channel=1, output_channel=32, hidden_size=256, batch_max_length=100,
                rgb=False, device=torch.device("cpu"), character=glyphs, num_class=len(chars))
net = Model(opt)
st = torch.load(args.weights, map_location="cpu", weights_only=True)
net.load_state_dict({k.removeprefix("module."): v for k, v in st.items()})
net.eval()


def read(img, mirror):
    img = img.convert("L")
    if mirror:
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    w, h = img.size
    rw = W if math.ceil(H * w / h) > W else math.ceil(H * w / h)
    a = np.asarray(img.resize((rw, H), Image.Resampling.BICUBIC), dtype="float32") / 255.0
    t = torch.from_numpy((a - 0.5) / 0.5).unsqueeze(0)
    x = torch.zeros(1, H, W)
    x[:, :, :rw] = t
    if rw < W:
        x[:, :, rw:] = t[:, :, rw - 1].unsqueeze(2).expand(1, H, W - rw)
    with torch.no_grad():
        idx = net(x.unsqueeze(0)).argmax(2)[0].tolist()
    out, prev = [], 0
    for k in idx:
        if k != 0 and k != prev:
            out.append(chars[k])
        prev = k
    return "".join(out)


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


KEEP = re.compile(r"[A-Za-z0-9]")
doc = fitz.open(M.PDF)
pua = D.load_map()
base = ROOT / "data" / "synth" / "real_pairs"
review = [json.loads(line) for line in (ROOT / "data" / "reviews" / "dictionary-200-lines" / "labels_review_test.jsonl").open(encoding="utf-8")]


def line_boxes(page):
    labels = M.pass2_labels(page)
    rows = MB.cluster_rows_full(MB.page_chars_full(doc[page - 1]))
    texts = [re.sub(r"\s+", " ", D.fmt_line(bb["chars"], pua, wrap_batool=False)).strip() for _y, bb in rows]
    keep_folio = str(page) in labels
    return [bb for (_y, bb), t in zip(rows, texts) if t and (keep_folio or t != str(page))]


def latin_runs(bb):
    runs, cur = [], []
    for x0, x1, font, c, o in sorted(bb["chars"], key=lambda t: t[0]):
        if "Batool" in font or 0xE000 <= o <= 0xF8FF:
            if cur:
                runs.append(cur)
                cur = []
        else:
            cur.append((x0, x1, c))
    if cur:
        runs.append(cur)
    return [(min(a for a, _, _ in r), max(b for _, b, _ in r), "".join(c for _, _, c in r)) for r in runs]


pages, total, samples = {}, {True: [0, 0], False: [0, 0]}, []
n_runs = 0
for r in review:
    page, line = int(r["page_line"][5:9]), int(r["page_line"].split(":L")[1])
    bb = pages.setdefault(page, line_boxes(page))[line - 1]
    img = Image.open(base / r["image"]).convert("L")
    rx0 = max(0, int((bb["x0"] - MB.PAD_PT) * MB.ZOOM))
    for x0, x1, text in latin_runs(bb):
        ref = "".join(KEEP.findall(text))
        a, b = max(0, int(x0 * MB.ZOOM - rx0)), min(img.width, int(x1 * MB.ZOOM - rx0))
        if len(ref) < 3 or b - a < 12:
            continue
        n_runs += 1
        seg = img.crop((a, 0, b, img.height))
        for mirror in (True, False):
            hyp = read(seg, mirror)
            total[mirror][0] += edit_distance(ref, "".join(KEEP.findall(hyp)))
            total[mirror][1] += len(ref)
            if not mirror and len(samples) < 6 and len(ref) > 12:
                samples.append((r["page_line"], text, hyp))
print(f"{n_runs} English runs from {len(review)} lines")
for mirror in (True, False):
    e, n = total[mirror]
    print(f"UTRNet-Large on English runs, {'mirrored (its normal input)' if mirror else 'not mirrored'}: "
          f"letter and digit error {100 * e / n:.1f}% ({e} of {n} characters)")
for s in samples:
    print(s[0], "| PDF text:", s[1][:70], "| UTRNet (not mirrored):", s[2][:70])
