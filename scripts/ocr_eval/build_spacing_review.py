"""Build a local review page for the word spaces of the Kahawat-Kosh idioms (for a Gojri speaker).

Why: the OCR joins or splits words because the print has no clear word gaps (plans/RESEARCH-nastaliq-word-spacing.md).
We need gold lines with correct spaces to measure any fix. Each card shows the printed rows of one idiom (right column)
and the OCR text in an editable box. The speaker fixes the spaces (and any wrong letter) and clicks OK or Fixed.
Cards come from the entries of an OCR run, seeded random, without the cards already reviewed in earlier pages.
Marks live in the browser (localStorage); the page downloads spacing_marks.json. Nothing is uploaded.

Run: py -3 -X utf8 scripts/ocr_eval/build_spacing_review.py data/ocr/kahawat-pdfmarks-v2 [--n 200] [--seed 20261116]
Output: <ocr dir>/review_spacing/index.html and sample.json. The page holds crops of the printed book: keep it local.
"""
import argparse
import base64
import hashlib
import html
import io
import json
import random
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "pdfs" / "anjumshanasi" / "Kahawat-Kosh.pdf"
ap = argparse.ArgumentParser()
ap.add_argument("ocr_dir")
ap.add_argument("--n", type=int, default=200)
ap.add_argument("--seed", type=int, default=20261116)
ap.add_argument("--dpi", type=int, default=200)
ap.add_argument("--min-letters", type=int, default=8, help="skip idioms shorter than this (too little spacing to judge)")
ap.add_argument("--exclude", nargs="*", default=[ROOT / "data/ocr/kahawat-marks/sample.json", ROOT / "data/ocr/kahawat-pdfmarks/review/sample.json"],
                help="sample.json files of earlier reviews: their cards are skipped")
args = ap.parse_args()
d = Path(args.ocr_dir)

old = []
for f in args.exclude:
    f = Path(f)
    if f.exists():
        s = json.loads(f.read_text(encoding="utf-8"))
        old += list(s.values()) if isinstance(s, dict) else s
ents = []
for f in sorted(d.glob("page_*.json")):
    info = json.loads(f.read_text(encoding="utf-8"))
    if info.get("kind") != "entries":
        continue
    for k, e in enumerate(info["entries"]):
        txt = e["idiom"]
        if len([c for c in txt if c.isalpha()]) < args.min_letters or not e.get("yr"):
            continue
        if any(o["page"] == info["page"] and abs(o["y0"] - e["y"]) <= 15 for o in old):
            continue
        ents.append({"page": info["page"], "k": k + 1, "y0": e["y"], "text": txt, "yr": e["yr"], "xb": info["line"][1]})
random.seed(args.seed)
sample = random.sample(ents, min(args.n, len(ents)))
sample.sort(key=lambda e: (e["page"], e["y0"]))
doc = fitz.open(PDF)
cache = {}


def fade_neighbour(piece, own_top, row_h):
    """Fade ink of the row above that shows in the top margin (see build_kahawat_review.py). In place."""
    if own_top <= 2:
        return
    a = np.asarray(piece).copy()
    lab, n = ndimage.label(a < O.otsu(a), structure=np.ones((3, 3)))
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if sl[0].start > 0 and h <= 0.45 * row_h and w <= 0.45 * row_h:
            continue
        zone = lab[sl[0].start:min(sl[0].stop, own_top), sl[1]] == k
        if zone.any():
            a[sl[0].start:min(sl[0].stop, own_top), sl[1]][zone] = 205
    piece.paste(Image.fromarray(a))


def crop(e):
    n = e["page"]
    if n not in cache:
        pix = doc[n - 1].get_pixmap(dpi=args.dpi, colorspace=fitz.csGRAY)
        cache[n] = Image.fromarray(np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width))
    im = cache[n]
    spans = e["yr"]
    top, bot = min(a for a, _ in spans) - 18, max(b for _, b in spans) + 7
    piece = im.crop((max(0, e["xb"] - 4), max(0, top), int(0.80 * im.width), min(im.height, bot)))
    fade_neighbour(piece, min(a for a, _ in spans) - max(0, top), float(np.median([b - a for a, b in spans])))
    buf = io.BytesIO()
    piece.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


cards = []
for i, e in enumerate(sample):
    e["id"] = i
    cards.append(f'''<section class="card" data-id="{i}">
<div class="meta">#{i + 1} &middot; PDF page {e["page"]} entry {e["k"]} &middot; {len(e["yr"])} printed row(s)</div>
<img src="data:image/png;base64,{crop(e)}" alt="printed idiom">
<input dir="rtl" class="txt" value="{html.escape(e["text"], quote=True)}" data-orig="{html.escape(e["text"], quote=True)}">
<div class="btns"><button data-m="ok">OK, spaces right</button><button data-m="fixed">Fixed (I changed the text)</button><button data-m="unsure">Unsure</button><span class="state"></span></div>
</section>''')
KEYHASH = hashlib.md5(json.dumps([(e["page"], e["k"], e["text"]) for e in sample], ensure_ascii=False).encode()).hexdigest()[:8]
page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kahawat spacing review</title><style>
:root{--bg:#fafafa;--fg:#1a1a1a;--card:#fff;--line:#d8d8d8;--ok:#1b7f3b;--bad:#b3261e;--un:#8a6d00}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--card:#222;--line:#444;--ok:#5ad17b;--bad:#ff8a80;--un:#e6c34d}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}
main{max-width:980px;margin:0 auto;padding:12px 16px 80px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:14px 0}
.card img{max-width:100%;background:#fff;border:1px solid var(--line);display:block;margin-bottom:8px}
.meta{font-size:13px;opacity:.7;margin-bottom:6px}
.txt{width:100%;box-sizing:border-box;font-size:22px;padding:8px;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:4px;margin-bottom:8px}
button{font:inherit;padding:6px 12px;margin-right:8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
.card.ok{border-color:var(--ok)}.card.fixed{border-color:var(--bad)}.card.unsure{border-color:var(--un)}
.state{font-size:13px}
</style></head><body><header><b>Kahawat spacing review</b> &middot; <span id="count"></span>
<button id="dl">Download spacing_marks.json</button></header><main>
<p>Compare the picture with the text. Write the text as <b>words</b>, not as the book shows it: the book often has no gap
between real words, so do not follow its gaps. Correct the spaces in the box (a wrong letter may be fixed too). Click
<b>OK</b> if the text is already right, <b>Fixed</b> after you changed it, <b>Unsure</b> if you cannot tell. Keep the marks
(pesh, zer) as they are.</p>
<p><b>Rules</b> (decided with the speaker, 2026-11-16):</p>
<ol>
<li>A space goes between two words. Test: does the part have its own meaning here? If it does, it is a word.</li>
<li>Small words are separate words when they have their own meaning: <span dir="rtl">بھلا تے</span> (تے = then, so), کو، نا، ناں، تیں، وی، ہی.</li>
<li>The same letters can be part of one word. Then keep them joined: <span dir="rtl">کھاتے</span> is one word. Decide by the meaning in the line.</li>
<li>Helping verbs and compound verbs are separate words: <span dir="rtl">کر کے</span>, not <span dir="rtl">کرکے</span>.</li>
<li>An ending or prefix that is part of one word stays joined, with no gap.</li>
<li>If a case is not clear, click Unsure.</li>
</ol>
<p>Marks are saved in this browser; Download at the end.</p>
''' + "\n".join(cards) + '''
</main><script>
const KEY="kk_spacing_''' + KEYHASH + '''";let marks={};
try{marks=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(marks))}catch(e){}count()}
function count(){const v=Object.values(marks);document.getElementById("count").textContent=
 v.length+" of "+document.querySelectorAll(".card").length+" marked (OK "+v.filter(x=>x.m=="ok").length+", fixed "+v.filter(x=>x.m=="fixed").length+", unsure "+v.filter(x=>x.m=="unsure").length+")"}
document.querySelectorAll(".card").forEach(c=>{const id=c.dataset.id,t=c.querySelector(".txt");
 const paint=()=>{const m=marks[id];c.classList.remove("ok","fixed","unsure");if(m){c.classList.add(m.m);c.querySelector(".state").textContent=m.m;t.value=m.text}};
 c.querySelectorAll("button").forEach(b=>b.onclick=()=>{let m=b.dataset.m;if(m=="ok"&&t.value!==t.dataset.orig)m="fixed";marks[id]={m:m,text:t.value};save();paint()});paint()});
document.getElementById("dl").onclick=()=>{const blob=new Blob([JSON.stringify(marks,null,1)],{type:"application/json"});
 const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="spacing_marks.json";a.click()};
count();
</script></body></html>'''
out = d / "review_spacing"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(page, encoding="utf-8")
(out / "sample.json").write_text(json.dumps(sample, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(sample), "cards ->", out / "index.html")
