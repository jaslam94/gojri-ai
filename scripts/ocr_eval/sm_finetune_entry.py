"""SageMaker entry: fine-tune UTRNet-Large on Gojri runs (finetune_utrnet.py) on a GPU.

Channels: `tools` = the UTRNet clone (utrnet/) and weights/large.pth; `data` = the folder from build_utrnet_runs.py
(img/, train.tsv, val.tsv, test.tsv). Output: /opt/ml/model (best.pth, last.pth, log.json, dropped.tsv).
Hyperparameters (command line): --epochs, --lr, --batch, --freeze_bn (1 = batch-norm layers stay in eval mode), --eval_every, --log_every, --fold (1 = fold ك ه ي in the labels), --train (all, lstm or head), --skip_drop, --max_steps.
"""
import argparse
import os
import runpy
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", default="6")
ap.add_argument("--lr", default="5e-5")
ap.add_argument("--batch", default="32")
ap.add_argument("--freeze_bn", default="0")
ap.add_argument("--eval_every", default="300")
ap.add_argument("--log_every", default="100")
ap.add_argument("--fold", default="0")
ap.add_argument("--train", default="all")
ap.add_argument("--skip_drop", default="0")
ap.add_argument("--max_steps", default="0")
a = ap.parse_args()
tools = Path(os.environ.get("SM_CHANNEL_TOOLS", "/opt/ml/input/data/tools"))
data = os.environ.get("SM_CHANNEL_DATA", "/opt/ml/input/data/data")
out = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
import torch  # noqa: E402
print("cuda:", torch.cuda.is_available(), flush=True)
sys.argv = ["finetune_utrnet.py", "--repo", str(tools / "utrnet"), "--weights", str(tools / "weights" / "large.pth"),
            "--data", data, "--out", out, "--epochs", a.epochs, "--lr", a.lr, "--batch", a.batch, "--eval-every", a.eval_every, "--log-every", a.log_every]
if a.freeze_bn == "1":
    sys.argv.append("--freeze-bn")
if a.fold == "1":
    sys.argv.append("--fold")
if a.skip_drop == "1":
    sys.argv.append("--skip-drop")
sys.argv += ["--train", a.train, "--max-steps", a.max_steps]
try:
    runpy.run_path(str(Path(__file__).resolve().parent / "finetune_utrnet.py"), run_name="__main__")
except BaseException as e:  # SageMaker shows only the start of stderr: put the short error in the failure file
    import traceback
    Path("/opt/ml/output").mkdir(parents=True, exist_ok=True)
    Path("/opt/ml/output/failure").write_text((type(e).__name__ + ": " + str(e)[:300] + " | " + traceback.format_exc()[-500:]), encoding="utf-8")
    raise
