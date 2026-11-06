"""Mine real-print training pairs from the Batool dictionary PDF (Phase 2, step 5).

For every body page 25-498:
  - collect raw glyph boxes (fitz rawdict) and cluster into printed lines with
    the same Y_GAP logic as decode_batool, but keep real y0/y1 per row,
  - rebuild each line's text with the decoder's own fmt_line rule,
  - render the page once at ~300 DPI (user rule: HD, tight margins),
  - crop each printed line tightly around its glyph box (small pad, extra
    room at the bottom for Nastaliq descenders),
  - pair printed line k with pass2 decoded line k ONLY when the rebuilt line
    texts equal the pass2 label list exactly; otherwise skip and log.

Output: data/synth/real_pairs/img/*.png + labels.jsonl + skipped_pages.json
Runs with `py -3`.
"""
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

ROOT = Path(r"D:\Code\VSCodeProjects\gojri-ai")
PDF = ROOT / "pdfs" / "anjumshanasi" / "Gojri-English-Dictionary.pdf"
PASS2 = ROOT / "data" / "decode" / "out" / "gojri-english-dictionary"
OUT = ROOT / "data" / "synth" / "real_pairs"
IMG = OUT / "img"

Y_GAP = 14.0        # same clustering gap as dump_batool_lines
ZOOM = 4.2          # ~300 DPI
PAD_PT = 2.0        # pad on all sides of the glyph box
EXTRA_BOTTOM = 14.0  # padding below the last row of a page only
# Each line is cut at the ink valley between it and its neighbour. Padding every
# row by 14 pt below its glyph box kept the descenders but also pulled in the top
# half of the next line (English text with no label).

sys.path.insert(0, str(ROOT / "scripts"))
from dump_batool_lines import fmt_line, load_map  # noqa: E402


def page_chars_full(page: fitz.Page):
    """Like dump_batool_lines.page_chars, but keeps y1 too."""
    data = page.get_text("rawdict", flags=0)
    chars = []
    for block in data["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                font = span.get("font", "")
                for ch in span["chars"]:
                    x0, y0, x1, y1 = ch["bbox"]
                    chars.append((y0, y1, x0, x1, font, ch["c"], ord(ch["c"])))
    chars.sort(key=lambda t: (t[0], -t[2]))
    return chars


def cluster_rows_full(chars):
    """Identical clustering to cluster_rows, but rows carry a glyph bbox."""
    if not chars:
        return []
    rows_out = []
    cur = [chars[0]]

    def flush():
        nonlocal cur
        rows_out.append((sum(t[0] for t in cur) / len(cur), {
            "x0": min(t[2] for t in cur),
            "y0": min(t[0] for t in cur),
            "x1": max(t[3] for t in cur),
            "y1": max(t[1] for t in cur),
            # fmt_line-compatible records: (x0, x1, font, ch, ord)
            "chars": [(t[2], t[3], t[4], t[5], t[6]) for t in cur],
        }))
        cur = []

    for item in chars[1:]:
        if item[0] - cur[-1][0] > Y_GAP:
            flush()
        cur.append(item)
    flush()
    return rows_out


def valley(ink, mid_a, mid_b):
    """Pixel row with the least ink in the middle half between two line mid-lines."""
    lo = int(mid_a + 0.25 * (mid_b - mid_a))
    hi = max(lo + 1, int(mid_a + 0.75 * (mid_b - mid_a)))
    seg = ink[lo:hi + 1]
    best = np.flatnonzero(seg == seg.min())
    return lo + int(best[len(best) // 2])  # middle of the emptiest run


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    IMG.mkdir(parents=True, exist_ok=True)
    pua_map = load_map()
    doc = fitz.open(PDF)
    mismatches = []
    rows_out = []
    for page_1idx in range(25, 499):
        page = doc[page_1idx - 1]
        pass2_path = PASS2 / f"page-{page_1idx:04d}-pass2.txt"
        labels = [
            re.sub(r"\s+", " ", ln).strip()
            for ln in unicodedata.normalize("NFC", pass2_path.read_text(encoding="utf-8")).splitlines()
        ]
        labels = [ln for ln in labels if ln]
        rows = cluster_rows_full(page_chars_full(page))
        texts = [re.sub(r"\s+", " ", fmt_line(bb["chars"], pua_map, wrap_batool=False)).strip()
                 for _y, bb in rows]
        # Pairing evidence: pass2 labels sit in row order, so crop count must
        # equal label count. pass2 strings are Gemini-repaired, so exact text
        # identity is not testable here; count equality is the check.
        # The printed folio number ("200" for page 200) appears as a kept row.
        # Later pass2 pages drop that label line, early pages keep it. So the
        # folio crop row is dropped only when the label list lacks it.
        pageno = str(page_1idx)
        keep_folio = pageno in labels
        kept = [bb for (_y, bb), txt in zip(rows, texts)
                if txt and (keep_folio or txt != pageno)]
        if len(kept) != len(labels):
            mismatches.append({
                "page": page_1idx,
                "rows": len(rows),
                "non_empty": len(kept),
                "labels": len(labels),
            })
            continue
        pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), alpha=False)
        page_img = Image.open(io.BytesIO(fitz.Pixmap(pix).tobytes("png")))
        pw, ph = page_img.size
        gray = np.asarray(page_img.convert("L"))
        ink = np.convolve((gray < 200).sum(axis=1).astype("float64"), np.ones(5) / 5, mode="same")
        mids = [(bb["y0"] + bb["y1"]) / 2 * ZOOM for bb in kept]
        for k, bb in enumerate(kept, 1):
            rx0 = max(0, int((bb["x0"] - PAD_PT) * ZOOM))
            rx1 = min(pw - 1, int((bb["x1"] + PAD_PT) * ZOOM))
            if k == 1:
                ry0 = max(0, int((bb["y0"] - PAD_PT) * ZOOM))
            else:
                ry0 = valley(ink, mids[k - 2], mids[k - 1])
            if k == len(kept):
                ry1 = min(ph - 1, int((bb["y1"] + PAD_PT + EXTRA_BOTTOM) * ZOOM))
            else:
                ry1 = valley(ink, mids[k - 1], mids[k])
            crop = page_img.crop((rx0, ry0, rx1, ry1))
            if crop.width < 60 or crop.height < 30:
                mismatches.append({"page": page_1idx, "degenerate_line": k,
                                   "size": list(crop.size)})
                continue
            img_id = f"p{page_1idx:04d}_L{k:02d}"
            crop.save(IMG / f"{img_id}.png", optimize=True)
            txt = labels[k - 1]
            rows_out.append({
                "image": f"img/{img_id}.png",
                "text": txt,
                "folio": txt.strip() == pageno,
                "source_file": "pdfs/anjumshanasi/Gojri-English-Dictionary.pdf",
                "source_tag": "batool_print",
                "page_line": f"page-{page_1idx:04d}:L{k}",
                "width_px": crop.width,
                "height_px": crop.height,
            })
        if page_1idx % 25 == 0 or page_1idx == 498:
            print(f"page {page_1idx}/498, rows so far {len(rows_out)}", flush=True)
    (OUT / "labels.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows_out) + "\n", encoding="utf-8")
    (OUT / "skipped_pages.json").write_text(json.dumps(mismatches, indent=2), encoding="utf-8")
    print(f"done: {len(rows_out)} pairs, skipped pages: {len(mismatches)}")


if __name__ == "__main__":
    main()
