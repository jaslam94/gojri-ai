"""Synthetic line-image generator.

Step 4 of the aligned plan. Walks decoded Gojri text, chunks long lines at
word boundaries, draws every chunk in the verified Nastaliq font in headless
Chrome at device scale 2 (HD), saves a clean PNG plus 3 degraded copies
(approved augmentation mix), and writes labels.jsonl.

Sources: dictionary pass2 pages 25-498 + all FLI corpus texts.
Output: data/synth/line_full/  (gitignored)
"""
import importlib.util
import json
import random
import re
import time
import unicodedata as uni
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / "data" / "synth" / "fonts" / "NotoNastaliqUrdu-Regular.ttf"
DATA_OUT = ROOT / "data" / "synth" / "line_full"
IMG_OUT = DATA_OUT / "img"
DATA_OUT.mkdir(parents=True, exist_ok=True)
IMG_OUT.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location("synth_aug", Path(__file__).with_name("synth_aug.py"))
synth_aug = importlib.util.module_from_spec(spec)
spec.loader.exec_module(synth_aug)

ARABIC = lambda ch: 0x0600 <= ord(ch) <= 0x06FF or 0x0700 <= ord(ch) <= 0x077F or ch in "\u200c\u200d\u200e\u200f"

DICT_PAGES = [ROOT / "data" / "decode" / "out" / "gojri-english-dictionary" / f"page-{n:04d}-pass2.txt" for n in range(25, 499)]
FLI = sorted((ROOT / "datasets" / "Gojri Language Corpus").glob("*.txt"))
SOURCES = [(p, "dictionary") for p in DICT_PAGES] + [(p, "fli") for p in FLI]

CHUNK_CHARS = 44  # word-boundary budget per rendered row, keeps image width sane

HTML_BATCH = """<!doctype html><html><head><meta charset="utf-8">
<style>
@font-face {{
  font-family: 'NastaliqGen';
  src: url('file:///{font}') format('truetype');
}}
body {{ background:#fff; margin:0; font-family:'NastaliqGen'; }}
.row {{
  display: inline-block;
  direction: rtl; unicode-bidi: isolate;
  line-height: 2.4;
  white-space: nowrap; width: max-content;
  padding: 3px 4px;
  margin-bottom: 6px;
}}
</style></head><body>{rows}</body></html>"""


def chunk_line(s: str):
    if len(s) <= CHUNK_CHARS + 8:
        return [s]
    words = s.split(" ")
    chunks, cur = [], ""
    for wd in words:
        if cur and len(cur) + 1 + len(wd) > CHUNK_CHARS:
            chunks.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def collect_rows():
    rows = []
    for path, tag in SOURCES:
        text = uni.normalize("NFC", path.read_text(encoding="utf-8"))
        for line_no, raw in enumerate(text.splitlines(), 1):
            s = re.sub(r"\s+", " ", raw).strip()
            if len(s) < 10:
                continue
            n_ar = sum(1 for c in s if ARABIC(c))
            if n_ar < 3:
                continue
            if not re.search(r"[\u0600-\u06FF]", s) and re.fullmatch(r"[\W\d]+", s):
                continue
            for k, ch in enumerate(chunk_line(s), 1):
                n_ar_chunk = sum(1 for c in ch if ARABIC(c))
                if n_ar_chunk < 3:
                    continue  # Latin- or digit-only tails: not a Nastaliq render target
                rows.append({
                    "text": ch,
                    "source_file": str(path.relative_to(ROOT)),
                    "source_tag": tag,
                    "page_line": f"{path.stem}:L{line_no}",
                    "chunk": k,
                    "n_chunks_in_line": 0,
                })
    return rows


def render_rows(rows, browser, context):
    import io
    page = context.new_page()
    labels = []
    t0 = time.time()
    BATCH = 64
    for start in range(0, len(rows), BATCH):
        batch = rows[start:start + BATCH]
        todo = []
        for j, row in enumerate(batch):
            img_id = f"{start + j:06d}"
            if (IMG_OUT / f"{img_id}.png").exists():
                img = Image.open(IMG_OUT / f"{img_id}.png")
                if img.size[0] > 60 and img.size[1] > 60:
                    row["image"] = f"img/{img_id}.png"
                    row.setdefault("font_size_css", 0)
                    row["dpr"] = 2
                    row["width_px"], row["height_px"] = img.size
                    labels.append(row)
                    continue
            todo.append((start + j, row))
        if not todo:
            continue
        trs = []
        for k, (idx, row) in enumerate(todo):
            size = random.choice([24, 25, 26, 27, 28])
            row["_size"] = size
            safe = row["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            trs.append(f'<div><div id="row_{k}" class="row" style="font-size:{size}px">{safe}</div></div>')
        page.set_content(HTML_BATCH.format(font=str(FONT).replace("\\", "/"), rows="".join(trs)))
        page.wait_for_timeout(700)
        rects = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('div.row')).map(e => {
                const r = e.getBoundingClientRect();
                const s = window.getComputedStyle(e);
                if (s.fontFamily.indexOf('NastaliqGen') === -1) return null;
                return {x: r.x, y: r.y, w: r.width, h: r.height, z: Intl.NumberFormat().format(0) && null};
            });
        }""")
        if any(r is None for r in rects):
            raise RuntimeError("font did not load; batch aborted before saving anything")
        shot = page.screenshot(full_page=True)
        sheet = Image.open(io.BytesIO(shot))
        dpr = 2.0
        pad_css = 4
        if sheet.width < 1500:
            raise RuntimeError("screenshot suspiciously narrow; abort batch")
        for k, (idx, row) in enumerate(todo):
            r = rects[k]
            x0 = max(0, int((r["x"] - pad_css) * dpr))
            y0 = max(0, int((r["y"] - pad_css) * dpr))
            x1 = min(sheet.width - 1, int((r["x"] + r["w"] + pad_css) * dpr))
            y1 = min(sheet.height - 1, int((r["y"] + r["h"] + pad_css) * dpr))
            crop = sheet.crop((x0, y0, x1, y1))
            if crop.width < 50 or crop.height < 30:
                raise RuntimeError(f"degenerate crop {idx}: {crop.size} for text {row['text'][:20]!r}")
            img_id = f"{idx:06d}"
            clean_path = IMG_OUT / f"{img_id}.png"
            crop.save(clean_path, optimize=True)
            row["image"] = f"img/{img_id}.png"
            row["font_size_css"] = row.pop("_size")
            row["dpr"] = 2
            row["width_px"], row["height_px"] = crop.size
            augs = [a for a in synth_aug.AUGS if a[0] != "clean"]
            row["variants"] = []
            for vi, (vname, fn) in enumerate(random.sample(augs, 3), 1):
                fn(crop).save(IMG_OUT / f"{img_id}_v{vi}.png", optimize=True)
                row["variants"].append(vname)
        labels.extend(row for _, row in todo)
        done = start + len(batch)
        rate = done / max(time.time() - t0, 1e-6)
        print(f"  {done}/{len(rows)} ({rate:.1f} rows/s)", flush=True)
    page.close()
    return labels


def main():
    rows = collect_rows()
    print(f"rows to render: {len(rows)}")
    (DATA_OUT / "pilot_rows.json").write_text(json.dumps(rows[:3], ensure_ascii=False, indent=2), encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1600, "height": 400}, device_scale_factor=2)
        labels = render_rows(rows, browser, context)
        browser.close()

    with (DATA_OUT / "labels.jsonl").open("w", encoding="utf-8") as f:
        for row in labels:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote labels.jsonl with {len(labels)} rows")


if __name__ == "__main__":
    main()
