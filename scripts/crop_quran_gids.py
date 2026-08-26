"""Crop unknown Quran GID glyphs from page bboxes.

  py -3 scripts/crop_quran_gids.py 1 80 40
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_quran_gids import (
    PDF,
    ROOT,
    SEED,
    is_keep_font,
    load_map,
    map_key,
    page_glyphs,
)

OUT = ROOT / "data" / "decode" / "_glyph_crops"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    gid_map = load_map()
    doc = fitz.open(PDF)
    end = min(end, doc.page_count)
    inst = Counter()
    samples: dict[str, list[tuple[int, float, float, float, float]]] = defaultdict(list)
    for page_1idx in range(start, end + 1):
        for y0, x0, x1, y1, font, gid, _ucs in page_glyphs(doc[page_1idx - 1]):
            if not is_keep_font(font):
                continue
            key = map_key(font, gid)
            if key in gid_map:
                continue
            inst[key] += 1
            if len(samples[key]) < 3:
                samples[key].append((page_1idx, x0, y0, x1, y1))
        if page_1idx % 50 == 0:
            print(f"...page {page_1idx}", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    top = inst.most_common(limit)
    print(f"unknown keys in range {len(inst)}; cropping top {len(top)}", flush=True)
    mat = fitz.Matrix(4, 4)
    written = []
    for key, n in top:
        page_1idx, x0, y0, x1, y1 = samples[key][0]
        page = doc[page_1idx - 1]
        pad_x, pad_y = 28, 6
        clip = fitz.Rect(x0 - pad_x, y0 - pad_y, x1 + pad_x, y1 + pad_y)
        pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
        safe = key.replace(":", "_")
        path = OUT / f"q_{safe}_p{page_1idx:03d}.png"
        pix.save(path)
        written.append((n, key, str(path.relative_to(ROOT).as_posix()), page_1idx))
        print(f"{n:5} {key:28} {path.name} p{page_1idx}", flush=True)

    index = OUT / "quran_gid_crops.json"
    index.write_text(
        json.dumps(
            [{"n": n, "key": k, "file": p, "page": pg} for n, k, p, pg in written],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"index {index.relative_to(ROOT).as_posix()}", flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
