"""Run the Omnilingual ASR zero-shot test (sm_omni/omni_entry.py) as one SageMaker job (ml.g5.xlarge, PyTorch 2.8, hard time cap).

Needs s3://$GOJRI_BUCKET/asr/cv-gju-26/ and the environment variable SAGEMAKER_ROLE_ARN (never commit it).
Run only when no other SageMaker job runs.
Quick check:  py -3 -X utf8 scripts/asr/launch_omni.py --models omniASR_CTC_300M --limit-eval 32 --max-run 3600
Full test:    py -3 -X utf8 scripts/asr/launch_omni.py
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
ap.add_argument("--models", default="omniASR_LLM_300M:gju_Arab,omniASR_LLM_1B:gju_Arab,omniASR_LLM_3B:gju_Arab,omniASR_LLM_7B:gju_Arab,omniASR_LLM_7B:urd_Arab,omniASR_LLM_7B,omniASR_CTC_1B")
ap.add_argument("--limit-eval", type=int, default=0)
ap.add_argument("--batch", type=int, default=4)
ap.add_argument("--instance", default="ml.g5.xlarge", help="3B and 7B need ml.g5.4xlarge (64 GB RAM); xlarge has 16 GB")
ap.add_argument("--max-run", type=int, default=10800, help="hard stop in seconds")
args = ap.parse_args()

est = PyTorch(
    entry_point="omni_entry.py",
    source_dir=str(HERE / "sm_omni"),
    role=ROLE,
    framework_version="2.8",
    py_version="py312",
    instance_count=1,
    instance_type=args.instance,
    max_run=args.max_run,
    volume_size=150,  # GB; the 7B checkpoints are 25 to 30 GB each
    hyperparameters={"models": args.models, "limit-eval": args.limit_eval, "batch": args.batch},
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/asr/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name="gojri-asr-omni",
)
est.fit({"data": f"s3://{BUCKET}/asr/cv-gju-26/"}, wait=False)
print("started:", est.latest_training_job.name)
