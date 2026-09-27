"""Pass 2: refine pass-1 Nastaliq with Gemini (Gojri-aware).

Reads pass1_aksharamukha.tsv, calls Gemini in batches, writes pass2_gemini.tsv.

Usage:
    py -3 scripts/dict_translit_pass2.py --page 19
    py -3 scripts/dict_translit_pass2.py              # all entries in pass1 file
    py -3 scripts/dict_translit_pass2.py --limit 20   # first N entries only

Requires GEMINI_API_KEY or GOOGLE_API_KEY in .env (same as gemini_ocr_test.py).
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from google import genai
from google.genai import types

from dict_translit_common import TRANSLIT_DIR, read_tsv, write_tsv

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "prompts" / "devanagari_to_gojri_nastaliq_v1.txt"
PASS1 = TRANSLIT_DIR / "pass1_aksharamukha.tsv"
OUT = TRANSLIT_DIR / "pass2_gemini.tsv"

MODEL = "gemini-3.6-flash"
BATCH_SIZE = 20


def english_snippet(raw_line: str) -> str:
    """Pull a short English gloss from the dictionary line, if present."""
    if not raw_line:
        return ""
    # After pos marker or first Latin run of 4+ letters.
    m = re.search(r"(?:nm:|nf:|v:|adj\.|adv\.|conj\.|A\.)\s*(.{0,120})", raw_line)
    if m:
        return m.group(1).strip()
    m = re.search(r"\)\s*([A-Za-z][^.\n]{3,80})", raw_line)
    return m.group(1).strip() if m else ""


def build_batch_payload(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        out.append(
            {
                "id": row["entry_id"],
                "devanagari": row["devanagari"],
                "roman": row.get("roman") or "",
                "english": english_snippet(row.get("raw_line", "")),
                "pass1_nastaliq": row.get("nastaliq_pass1") or "",
            }
        )
    return out


def parse_json_array(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("expected JSON array")
    return data


def call_gemini(client: genai.Client, prompt_prefix: str, batch: list[dict], retries: int = 4) -> list[dict]:
    payload = prompt_prefix + json.dumps(batch, ensure_ascii=False, indent=2)
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=[payload],
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                    response_mime_type="application/json",
                ),
            )
            return parse_json_array(response.text or "[]")
        except Exception as exc:
            last_err = exc
            if attempt < retries:
                wait = 5 * attempt
                print(f"  retry {attempt}/{retries - 1} after error: {exc} (sleep {wait}s)")
                time.sleep(wait)
    raise last_err


def main() -> None:
    p = argparse.ArgumentParser(description="Dictionary pass 2: Gemini Gojri Nastaliq refinement")
    p.add_argument("--page", type=int, action="append", dest="pages", help="limit to page number(s)")
    p.add_argument("--limit", type=int, default=0, help="max entries to process (0 = all)")
    p.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = p.parse_args()

    if not PASS1.exists():
        print(f"Missing {PASS1}. Run dict_translit_pass1.py first.")
        sys.exit(1)

    rows = read_tsv(PASS1)
    if args.pages:
        wanted = set(args.pages)
        rows = [r for r in rows if int(r["page"]) in wanted]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("No entries to process.")
        sys.exit(1)

    load_dotenv()
    client = genai.Client()
    prompt_prefix = PROMPT_PATH.read_text(encoding="utf-8")

    by_id = {r["entry_id"]: r for r in rows}
    pending = list(rows)
    done = 0

    while pending:
        batch_rows = pending[: args.batch_size]
        pending = pending[args.batch_size :]
        payload = build_batch_payload(batch_rows)
        try:
            results = call_gemini(client, prompt_prefix, payload)
        except Exception as exc:
            print(f"Batch failed ({batch_rows[0]['entry_id']}..): {exc}")
            sys.exit(1)
        result_map = {item["id"]: item.get("nastaliq", "") for item in results if "id" in item}
        for row in batch_rows:
            nastaliq = result_map.get(row["entry_id"], "")
            by_id[row["entry_id"]]["nastaliq_pass2"] = nastaliq
            done += 1
        print(f"  batch done ({done}/{len(rows)})")

    final = list(by_id.values())
    write_tsv(OUT, final)
    print(f"Wrote {len(final)} rows to {OUT.relative_to(ROOT)}")
    print("Sample (pass1 vs pass2):")
    for row in final[:5]:
        if row.get("nastaliq_pass2"):
            print(f"  {row['devanagari']}: {row['nastaliq_pass1']} -> {row['nastaliq_pass2']}")


if __name__ == "__main__":
    main()
