"""
A/B test: transcribe a gold-set page image with a Bedrock Converse API model
using the shared canonical prompt, save the output under
data/gold/transcriptions/<page_id>/, and log the run (including exact inference
settings used) to data/gold/ocr_runs_log.csv.

Settings: temperature=0 and an explicit max_tokens ceiling are set for every model,
since this is an exact-transcription task, not a creative one. Extended
thinking/reasoning is not enabled for any model - Claude's thinking is opt-in
(off unless explicitly requested), and Haiku 4.5 does not support the
adaptive-thinking/effort parameter at all (confirmed against AWS's own docs -
that feature is limited to the Opus 4.6+/5-tier and Sonnet 4.6 models).

Model IDs verified against each provider's actual AWS model card (not the Bedrock
console's summary blurbs, which have repeatedly omitted real capabilities). Llama 4
Maverick and Pixtral Large are not available in-region for us-east-1 and need the
cross-region ("us.") inference profile ID; Kimi K2.5 and Qwen3-VL are in-region.

Usage:
    py -3 scripts/bedrock_ocr_test.py <path-to-image> <model_tag> [prompt_version]
    model_tag one of: haiku_4.5, qwen3_vl, kimi_k2.5, llama4_maverick, pixtral_large
"""

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import boto3

from ocr_test_common import (
    LATEST_PROMPT_VERSION, load_prompt, log_run, output_path, print_call_settings,
)

REGION = "us-east-1"
TEMPERATURE = 0
MAX_TOKENS = 4096

MODELS = {
    "haiku_4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "qwen3_vl": "qwen.qwen3-vl-235b-a22b",
    "kimi_k2.5": "moonshotai.kimi-k2.5",
    "llama4_maverick": "us.meta.llama4-maverick-17b-instruct-v1:0",
    "pixtral_large": "us.mistral.pixtral-large-2502-v1:0",
}

THINKING_NOTES = {
    "haiku_4.5": "not enabled (opt-in only; Haiku 4.5 does not support adaptive-thinking/effort)",
    "qwen3_vl": "not enabled (no thinking/reasoning field sent)",
    "kimi_k2.5": "not enabled (no thinking/reasoning field sent)",
    "llama4_maverick": "not enabled (no thinking/reasoning field sent)",
    "pixtral_large": "not enabled (no thinking/reasoning field sent)",
}


def main():
    if len(sys.argv) not in (3, 4):
        print(f"Usage: py -3 scripts/bedrock_ocr_test.py <path-to-image> <model_tag> [prompt_version]")
        print(f"model_tag one of: {list(MODELS)}")
        sys.exit(1)

    image_path = Path(sys.argv[1]).resolve()
    model_tag = sys.argv[2]
    if model_tag not in MODELS:
        print(f"Unknown model tag '{model_tag}'. Choose from: {list(MODELS)}")
        sys.exit(1)
    model_id = MODELS[model_tag]
    prompt_version = sys.argv[3] if len(sys.argv) == 4 else LATEST_PROMPT_VERSION

    page_id = image_path.stem
    thinking_note = THINKING_NOTES[model_tag]
    prompt_text = load_prompt(prompt_version)  # echoes path + full text to console

    inference_config = {"temperature": TEMPERATURE, "maxTokens": MAX_TOKENS}
    print_call_settings(model_id, TEMPERATURE, MAX_TOKENS, thinking_note, extra_settings={})

    client = boto3.client("bedrock-runtime", region_name=REGION)
    response = client.converse(
        modelId=model_id,
        messages=[{
            "role": "user",
            "content": [
                {"image": {"format": "png", "source": {"bytes": image_path.read_bytes()}}},
                {"text": prompt_text},
            ],
        }],
        inferenceConfig=inference_config,
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
    log_run(
        page_id, model_tag, prompt_version, in_tok, out_tok, total_tok, out_path,
        stop_reason=stop_reason, temperature=TEMPERATURE, max_tokens_requested=MAX_TOKENS,
        thinking=thinking_note,
    )
    print(f"\n(saved to {out_path}, run logged)")


if __name__ == "__main__":
    main()
