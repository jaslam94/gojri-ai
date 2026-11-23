"""Make the Kahawat-Kosh text release: OCR with PDF marks, plus the word-spaced idiom from the character n-gram inserter.

Input:  an OCR run folder with page_NNN.json (default data/ocr/kahawat-final, made by pdf_marks/marks_insert.py --host-fix ڈد).
Output: <out>/entries.tsv and <out>/entries.jsonl, columns
  pdf_page, entry, idiom, idiom_as_read, meaning, idiom_conf, meaning_conf
  idiom          the idiom with a space after ۔ and ، (text rule, ruling 2026-11-16) and with word spaces added by spacing_lm.py
  idiom_as_read  the idiom as the OCR read it (after the punctuation rule only)
  meaning        the meaning as read (punctuation rule only; the space model was tuned on idioms, not on the Urdu meanings)
Letters never change between idiom and idiom_as_read: the script checks this.
Run: py -3 -X utf8 scripts/ocr_eval/kahawat_release.py [--run data/ocr/kahawat-final] [--out data/release/kahawat-kosh]
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_prose_spacing as P  # noqa: E402
import score_spacing as SS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(ROOT / "data/ocr/kahawat-final"))
    ap.add_argument("--out", default=str(ROOT / "data/release/kahawat-kosh"))
    a = ap.parse_args()
    model = P.build_model()
    rows = []
    for f in sorted(Path(a.run).glob("page_*.json")):
        j = json.loads(f.read_text(encoding="utf-8"))
        for k, e in enumerate(j.get("entries", []), 1):
            read = P.punct(e.get("idiom", ""))
            spaced = P.add_spaces(read, model) if SS.parse(read)[0] and not re.search(r"[0-9A-Za-z]", read) else read
            assert SS.parse(read)[0] == SS.parse(spaced)[0], (j["page"], k)
            rows.append({"pdf_page": j["page"], "entry": k, "idiom": spaced, "idiom_as_read": read, "meaning": P.punct(e.get("meaning", "")),
                         "idiom_conf": round(float(e.get("idiom_conf", 0)), 3), "meaning_conf": round(float(e.get("meaning_conf", 0)), 3)})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0])
    with open(out / "entries.tsv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(cols)
        w.writerows([[r[c] for c in cols] for r in rows])
    with open(out / "entries.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    changed = sum(r["idiom"] != r["idiom_as_read"] for r in rows)
    print(len(rows), "entries on", len({r["pdf_page"] for r in rows}), "pages;", changed, "idioms got added spaces ->", out)


if __name__ == "__main__":
    main()
