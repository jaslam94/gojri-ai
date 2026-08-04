"""
A/B test: transcribe a gold-set page image with a Bedrock Converse API model
(Claude Haiku 4.5 or Qwen3-VL) using the shared canonical prompt, save the output
under data/gold/transcriptions/<page_id>/, and log the run to
data/gold/ocr_runs_log.csv.

Usage:
    py -3 scripts/bedrock_ocr_test.py <path-to-image> <haiku_4.5|qwen3_vl> [prompt_version]
"""

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import boto3

from ocr_test_common import LATEST_PROMPT_VERSION, load_prompt, log_run, output_path

REGION = "us-east-1"

MODELS = {
    "haiku_4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "qwen3_vl": "qwen.qwen3-vl-235b-a22b",
}


def main():
    if len(sys.argv) not in (3, 4):
        print("Usage: py -3 scripts/bedrock_ocr_test.py <path-to-image> <haiku_4.5|qwen3_vl> [prompt_version]")
        sys.exit(1)

    image_path = Path(sys.argv[1]).resolve()
    model_tag = sys.argv[2]
    if model_tag not in MODELS:
        print(f"Unknown model tag '{model_tag}'. Choose from: {list(MODELS)}")
        sys.exit(1)
    model_id = MODELS[model_tag]
    prompt_version = sys.argv[3] if len(sys.argv) == 4 else LATEST_PROMPT_VERSION

    page_id = image_path.stem
    client = boto3.client("bedrock-runtime", region_name=REGION)

    response = client.converse(
        modelId=model_id,
        messages=[{
            "role": "user",
            "content": [
                {"image": {"format": "png", "source": {"bytes": image_path.read_bytes()}}},
                {"text": load_prompt(prompt_version)},
            ],
        }],
    )

    text = response["output"]["message"]["content"][0]["text"]
    usage = response.get("usage", {})
    in_tok = usage.get("inputTokens")
    out_tok = usage.get("outputTokens")
    total_tok = usage.get("totalTokens")
    stop_reason = response.get("stopReason")

    print(f"--- {model_id} ({prompt_version}) transcription of {image_path.name} ---\n")
    print(text)
    print(f"\n--- tokens: input={in_tok} output={out_tok} total={total_tok} stop_reason={stop_reason} ---")

    out_path = output_path(image_path, model_tag, prompt_version)
    out_path.write_text(text, encoding="utf-8")
    log_run(page_id, model_tag, prompt_version, in_tok, out_tok, total_tok, out_path, stop_reason)
    print(f"\n(saved to {out_path}, run logged)")


if __name__ == "__main__":
    main()
