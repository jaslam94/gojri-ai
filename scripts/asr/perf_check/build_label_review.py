"""Review page for the 50 hand-labelled ASR substitutions (docs/asr_performance_check.md).

The speaker tags each wrong word: Real error, Spelling variant, Reference spacing, Unsure. Claude's draft label is hidden on the
page (no bias) and kept in the TSV. Each card has the clip's audio, so the speaker can listen. After the speaker downloads the
marks, `score` compares them with the draft labels.

Build: python build_label_review.py build --tsv local\\asr-check\\analysis_job\\sample50_labelled.tsv --clips <gju/clips dir> --out local\\asr-check\\label_review
Score: python build_label_review.py score --tsv local\\asr-check\\analysis_job\\sample50_labelled.tsv --marks asr_label_tags.json
Output is local only: the page holds Common Voice sentence text and links to the audio files. Do not commit it.
"""
import argparse
import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

LABELS = {"real": "Real error", "variant": "Spelling variant", "ref-spacing": "Reference spacing", "unclear": "Unsure"}
KEYS = ["real", "variant", "ref-spacing", "unclear"]


def read(tsv):
    return list(csv.DictReader(open(tsv, encoding="utf-8", newline=""), delimiter="\t", quoting=csv.QUOTE_NONE))


def mark(sentence, word):
    s = html.escape(sentence)
    w = html.escape(word)
    return s.replace(w, f"<mark>{w}</mark>", 1) if w and w in s else s


def build(a):
    rows = read(a.tsv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    clips = Path(a.clips).resolve()
    cards = []
    for r in rows:
        src = (clips / r["clip"]).as_uri()
        cards.append(
            f'<section class="card" data-id="{r["id"]}"><div class="meta">#{r["id"]} of {len(rows)}</div>'
            f'<audio controls preload="none" src="{src}"></audio>'
            f'<div class="row"><span class="tag">Correct text</span><span class="txt" dir="rtl">{mark(r["ref_sentence"], r["ref_word"])}</span></div>'
            f'<div class="row"><span class="tag">Model wrote<br><small>(you can edit)</small></span>'
            f'<span class="txt edit" dir="rtl" contenteditable="plaintext-only" spellcheck="false" data-orig="{html.escape(r["hyp_sentence"])}">{mark(r["hyp_sentence"], r["hyp_word"])}</span>'
            '<button class="rs" title="Put the model text back">Reset</button></div>'
            '<div class="btns"><button data-m="real">1 Real error</button><button data-m="variant">2 Spelling variant</button>'
            '<button data-m="ref-spacing">3 Reference spacing</button><button data-m="unclear">4 Unsure</button><span class="state"></span></div></section>')
    key = "asr_label_" + hashlib.md5(json.dumps([r["id"] for r in rows]).encode()).hexdigest()[:8]
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASR errors: check the labels</title><style>
:root{--bg:#fafafa;--fg:#1a1a1a;--card:#fff;--line:#d8d8d8}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--card:#222;--line:#444}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}
main{max-width:900px;margin:0 auto;padding:12px 16px 80px}
.card{background:var(--card);border:2px solid var(--line);border-radius:8px;padding:10px 12px;margin:14px 0}
.meta{font-size:13px;opacity:.7}
.row{display:flex;gap:12px;align-items:baseline;margin:4px 0}.tag{font-size:13px;opacity:.7;min-width:92px}
.txt{font-size:24px;line-height:1.9;flex:1}
mark{background:#ffe08a;color:inherit;border-radius:3px;padding:0 2px}
audio{width:100%;margin:6px 0}
.edit{border:1px dashed var(--line);border-radius:6px;padding:0 8px}.edit:focus{outline:2px solid #1a5fb4}.edit.changed{border:2px solid #d98200}
.rs{margin:0;padding:2px 8px;font-size:13px}
button{font:inherit;padding:6px 12px;margin:6px 6px 0 0;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
.card.done{border-color:#1b7f3b}.state{font-size:13px;margin-left:6px}
</style></head><body><header><b>Is the highlighted word a real error?</b> &middot; <span id="count"></span> <button id="dl">Download asr_label_tags.json</button></header><main>
<p>The model heard each clip and wrote text. The highlighted word is where it differs from the Common Voice text. Listen, then tag the difference.
<b>Real error</b>: the model got the word wrong. <b>Spelling variant</b>: both are the same word, only the spelling differs. <b>Reference spacing</b>:
the Common Voice text has a stray space inside a word, or two words glued together. <b>Unsure</b>: you cannot decide. Keys <b>1 to 4</b> tag the
blue-marked card and move on. The <b>Model wrote</b> line is editable: click it and type what you really said. An edited line gets an orange border.
Your marks and edits stay in this browser; download them at the end.</p>
""" + "\n".join(cards) + """
</main><script>
const KEY=\"""" + key + """\";let marks={};try{marks=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
const EKEY=KEY+"_edits";let edits={};try{edits=JSON.parse(localStorage.getItem(EKEY)||"{}")}catch(e){}
const cards=[...document.querySelectorAll(".card")];let cur=0;
const NAMES={real:"Real error",variant:"Spelling variant","ref-spacing":"Reference spacing",unclear:"Unsure"},KEYS={"1":"real","2":"variant","3":"ref-spacing","4":"unclear"};
function save(){try{localStorage.setItem(KEY,JSON.stringify(marks))}catch(e){}count()}
function saveEdits(){try{localStorage.setItem(EKEY,JSON.stringify(edits))}catch(e){}count()}
function count(){document.getElementById("count").textContent=Object.keys(marks).length+" of "+cards.length+" tagged, "+Object.keys(edits).length+" edited"}
function paint(c){const m=marks[c.dataset.id];c.classList.toggle("done",!!m);c.querySelector(".state").textContent=m?NAMES[m]:""}
function show(i){cur=Math.max(0,Math.min(cards.length-1,i));cards.forEach((c,k)=>c.style.outline=k==cur?"3px solid #1a5fb4":"none");cards[cur].scrollIntoView({block:"center"})}
function mark(c,m){marks[c.dataset.id]=m;save();paint(c)}
cards.forEach((c,i)=>{paint(c);c.querySelectorAll("button[data-m]").forEach(b=>b.onclick=()=>{mark(c,b.dataset.m);show(i+1)});
const ed=c.querySelector(".edit"),id=c.dataset.id;
if(edits[id]!=null){ed.textContent=edits[id];ed.classList.add("changed")}
ed.addEventListener("input",()=>{const t=ed.innerText.replace(/\\s+/g," ").trim();if(t===ed.dataset.orig)delete edits[id];else edits[id]=t;ed.classList.toggle("changed",id in edits);saveEdits()});
ed.addEventListener("focus",()=>{cur=i;cards.forEach((x,k)=>x.style.outline=k==cur?"3px solid #1a5fb4":"none")});
c.querySelector(".rs").onclick=()=>{ed.textContent=ed.dataset.orig;delete edits[id];ed.classList.remove("changed");saveEdits()}});
document.addEventListener("keydown",e=>{if(e.target.isContentEditable){if(e.key=="Enter"||e.key=="Escape"){e.preventDefault();e.target.blur()}return}if(KEYS[e.key]){mark(cards[cur],KEYS[e.key]);show(cur+1);e.preventDefault()}else if(e.key=="ArrowDown"){show(cur+1);e.preventDefault()}else if(e.key=="ArrowUp"){show(cur-1);e.preventDefault()}});
document.getElementById("dl").onclick=()=>{const blob=new Blob([JSON.stringify({marks:marks,edits:edits},null,1)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="asr_label_tags.json";a.click()};
count();show(0);
</script></body></html>"""
    (out / "review.html").write_text(page, encoding="utf-8")
    print(len(rows), "cards ->", out / "review.html")


def score(a):
    rows = {r["id"]: r for r in read(a.tsv)}
    data = json.load(open(a.marks, encoding="utf-8"))
    marks = data["marks"] if "marks" in data else data  # older files hold the marks only
    edits = data.get("edits", {}) if "marks" in data else {}
    both = [(i, rows[i]["label"], m) for i, m in marks.items() if i in rows]
    agree = sum(1 for _, d, m in both if d == m)
    print(f"{len(both)} of {len(rows)} cards tagged by the speaker; draft label equals speaker label on {agree}.")
    print("\nSpeaker counts (final):")
    c = Counter(m for _, _, m in both)
    for k in KEYS:
        print(f"  {LABELS[k]:18} {c.get(k, 0)}")
    print("\nDraft against speaker (rows: draft, columns: speaker):")
    conf = Counter((d, m) for _, d, m in both)
    print("  " + " " * 18 + "".join(f"{LABELS[k][:10]:>12}" for k in KEYS))
    for d in KEYS:
        print(f"  {LABELS[d]:18}" + "".join(f"{conf.get((d, m), 0):>12}" for m in KEYS))
    print("\nChanged cards (id, draft, speaker):")
    for i, d, m in sorted(both, key=lambda x: int(x[0])):
        if d != m:
            print(f"  #{i}: {d} -> {m}")
    print(f"\nEdited model lines (the speaker's own text): {len(edits)}")
    for i in sorted(edits, key=int):
        print(f"  #{i}: {rows[i]['hyp_sentence']}  ->  {edits[i]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--tsv", required=True)
    b.add_argument("--clips", required=True)
    b.add_argument("--out", required=True)
    s = sub.add_parser("score")
    s.add_argument("--tsv", required=True)
    s.add_argument("--marks", required=True)
    a = ap.parse_args()
    build(a) if a.cmd == "build" else score(a)
