"""Correction page for the locked test set: the speaker turns each draft into gold text.

  py -3 -X utf8 scripts/build_test_gold_page.py build
      writes data/test-locked/review.html (local, gitignored). Open it in Chrome or Edge from that folder. Each card
      shows the page image and the draft in an edit box. Correct the text, click "Done", and download test_gold.json
      when you stop (work is also kept in the browser).
  py -3 -X utf8 scripts/build_test_gold_page.py apply <test_gold.json>
      writes data/test-locked/gold/Txx_gold.txt for every page marked Done.

Gold rules (as for data/gold): letters as printed; word spaces by meaning; page numbers and headers as printed;
`[...]` for a picture or ornament; `[[...]]` only for a word that stays unreadable.
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "data" / "test-locked"

CSS = (":root{--bg:#fafafa;--fg:#1a1a1a;--card:#fff;--line:#ccc;--ok:#1b7f3b}"
       "@media(prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--card:#222;--line:#444;--ok:#5ad17b}}"
       "body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}"
       "header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:2}"
       "main{max-width:1500px;margin:0 auto;padding:12px 16px}"
       ".card{display:grid;grid-template-columns:1fr 1fr;gap:12px;background:var(--card);border:1px solid var(--line);"
       "border-radius:8px;padding:10px;margin:12px 0}.card.done{border-color:var(--ok)}"
       "@media(max-width:900px){.card{grid-template-columns:1fr}}"
       ".card img{width:100%;height:auto;background:#fff;border:1px solid var(--line)}"
       "textarea{width:100%;box-sizing:border-box;min-height:600px;direction:rtl;text-align:right;"
       "font:24px/1.9 'Noto Nastaliq Urdu','Jameel Noori Nastaleeq',serif;background:var(--bg);color:var(--fg);"
       "border:1px solid var(--line);border-radius:4px;padding:8px}button{font:inherit;padding:5px 12px;margin:4px 8px 0 0}")
JS = ("let g={};try{g=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}"
      "function save(){try{localStorage.setItem(KEY,JSON.stringify(g))}catch(e){}"
      "document.getElementById('n').textContent=Object.values(g).filter(x=>x.done).length+' of '+document.querySelectorAll('.card').length+' done'}"
      "document.querySelectorAll('.card').forEach(c=>{const id=c.dataset.id,ta=c.querySelector('textarea');"
      "if(g[id]){ta.value=g[id].text;if(g[id].done)c.classList.add('done')}"
      "ta.oninput=()=>{g[id]={text:ta.value,done:false};c.classList.remove('done');save()};"
      "c.querySelector('button').onclick=()=>{g[id]={text:ta.value,done:true};c.classList.add('done');save()}});"
      "document.getElementById('dl').onclick=()=>{const a=document.createElement('a');"
      "a.href=URL.createObjectURL(new Blob([JSON.stringify(g,null,1)],{type:'application/json'}));a.download='test_gold.json';a.click()};save();")


def build():
    cards = []
    for d in sorted((T / "drafts").glob("T*_draft.txt")):
        tid = d.name.split("_")[0]
        text = d.read_text(encoding="utf-8")
        cards.append(f'<section class="card" data-id="{tid}"><div><b>{tid}</b><br><img src="images/{tid}.png" alt="page {tid}"></div>'
                     f'<div><textarea spellcheck="false">{html.escape(text)}</textarea><button>Done</button></div></section>')
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Test gold check</title><style>{CSS}</style></head><body><header><b>Locked test set: gold text</b> &middot; '
            '<span id="n"></span> <button id="dl">Download test_gold.json</button></header><main>'
            '<p>Correct each draft against the page image: letters as printed, word spaces by meaning, [...] for pictures, '
            '[[...]] only for a word you cannot read. Click Done for each page. Download the file when you stop.</p>'
            + "".join(cards) + f'</main><script>const KEY="test_gold_v1";{JS}</script></body></html>')
    (T / "review.html").write_text(page, encoding="utf-8")
    print("wrote", T / "review.html", len(cards), "pages")


def apply(path):
    g = json.load(open(path, encoding="utf-8"))
    (T / "gold").mkdir(exist_ok=True)
    n = 0
    for tid, x in sorted(g.items()):
        if x.get("done"):
            (T / "gold" / f"{tid}_gold.txt").write_text(x["text"].rstrip() + "\n", encoding="utf-8")
            n += 1
    print("wrote", n, "gold files")


if __name__ == "__main__":
    build() if sys.argv[1:2] == ["build"] else apply(sys.argv[2])
