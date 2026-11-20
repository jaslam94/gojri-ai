"""Run the prose and poetry page OCR (ocr_prose_pages.py) as one SageMaker job (ml.g5.xlarge, hard time cap).

Needs in s3://$GOJRI_BUCKET/ocr-eval/: tools/utrnet/, tools/weights/large.pth (same as launch_ocr_pdf.py),
and prose-pdf/<book>.pdf (only the books to read; every PDF there is read; --pdf-prefix picks another folder).
Needs env var SAGEMAKER_ROLE_ARN (and optionally GOJRI_BUCKET). Run only when no other SageMaker job runs.

The code is staged in a temporary folder first: the entry file at its root, the scripts under scripts/ocr_eval/ (so the
repo-relative paths of the mark code work), the mark table at data/decode/noori_marks_seed.json, and a requirements.txt.

Test run on the checked pages, with PDF marks:
  py -3 -X utf8 scripts/ocr_eval/launch_prose_pages.py --pages 12,50,60,100,150,200,300,450 --pdf-marks --max-run 3600
Whole books: --first 1 --last 0 --pdf-marks --max-run 14400 (every page of every PDF in prose-pdf/).
"""
import argparse
import os
import shutil
import tempfile
from pathlib import Path

import sagemaker
from sagemaker.pytorch import PyTorch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUCKET = os.environ.get("GOJRI_BUCKET", "gojri-ai-sagemaker-data")
ROLE = os.environ["SAGEMAKER_ROLE_ARN"]  # IAM execution role ARN; set it in your shell, never commit it

ap = argparse.ArgumentParser()
ap.add_argument("--pages", default="", help="comma list of page numbers; empty means --first to --last")
ap.add_argument("--first", type=int, default=1)
ap.add_argument("--last", type=int, default=0)
ap.add_argument("--dpi", default="300")
ap.add_argument("--words", default="auto", choices=["auto", "on", "off"])
ap.add_argument("--pdf-marks", action="store_true", help="put pesh, zer and other marks in from the PDF mark glyphs")
ap.add_argument("--weights", default="large.pth", help="file name under ocr-eval/tools/weights/ in S3")
ap.add_argument("--max-run", type=int, default=3600, help="hard stop in seconds")
ap.add_argument("--pdf-prefix", default="prose-pdf", help="S3 folder under ocr-eval/ that holds the PDFs to read (all of them are read)")
args = ap.parse_args()

stage = Path(tempfile.mkdtemp(prefix="gojri_prose_src_"))
(stage / "scripts" / "ocr_eval" / "pdf_marks").mkdir(parents=True)
for f in HERE.glob("*.py"):
    shutil.copy(f, stage / "scripts" / "ocr_eval" / f.name)
for f in (HERE / "pdf_marks").glob("*.py"):
    shutil.copy(f, stage / "scripts" / "ocr_eval" / "pdf_marks" / f.name)
(stage / "data" / "decode").mkdir(parents=True)
shutil.copy(ROOT / "data" / "decode" / "noori_marks_seed.json", stage / "data" / "decode" / "noori_marks_seed.json")
shutil.copy(HERE / "sm_prose_entry.py", stage / "sm_prose_entry.py")
(stage / "requirements.txt").write_text("pymupdf\npillow\nnumpy\nscipy\nfonttools\n", encoding="utf-8")

est = PyTorch(
    entry_point="sm_prose_entry.py",
    source_dir=str(stage),
    role=ROLE,
    framework_version="2.3",
    py_version="py311",
    instance_count=1,
    instance_type="ml.g5.xlarge",
    max_run=args.max_run,
    # an empty value would reach the entry as a bare "--pages" with no argument (argparse exit 2), so leave "pages" out
    hyperparameters={**({"pages": args.pages} if args.pages else {}), "first": args.first, "last": args.last,
                     "dpi": args.dpi, "words": args.words, "weights": args.weights, "pdf-marks": int(args.pdf_marks)},
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/ocr-eval/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name="gojri-ocr-prose",
)
est.fit({"tools": f"s3://{BUCKET}/ocr-eval/tools/", "pdf": f"s3://{BUCKET}/ocr-eval/{args.pdf_prefix}/"}, wait=False)
print("started:", est.latest_training_job.name)
shutil.rmtree(stage, ignore_errors=True)
