"""SageMaker entry: diagnostic sweep for the UTRNet fine-tune.

Round 3 (2026-11-11): the output layer only (letters stay as they are), folded labels, 1,500 steps, three learning rates.
Scores val, test (25 held-out pages) and test_seen (the 200 reviewed lines) every 250 steps.
Rounds 1 and 2 (all weights, or sequence layer, or letters-only labels, and so on) damaged the letters: see LOG.md 2026-11-10 and 11.
Channels: `tools` (UTRNet clone and weights/large.pth), `data` (build_utrnet_runs.py output).
Output: /opt/ml/model/<variant>/log.json and summary.json.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

tools = Path(os.environ.get("SM_CHANNEL_TOOLS", "/opt/ml/input/data/tools"))
data = os.environ.get("SM_CHANNEL_DATA", "/opt/ml/input/data/data")
out = Path(os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
script = Path(__file__).resolve().parent / "finetune_utrnet.py"
common = ["--repo", str(tools / "utrnet"), "--weights", str(tools / "weights" / "large.pth"), "--data", data,
          "--epochs", "2", "--max-steps", "1500", "--batch", "12", "--warmup", "50", "--freeze-bn",
          "--no-save", "--eval-every", "250", "--fold", "--train", "head", "--skip-drop"]
variants = {"head_2e-4": ["--lr", "2e-4"], "head_6e-4": ["--lr", "6e-4"], "head_2e-3": ["--lr", "2e-3"]}
summary = {}
for name, extra in variants.items():
    d = out / name
    d.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([sys.executable, str(script)] + common + extra + ["--out", str(d)], capture_output=True, text=True)
    print(name, "exit", p.returncode, flush=True)
    print(p.stdout[-1500:], flush=True)
    if p.returncode:
        print(p.stderr[-1500:], flush=True)
    try:
        log = json.loads((d / "log.json").read_text(encoding="utf-8"))
        summary[name] = [(r["tag"],) + tuple((r[k]["letter_err"], r[k]["mark_err"], r[k]["full_err"]) for k in ("val", "test", "test_seen")) for r in log]
    except Exception as e:  # keep going: one failed variant must not hide the others
        summary[name] = f"no log: {e}"
(out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print(json.dumps(summary, indent=1))
