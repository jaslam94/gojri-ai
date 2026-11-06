"""Can Tesseract (English) tell Latin chunks from Arabic-script chunks, and how well does it read the Latin ones?

Input: a chunk folder from dump_script_chunks.py. For a balanced sample it runs
`tesseract <img> stdout --psm 7 -l eng tsv` and keeps the mean word confidence (0 to 100, -1 if no word).
Reports: accuracy of the rule "confidence >= T means Latin" for several T, the best T, and the English
character error (Levenshtein, spaces removed, case kept) of Tesseract on the Latin chunks.

Run: py -3 -X utf8 scripts/ocr_eval/eval_script_tesseract.py <chunk dir> [--n 300]
"""
import argparse
import csv
import io
import json
import random
import subprocess
from pathlib import Path

from PIL import Image

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
ap = argparse.ArgumentParser()
ap.add_argument("chunks")
ap.add_argument("--n", type=int, default=300, help="chunks per class")
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()
d = Path(args.chunks)
man = [json.loads(l) for l in (d / "manifest.jsonl").open(encoding="utf-8")]
random.seed(args.seed)
sample = []
for lab in ("arabic", "latin"):
    items = [m for m in man if m["label"] == lab]
    sample += random.sample(items, min(args.n, len(items)))


def ed(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def run(m):
    img = Image.open(d / m["file"]).convert("L")
    pad = 12  # white margin helps Tesseract on tight crops
    canvas = Image.new("L", (img.width + 2 * pad, img.height + 2 * pad), 255)
    canvas.paste(img, (pad, pad))
    buf = io.BytesIO(); canvas.save(buf, "PNG")
    p = subprocess.run([TESS, "stdin", "stdout", "--psm", "7", "-l", "eng", "tsv"], input=buf.getvalue(),
                       capture_output=True, timeout=60)
    rows = list(csv.reader(io.StringIO(p.stdout.decode("utf-8", "replace")), delimiter="\t", quoting=csv.QUOTE_NONE))
    words = [r for r in rows[1:] if len(r) >= 12 and r[0] == "5" and r[11].strip()]
    conf = sum(float(r[10]) for r in words) / len(words) if words else -1.0
    return conf, " ".join(r[11] for r in words)


res = []
for m in sample:
    conf, text = run(m)
    res.append((m, conf, text))

print(f"{len(res)} chunks ({sum(r[0]['label'] == 'arabic' for r in res)} arabic, {sum(r[0]['label'] == 'latin' for r in res)} latin)")
best = (0, None)
for t in (-1, 10, 20, 30, 40, 50, 60, 70, 80):
    ok = sum((c >= t and t >= 0) == (m["label"] == "latin") for m, c, _ in res if t >= 0) if t >= 0 else 0
    if t < 0:
        continue
    acc = ok / len(res)
    fa = sum(c >= t for m, c, _ in res if m["label"] == "arabic")  # Arabic called Latin
    fl = sum(c < t for m, c, _ in res if m["label"] == "latin")   # Latin called Arabic
    print(f"threshold {t:3d}: accuracy {100 * acc:5.1f}%  arabic->latin {fa:4d}  latin->arabic {fl:4d}")
    if acc > best[0]:
        best = (acc, t)
print("best threshold", best[1], f"accuracy {100 * best[0]:.1f}%")
lat = [(m, t) for m, c, t in res if m["label"] == "latin"]
e = sum(ed(m["text"].replace(" ", ""), t.replace(" ", "")) for m, t in lat)
n = sum(len(m["text"].replace(" ", "")) for m, t in lat)
print(f"Tesseract English on {len(lat)} Latin chunks: character error {100 * e / n:.1f}% ({e} of {n})")
