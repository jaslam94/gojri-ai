"""Second pass of the language tagging: show the rows the speaker tagged Mixed or Unsure again, with the lines around them.

Why (speaker, 2026-11-24): Gojri and Urdu are sometimes 100% the same (names of people and places, for example قلی قطب شاہ، ملا وجہیؔ),
so one row alone can not be tagged. The page shows CONTEXT rows before and after the row (same book, in reading order, across a page
break too). A new tag `same` means: in this row the two languages write the same (names, places, references). Keys 1 to 6.

Run: py -3 -X utf8 scripts/ocr_eval/build_lang_context_review.py lang_tags.json [--context 2] [--labels mixed unsure]
Output: data/ocr/prose-words/lang_context_review.html and lang_context_sample.json (local; the page holds book text).
"""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "data/ocr/prose-aws-full2"
OUT = ROOT / "data/ocr/prose-words"


def punct(s):
    return re.sub(r"([۔،])(?=[^\s۔،])", r"\1 ", s)


def book_rows(book):
    seq = []
    for f in sorted((RUN / book / "dpi300").glob("page_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for r in d["rows"]:
            seq.append({"key": f"{book}|{d['page']}|{r['row']}", "page": d["page"], "text": punct(r["text"]), "header": "header" in (r.get("flags") or [])})
    return seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tags")
    ap.add_argument("--context", type=int, default=2)
    ap.add_argument("--labels", nargs="+", default=["mixed", "unsure"])
    a = ap.parse_args()
    tags = json.loads(Path(a.tags).read_text(encoding="utf-8"))
    sample = {str(r["id"]): r for r in json.loads((OUT / "lang_tag_sample.json").read_text(encoding="utf-8"))}
    books = {}
    items = []
    for k, v in tags.items():
        if v not in a.labels:
            continue
        r = sample[k]
        seq = books.setdefault(r["book"], book_rows(r["book"]))
        body = [x for x in seq if not x["header"]]
        i = next(j for j, x in enumerate(body) if x["key"] == r["key"])
        items.append({"key": r["key"], "book": r["book"], "page": r["page"], "old": v, "text": r["text"],
                      "before": [x["text"] for x in body[max(0, i - a.context):i]], "after": [x["text"] for x in body[i + 1:i + 1 + a.context]]})
    cards = []
    for n, it in enumerate(items):
        it["id"] = n
        ctx = lambda L: "".join(f'<div class="ctx" dir="rtl">{html.escape(t)}</div>' for t in L)
        cards.append(f'<section class="card" data-id="{n}"><div class="meta">#{n + 1} &middot; {it["book"]} p.{it["page"]} &middot; you tagged it: {it["old"]}</div>'
                     f'{ctx(it["before"])}<div class="txt" dir="rtl">{html.escape(it["text"])}</div>{ctx(it["after"])}'
                     '<div class="btns"><button data-m="gju">1 Gojri</button><button data-m="urd">2 Urdu</button><button data-m="same">3 Same in both</button>'
                     '<button data-m="mixed">4 Mixed</button><button data-m="other">5 Other</button><button data-m="unsure">6 Unsure</button><span class="state"></span></div></section>')
    key = "lang_ctx_" + hashlib.md5(json.dumps([i["key"] for i in items]).encode()).hexdigest()[:8]
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gojri or Urdu, with context</title><style>
:root{--bg:#fafafa;--fg:#1a1a1a;--card:#fff;--line:#d8d8d8;--hi:#fff6c8}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--card:#222;--line:#444;--hi:#3a3510}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}
main{max-width:900px;margin:0 auto;padding:12px 16px 80px}
.card{background:var(--card);border:2px solid var(--line);border-radius:8px;padding:10px 12px;margin:14px 0}
.meta{font-size:13px;opacity:.7}
.ctx{font-size:20px;line-height:1.8;opacity:.6}
.txt{font-size:24px;line-height:1.9;margin:4px 0;background:var(--hi);border-radius:4px;padding:2px 6px}
button{font:inherit;padding:6px 12px;margin:6px 6px 0 0;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
.card.done{border-color:#1b7f3b}.state{font-size:13px;margin-left:6px}
</style></head><body><header><b>Tag the yellow row, with its context</b> &middot; <span id="count"></span> <button id="dl">Download lang_tags_context.json</button></header><main>
<p>The grey lines are only context. Tag the <b>yellow</b> row. <b>Same in both</b>: the row is names, places or references that Gojri and Urdu write the same way.
Keys <b>1 to 6</b> tag the blue-marked card and move on.</p>
""" + "\n".join(cards) + """
</main><script>
const KEY=\"""" + key + """\";let marks={};try{marks=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
const cards=[...document.querySelectorAll(".card")];let cur=0;
const NAMES={gju:"Gojri",urd:"Urdu",same:"Same in both",mixed:"Mixed",other:"Other",unsure:"Unsure"},KEYS={"1":"gju","2":"urd","3":"same","4":"mixed","5":"other","6":"unsure"};
function save(){try{localStorage.setItem(KEY,JSON.stringify(marks))}catch(e){}count()}
function count(){document.getElementById("count").textContent=Object.keys(marks).length+" of "+cards.length+" tagged"}
function paint(c){const m=marks[c.dataset.id];c.classList.toggle("done",!!m);c.querySelector(".state").textContent=m?NAMES[m]:""}
function show(i){cur=Math.max(0,Math.min(cards.length-1,i));cards.forEach((c,k)=>c.style.outline=k==cur?"3px solid #1a5fb4":"none");cards[cur].scrollIntoView({block:"center"})}
function mark(c,m){marks[c.dataset.id]=m;save();paint(c)}
cards.forEach((c,i)=>{paint(c);c.querySelectorAll("button").forEach(b=>b.onclick=()=>{mark(c,b.dataset.m);show(i+1)})});
document.addEventListener("keydown",e=>{if(KEYS[e.key]){mark(cards[cur],KEYS[e.key]);show(cur+1);e.preventDefault()}else if(e.key=="ArrowDown"){show(cur+1);e.preventDefault()}else if(e.key=="ArrowUp"){show(cur-1);e.preventDefault()}});
document.getElementById("dl").onclick=()=>{const blob=new Blob([JSON.stringify(marks,null,1)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="lang_tags_context.json";a.click()};
count();show(0);
</script></body></html>"""
    (OUT / "lang_context_review.html").write_text(page, encoding="utf-8")
    (OUT / "lang_context_sample.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(items), "rows ->", OUT / "lang_context_review.html")


if __name__ == "__main__":
    main()
