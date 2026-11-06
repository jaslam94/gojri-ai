"""Cut labeled script chunks (Arabic-script run vs Latin run) from real dictionary line images.

Glyph boxes from the dictionary PDF give the truth: a run of Batool/PUA characters is Arabic script, a run of
other characters (English words, digits, brackets) is Latin. This is training/test data for a script detector
and a test for an English reader. The 200 reviewed lines (labels_review_test.jsonl) are never used.

Run: py -3 -X utf8 scripts/ocr_eval/dump_script_chunks.py <out dir> [--every 6] [--limit-lines 3000]
Output: <out dir>/<label>_<page_line>_<i>.png and manifest.jsonl (label, page, text for Latin chunks).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(1, str(ROOT / "scripts" / "synth"))
import fitz  # noqa: E402
from PIL import Image  # noqa: E402

import dump_batool_lines as D  # noqa: E402
import merge_decode_letters as M  # noqa: E402
import mine_batool_pairs as MB  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--every", type=int, default=6, help="use pages where page %% every == 0")
ap.add_argument("--limit-lines", type=int, default=3000)
args = ap.parse_args()
out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

base = ROOT / "data" / "synth" / "real_pairs"
review = {json.loads(l)["page_line"] for l in (base / "labels_review_test.jsonl").open(encoding="utf-8")}
rows = [json.loads(l) for l in (base / "labels_merged_clean.jsonl").open(encoding="utf-8")]
rows = [r for r in rows if not r["folio"] and r["page_line"] not in review
        and int(r["page_line"][5:9]) % args.every == 0][: args.limit_lines]

doc = fitz.open(M.PDF); pua = D.load_map()
pages = {}


def line_boxes(page):
    labels = M.pass2_labels(page)
    rws = MB.cluster_rows_full(MB.page_chars_full(doc[page - 1]))
    texts = [re.sub(r"\s+", " ", D.fmt_line(bb["chars"], pua, wrap_batool=False)).strip() for _y, bb in rws]
    keep = str(page) in labels
    return [bb for (_y, bb), t in zip(rws, texts) if t and (keep or t != str(page))]


def is_arabic(font, o):
    return "Batool" in font or 0xE000 <= o <= 0xF8FF


def runs(bb):
    """[(label, x0, x1, text)] left to right."""
    res, cur, cur_lab = [], [], None
    for x0, x1, font, c, o in sorted(bb["chars"], key=lambda t: t[0]):
        lab = "arabic" if is_arabic(font, o) else "latin"
        if lab != cur_lab and cur:
            res.append((cur_lab, cur))
            cur = []
        cur_lab = lab
        cur.append((x0, x1, c))
    if cur:
        res.append((cur_lab, cur))
    return [(lab, min(a for a, _, _ in r), max(b for _, b, _ in r), "".join(c for _, _, c in r).strip()) for lab, r in res]


man, n = [], 0
for r in rows:
    page, line = int(r["page_line"][5:9]), int(r["page_line"].split(":L")[1])
    try:
        bb = pages.setdefault(page, line_boxes(page))[line - 1]
    except IndexError:
        continue
    img = Image.open(base / r["image"]).convert("RGB")
    rx0 = max(0, int((bb["x0"] - MB.PAD_PT) * MB.ZOOM))
    for i, (lab, x0, x1, text) in enumerate(runs(bb)):
        a, b = max(0, int(x0 * MB.ZOOM - rx0)), min(img.width, int(x1 * MB.ZOOM - rx0))
        if b - a < 12 or (lab == "latin" and len(text) < 2):
            continue
        name = f"{lab}_{r['page_line'].replace(':', '_')}_{i}.png"
        img.crop((a, 0, b, img.height)).save(out / name)
        man.append({"file": name, "label": lab, "page": page, "page_line": r["page_line"],
                    "text": text if lab == "latin" else ""})
        n += 1
(out / "manifest.jsonl").write_text("\n".join(json.dumps(m, ensure_ascii=False) for m in man) + "\n", encoding="utf-8")
print(n, "chunks from", len(rows), "lines;", sum(m["label"] == "arabic" for m in man), "arabic,",
      sum(m["label"] == "latin" for m in man), "latin")
