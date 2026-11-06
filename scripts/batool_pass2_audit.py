"""Audit Pass 2 text against page images with Gemini vision.

Reports only real inconsistencies (wrong Gojri letters, dropped/added
headwords, wrong heh forms). Ignores trivial Latin spacing unless it
changes meaning.

Usage:
  py -3 scripts/batool_pass2_audit.py --list data/decode/out/gojri-english-dictionary/pass2_sample_40.txt
  py -3 scripts/batool_pass2_audit.py 25 37 49
  py -3 scripts/batool_pass2_audit.py --list ... --skip-existing --sleep 3
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
AUDIT_OUT = DECODE_OUT / "audit"

MODEL = "gemini-3.6-flash"
FALLBACK_MODELS = ("gemini-3.5-flash", "gemini-3.6-flash")

AUDIT_PROMPT = """You are auditing a Gojri-English dictionary page digitisation.

Gojri (گوجری) uses Nastaliq. It is NOT Urdu. Keep Gojri spellings.

You get:
1) PAGE IMAGE (ground truth)
2) PASS 2 TEXT (digitised transcription)

Compare Pass 2 to the printed page. List ONLY real inconsistencies.

Count as errors:
- Wrong Gojri / Nastaliq letters (including heh forms ہ vs ھ vs ه)
- Wrong retroflex (ٹ ڈ ڑ) or missing/extra diacritics that change the word
- Dropped or invented headwords / example phrases
- Wrong proverb label if the page shows lpp: and text has something else
- Headword clearly mismatched to the printed word

Do NOT count as errors:
- Minor English spelling/punctuation differences that do not change sense
- Extra/missing spaces between Nastaliq and Latin if letters match
- Line-break differences if the same words are present
- Romanisation differences if Nastaliq headword is correct

Output format (plain text only):
Line 1: PAGE <n> | OK or ISSUES:<count>
Then zero or more lines:
  - printed: <exact snippet> | pass2: <exact snippet> | note: <short>

If fully consistent for Gojri content, output only:
PAGE <n> | OK

PASS 2 TEXT:
---
{pass2_text}
---
"""


def audit_page(page_num: int, client: genai.Client, model: str) -> str:
    pass2_path = DECODE_OUT / f"page-{page_num:04d}-pass2.txt"
    img_path = IMAGE_DIR / f"page_{page_num:04d}.png"
    if not pass2_path.exists():
        raise FileNotFoundError(pass2_path)
    if not img_path.exists():
        raise FileNotFoundError(img_path)

    pass2_text = pass2_path.read_text(encoding="utf-8")
    prompt = AUDIT_PROMPT.format(pass2_text=pass2_text)
    print(f"Auditing page {page_num} with {model}...")
    last_err: Exception | None = None
    for attempt in range(1, 8):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(
                        data=img_path.read_bytes(), mime_type="image/png"
                    ),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                ),
            )
            return response.text.strip() + "\n"
        except errors.ServerError as e:
            last_err = e
            wait = min(60, attempt * 5)
            print(f"  server busy (attempt {attempt}); wait {wait}s")
            time.sleep(wait)
        except errors.ClientError as e:
            last_err = e
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                raise
            wait = min(60, attempt * 5)
            print(f"  client error (attempt {attempt}); wait {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"audit failed page {page_num}: {last_err}")


def parse_pages(args: argparse.Namespace) -> list[int]:
    if args.list:
        text = Path(args.list).read_text(encoding="utf-8")
        return [int(line.strip()) for line in text.splitlines() if line.strip()]
    if not args.pages:
        raise SystemExit("Provide page numbers or --list PATH")
    return args.pages


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("pages", nargs="*", type=int)
    parser.add_argument("--list", type=str)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--sleep", type=float, default=3.0)
    parser.add_argument("--model", type=str, default=MODEL)
    args = parser.parse_args()

    load_dotenv()
    client = genai.Client()
    pages = parse_pages(args)
    AUDIT_OUT.mkdir(parents=True, exist_ok=True)
    models = [args.model] + [m for m in FALLBACK_MODELS if m != args.model]

    summary_lines = []
    for p in pages:
        out = AUDIT_OUT / f"page-{p:04d}-audit.txt"
        if args.skip_existing and out.exists():
            text = out.read_text(encoding="utf-8")
            summary_lines.append(text.splitlines()[0] if text.strip() else f"PAGE {p} | (empty)")
            print(f"skip existing {out.relative_to(ROOT)}")
            continue
        result = None
        for model in models:
            try:
                result = audit_page(p, client, model)
                break
            except errors.ClientError as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"Quota hit on {model} at page {p}")
                    continue
                raise
        if result is None:
            print(f"Stopped at page {p}: quota exhausted")
            sys.exit(3)
        out.write_text(result, encoding="utf-8")
        first = result.splitlines()[0] if result.strip() else f"PAGE {p} | (empty)"
        summary_lines.append(first)
        print(first)
        print(f"Wrote {out.relative_to(ROOT)}")
        if args.sleep > 0:
            time.sleep(args.sleep)

    summary_path = AUDIT_OUT / "audit_summary.txt"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Summary: {summary_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
