import json, re, sys
from pathlib import Path
ROOT = Path("d:/Code/VSCodeProjects/gojri-ai")
sys.path.insert(0, str(ROOT/"scripts")); sys.path.insert(1, str(ROOT/"scripts"/"synth"))
import fitz
from PIL import Image
import dump_batool_lines as D, merge_decode_letters as M, mine_batool_pairs as MB
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
doc = fitz.open(M.PDF); pua = D.load_map()
base = ROOT/"data"/"synth"/"real_pairs"
review = [json.loads(l) for l in (base/"labels_review_test.jsonl").open(encoding="utf-8")]

def line_boxes(page):
    labels = M.pass2_labels(page)
    rows = MB.cluster_rows_full(MB.page_chars_full(doc[page-1]))
    texts = [re.sub(r"\s+", " ", D.fmt_line(bb["chars"], pua, wrap_batool=False)).strip() for _y, bb in rows]
    keep = str(page) in labels
    return [bb for (_y, bb), t in zip(rows, texts) if t and (keep or t != str(page))]

def arabic_runs(bb):
    runs, cur = [], []
    for x0, x1, font, _c, o in sorted(bb["chars"], key=lambda t: t[0]):
        if "Batool" in font or 0xE000 <= o <= 0xF8FF: cur.append((x0, x1))
        elif cur: runs.append(cur); cur = []
    if cur: runs.append(cur)
    return [(min(a for a, _ in r), max(b for _, b in r)) for r in runs]

def cut(img, bb, pad=0):
    rx0 = max(0, int((bb["x0"]-MB.PAD_PT)*MB.ZOOM)); parts = []
    for x0, x1 in arabic_runs(bb):
        a, b = max(0, int(x0*MB.ZOOM-rx0)-pad), min(img.width, int(x1*MB.ZOOM-rx0)+pad)
        if b-a >= 12: parts.append(img.crop((a, 0, b, img.height)))
    return parts

pages = {}; man = []
for r in review:
    page, line = int(r["page_line"][5:9]), int(r["page_line"].split(":L")[1])
    bb = pages.setdefault(page, line_boxes(page))[line-1]
    img = Image.open(base/r["image"]).convert("RGB")
    for i, c in enumerate(cut(img, bb), 1):
        name = f"{r['page_line'].replace(':', '_')}_{i}.png"; c.save(out/name)
        man.append({"page_line": r["page_line"], "idx": i, "file": name})
(out/"manifest.json").write_text(json.dumps(man), encoding="utf-8")
print(len(man), "runs")
