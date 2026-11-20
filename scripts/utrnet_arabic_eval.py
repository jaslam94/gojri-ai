"""Zero-shot UTRNet-Large on the Arabic parts of the 200 held-out dictionary lines.

Test set: data/reviews/dictionary-200-lines/labels_review_test.jsonl, the 200 lines the user
reviewed (one line per equal-size stratum of the dictionary, pages 26 to 498).
Each line crop (data/synth/real_pairs/img) is cut into its Arabic runs with the
glyph boxes stored in the PDF, so English text never reaches the model. Each run
is read by UTRNet-Large (CPU, no training) and the outputs are joined.

Score: Arabic-letter error against the user's fix (`text_fix`). Both sides are
NFC-normalised, short-vowel marks removed, only Arabic-block characters kept
(spaces and Latin dropped), then ك=ک and ه=ہ are folded (ھ stays separate). Error
is the Levenshtein distance (insert, delete, substitute) summed over the lines,
divided by the number of reference letters.

Results on 2026-11-05 (1,400 reference letters): UTRNet on Arabic runs 2.1% at
--pads 0 (30 letters, 178 of 200 lines exact), 2.9% at 2, 10.9% at 6 (the margin
then catches a sliver of the "(" and UTRNet adds an alef). See
data/utrnet-test/README.md for the full table and examples.

Setup (UTRNet is third-party code, CC BY-NC-SA 4.0, research use):
  1. git clone https://github.com/abdur75648/UTRNet-High-Resolution-Urdu-Text-Recognition
     into a new folder (commit 049c2d6 or later).
  2. Download UTRNet-Large from the link in that repo's README (Google Drive) as large.pth.
  3. py -3 -X utf8 scripts/utrnet_arabic_eval.py --repo <clone folder> --weights <large.pth>
     Full report (about 15 minutes on CPU):
     ... --pads 0 2 6 --crnn-base <baseline crnn_last.pt> --crnn-new <new crnn_last.pt>
         --report-dir data/utrnet-test
Only model.py and modules/ from the clone are imported. Weights load with weights_only=True.
"""
import argparse
import csv
import json
import math
import re
import sys
import unicodedata
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(1, str(ROOT / "scripts" / "synth"))

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True, help="folder of the UTRNet clone")
ap.add_argument("--weights", required=True, help="UTRNet-Large .pth file")
ap.add_argument("--pads", type=int, nargs="+", default=[0], help="pixel margins around each Arabic run")
ap.add_argument("--crnn-base", default="", help="our baseline CRNN crnn_last.pt (optional)")
ap.add_argument("--crnn-new", default="", help="our retrained CRNN crnn_last.pt (optional)")
ap.add_argument("--report-dir", default="", help="write results.tsv, summary.json and examples/ here")
args = ap.parse_args()
sys.path.insert(2, args.repo)

import fitz  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import dump_batool_lines as D  # noqa: E402
import merge_decode_letters as M  # noqa: E402
import mine_batool_pairs as MB  # noqa: E402
from model import Model  # noqa: E402  (UTRNet; the only file imported from the clone)

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
    """UTRNet input: grey, mirrored, 32 px high, padded on the right to 400 px, scaled to [-1, 1]."""
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


MARKS = re.compile(r"[ً-ٰٟۖ-ۭؐ-ؚ]")
ARAB = re.compile(r"[؀-ۿ]")
FOLD = str.maketrans({"ك": "ک", "ه": "ہ"})


def arabic(s):
    return "".join(ARAB.findall(MARKS.sub("", unicodedata.normalize("NFC", s)))).translate(FOLD)


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


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


def arabic_runs(bb):
    runs, cur = [], []
    for x0, x1, font, _c, o in sorted(bb["chars"], key=lambda t: t[0]):
        if "Batool" in font or 0xE000 <= o <= 0xF8FF:
            cur.append((x0, x1))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [(min(a for a, _ in r), max(b for _, b in r)) for r in runs]


def cut(img, bb, pad):
    """Arabic runs of one line crop, left to right, with `pad` pixels kept on each side."""
    rx0 = max(0, int((bb["x0"] - MB.PAD_PT) * MB.ZOOM))  # crop origin, as in mine_batool_pairs.py
    parts = []
    for x0, x1 in arabic_runs(bb):
        a, b = max(0, int(x0 * MB.ZOOM - rx0) - pad), min(img.width, int(x1 * MB.ZOOM - rx0) + pad)
        if b - a >= 12:
            parts.append(img.crop((a, 0, b, img.height)))
    return parts


def load_crnn(path):
    import ocr_train as T
    ck = torch.load(path, map_location="cpu")
    cs = T.Charset([""])
    cs.chars, cs.idx = ck["chars"], {c: i for i, c in enumerate(ck["chars"])}
    m = T.CRNN(len(cs.chars))
    m.load_state_dict(ck["state"])
    return T, m.eval(), cs


def crnn_read(model, img):
    T, m, cs = model
    nw = max(16, min(T.MAX_W, int(img.width * T.IMG_H / img.height)))
    a = 1.0 - np.asarray(img.convert("L").resize((nw, T.IMG_H), Image.LANCZOS), dtype="float32") / 255.0
    with torch.no_grad():
        o = m(torch.from_numpy(a).unsqueeze(0).unsqueeze(0))
    return cs.decode(o.argmax(2).permute(1, 0).tolist()[0])


crnns = {}
if args.crnn_base:
    crnns["crnn_baseline"] = load_crnn(args.crnn_base)
if args.crnn_new:
    crnns["crnn_new"] = load_crnn(args.crnn_new)

pages, boxes = {}, {}
outs = {}  # system name -> page_line -> output
for r in review:
    page, line = int(r["page_line"][5:9]), int(r["page_line"].split(":L")[1])
    boxes[r["page_line"]] = pages.setdefault(page, line_boxes(page))[line - 1]
for pad in args.pads:
    name = f"utrnet_pad{pad}"
    outs[name] = {}
    for r in review:
        img = Image.open(base / r["image"]).convert("L")
        outs[name][r["page_line"]] = " ".join(utrnet_read(c) for c in cut(img, boxes[r["page_line"]], pad))
    print(name, "done", flush=True)
if args.report_dir:
    outs["utrnet_whole_line"] = {r["page_line"]: utrnet_read(Image.open(base / r["image"])) for r in review}
for cname, model in crnns.items():
    outs[f"{cname}_whole_line"] = {r["page_line"]: crnn_read(model, Image.open(base / r["image"])) for r in review}
    if args.report_dir:
        outs[f"{cname}_arabic_runs_pad0"] = {
            r["page_line"]: " ".join(crnn_read(model, c) for c in cut(Image.open(base / r["image"]).convert("L"), boxes[r["page_line"]], 0))
            for r in review}


def score(system):
    errors = letters = exact = 0
    for r in review:
        ref = arabic(r["text_fix"])
        e = edit_distance(ref, arabic(outs[system][r["page_line"]]))
        errors += e
        letters += len(ref)
        exact += e == 0
    return errors, letters, exact


summary = {}
for system in outs:
    e, n, x = score(system)
    summary[system] = {"errors": e, "letters": n, "error_pct": round(100 * e / n, 1), "lines_exact": x, "lines": len(review)}
    print(f"{system:32s} Arabic-letter error {100 * e / n:5.1f}% ({e} of {n} letters); {x} of {len(review)} lines exact")

if args.report_dir:
    out = Path(args.report_dir)
    (out / "examples").mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    cols = ["page_line", "reference_text_fix", "reference_arabic"] + list(outs)
    with (out / "results.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(cols + ["utrnet_pad0_exact"])
        for r in review:
            k = r["page_line"]
            w.writerow([k, r["text_fix"], arabic(r["text_fix"])] + [arabic(outs[s][k]) for s in outs]
                       + [int(arabic(r["text_fix"]) == arabic(outs["utrnet_pad0"][k]))])

    def exact(k):
        return arabic(next(r for r in review if r["page_line"] == k)["text_fix"]) == arabic(outs["utrnet_pad0"][k])

    ok = sorted(r["page_line"] for r in review if exact(r["page_line"]))
    pick = {"exact, short": next(k for k in ok if 5 <= len(arabic(next(r for r in review if r["page_line"] == k)["text_fix"])) <= 10),
            "exact, medium": next(k for k in ok if 15 <= len(arabic(next(r for r in review if r["page_line"] == k)["text_fix"])) <= 24),
            "exact, longest": max(ok, key=lambda k: len(arabic(next(r for r in review if r["page_line"] == k)["text_fix"])))}
    for k in ("page-0164:L24", "page-0227:L3", "page-0215:L15", "page-0087:L7", "page-0050:L2", "page-0066:L9"):
        pick[f"example {k}"] = k
    examples = {}
    for label, k in pick.items():
        r = next(x for x in review if x["page_line"] == k)
        img = Image.open(base / r["image"]).convert("L")
        rows = [("whole line as printed", img)]
        for i, c in enumerate(cut(img, boxes[k], 0), 1):
            rows.append((f"Arabic run {i}, margin 0 px (what UTRNet reads)", c))
        if k == "page-0066:L9":
            for i, c in enumerate(cut(img, boxes[k], 6), 1):
                rows.append((f"Arabic run {i}, margin 6 px (first try: the ( sliver at the right edge)", c))
        W = max(c.width for _, c in rows) + 12
        H = sum(c.height + 20 for _, c in rows)
        sheet = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(sheet)
        y = 0
        for text, c in rows:
            d.text((4, y + 3), text, fill=(150, 0, 0))
            sheet.paste(c.convert("RGB"), (0, y + 18))
            y += c.height + 20
        name = k.replace(":", "_").replace("page-", "p") + ".png"
        sheet.save(out / "examples" / name, optimize=True)
        examples[k] = {"group": label, "image": f"examples/{name}", "reference_arabic": arabic(r["text_fix"]),
                       **{s: arabic(outs[s][k]) for s in outs if s in ("utrnet_pad0", "utrnet_pad6", "crnn_baseline_whole_line", "crnn_new_whole_line")}}
    (out / "examples.json").write_text(json.dumps(examples, ensure_ascii=False, indent=1), encoding="utf-8")
    print("report written to", out)
