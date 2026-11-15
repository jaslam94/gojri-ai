"""Run the diagnostic sweep (sm_sweep_entry.py) as one SageMaker training job (ml.g5.xlarge, 2 h cap).
Needs the same S3 inputs as launch_finetune.py and env var SAGEMAKER_ROLE_ARN."""
import os
from pathlib import Path

import sagemaker
from sagemaker.pytorch import PyTorch

HERE = Path(__file__).resolve().parent
BUCKET = os.environ.get("GOJRI_BUCKET", "gojri-ai-sagemaker-data")
est = PyTorch(
    entry_point="sm_sweep_entry.py", source_dir=str(HERE), role=os.environ["SAGEMAKER_ROLE_ARN"],
    framework_version="2.3", py_version="py311", instance_count=1, instance_type="ml.g5.xlarge", max_run=7200,
    code_location=f"s3://{BUCKET}/code", output_path=f"s3://{BUCKET}/ocr-eval/output",
    sagemaker_session=sagemaker.Session(default_bucket=BUCKET), base_job_name="gojri-utrnet-sweep",
)
est.fit({"tools": f"s3://{BUCKET}/ocr-eval/tools/", "data": f"s3://{BUCKET}/ocr-eval/ft/data/"}, wait=False)
print("started:", est.latest_training_job.name)
