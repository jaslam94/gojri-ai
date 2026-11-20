"""Run the Whisper fine-tune and scoring (sm_whisper_entry.py) as one SageMaker job (ml.g5.xlarge, hard time cap).

Needs s3://$GOJRI_BUCKET/asr/cv-gju-26/ (made by prepare_cv_split.py --upload) and the environment variable
SAGEMAKER_ROLE_ARN (never commit it). Run only when no other SageMaker job runs.
Smoke test:  py -3 -X utf8 scripts/asr/launch_whisper.py --max-steps 20 --eval-every 10 --limit-train 64 --limit-eval 32 --max-run 1800
Full run:    py -3 -X utf8 scripts/asr/launch_whisper.py --max-run 10800
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
ap.add_argument("--model", default="openai/whisper-small")
ap.add_argument("--max-steps", type=int, default=2500)
ap.add_argument("--eval-every", type=int, default=500)
ap.add_argument("--limit-train", type=int, default=0)
ap.add_argument("--limit-eval", type=int, default=0)
ap.add_argument("--max-run", type=int, default=10800, help="hard stop in seconds")
args = ap.parse_args()

est = PyTorch(
    entry_point="sm_whisper_entry.py",
    source_dir=str(HERE / "sm_whisper"),
    role=ROLE,
    framework_version="2.3",
    py_version="py311",
    instance_count=1,
    instance_type="ml.g5.xlarge",
    max_run=args.max_run,
    hyperparameters={"model": args.model, "max-steps": args.max_steps, "eval-every": args.eval_every,
                     "limit-train": args.limit_train, "limit-eval": args.limit_eval},
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/asr/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name="gojri-asr-whisper",
)
est.fit({"data": f"s3://{BUCKET}/asr/cv-gju-26/"}, wait=False)
print("started:", est.latest_training_job.name)
