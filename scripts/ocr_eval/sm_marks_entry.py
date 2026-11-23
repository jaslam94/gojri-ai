"""SageMaker entry: put the PDF mark glyphs into the Kahawat-Kosh OCR entries (pdf_marks/marks_insert.py) on a GPU.

Channels: `tools` = UTRNet clone (utrnet/) and weights/large.pth; `pdf` = Kahawat-Kosh.pdf;
          `stage` = a repo-shaped data tree: data/ocr/pdfmarks-work/{trace,fonts}, data/ocr/kahawat-gpu6/page_*.json (the base run),
          data/decode/noori_marks_seed.json, data/reviews/kahawat-first-30/*.json (see launch_marks.py for how it is made).
The code expects a repo layout (paths are relative to the repo root), so this entry builds one in /tmp/repo.
Hyperparameters: --pages "1 2 3" (PDF pages), --host-fix "0688+062f" (hex code points: OCR letter + glyph letter). Output: /opt/ml/model/page_NNN.json.
"""
import argparse
import os
import runpy
import shutil
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--pages", nargs="*", default=[])  # one quoted string or several tokens, both work
ap.add_argument("--host-fix", nargs="*", default=[])
ap.add_argument("--weights", default="large.pth")
a = ap.parse_args()
pages = " ".join(a.pages).replace('"', " ").split()
host_fix = " ".join(a.host_fix).replace('"', " ").split()
chan = lambda n, d: Path(os.environ.get(n, d))  # noqa: E731
tools = chan("SM_CHANNEL_TOOLS", "/opt/ml/input/data/tools")
pdf = next(chan("SM_CHANNEL_PDF", "/opt/ml/input/data/pdf").glob("*.pdf"))
stage = chan("SM_CHANNEL_STAGE", "/opt/ml/input/data/stage")
out = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
root = Path("/tmp/repo")
shutil.copytree(Path(__file__).resolve().parent, root / "scripts/ocr_eval", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copytree(stage / "data", root / "data")
(root / "pdfs/anjumshanasi").mkdir(parents=True)
shutil.copy(pdf, root / "pdfs/anjumshanasi/Kahawat-Kosh.pdf")
os.environ["UTRNET_REPO"] = str(tools / "utrnet")
os.environ["UTRNET_WEIGHTS"] = str(tools / "weights" / a.weights)
import torch  # noqa: E402
print("cuda:", torch.cuda.is_available(), flush=True)
sys.argv = ["marks_insert.py", "--out", out, "--threads", "4"]
if pages:
    sys.argv += ["--pages"] + pages
if host_fix:
    # pairs come as hex code points "0688+062f" (OCR letter + glyph letter), so no non-ASCII text goes through the job arguments
    sys.argv += ["--host-fix"] + [chr(int(x, 16)) + chr(int(y, 16)) for x, y in (t.split("+") for t in host_fix)]
runpy.run_path(str(root / "scripts/ocr_eval/pdf_marks/marks_insert.py"), run_name="__main__")
