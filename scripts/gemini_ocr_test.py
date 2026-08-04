"""
A/B test: transcribe a gold-set page image with Gemini using the shared canonical
prompt (prompts/ocr_transcription_v1.txt), save the output next to the image as
<page_id>_<model_tag>.txt, and log the run to data/gold/ocr_runs_log.csv.

Usage:
    py -3 scripts/gemini_ocr_test.py data/gold/images/dict_alif.png
"""

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from google import genai
from google.genai import types

from ocr_test_common import load_prompt, log_run, output_path

MODEL = "gemini-3.6-flash"
MODEL_TAG = "gemini_3.6_flash"


def main():
    if len(sys.argv) != 2:
        print("Usage: py -3 scripts/gemini_ocr_test.py <path-to-image>")
        sys.exit(1)

    load_dotenv()
    image_path = Path(sys.argv[1]).resolve()
    page_id = image_path.stem
    client = genai.Client()

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_path.read_bytes(), mime_type="image/png"),
            load_prompt(),
        ],
    )

    print(f"--- {MODEL} transcription of {image_path.name} ---\n")
    print(response.text)

    usage = response.usage_metadata
    in_tok = usage.prompt_token_count if usage else None
    out_tok = usage.candidates_token_count if usage else None
    total_tok = usage.total_token_count if usage else None
    if usage:
        print(f"\n--- tokens: prompt={in_tok} output={out_tok} total={total_tok} ---")

    out_path = output_path(image_path, MODEL_TAG)
    out_path.write_text(response.text, encoding="utf-8")
    log_run(page_id, MODEL_TAG, in_tok, out_tok, total_tok, out_path)
    print(f"\n(saved to {out_path}, run logged)")


if __name__ == "__main__":
    main()
