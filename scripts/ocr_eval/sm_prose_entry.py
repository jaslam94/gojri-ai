"""SageMaker entry: run the prose and poetry page OCR (ocr_prose_pages.py) on a GPU.

Channels: `tools` = the UTRNet clone (model.py, modules/, UrduGlyphs.txt) and weights/large.pth;
          `pdf`   = one or more PDFs. Every PDF in the channel is read with the same page list.
Output: /opt/ml/model/<pdf stem>/dpi300/page_NNN.txt|json and crops/pNNN/Lkk.png.
Hyperparameters: --pages "12,60,150" (a list) or --first/--last (last 0 means to the end of each PDF), --dpi, --words,
--weights, --pdf-marks 1 (put pesh, zer and the other mark glyphs in from the PDF; needs the NOORIN fonts in the PDF).
launch_prose_pages.py stages this file at the root of the source dir and the scripts under scripts/ocr_eval/, with the mark
table at data/decode/noori_marks_seed.json, so the repo-relative paths of the mark code resolve.
"""
import argparse
import os
import runpy
import sys
from pathlib import Path

import fitz

ap = argparse.ArgumentParser()
ap.add_argument("--pages", default="", help="comma list, for example 12,60,150; empty means use first and last")
ap.add_argument("--first", type=int, default=1)
ap.add_argument("--last", type=int, default=0)
ap.add_argument("--dpi", default="300")
ap.add_argument("--words", default="auto")
ap.add_argument("--pdf-marks", type=int, default=0)
ap.add_argument("--weights", default="large.pth", help="file name under weights/ in the tools channel")
a = ap.parse_args()
tools = Path(os.environ.get("SM_CHANNEL_TOOLS", "/opt/ml/input/data/tools"))
pdfs = sorted(Path(os.environ.get("SM_CHANNEL_PDF", "/opt/ml/input/data/pdf")).glob("*.pdf"))
out = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
import torch  # noqa: E402
print("cuda:", torch.cuda.is_available(), "pdfs:", [p.name for p in pdfs], "pdf marks:", bool(a.pdf_marks), flush=True)
here = Path(__file__).resolve().parent
script = next(p for p in (here / "ocr_prose_pages.py", here / "scripts" / "ocr_eval" / "ocr_prose_pages.py") if p.exists())
for pdf in pdfs:
    n_pages = len(fitz.open(str(pdf)))
    if a.pages:
        pages = [int(x) for x in a.pages.split(",") if x.strip()]
        pages = [n for n in pages if 1 <= n <= n_pages]  # one list for all books; skip pages a short book lacks
    else:
        pages = list(range(a.first, (a.last or n_pages) + 1))
    sys.argv = ["ocr_prose_pages.py", "--repo", str(tools / "utrnet"), "--weights", str(tools / "weights" / a.weights),
                "--pdf", str(pdf), "--pages", *map(str, pages), "--dpis", a.dpi, "--out", out, "--words", a.words]
    if a.pdf_marks:
        sys.argv.append("--pdf-marks")
    runpy.run_path(str(script), run_name="__main__")
