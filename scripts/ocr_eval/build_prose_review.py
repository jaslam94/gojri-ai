"""Build a local review page for ocr_prose_pages.py output, for a Gojri speaker to check and correct.

Each card shows one row: the clean crop and the OCR text in an edit box. Buttons: OK (text is right), Wrong (the box
holds the corrected text), Unsure. Marks and edits are kept in the browser (localStorage) and can be downloaded as
review_marks.json (keys "book|page|row", with the OCR text and the corrected text). Nothing is uploaded.
Verse rows hold two halves split by a TAB; keep the TAB where it is. Text is right to left.
Rows flagged "touch" (two lines touch, the crop may lack a piece) or "header" are marked on the card.
Judge three things: letters, marks, spaces. In the "Wrong" case also pick the error types, so we can score each.

Run: py -3 -X utf8 scripts/ocr_eval/build_prose_review.py --root data/ocr/prose-words --dpi 300
Writes <root>/review.html. Open it in Chrome or Edge from the same folder (the crops are read from <root>/<book>/crops).
"""
import argparse
import hashlib
import html
import json
from pathlib import Path

CSS = '''
:root{--bg:#fafafa;--fg:#1a1a1a;--card:#fff;--line:#d8d8d8;--ok:#1b7f3b;--bad:#b3261e;--un:#8a6d00}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--card:#222;--line:#444;--ok:#5ad17b;--bad:#ff8a80;--un:#e6c34d}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}
main{max-width:1000px;margin:0 auto;padding:12px 16px 80px}
h2{margin-top:36px;font-size:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;margin:10px 0}
.card img{max-width:100%;height:auto;background:#fff;border:1px solid var(--line)}
.meta{font-size:12px;opacity:.75;margin-bottom:4px}.flag{color:var(--bad)}
textarea{width:100%;box-sizing:border-box;direction:rtl;text-align:right;white-space:pre-wrap;font:26px "Noto Nastaliq Urdu","Jameel Noori Nastaleeq",serif;
 line-height:1.9;padding:6px;margin:6px 0;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:4px;resize:vertical}
button{font:inherit;padding:5px 12px;margin-right:8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
label.t{font-size:13px;margin-right:12px;opacity:.9}
.card.ok{border-color:var(--ok)}.card.wrong{border-color:var(--bad)}.card.unsure{border-color:var(--un)}
.state{font-size:13px}
'''

JS = '''
let marks={};
try{marks=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(marks))}catch(e){}count()}
function count(){const v=Object.values(marks);document.getElementById("count").textContent=
 v.length+" of "+document.querySelectorAll(".card").length+" marked (OK "+v.filter(x=>x.m=="ok").length+", wrong "+v.filter(x=>x.m=="wrong").length+", unsure "+v.filter(x=>x.m=="unsure").length+")"}
document.querySelectorAll(".card").forEach(c=>{const id=c.dataset.id;const ta=c.querySelector("textarea");const ocr=ta.value;
 const types=()=>[...c.querySelectorAll("input[type=checkbox]:checked")].map(x=>x.value);
 const paint=()=>{const m=marks[id];c.classList.remove("ok","wrong","unsure");if(m){c.classList.add(m.m);c.querySelector(".state").textContent=m.m;
  ta.value=m.text;c.querySelectorAll("input[type=checkbox]").forEach(x=>x.checked=(m.types||[]).includes(x.value))}};
 c.querySelectorAll("button").forEach(b=>b.onclick=()=>{marks[id]={m:b.dataset.m,ocr:ocr,text:ta.value,types:types()};save();paint()});paint()});
document.getElementById("dl").onclick=()=>{const blob=new Blob([JSON.stringify(marks,null,1)],{type:"application/json"});
 const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="review_marks.json";a.click()};
count();
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()
    root = Path(args.root)
    cards = []
    ident = []
    for book in sorted(p for p in root.iterdir() if p.is_dir()):
        for jf in sorted((book / f"dpi{args.dpi}").glob("page_*.json")):
            j = json.loads(jf.read_text(encoding="utf-8"))
            cards.append(f"<h2>{html.escape(book.name)} page {j['page']} "
                         f"<small>(word mode {j['word_mode']})</small></h2>")
            for r in j["rows"]:
                if not r["text"]:
                    continue
                cid = f"{book.name}|{j['page']}|{r['row']}"
                ident.append((cid, r["text"]))
                img = f"{book.name}/crops/p{j['page']:03d}/L{r['row']:02d}.png"
                fl = " ".join(r["flags"])
                nlines = r["text"].count("\n") + 2
                cards.append(
                    f'<section class="card" data-id="{html.escape(cid, quote=True)}">'
                    f'<div class="meta">{html.escape(book.name)} page {j["page"]} row {r["row"]}'
                    f'{(" <span class=flag>" + html.escape(fl) + "</span>") if fl else ""}</div>'
                    f'<img src="{img}" alt="row crop">'
                    f'<textarea rows="{nlines}" spellcheck="false">{html.escape(r["text"])}</textarea>'
                    '<div><button data-m="ok">OK</button><button data-m="wrong">Wrong (I fixed the text)</button>'
                    '<button data-m="unsure">Unsure</button> <span class="state"></span></div>'
                    '<div><label class="t"><input type="checkbox" value="letters"> letters wrong</label>'
                    '<label class="t"><input type="checkbox" value="marks"> marks wrong</label>'
                    '<label class="t"><input type="checkbox" value="spaces"> spaces wrong</label>'
                    '<label class="t"><input type="checkbox" value="crop"> crop cut or has other line</label></div>'
                    '</section>')
    key = "prose_review_" + hashlib.md5(json.dumps(ident, ensure_ascii=False).encode()).hexdigest()[:8]
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Prose OCR review</title><style>{CSS}</style></head><body>'
            '<header><b>Prose and poetry OCR review</b> &middot; <span id="count"></span> '
            '<button id="dl">Download review_marks.json</button></header><main>'
            '<p>For each card, compare the picture with the text box. Click <b>OK</b> if it is right. If not, correct the text '
            'in the box (keep the TAB between verse halves), tick what was wrong, then click <b>Wrong</b>. '
            'Judge letters, marks and spaces separately. Your work is saved in this browser; use Download when you stop.</p>'
            + "\n".join(cards) + f'</main><script>const KEY="{key}";{JS}</script></body></html>')
    (root / "review.html").write_text(page, encoding="utf-8")
    print("wrote", root / "review.html", len(ident), "cards")


if __name__ == "__main__":
    main()
