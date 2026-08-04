"""Shared helpers for the per-model OCR test scripts (gemini_ocr_test.py,
bedrock_ocr_test.py, ...), so every run is logged the same way regardless of
provider.
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
TRANSCRIPTIONS_DIR = ROOT / "data" / "gold" / "transcriptions"
LATEST_PROMPT_VERSION = "v2"
RUNS_LOG = ROOT / "data" / "gold" / "ocr_runs_log.csv"

RUNS_LOG_FIELDS = [
    "timestamp_utc", "page_id", "model", "prompt_version",
    "temperature", "max_tokens_requested", "thinking",
    "input_tokens", "output_tokens", "total_tokens", "stop_reason",
    "extra_settings", "output_file",
]


def prompt_path(version=LATEST_PROMPT_VERSION):
    return PROMPTS_DIR / f"ocr_transcription_{version}.txt"


def load_prompt(version=LATEST_PROMPT_VERSION, echo=True):
    path = prompt_path(version)
    text = path.read_text(encoding="utf-8")
    if echo:
        print(f"--- prompt file: {path.relative_to(ROOT).as_posix()} ---")
        print(text)
        print("--- end prompt ---\n")
    return text


def output_path(image_path, model_tag, prompt_version=LATEST_PROMPT_VERSION):
    page_id = image_path.stem
    page_dir = TRANSCRIPTIONS_DIR / page_id
    page_dir.mkdir(parents=True, exist_ok=True)
    return page_dir / f"{page_id}_{model_tag}_{prompt_version}.txt"


def print_call_settings(model_id, temperature, max_tokens, thinking, extra_settings=None):
    print("--- invocation settings ---")
    print(f"model_id:        {model_id}")
    print(f"temperature:     {temperature}")
    print(f"max_tokens:      {max_tokens}")
    print(f"thinking:        {thinking}")
    print(f"extra_settings:  {extra_settings or {}}")
    print("--- end invocation settings ---\n")


def log_run(page_id, model, prompt_version, input_tokens, output_tokens, total_tokens,
            output_file, stop_reason=None, temperature=None, max_tokens_requested=None,
            thinking=None, extra_settings=None):
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
            "temperature": temperature,
            "max_tokens_requested": max_tokens_requested,
            "thinking": thinking,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "stop_reason": stop_reason,
            "extra_settings": json.dumps(extra_settings) if extra_settings else None,
            "output_file": str(output_file.relative_to(ROOT).as_posix()),
        })
