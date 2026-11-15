"""Run the UTRNet fine-tune (finetune_utrnet.py) as one SageMaker training job (ml.g5.xlarge, hard time cap).

Needs in s3://$GOJRI_BUCKET/ocr-eval/: tools/utrnet/ and tools/weights/large.pth (as for launch_ocr_pdf.py) and
ft/data/ (the folder made by scripts/synth/build_utrnet_runs.py; upload it first, see LOG.md 2026-11-10).
Needs env var SAGEMAKER_ROLE_ARN (and optionally GOJRI_BUCKET).
Run: py -3 -X utf8 scripts/ocr_eval/launch_finetune.py [--epochs 1 --lr 2e-4 --batch 12 --freeze-bn --fold --train head --skip-drop --max-steps 750 --eval-every 250]
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
ap.add_argument("--epochs", type=int, default=6)
ap.add_argument("--lr", type=float, default=5e-5)
ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--freeze-bn", action="store_true")
ap.add_argument("--eval-every", type=int, default=300)
ap.add_argument("--log-every", type=int, default=100)
ap.add_argument("--fold", action="store_true")
ap.add_argument("--train", default="all", choices=["all", "lstm", "head"])
ap.add_argument("--skip-drop", action="store_true")
ap.add_argument("--max-steps", type=int, default=0)
ap.add_argument("--max-run", type=int, default=7200, help="hard stop in seconds")
args = ap.parse_args()

est = PyTorch(
    entry_point="sm_finetune_entry.py",
    source_dir=str(HERE),
    role=ROLE,
    framework_version="2.3",
    py_version="py311",
    instance_count=1,
    instance_type="ml.g5.xlarge",
    max_run=args.max_run,
    hyperparameters={"epochs": args.epochs, "lr": args.lr, "batch": args.batch, "freeze_bn": int(args.freeze_bn), "eval_every": args.eval_every, "log_every": args.log_every,
                     "fold": int(args.fold), "train": args.train, "skip_drop": int(args.skip_drop), "max_steps": args.max_steps},
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/ocr-eval/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name="gojri-utrnet-ft",
)
est.fit({"tools": f"s3://{BUCKET}/ocr-eval/tools/", "data": f"s3://{BUCKET}/ocr-eval/ft/data/"}, wait=False)
print("started:", est.latest_training_job.name)
