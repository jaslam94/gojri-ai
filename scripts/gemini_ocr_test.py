"""
A/B test: transcribe a gold-set page image with Gemini using the shared canonical
prompt (prompts/ocr_transcription_<version>.txt), save the output under
data/gold/transcriptions/<page_id>/, and log the run (including exact inference
settings used) to data/gold/ocr_runs_log.csv.

Settings: thinking_level is explicitly set to "low" (deliberate minimal-reasoning
choice for a transcription task; Gemini 3.6 Flash's own default is "minimal", i.e.
close to this already). Temperature is deliberately left at the SDK default (1.0)
rather than forced to 0 - Google's own Gemini 3 docs explicitly warn against
changing it, stating this "may cause looping or degraded performance". This is a
different choice than the Bedrock script makes for Claude/Qwen, and is intentional,
not an oversight - logged explicitly so the asymmetry is visible, not silent.

Usage:
    py -3 scripts/gemini_ocr_test.py data/gold/images_cropped/dict_alif.png [prompt_version]
"""

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from google import genai
from google.genai import types

from ocr_test_common import LATEST_PROMPT_VERSION, load_prompt, log_run, output_path, print_call_settings

MODEL = "gemini-3.6-flash"
MODEL_TAG = "gemini_3.6_flash"
THINKING_LEVEL = "low"
TEMPERATURE = None  # deliberately left at SDK default; see module docstring


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: py -3 scripts/gemini_ocr_test.py <path-to-image> [prompt_version]")
        sys.exit(1)

    prompt_version = sys.argv[2] if len(sys.argv) == 3 else LATEST_PROMPT_VERSION

    load_dotenv()
    image_path = Path(sys.argv[1]).resolve()
    page_id = image_path.stem
    prompt_text = load_prompt(prompt_version)  # echoes path + full text to console

    print_call_settings(
        MODEL, temperature=f"{TEMPERATURE} (SDK default, not overridden - see docstring)",
        max_tokens="default (not set)", thinking=f"thinking_level={THINKING_LEVEL}",
    )

    client = genai.Client()
    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_path.read_bytes(), mime_type="image/png"),
            prompt_text,
        ],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
        ),
    )

    print(f"--- {MODEL} ({prompt_version}) transcription of {image_path.name} ---\n")
    print(response.text)

    usage = response.usage_metadata
    in_tok = usage.prompt_token_count if usage else None
    out_tok = usage.candidates_token_count if usage else None
    total_tok = usage.total_token_count if usage else None
    thoughts_tok = getattr(usage, "thoughts_token_count", None) if usage else None
    finish_reason = response.candidates[0].finish_reason if response.candidates else None
    if usage:
        print(
            f"\n--- tokens: prompt={in_tok} output={out_tok} thoughts={thoughts_tok} "
            f"total={total_tok} finish_reason={finish_reason} ---"
        )

    out_path = output_path(image_path, MODEL_TAG, prompt_version)
    out_path.write_text(response.text, encoding="utf-8")
    log_run(
        page_id, MODEL_TAG, prompt_version, in_tok, out_tok, total_tok, out_path,
        stop_reason=str(finish_reason), temperature=TEMPERATURE, max_tokens_requested=None,
        thinking=f"thinking_level={THINKING_LEVEL}",
        extra_settings={"thoughts_token_count": thoughts_tok} if thoughts_tok else None,
    )
    print(f"\n(saved to {out_path}, run logged)")


if __name__ == "__main__":
    main()
