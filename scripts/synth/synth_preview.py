"""Build a 12-sample preview sheet from a synthetic label file."""
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "data" / "synth" / "line_full"
rows = [json.loads(l) for l in (out / "labels.jsonl").open(encoding="utf-8")]
rows = [r for r in rows if r["width_px"] >= 400 and r["height_px"] >= 100]
random.seed(7)
sample = random.sample(rows, 12)
CW, CAP = 820, 26
try:
    font = ImageFont.truetype("consola.ttf", 13)
except Exception:
    font = ImageFont.load_default()

cells = []
for r in sample:
    for tag, vkey in (("clean", "image"), ("v1", None)):
        if vkey:
            im_path = out / r["image"]
            caption = f"{r['source_tag'][:4]} | {r['page_line']} | clean"
        else:
            im_path = out / r["image"].replace(".png", "_v1.png")
            caption = f"v1 = {r['variants'][0]}"
        im = Image.open(im_path)
        im = im.resize((CW, max(1, int(im.height * CW / im.width))), Image.LANCZOS)
        cell = Image.new("RGB", (CW, CAP + im.height + 2), (255, 255, 255))
        d = ImageDraw.Draw(cell)
        d.text((4, 4), caption, fill=(0, 0, 0) if vkey else (120, 0, 0), font=font)
        cell.paste(im, (0, CAP))
        cells.append(cell)

cols = 2
n_rows = (len(cells) + cols - 1) // cols
r_heights = [max(c.height for c in cells[r * cols:(r + 1) * cols]) + 8 for r in range(n_rows)]
c_widths = [max(c.width for c in cells[r::n_rows]) + 8 for r in range(cols)]
sheet = Image.new("RGB", (sum(c_widths), sum(r_heights)), (255, 255, 255))
y = 0
for r in range(n_rows):
    x = 0
    for c in range(cols):
        i = r * cols + c
        if i < len(cells):
            sheet.paste(cells[i], (x, y))
        x += c_widths[c]
    y += r_heights[r]
p = out / "preview_sheet.png"
sheet.save(p)
print(p)
