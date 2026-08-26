"""Decode Quran GID pages to Unicode text files.

Decodes in short child processes. PyMuPDF texttrace can crash if many
pages stay in one Python session.

  py -3 scripts/decode_quran.py 17
  py -3 scripts/decode_quran.py 1 80
  py -3 scripts/decode_quran.py 1 717
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_quran_gids import PDF, ROOT, decode_page, load_map

OUT = ROOT / "data" / "decode" / "out" / "quranic-translation-gojri"
BATCH = 10


def decode_range(start: int, end: int) -> None:
    gid_map = load_map()
    OUT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    end = min(end, doc.page_count)
    for page_1idx in range(start, end + 1):
        text = decode_page(doc[page_1idx - 1], gid_map)
        path = OUT / f"page-{page_1idx:04d}.txt"
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT).as_posix()} ({len(text)} chars)", flush=True)
    sys.stdout.flush()
    os._exit(0)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("usage: py -3 scripts/decode_quran.py START [END]")
        sys.exit(2)
    args = [a for a in sys.argv[1:] if a != "--worker"]
    worker = "--worker" in sys.argv
    start = int(args[0])
    end = int(args[1]) if len(args) > 1 else start
    if worker:
        decode_range(start, end)

    doc = fitz.open(PDF)
    end = min(end, doc.page_count)
    doc.close()
    script = str(Path(__file__).resolve())
    for batch_start in range(start, end + 1, BATCH):
        batch_end = min(batch_start + BATCH - 1, end)
        print(f"...decode {batch_start}-{batch_end}", flush=True)
        subprocess.run(
            [sys.executable, script, str(batch_start), str(batch_end), "--worker"],
            check=True,
        )


if __name__ == "__main__":
    main()
