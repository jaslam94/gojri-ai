"""Shared helpers for the per-model OCR test scripts (gemini_ocr_test.py,
claude_ocr_test.py, ...), so every run is logged the same way regardless of
provider.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
TRANSCRIPTIONS_DIR = ROOT / "data" / "gold" / "transcriptions"
LATEST_PROMPT_VERSION = "v2"
RUNS_LOG = ROOT / "data" / "gold" / "ocr_runs_log.csv"

RUNS_LOG_FIELDS = [
    "timestamp_utc", "page_id", "model", "prompt_version",
    "input_tokens", "output_tokens", "total_tokens", "stop_reason", "output_file",
]


def load_prompt(version=LATEST_PROMPT_VERSION):
    path = PROMPTS_DIR / f"ocr_transcription_{version}.txt"
    return path.read_text(encoding="utf-8")


def output_path(image_path, model_tag, prompt_version=LATEST_PROMPT_VERSION):
    page_dir = TRANSCRIPTIONS_DIR / image_path.stem
    page_dir.mkdir(parents=True, exist_ok=True)
    return page_dir / f"{model_tag}_{prompt_version}.txt"


def log_run(page_id, model, prompt_version, input_tokens, output_tokens, total_tokens, output_file, stop_reason=None):
    is_new = not RUNS_LOG.exists()
    RUNS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNS_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RUNS_LOG_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "page_id": page_id,
            "model": model,
            "prompt_version": prompt_version,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "stop_reason": stop_reason,
            "output_file": str(output_file.relative_to(ROOT).as_posix()),
        })
