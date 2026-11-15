"""Build a local review page for the Kahawat-Kosh OCR (for a Gojri speaker to check).

Sample: N random entries from the "entries" pages (seeded) plus the M entries with the lowest confidence (to test
whether low confidence really marks errors). Each card shows the entry's band cut from the page image and the OCR
text (idiom, meaning) in editable boxes. Marks: OK, wrong (type the right text), unsure. Marks are kept in the browser
(localStorage) and can be downloaded as review_marks.json. Nothing is uploaded.

Run: py -3 -X utf8 scripts/ocr_eval/build_kahawat_review.py <ocr dir> [--n 120] [--low 40] [--seed 20261106]
Output: <ocr dir>/review/index.html (open in Chrome or Edge), review/sample.json. The folder holds crops of the printed
book: keep it local.
"""
import argparse
import base64
import html
import io
import json
import random
import re
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402
from ocr_kahawat import absorb_thin  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "pdfs" / "anjumshanasi" / "Kahawat-Kosh.pdf"
ap = argparse.ArgumentParser()
ap.add_argument("ocr_dir")
ap.add_argument("--n", type=int, default=120)
ap.add_argument("--low", type=int, default=40)
ap.add_argument("--seed", type=int, default=20261106)
ap.add_argument("--dpi", type=int, default=200)
ap.add_argument("--keep-sample", action="store_true", help="reuse review/sample.json (same cards, so earlier marks stay valid); only the crops change")
ap.add_argument("--only-marked", action="store_true", help="sample only entries with a pesh or zer (marks put in from the PDF)")
ap.add_argument("--exclude-sample", help="sample.json of an earlier review: skip its cards (same page, y within 15 px)")
args = ap.parse_args()
d = Path(args.ocr_dir)
ents = []
for f in sorted(d.glob("page_*.json")):
    info = json.loads(f.read_text(encoding="utf-8"))
    if info["kind"] != "entries":
        continue
    es = info["entries"]
    for k, e in enumerate(es):
        y1 = es[k + 1]["y"] if k + 1 < len(es) else e["y"] + int(0.3 * args.dpi)
        ents.append({"page": info["page"], "k": k + 1, "y0": e["y"], "y1": y1, "idiom": e["idiom"],
                     "meaning": e["meaning"], "conf": min(e["idiom_conf"], e["meaning_conf"]),
                     "merged": bool(e.get("merged")), "yr": e.get("yr", []), "yl": e.get("yl", [])})
if args.only_marked:
    ents = [e for e in ents if re.search("[ُِ]", e["idiom"] + e["meaning"])]
if args.exclude_sample:
    old = json.loads(Path(args.exclude_sample).read_text(encoding="utf-8"))
    ents = [e for e in ents if not any(o["page"] == e["page"] and abs(o["y0"] - e["y0"]) <= 15 for o in old)]
if not ents:
    sys.exit("no entries pages found in " + str(d))
kept = d / "review" / "sample.json"
if args.keep_sample and kept.exists():
    sample = json.loads(kept.read_text(encoding="utf-8"))  # same cards, same order, same ids
else:
    random.seed(args.seed)
    rand = random.sample(ents, min(args.n, len(ents)))
    seen = {(e["page"], e["k"]) for e in rand}
    low = [e for e in sorted(ents, key=lambda e: e["conf"]) if (e["page"], e["k"]) not in seen][: args.low]
    for e in rand:
        e["group"] = "random"
    for e in low:
        e["group"] = "low-confidence"
    sample = rand + low
    random.shuffle(sample)
doc = fitz.open(PDF)
cache = {}
bands_cache = {}


def page_bands(n):
    """Ink bands of a page: the text rows of both columns (same cut as the OCR), overlapping rows joined.
    Returns (bands, entry tops). A band holds every ink pixel of its rows, so tall strokes and tails are never cut."""
    info = json.loads((d / f"page_{n:03d}.json").read_text(encoding="utf-8"))
    xa, xb, y0, y1 = info["line"]
    if info.get("region"):
        y0, y1 = info["region"]
    im = cache[n]
    g = np.asarray(im)
    iv = []
    for reg in (g[y0:y1, xb + 3:], g[y0:y1, :max(1, xa - 3)]):
        iv += [(y0 + a, y0 + b) for a, b in absorb_thin(O.split_rows(reg < O.otsu(reg)))]
    iv.sort()
    bands = []
    for a, b in iv:
        if bands and a <= bands[-1][1]:
            bands[-1][1] = max(bands[-1][1], b)
        else:
            bands.append([a, b])
    return bands, sorted(x["y"] for x in info["entries"])


def fade_neighbour(piece, own_top, row_h):
    """The margin above the entry's own rows shows the bottom of the row above (the gap between entries is a few px).
    In that margin, ink that touches the crop's top edge or is larger than a mark is faded to grey; small separate pieces
    (pesh, zer, zabar, dots) stay black. Rows of the entry itself are never changed. In place."""
    from scipy import ndimage
    if own_top <= 2:
        return
    a = np.asarray(piece).copy()
    ink = a < O.otsu(a)
    lab, n = ndimage.label(ink, structure=np.ones((3, 3)))
    if n == 0:
        return
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if sl[0].start > 0 and h <= 0.45 * row_h and w <= 0.45 * row_h:
            continue  # a small piece that does not touch the top edge: a mark or a dot, keep it black
        zone = lab[sl[0].start:min(sl[0].stop, own_top), sl[1]] == k
        if zone.any():
            sub = a[sl[0].start:min(sl[0].stop, own_top), sl[1]]
            sub[zone] = 205
    piece.paste(Image.fromarray(a))


def crop(e):
    n = e["page"]
    if n not in cache:
        pix = doc[n - 1].get_pixmap(dpi=args.dpi, colorspace=fitz.csGRAY)
        cache[n] = Image.fromarray(np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width))
    im = cache[n]
    spans = (e.get("yr") or []) + (e.get("yl") or [])
    if spans:
        # the entry's own rows (both columns): the card shows exactly the text that is read, no row of a neighbour
        top, bot = min(a for a, _ in spans) - 18, max(b for _, b in spans) + 7
        buf = io.BytesIO()
        piece = im.crop((int(0.10 * im.width), max(0, top), int(0.66 * im.width), min(im.height, bot)))
        fade_neighbour(piece, min(a for a, _ in spans) - max(0, top), float(np.median([b - a for a, b in spans])))
        piece.save(buf, "PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    if n not in bands_cache:
        bands_cache[n] = page_bands(n)
    bands, tops = bands_cache[n]
    y = e["y0"]
    nxt = next((t for t in tops if t > y + 3), None)
    # the band that holds this entry's first idiom row, then the following bands that start before the next entry
    i0 = next((k for k, (a, b) in enumerate(bands) if a - 3 <= y <= b + 3), None)
    if i0 is None:
        i0 = min(range(len(bands)), key=lambda k: abs(bands[k][0] - y)) if bands else None
    if i0 is None:
        top, bot = y - 24, e["y1"] - 4
    else:
        last = i0
        while last + 1 < len(bands) and (bands[last + 1][0] < nxt - 3 if nxt is not None else bands[last + 1][0] - bands[last][1] <= 12):
            last += 1
        top, bot = bands[i0][0] - 18, bands[last][1] + 7
        if nxt is not None:  # never run into the next entry's idiom row
            bot = min(bot, nxt - 2) if bands[i0][1] >= nxt - 3 else bot
    box = (int(0.10 * im.width), max(0, top), int(0.66 * im.width), min(im.height, bot))
    buf = io.BytesIO()
    im.crop(box).save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


cards = []
for i, e in enumerate(sample):
    e["id"] = i
    cards.append(f'''<section class="card" data-id="{i}">
<div class="meta">#{i + 1} &middot; PDF page {e["page"]} entry {e["k"]} &middot; {e["group"]} &middot; confidence {e["conf"]:.2f}{' &middot; merged rows' if e["merged"] else ''}</div>
<img src="data:image/png;base64,{crop(e)}" alt="entry crop">
<div class="row"><label>Idiom (right column)</label><input dir="rtl" class="idiom" value="{html.escape(e["idiom"], quote=True)}"></div>
<div class="row"><label>Meaning (left column)</label><input dir="rtl" class="meaning" value="{html.escape(e["meaning"], quote=True)}"></div>
<div class="btns"><button data-m="ok">OK</button><button data-m="wrong">Wrong (I fixed the text)</button><button data-m="unsure">Unsure</button><span class="state"></span></div>
</section>''')
import hashlib
# the browser key depends on the sample, so marks of an older sample never show on new cards
KEYHASH = hashlib.md5(json.dumps([(e["page"], e["k"], e["idiom"], e["meaning"]) for e in sample], ensure_ascii=False).encode()).hexdigest()[:8]
page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kahawat-Kosh OCR review</title><style>
:root{--bg:#fafafa;--fg:#1a1a1a;--card:#fff;--line:#d8d8d8;--ok:#1b7f3b;--bad:#b3261e;--un:#8a6d00}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--card:#222;--line:#444;--ok:#5ad17b;--bad:#ff8a80;--un:#e6c34d}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}
main{max-width:980px;margin:0 auto;padding:12px 16px 80px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:14px 0}
.card img{max-width:100%;background:#fff;border:1px solid var(--line)}
.meta{font-size:13px;opacity:.7;margin-bottom:6px}
.row{display:flex;gap:8px;align-items:center;margin:6px 0}.row label{width:160px;font-size:13px;opacity:.8}
.row input{flex:1;font-size:20px;padding:6px;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:4px}
button{font:inherit;padding:6px 12px;margin-right:8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
.card.ok{border-color:var(--ok)}.card.wrong{border-color:var(--bad)}.card.unsure{border-color:var(--un)}
.state{font-size:13px}
</style></head><body><header><b>Kahawat-Kosh OCR review</b> &middot; <span id="count"></span>
<button id="dl">Download review_marks.json</button></header><main>
<p>For each card, compare the picture with the two text boxes. Click <b>OK</b> if both are right (spaces and tiny
punctuation do not matter). If a word is wrong, correct the text in the box, then click <b>Wrong</b>. Marks are saved in this browser.</p>
''' + "\n".join(cards) + '''
</main><script>
const KEY="kk_review_''' + KEYHASH + '''";let marks={};
try{marks=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(marks))}catch(e){}count()}
function count(){const v=Object.values(marks);document.getElementById("count").textContent=
 v.length+" of "+document.querySelectorAll(".card").length+" marked (OK "+v.filter(x=>x.m=="ok").length+", wrong "+v.filter(x=>x.m=="wrong").length+", unsure "+v.filter(x=>x.m=="unsure").length+")"}
document.querySelectorAll(".card").forEach(c=>{const id=c.dataset.id;
 const paint=()=>{const m=marks[id];c.classList.remove("ok","wrong","unsure");if(m){c.classList.add(m.m);c.querySelector(".state").textContent=m.m;
  if(m.idiom!=null){c.querySelector(".idiom").value=m.idiom;c.querySelector(".meaning").value=m.meaning}}};
 c.querySelectorAll("button").forEach(b=>b.onclick=()=>{marks[id]={m:b.dataset.m,idiom:c.querySelector(".idiom").value,meaning:c.querySelector(".meaning").value};save();paint()});paint()});
document.getElementById("dl").onclick=()=>{const blob=new Blob([JSON.stringify(marks,null,1)],{type:"application/json"});
 const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="review_marks.json";a.click()};
count();
</script></body></html>'''
out = d / "review"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(page, encoding="utf-8")
(out / "sample.json").write_text(json.dumps(sample, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(sample), "cards (", sum(e["group"] == "random" for e in sample), "random +", sum(e["group"] != "random" for e in sample), "lowest confidence ) ->", out / "index.html")
