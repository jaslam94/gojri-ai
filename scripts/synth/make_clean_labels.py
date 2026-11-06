"""Write the cleaned label files that training reads, minus rows that must not train.

Drops: gold leakage (dictionary page 25), the 200 lines the user reviewed
(held out as a test set), U+FFFF rows (corrupt FLI marks), folio rows (page
numbers), and rows with characters that are not Gojri ([ ] and the star
ornament). Source label files stay untouched.

Writes, under data/synth/:
  line_full/labels_clean.jsonl                synthetic rows
  real_pairs/labels_merged_clean.jsonl        real print crops, heh/kaf/letters/spacing
                                              from merge_decode_letters.py
  real_pairs/labels_review_test.jsonl         the 200 reviewed lines, never trained on;
                                              `text` is the merged label, `text_fix`
                                              is the user's fix from the review

Run: py -3 -X utf8 scripts/synth/make_clean_labels.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SYNTH = ROOT / "data" / "synth"
MARKS = ROOT / "data" / "review" / "marks_final_20261104.json"
SETS = [
    ("line_full", "labels.jsonl", "labels_clean.jsonl"),
    ("real_pairs", "labels_merged.jsonl", "labels_merged_clean.jsonl"),
]
GOLD_PAGES = {"page-0025"}  # dict_alif gold page
BAD_CHARS = set("￿[]☆")


def line_key(r):
    """page-0026-pass2:L2 and page-0026:L2 name the same printed line."""
    return r["page_line"].replace("-pass2", "")


def reason(r, review_lines):
    if line_key(r).split(":")[0] in GOLD_PAGES:
        return "gold_page_25"
    if line_key(r) in review_lines:
        return "review_holdout"
    if r.get("folio"):
        return "folio"
    if BAD_CHARS & set(r["text"]):
        return "bad_char"
    return None


def read_jsonl(path):
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    # No marks file means no holdout, and the 200 lines would leak into training.
    reviewed = {x["page_line"]: x for x in json.loads(MARKS.read_text(encoding="utf-8"))["lines"]}
    for name, src, dst in SETS:
        rows = read_jsonl(SYNTH / name / src)
        why = Counter()
        keep = []
        for r in rows:
            w = reason(r, reviewed)
            if w:
                why[w] += 1
            else:
                keep.append(r)
        write_jsonl(SYNTH / name / dst, keep)
        print(f"{name}/{dst}: {len(rows)} -> {len(keep)} kept | dropped {dict(why)}")

    merged = read_jsonl(SYNTH / "real_pairs" / "labels_merged.jsonl")
    test = [{**r, "text_fix": reviewed[r["page_line"]].get("fix") or reviewed[r["page_line"]]["label"]}
            for r in merged if r["page_line"] in reviewed]
    write_jsonl(SYNTH / "real_pairs" / "labels_review_test.jsonl", test)
    print(f"real_pairs/labels_review_test.jsonl: {len(test)} lines")


if __name__ == "__main__":
    main()
