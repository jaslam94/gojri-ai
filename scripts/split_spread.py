"""
Stage 1 helper: split a two-page-spread PDF page image into its two real pages.

Why this exists: 26 files (6,295 pages) in the collection export one physical
book-page-pair as a single wide PDF page. Verified (Aug 2026) across 6 sample
files x 3 pages each: the exact geometric horizontal center always falls inside a
contiguous white gutter, with a worst-case safety margin of 61px on a 1684px-wide
page (~3.6%). So a plain 50/50 crop is safe; no need for per-page gap detection.

Reading order: these books are Nastaliq, right-to-left. In a two-page spread, the
RIGHT half is the earlier page in reading order, the LEFT half is the later page.
Callers must preserve that when reassembling text, or pages will come out swapped.
"""

from pathlib import Path

import fitz


def render_spread_halves(pdf_path, page_index, zoom=2, out_dir=None):
    """Render one spread page and split it into (right_half, left_half) PNGs.

    Returns (right_path, left_half_path) — RIGHT FIRST, since that's reading order
    for a right-to-left book. Caller must not just sort filenames alphabetically.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    w, h = pix.width, pix.height
    center = w // 2

    full = fitz.Pixmap(pix)  # keep a handle; we'll crop via separate clips
    doc.close()

    stem = Path(pdf_path).stem
    out_dir = Path(out_dir) if out_dir else Path(pdf_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Re-render each half directly from the page at the target crop, rather than
    # cropping the rasterized pixmap, so we don't lose sharpness.
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    full_rect = page.rect
    mid_x = full_rect.x0 + full_rect.width / 2

    right_rect = fitz.Rect(mid_x, full_rect.y0, full_rect.x1, full_rect.y1)
    left_rect = fitz.Rect(full_rect.x0, full_rect.y0, mid_x, full_rect.y1)

    right_pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=right_rect)
    left_pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=left_rect)

    right_path = out_dir / f"{stem}_p{page_index+1:04d}_a_right.png"
    left_path = out_dir / f"{stem}_p{page_index+1:04d}_b_left.png"
    right_pix.save(right_path)
    left_pix.save(left_path)
    doc.close()

    return right_path, left_path


if __name__ == "__main__":
    import sys
    pdf = sys.argv[1] if len(sys.argv) > 1 else \
        "PDFs/javaidrahi-blog/kulyate_rana_fazal_hussan_ed-dr-javaid-rah.pdf"
    page_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    r, l = render_spread_halves(pdf, page_idx, out_dir="data/gold/spread_test")
    print(f"right (read first): {r}")
    print(f"left  (read second): {l}")
