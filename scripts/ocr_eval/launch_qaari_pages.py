"""Start the Qaari whole-page test as one SageMaker training job (ml.g5.xlarge, hard time cap).

Pages must be in s3://gojri-ai-sagemaker-data/ocr-eval/pages/ (the gold page PNGs).
Needs env var SAGEMAKER_ROLE_ARN (and optionally GOJRI_BUCKET).
Run: py -3 -X utf8 scripts/ocr_eval/launch_qaari_pages.py
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
ap.add_argument("--max-run", type=int, default=3600, help="hard stop in seconds")
args = ap.parse_args()

est = PyTorch(
    entry_point="qaari_pages_entry.py",
    source_dir=str(HERE / "sm_qaari"),
    role=ROLE,
    framework_version="2.3",
    py_version="py311",
    instance_count=1,
    instance_type="ml.g5.xlarge",
    max_run=args.max_run,
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/ocr-eval/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name="gojri-qaari-pages",
)
est.fit({"pages": f"s3://{BUCKET}/ocr-eval/pages/"}, wait=False)
print("started:", est.latest_training_job.name)
