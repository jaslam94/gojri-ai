"""Review page for the Gojri-only filter of the blog text (filter_gojri_blog.py).

The speaker tags a random sample of chunks: Gojri, Urdu, Same in both, Mixed, Unsure. The tagger's draft tag is hidden on the page
(no bias) and kept in the sample file. After the speaker downloads the marks, score_blog_lang_review.py gives precision and recall of
the filter.

Sample: SEED fixed. 50 chunks tagged gju, 35 urd, 35 unsure (A01), plus 5 chunks of each class from A04 when it has them.
Chunks under 30 letters are left out.

Run: py -3 -X utf8 scripts/corpus/build_blog_lang_review.py
Output (local, gitignored: the page holds third-party text): datasets/gojri-blogs/review/review.html and sample.json
"""
import hashlib
import html
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLOGS = ROOT / "datasets/gojri-blogs"
OUT = BLOGS / "review"
SEED = 20261124
N = {"gojrizubanoadab": {"gju": 50, "urd": 35, "unsure": 35}, "rungewatan-hasan": {"gju": 5, "urd": 3, "unsure": 3}}


def main():
    rows = [json.loads(l) for l in open(BLOGS / "chunks.jsonl", encoding="utf-8")]
    rng = random.Random(SEED)
    pick = []
    for blog, want in N.items():
        for tag, n in want.items():
            pool = [r for r in rows if r["blog"] == blog and r["tag"] == tag and r["letters"] >= 30]
            pick += rng.sample(pool, min(n, len(pool)))
    rng.shuffle(pick)
    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    cards = []
    for n, r in enumerate(pick):
        items.append({"id": n, "blog": r["blog"], "post": r["post"], "chunk": r["chunk"], "url": r["url"], "title": r["title"],
                      "draft": r["tag"], "score": r["score"], "text": r["text"]})
        body = "".join(f'<div class="l">{html.escape(t)}</div>' for t in r["text"].split("\n"))
        cards.append(f'<section class="card" data-id="{n}"><div class="meta">#{n + 1} &middot; {html.escape(r["blog"])} &middot; {html.escape(r["title"][:70])}</div>'
                     f'<div class="txt" dir="rtl">{body}</div>'
                     '<div class="btns"><button data-m="gju">1 Gojri</button><button data-m="urd">2 Urdu</button><button data-m="same">3 Same in both</button>'
                     '<button data-m="mixed">4 Mixed</button><button data-m="unsure">5 Unsure</button><span class="state"></span></div></section>')
    key = "blog_lang_" + hashlib.md5(json.dumps([[i["post"], i["chunk"]] for i in items]).encode()).hexdigest()[:8]
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blog text: Gojri or Urdu</title><style>
:root{--bg:#fafafa;--fg:#1a1a1a;--card:#fff;--line:#d8d8d8}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--card:#222;--line:#444}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}
main{max-width:900px;margin:0 auto;padding:12px 16px 80px}
.card{background:var(--card);border:2px solid var(--line);border-radius:8px;padding:10px 12px;margin:14px 0}
.meta{font-size:13px;opacity:.7}
.txt{font-size:24px;line-height:1.9;margin:4px 0}
button{font:inherit;padding:6px 12px;margin:6px 6px 0 0;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
.card.done{border-color:#1b7f3b}.state{font-size:13px;margin-left:6px}
</style></head><body><header><b>Is this text Gojri or Urdu?</b> &middot; <span id="count"></span> <button id="dl">Download blog_lang_tags.json</button></header><main>
<p>Tag each block of text. <b>Gojri</b>: the text is Gojri. <b>Urdu</b>: the text is Urdu. <b>Same in both</b>: names, places or references that Gojri and Urdu write the same way.
<b>Mixed</b>: part Gojri, part Urdu. Keys <b>1 to 5</b> tag the blue-marked card and move on. Your marks stay in this browser; download them at the end.</p>
""" + "\n".join(cards) + """
</main><script>
const KEY=\"""" + key + """\";let marks={};try{marks=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
const cards=[...document.querySelectorAll(".card")];let cur=0;
const NAMES={gju:"Gojri",urd:"Urdu",same:"Same in both",mixed:"Mixed",unsure:"Unsure"},KEYS={"1":"gju","2":"urd","3":"same","4":"mixed","5":"unsure"};
function save(){try{localStorage.setItem(KEY,JSON.stringify(marks))}catch(e){}count()}
function count(){document.getElementById("count").textContent=Object.keys(marks).length+" of "+cards.length+" tagged"}
function paint(c){const m=marks[c.dataset.id];c.classList.toggle("done",!!m);c.querySelector(".state").textContent=m?NAMES[m]:""}
function show(i){cur=Math.max(0,Math.min(cards.length-1,i));cards.forEach((c,k)=>c.style.outline=k==cur?"3px solid #1a5fb4":"none");cards[cur].scrollIntoView({block:"center"})}
function mark(c,m){marks[c.dataset.id]=m;save();paint(c)}
cards.forEach((c,i)=>{paint(c);c.querySelectorAll("button").forEach(b=>b.onclick=()=>{mark(c,b.dataset.m);show(i+1)})});
document.addEventListener("keydown",e=>{if(KEYS[e.key]){mark(cards[cur],KEYS[e.key]);show(cur+1);e.preventDefault()}else if(e.key=="ArrowDown"){show(cur+1);e.preventDefault()}else if(e.key=="ArrowUp"){show(cur-1);e.preventDefault()}});
document.getElementById("dl").onclick=()=>{const blob=new Blob([JSON.stringify(marks,null,1)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="blog_lang_tags.json";a.click()};
count();show(0);
</script></body></html>"""
    (OUT / "review.html").write_text(page, encoding="utf-8")
    (OUT / "sample.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(len(items), "cards;", dict(Counter(i["draft"] for i in items)), "->", OUT / "review.html")


if __name__ == "__main__":
    main()
