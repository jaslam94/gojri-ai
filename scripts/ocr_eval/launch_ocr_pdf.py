"""Run the Kahawat-Kosh OCR as one SageMaker training job (ml.g5.xlarge, hard time cap).

Needs in s3://$GOJRI_BUCKET/ocr-eval/: tools/utrnet/ (clone without .git), tools/weights/large.pth, pdf/<book>.pdf.
Needs env var SAGEMAKER_ROLE_ARN (and optionally GOJRI_BUCKET).
Run: py -3 -X utf8 scripts/ocr_eval/launch_ocr_pdf.py [--first 1 --last 169]
"""
import argparse
import os
from pathlib import Path

import sagemaker
from sagemaker.pytorch import PyTorch

HERE = Path(__file__).resolve().parent
BUCKET = os.environ.get("GOJRI_BUCKET", "gojri-ai-sagemaker-data")
ROLE = os.environ["SAGEMAKER_ROLE_ARN"]  # IAM execution role ARN; set it in your shell, never commit it

ap = argparse.ArgumentParser()
ap.add_argument("--first", type=int, default=1)
ap.add_argument("--last", type=int, default=0)
ap.add_argument("--dpi", type=int, default=200)
ap.add_argument("--weights", default="large.pth", help="file name under ocr-eval/tools/weights/ in S3")
ap.add_argument("--eng", action="store_true", help="also send s3://$GOJRI_BUCKET/ocr-eval/eng/ (English runs from english_spans.py)")
ap.add_argument("--max-run", type=int, default=7200, help="hard stop in seconds")
args = ap.parse_args()

est = PyTorch(
    entry_point="sm_ocr_entry.py",
    source_dir=str(HERE),
    role=ROLE,
    framework_version="2.3",
    py_version="py311",
    instance_count=1,
    instance_type="ml.g5.xlarge",
    max_run=args.max_run,
    hyperparameters={"first": args.first, "last": args.last, "dpi": args.dpi, "weights": args.weights},
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/ocr-eval/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name="gojri-ocr-kahawat",
)
channels = {"tools": f"s3://{BUCKET}/ocr-eval/tools/", "pdf": f"s3://{BUCKET}/ocr-eval/pdf/"}
if args.eng:
    channels["eng"] = f"s3://{BUCKET}/ocr-eval/eng/"
est.fit(channels, wait=False)
print("started:", est.latest_training_job.name)
