"""Start one SageMaker training job for the Gojri line-OCR model (GPU).

Needs: the upload files in s3://BUCKET/train/ (see sagemaker_upload.md in LOG.md),
and boto3 plus sagemaker<3. Cost cap: max_run seconds on one ml.g5.xlarge.

Needs env var SAGEMAKER_ROLE_ARN (and optionally GOJRI_BUCKET).
Run: py -3 -X utf8 scripts/synth/sagemaker_launch.py --epochs 8
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
ap.add_argument("--epochs", type=int, default=8)
ap.add_argument("--bs", type=int, default=64)
ap.add_argument("--real-rep", type=int, default=3)
ap.add_argument("--limit", type=int, default=0, help="test run on N rows")
ap.add_argument("--max-run", type=int, default=3 * 3600, help="hard stop in seconds")
ap.add_argument("--instance", default="ml.g5.xlarge")
args = ap.parse_args()

hp = {"epochs": args.epochs, "bs": args.bs, "workers": 4, "real-rep": args.real_rep}
if args.limit:
    hp["limit"] = args.limit

est = PyTorch(
    entry_point="sm_entry.py",
    source_dir=str(HERE),
    role=ROLE,
    framework_version="2.3",
    py_version="py311",
    instance_count=1,
    instance_type=args.instance,
    max_run=args.max_run,
    hyperparameters=hp,
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name="gojri-crnn",
)
est.fit({"train": f"s3://{BUCKET}/train/"}, wait=False)
print("started:", est.latest_training_job.name)
