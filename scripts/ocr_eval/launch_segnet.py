"""Train the script segmenter (SegNet) as one SageMaker training job (ml.g5.xlarge, hard time cap).

Data: s3://$GOJRI_BUCKET/ocr-eval/seg/seg_data.pkl.gz (from build_segmenter_data.py).
Needs env var SAGEMAKER_ROLE_ARN (and optionally GOJRI_BUCKET).
Run: py -3 -X utf8 scripts/ocr_eval/launch_segnet.py [--epochs 14]
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
ap.add_argument("--epochs", type=int, default=14)
ap.add_argument("--max-run", type=int, default=3600, help="hard stop in seconds")
ap.add_argument("--data-prefix", default="ocr-eval/seg", help="S3 prefix (inside the bucket) holding the one seg_data*.pkl.gz")
args = ap.parse_args()

est = PyTorch(
    entry_point="segnet_entry.py",
    source_dir=str(HERE / "sm_seg"),
    role=ROLE,
    framework_version="2.3",
    py_version="py311",
    instance_count=1,
    instance_type="ml.g5.xlarge",
    max_run=args.max_run,
    hyperparameters={"epochs": args.epochs},
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/ocr-eval/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name="gojri-segnet",
)
est.fit({"data": f"s3://{BUCKET}/{args.data_prefix}/"}, wait=False)
print("started:", est.latest_training_job.name)
