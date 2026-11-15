"""SageMaker entry: run the Kahawat-Kosh OCR (ocr_kahawat.py) on a GPU.

Channels: `tools` = the UTRNet clone (model.py, modules/, UrduGlyphs.txt) and weights/large.pth;
          `pdf`   = the PDF; `eng` (optional) = eng_NNN.json English runs. Output: /opt/ml/model (page JSON/TXT files and kahawat_kosh_entries.tsv).
Hyperparameters (command line): --first, --last, --dpi, --weights (default large.pth).
"""
import argparse
import os
import runpy
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--first", default="1")
ap.add_argument("--last", default="0")
ap.add_argument("--dpi", default="200")
ap.add_argument("--weights", default="large.pth", help="file name under weights/ in the tools channel")
a = ap.parse_args()
tools = Path(os.environ.get("SM_CHANNEL_TOOLS", "/opt/ml/input/data/tools"))
pdf = next(Path(os.environ.get("SM_CHANNEL_PDF", "/opt/ml/input/data/pdf")).glob("*.pdf"))
out = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
import torch  # noqa: E402
print("cuda:", torch.cuda.is_available(), flush=True)
sys.argv = ["ocr_kahawat.py", "--repo", str(tools / "utrnet"), "--weights", str(tools / "weights" / a.weights),
            "--out", out, "--first", a.first, "--last", a.last, "--dpi", a.dpi, "--pdf", str(pdf)]
eng = os.environ.get("SM_CHANNEL_ENG")  # optional channel: eng_NNN.json files from english_spans.py
if eng:
    sys.argv += ["--eng-dir", eng]
runpy.run_path(str(Path(__file__).resolve().parent / "ocr_kahawat.py"), run_name="__main__")
