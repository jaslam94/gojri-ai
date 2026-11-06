"""Build the Hugging Face release files for the Gojri-English dictionary text.

Starts from the pass2 page files that the published dataset was made from and
replaces each line that `scripts/synth/merge_decode_letters.py` changed (letters
and the spaces around the romanisation group). A line the merge left alone keeps
its original text, so double spaces and blank lines survive. A page whose row
count does not match its non-empty line count (9 pages were never mined) is
copied unchanged.

Writes data/release/gojri-english-dictionary/:
  pages/page-NNNN.txt                        CRLF, as before
  gojri_english_dictionary_pages.csv         page_number, page_file, line_count, text
  gojri_english_dictionary_pages.jsonl       same fields, one JSON object per line

Run: py -3 -X utf8 scripts/build_dictionary_release.py
"""
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PASS2 = ROOT / "data" / "decode" / "out" / "gojri-english-dictionary"
MERGED = ROOT / "data" / "synth" / "real_pairs" / "labels_merged.jsonl"
OUT = ROOT / "data" / "release" / "gojri-english-dictionary"
PAGES = range(25, 499)


def norm(line):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", line)).strip()


def merged_rows():
    by_page = defaultdict(dict)
    for line in MERGED.open(encoding="utf-8"):
        r = json.loads(line)
        page, k = r["page_line"].split(":L")
        by_page[int(page[5:])][int(k)] = r
    return by_page


def rebuild(lines, rows):
    """Return (new_lines, changed_count, matched). lines are the pass2 lines without line ends."""
    filled = [i for i, ln in enumerate(lines) if norm(ln)]
    if len(filled) != len(rows):
        return lines, 0, False
    out, changed = list(lines), 0
    for k, i in enumerate(filled, 1):
        r = rows[k]
        if norm(lines[i]) != r["text_pass2"]:
            raise ValueError(f"row {r['page_line']} does not match its pass2 line")
        if r["text"] != r["text_pass2"]:
            out[i] = r["text"]
            changed += 1
    return out, changed, True


def main():
    (OUT / "pages").mkdir(parents=True, exist_ok=True)
    rows = merged_rows()
    records, total, pages_changed, unchanged_pages = [], 0, 0, []
    for n in PAGES:
        raw = (PASS2 / f"page-{n:04d}-pass2.txt").read_text(encoding="utf-8")
        lines = raw.replace("\r\n", "\n").rstrip("\n").split("\n")
        new, changed, matched = rebuild(lines, rows.get(n, {}))
        if not matched:
            unchanged_pages.append(n)
        total += changed
        pages_changed += changed > 0
        with (OUT / "pages" / f"page-{n:04d}.txt").open("w", encoding="utf-8", newline="") as f:
            f.write("\r\n".join(new) + "\r\n")
        records.append({"page_number": n, "page_file": f"page-{n:04d}.txt",
                        "line_count": sum(1 for x in new if x.strip()), "text": "\n".join(new)})
    with (OUT / "gojri_english_dictionary_pages.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator="\r\n")
        w.writeheader()
        w.writerows(records)
    with (OUT / "gojri_english_dictionary_pages.jsonl").open("w", encoding="utf-8", newline="") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\r\n")
    print(f"{len(records)} pages, {pages_changed} pages and {total} lines changed")
    print(f"pages copied unchanged because they were not mined: {unchanged_pages}")


if __name__ == "__main__":
    main()
