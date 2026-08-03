"""
Quick A/B test: transcribe a gold-set page image with Gemini and print the result,
for comparison against the existing Claude-drafted transcription in data/gold/images.

Usage:
    py -3 scripts/gemini_ocr_test.py data/gold/images/dict_alif.png
"""

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from dotenv import load_dotenv
from google import genai
from google.genai import types

MODEL = "gemini-3.6-flash"

PROMPT = (
    "Transcribe exactly what is written on this page image. This is Gojri/Urdu "
    "text in Perso-Arabic (Nastaliq) script, or Devanagari script, or English, "
    "depending on the page. Rules:\n"
    "- Transcribe only, do not translate.\n"
    "- Preserve line breaks and layout order as they appear on the page.\n"
    "- Pay close attention to diacritics and small marks (dots, nasalization "
    "strokes) - these are frequently the hardest part to get right.\n"
    "- If something is a non-text element (illustration, logo, decoration), "
    "describe it briefly in [brackets] instead of inventing text.\n"
    "- If a word or mark is genuinely illegible or ambiguous, mark it with "
    "[unclear: best guess] rather than silently guessing.\n"
)


def main():
    if len(sys.argv) != 2:
        print("Usage: py -3 scripts/gemini_ocr_test.py <path-to-image>")
        sys.exit(1)

    load_dotenv()
    image_path = Path(sys.argv[1])
    client = genai.Client()

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(
                data=image_path.read_bytes(),
                mime_type="image/png",
            ),
            PROMPT,
        ],
    )

    print(f"--- {MODEL} transcription of {image_path.name} ---\n")
    print(response.text)

    usage = response.usage_metadata
    if usage:
        print(
            f"\n--- tokens: prompt={usage.prompt_token_count} "
            f"output={usage.candidates_token_count} "
            f"total={usage.total_token_count} ---"
        )

    out_path = image_path.with_name(image_path.stem + "_gemini.txt")
    out_path.write_text(response.text, encoding="utf-8")
    print(f"\n(saved to {out_path})")


if __name__ == "__main__":
    main()
