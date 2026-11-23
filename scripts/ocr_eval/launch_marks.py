"""Run the PDF mark step for Kahawat-Kosh as one SageMaker training job (ml.g5.xlarge, hard time cap).

Needs in s3://$GOJRI_BUCKET/ocr-eval/: tools/ (UTRNet clone and weights), pdf/Kahawat-Kosh.pdf and kahawat-marks-in/ (the staged data tree:
data/ocr/pdfmarks-work/{trace,fonts}, data/ocr/kahawat-gpu6/page_*.json, data/decode/noori_marks_seed.json, data/reviews/kahawat-first-30/*.json).
Needs env var SAGEMAKER_ROLE_ARN (never commit it). Run:
  py -3 -X utf8 scripts/ocr_eval/launch_marks.py --pages-file data/ocr/kahawat-final-remaining.txt --host-fix 0688+062f
"""
import argparse
import os
from pathlib import Path

import sagemaker
from sagemaker.pytorch import PyTorch

HERE = Path(__file__).resolve().parent
BUCKET = os.environ.get("GOJRI_BUCKET", "gojri-ai-sagemaker-data")
ROLE = os.environ["SAGEMAKER_ROLE_ARN"]

ap = argparse.ArgumentParser()
ap.add_argument("--pages-file", required=True, help="text file with PDF page numbers separated by spaces")
ap.add_argument("--host-fix", default="")
ap.add_argument("--max-run", type=int, default=5400, help="hard stop in seconds")
args = ap.parse_args()
pages = Path(args.pages_file).read_text(encoding="utf-8").strip()
est = PyTorch(
    entry_point="sm_marks_entry.py",
    source_dir=str(HERE),
    role=ROLE,
    framework_version="2.3",
    py_version="py311",
    instance_count=1,
    instance_type="ml.g5.xlarge",
    max_run=args.max_run,
    hyperparameters={"pages": pages, "host-fix": args.host_fix},
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/ocr-eval/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name="gojri-marks-kahawat",
)
est.fit({"tools": f"s3://{BUCKET}/ocr-eval/tools/", "pdf": f"s3://{BUCKET}/ocr-eval/pdf/", "stage": f"s3://{BUCKET}/ocr-eval/kahawat-marks-in/"}, wait=False)
print("started:", est.latest_training_job.name)
