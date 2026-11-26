"""Run the Omnilingual ASR fine-tune (sm_omni_ft/omni_ft_entry.py) as one SageMaker job on ml.g5.12xlarge (4 x A10G, 24 GB each).

Needs s3://$GOJRI_BUCKET/asr/omni-ft/ (made by scripts/asr/omni_ft/make_parquet.py, plus splits/*.tsv copied in) and the environment
variable SAGEMAKER_ROLE_ARN (never commit it). One job per instance type at a time (service quota).
Smoke test:  py -3 -X utf8 scripts/asr/launch_omni_ft.py --tag smoke --num-steps 20 --checkpoint-every 10 --limit-eval 32 --max-run 7200
Real run:    py -3 -X utf8 scripts/asr/launch_omni_ft.py --tag 1b --upload-ckpt 1
Plan and risks: plans/PLAN-omnilingual-finetune-20261126.md.
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
ap.add_argument("--tag", default="1b", help="part of the job name")
ap.add_argument("--model-card", default="omniASR_LLM_1B")
ap.add_argument("--tokenizer", default="omniASR_tokenizer_v1")
ap.add_argument("--num-steps", type=int, default=400)
ap.add_argument("--checkpoint-every", type=int, default=80)
ap.add_argument("--lr", type=float, default=5e-5)
ap.add_argument("--accum", type=int, default=4)
ap.add_argument("--max-num-elements", type=int, default=320000)
ap.add_argument("--max-audio-len", type=int, default=320000)
ap.add_argument("--limit-eval", type=int, default=0)
ap.add_argument("--upload-ckpt", type=int, default=0)
ap.add_argument("--instance", default="ml.g5.12xlarge")
ap.add_argument("--max-run", type=int, default=21600, help="hard stop in seconds")
args = ap.parse_args()

est = PyTorch(
    entry_point="omni_ft_entry.py",
    source_dir=str(HERE / "sm_omni_ft"),
    role=ROLE,
    framework_version="2.8",
    py_version="py312",
    instance_count=1,
    instance_type=args.instance,
    max_run=args.max_run,
    volume_size=300,  # GB; model download plus model-only checkpoints
    hyperparameters={"model-card": args.model_card, "tokenizer": args.tokenizer, "num-steps": args.num_steps,
                     "checkpoint-every": args.checkpoint_every, "max-num-elements": args.max_num_elements, "max-audio-len": args.max_audio_len,
                     "lr": args.lr, "accum": args.accum, "limit-eval": args.limit_eval, "upload-ckpt": args.upload_ckpt, "bucket": BUCKET},
    code_location=f"s3://{BUCKET}/code",
    output_path=f"s3://{BUCKET}/asr/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
    base_job_name=f"gojri-asr-omni-ft-{args.tag}",
)
est.fit({"data": f"s3://{BUCKET}/asr/omni-ft/"}, wait=False)
print("started:", est.latest_training_job.name)
