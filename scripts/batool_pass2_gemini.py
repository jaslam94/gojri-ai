"""
Pass 2: Refine Batool PUA decoded text using Gemini 3.6 Flash + page image reference.

Combines:
1. Pass 1 Batool font-decoded text (accurate letter glyphs, minor spacing/Latin glitches).
2. Page image (visual ground truth).
3. Gojri orthographic rules & dictionary layout conventions from Gold set.

Usage:
    py -3 scripts/batool_pass2_gemini.py 26
    py -3 scripts/batool_pass2_gemini.py 25 28
    py -3 scripts/batool_pass2_gemini.py --list data/decode/out/gojri-english-dictionary/pass2_sample_40.txt
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

ROOT = Path(__file__).resolve().parent.parent
DECODE_OUT = ROOT / "data" / "decode" / "out" / "gojri-english-dictionary"
IMAGE_DIR = ROOT / "data" / "decode" / "out" / "page_images"

MODEL = "gemini-3.6-flash"
FALLBACK_MODELS = ("gemini-3.5-flash", "gemini-3.6-flash")

PASS2_PROMPT = """You are performing Pass 2 refinement for a Gojri-English dictionary digitisation project.

Gojri (گوجری) is an Indo-Aryan language spoken by Gujjar communities. It uses the Nastaliq (Perso-Arabic) script and has its own distinct orthography, grammar, and vocabulary.

Below you are given TWO inputs for a dictionary page:
1. RAW BATOOL PASS 1 DECODED TEXT: Extracted directly from font glyphs. The Gojri letters are mostly accurate, but it contains technical glitches such as:
   - Misread English label prefixes (e.g. 'Ipp:' instead of 'lpp:')
   - Merged words or missing spaces between Nastaliq and Latin text
   - Minor typos in Latin glosses or grammatical abbreviations
2. PAGE IMAGE: The visual image of the printed page.

YOUR TASK:
Produce the final, highly accurate Pass 2 refined text for this dictionary page by aligning the Pass 1 decoded text with the visual page image.

STRICT RULES & GOJRI ORTHOGRAPHY GUIDELINES:

1. GOJRI SPELLING & LETTER PRESERVATION (DO NOT NORMALISE TO URDU):
   - Keep Gojri word endings (-و like آپنو, آٹو, آتھرنو, ابھارو). Do NOT convert -و to -ا or -ے۔
   - Keep Gojri vocabulary intact (e.g., مُنہ, هنڄو, دھُپ, ھُدرو, پوهچنو, پڑکل, نکیڑنی).
   - Preserve retroflexes (ٹ, ڈ, ڑ, ݨ).
   - Keep the correct heh forms as printed:
     * goal heh (ہ)
     * do-chashmi heh (ھ) in aspirated sounds (دھ, بھ, تھ, کھ, پھ, جھ, چھ, گھ)
     * Arabic heh (ه)
   - Preserve all printed diacritics (pesh ُ, zer ِ, zabar َ, shadda ّ, hamza, noon-ghunna ں).

2. DICTIONARY ENTRY STRUCTURE & FIXES:
   - Each entry has: Gojri Nastaliq headword + (romanisation) + part of speech/label + English definition + optional example phrase.
   - Example phrases/proverbs in this dictionary use the label 'lpp:' (proverb/idiom label). Fix raw decoding errors like 'Ipp:' or '1pp:' to 'lpp:'.
   - Fix merged Nastaliq and Latin text by inserting a space (e.g., 'آپنی(aapni)' -> 'آپنی (aapni)').
   - Maintain the line-by-line dictionary layout as printed on the page.

3. FIDELITY & NO HALLUCINATION:
   - Transcribe ONLY what is on the page.
   - Do NOT add new example sentences, words, or commentary that do not exist on the page image or Pass 1 text.
   - Do NOT drop any headword or line present in the Pass 1 text / image.

4. OUTPUT FORMAT:
   - Output plain text only.
   - No markdown code fences (```), no introductory preamble, no post-explanation.

Here is the RAW PASS 1 BATOOL DECODED TEXT:
---
{pass1_text}
---

Now inspect the attached page image and produce the final Pass 2 refined text.
"""


def process_page(page_num: int, client: genai.Client, model: str = MODEL) -> str:
    pass1_path = DECODE_OUT / f"page-{page_num:04d}.txt"
    img_path = IMAGE_DIR / f"page_{page_num:04d}.png"

    if not pass1_path.exists():
        raise FileNotFoundError(f"Pass 1 text not found: {pass1_path}")
    if not img_path.exists():
        raise FileNotFoundError(f"Page image not found: {img_path}")

    pass1_text = pass1_path.read_text(encoding="utf-8")
    prompt = PASS2_PROMPT.format(pass1_text=pass1_text)

    print(f"Calling {model} for Pass 2 on page {page_num}...")
    last_err: Exception | None = None
    for attempt in range(1, 6):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=img_path.read_bytes(), mime_type="image/png"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                ),
            )
            return response.text
        except errors.ServerError as e:
            last_err = e
            print(f"  Attempt {attempt} failed (server). Retrying in {attempt * 3}s...")
            time.sleep(attempt * 3)
        except errors.ClientError as e:
            last_err = e
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                raise
            print(f"  Attempt {attempt} failed (client). Retrying in {attempt * 3}s...")
            time.sleep(attempt * 3)
    raise RuntimeError(f"Failed to process page {page_num} after retries: {last_err}")


def parse_pages(args: argparse.Namespace) -> list[int]:
    if args.list:
        text = Path(args.list).read_text(encoding="utf-8")
        pages = [int(line.strip()) for line in text.splitlines() if line.strip()]
        return pages
    if args.start is None:
        raise SystemExit(
            "Usage: py -3 scripts/batool_pass2_gemini.py START [END]\n"
            "   or: py -3 scripts/batool_pass2_gemini.py --list PATH"
        )
    end = args.end if args.end is not None else args.start
    return list(range(args.start, end + 1))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Batool Pass 2 Gemini refinement")
    parser.add_argument("start", nargs="?", type=int, help="Start page (1-indexed)")
    parser.add_argument("end", nargs="?", type=int, help="End page (inclusive)")
    parser.add_argument("--list", type=str, help="Text file with one page number per line")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip pages that already have page-NNNN-pass2.txt",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=2.0,
        help="Seconds to wait between successful API calls (default 2)",
    )
    parser.add_argument("--model", type=str, default=MODEL, help=f"Gemini model (default {MODEL})")
    args = parser.parse_args()

    load_dotenv()
    client = genai.Client()
    pages = parse_pages(args)
    models = [args.model] + [m for m in FALLBACK_MODELS if m != args.model]

    for p in pages:
        out_path = DECODE_OUT / f"page-{p:04d}-pass2.txt"
        if args.skip_existing and out_path.exists():
            print(f"skip existing {out_path.relative_to(ROOT)}")
            continue
        refined_text = None
        for model in models:
            try:
                refined_text = process_page(p, client, model=model)
                break
            except errors.ClientError as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    print(f"Quota hit on {model} for page {p}: {e}")
                    continue
                raise
        if refined_text is None:
            print(f"Stopped at page {p}: quota exhausted on all tried models.")
            sys.exit(3)
        out_path.write_text(refined_text, encoding="utf-8")
        print(f"Wrote Pass 2 result to {out_path.relative_to(ROOT)}")
        if args.sleep > 0:
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
