"""Build a local, text-only page where the speaker tags prose rows as Gojri, Urdu, Mixed, Other or Unsure.

Why: no public language-ID model knows Gojri, so the tagger is trained on free labels (FLI, Kahawat idiom/meaning) and tested on rows
that the speaker tags (plans/RESEARCH-urdu-gojri-language-id-and-mixed-spacing.md, Q6). This is the only speaker work the tagger needs.
Rows: the prose rows that the speaker already reviewed (review_marks.json; the speaker's own text where he fixed it) plus new random
rows of the full OCR run (prose-aws-full2). Rows under MIN letters, headers, and rows with Latin letters are left out.
The page shows no model output, so the tags are not biased. Keys 1 to 5 tag the marked row and go to the next one.

Run: py -3 -X utf8 scripts/ocr_eval/build_lang_tag_review.py [--new 120] [--seed 20261123]
Output: data/ocr/prose-words/lang_tag_review.html and lang_tag_sample.json (local; the page holds book text, keep it local).
"""
import argparse
import hashlib
import html
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "data/ocr/prose-aws-full2"
REV = ROOT / "data/reviews/prose-banjara-dildarya/review_marks.json"
OUT = ROOT / "data/ocr/prose-words"
MIN = 20


def n_arabic(s):
    return sum(1 for c in s if "؀" <= c <= "ۿ" and c.isalpha())


def punct(s):
    return re.sub(r"([۔،])(?=[^\s۔،])", r"\1 ", s)


def ok(s):
    return n_arabic(s) >= MIN and not re.search(r"[A-Za-z]", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", type=int, default=120)
    ap.add_argument("--seed", type=int, default=20261123)
    a = ap.parse_args()
    rows, seen = [], set()
    rev = json.loads(REV.read_text(encoding="utf-8"))
    for k, x in sorted(rev.items(), key=lambda t: (t[0].split("|")[0], int(t[0].split("|")[1]), int(t[0].split("|")[2]))):
        if x["m"] == "unsure":
            continue
        text = punct(x["text"] if x["m"] == "wrong" else x["ocr"])
        if ok(text):
            book, page, row = k.split("|")
            rows.append({"key": k, "book": book, "page": int(page), "row": int(row), "text": text, "origin": "reviewed"})
            seen.add(k)
    pool = []
    for book in ("Banjara", "Dil-Darya"):
        for f in sorted((RUN / book / "dpi300").glob("page_*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            for r in d["rows"]:
                key = f"{book}|{d['page']}|{r['row']}"
                if key in seen or "header" in (r.get("flags") or []):
                    continue
                t = punct(r["text"])
                if ok(t):
                    pool.append({"key": key, "book": book, "page": d["page"], "row": r["row"], "text": t, "origin": "new"})
    random.Random(a.seed).shuffle(pool)
    rows += pool[: a.new]
    random.Random(a.seed + 1).shuffle(rows)
    for i, r in enumerate(rows):
        r["id"] = i
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lang_tag_sample.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    cards = "\n".join(
        f'<section class="card" data-id="{r["id"]}"><div class="meta">#{r["id"] + 1} &middot; {r["book"]} p.{r["page"]}</div>'
        f'<div class="txt" dir="rtl">{html.escape(r["text"])}</div>'
        '<div class="btns"><button data-m="gju">1 Gojri</button><button data-m="urd">2 Urdu</button><button data-m="mixed">3 Mixed</button>'
        '<button data-m="other">4 Other</button><button data-m="unsure">5 Unsure</button><span class="state"></span></div></section>'
        for r in rows
    )
    key = "lang_tag_" + hashlib.md5(json.dumps([r["key"] for r in rows]).encode()).hexdigest()[:8]
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gojri or Urdu tagging</title><style>
:root{--bg:#fafafa;--fg:#1a1a1a;--card:#fff;--line:#d8d8d8;--cur:#1a5fb4;--g:#1b7f3b;--u:#a35200;--m:#7a3db8;--o:#555;--s:#8a6d00}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--card:#222;--line:#444;--cur:#6aa9ff;--g:#5ad17b;--u:#ffb066;--m:#c9a0ff;--o:#aaa;--s:#e6c34d}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}
main{max-width:900px;margin:0 auto;padding:12px 16px 80px}
.card{background:var(--card);border:2px solid var(--line);border-radius:8px;padding:10px 12px;margin:10px 0}
.card.cur{border-color:var(--cur)}
.meta{font-size:13px;opacity:.7}
.txt{font-size:24px;line-height:1.9;margin:6px 0}
button{font:inherit;padding:6px 12px;margin-right:6px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
.card.gju{border-color:var(--g)}.card.urd{border-color:var(--u)}.card.mixed{border-color:var(--m)}.card.other{border-color:var(--o)}.card.unsure{border-color:var(--s)}
.state{font-size:13px;margin-left:6px}
</style></head><body><header><b>Gojri or Urdu?</b> &middot; <span id="count"></span>
<button id="next">Next unmarked</button> <button id="dl">Download lang_tags.json</button></header><main>
<p>Tag the <b>language of the line</b>, by its grammar and words (not by the topic).
<b>Gojri</b>: the line is Gojri. <b>Urdu</b>: the line is Urdu. <b>Mixed</b>: Urdu with Gojri words or phrases in it, or Gojri with Urdu phrases.
<b>Other</b>: Arabic, Persian, a name list, a reference or a number table. <b>Unsure</b>: you cannot tell.
Keys <b>1 to 5</b> tag the blue row and go to the next one; arrow keys move; a button click marks that card. Marks stay in this browser; download at the end.
You can stop at any time and continue later.</p>
""" + cards + """
</main><script>
const KEY=\"""" + key + """\";let marks={};
try{marks=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
const cards=[...document.querySelectorAll(".card")];let cur=0;
const NAMES={gju:"Gojri",urd:"Urdu",mixed:"Mixed",other:"Other",unsure:"Unsure"},KEYS={"1":"gju","2":"urd","3":"mixed","4":"other","5":"unsure"};
function save(){try{localStorage.setItem(KEY,JSON.stringify(marks))}catch(e){}count()}
function count(){const v=Object.values(marks);const c=m=>v.filter(x=>x==m).length;
 document.getElementById("count").textContent=v.length+" of "+cards.length+" tagged (Gojri "+c("gju")+", Urdu "+c("urd")+", mixed "+c("mixed")+", other "+c("other")+", unsure "+c("unsure")+")"}
function paint(c){const id=c.dataset.id,m=marks[id];c.classList.remove("gju","urd","mixed","other","unsure");
 if(m){c.classList.add(m);c.querySelector(".state").textContent=NAMES[m]}else c.querySelector(".state").textContent=""}
function show(i){cur=Math.max(0,Math.min(cards.length-1,i));cards.forEach((c,k)=>c.classList.toggle("cur",k==cur));cards[cur].scrollIntoView({block:"center"})}
function mark(c,m){marks[c.dataset.id]=m;save();paint(c)}
cards.forEach((c,i)=>{paint(c);c.querySelectorAll("button").forEach(b=>b.onclick=()=>{mark(c,b.dataset.m);show(i+1)});c.querySelector(".txt").onclick=()=>show(i)});
document.addEventListener("keydown",e=>{if(KEYS[e.key]){mark(cards[cur],KEYS[e.key]);show(cur+1);e.preventDefault()}
 else if(e.key=="ArrowDown"){show(cur+1);e.preventDefault()}else if(e.key=="ArrowUp"){show(cur-1);e.preventDefault()}});
document.getElementById("next").onclick=()=>{const i=cards.findIndex(c=>!marks[c.dataset.id]);if(i>=0)show(i)};
document.getElementById("dl").onclick=()=>{const blob=new Blob([JSON.stringify(marks,null,1)],{type:"application/json"});
 const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="lang_tags.json";a.click()};
count();const first=cards.findIndex(c=>!marks[c.dataset.id]);show(first>=0?first:0);
</script></body></html>"""
    (OUT / "lang_tag_review.html").write_text(page, encoding="utf-8")
    print(len(rows), "rows (", sum(r["origin"] == "reviewed" for r in rows), "reviewed,", sum(r["origin"] == "new" for r in rows), "new ) ->", OUT / "lang_tag_review.html")


if __name__ == "__main__":
    main()
