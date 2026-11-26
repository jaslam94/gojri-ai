"""Put the speaker's text for the 5 flagged اللہ fields (build_allah_review.py, data/reviews/kahawat-allah/) into a Kahawat run folder.

Key `page|entry|field`, entry counted from 0 (as in word_glyph_flags.json). The old text stays in `<field>_before_allah_fix`. Only fields marked wrong are changed;
the OCR text must still be the one the speaker saw (`ocr`), else the script stops.
Run: py -3 -X utf8 scripts/ocr_eval/apply_allah_fixes.py [--run data/ocr/kahawat-final3]
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(ROOT / "data/ocr/kahawat-final3"))
    ap.add_argument("--marks", default=str(ROOT / "data/reviews/kahawat-allah/review_marks_20261126.json"))
    a = ap.parse_args()
    marks = json.loads(Path(a.marks).read_text(encoding="utf-8"))
    n = 0
    for key, v in marks.items():
        page, entry, field = key.split("|")
        fn = Path(a.run) / f"page_{int(page):03d}.json"
        j = json.loads(fn.read_text(encoding="utf-8"))
        e = j["entries"][int(entry)]
        if v["m"] != "wrong":
            continue
        assert e[field] == v["ocr"] or e.get(field + "_before_allah_fix") == v["ocr"], (key, e[field])
        if e[field] == v["text"]:
            continue
        e[field + "_before_allah_fix"] = v["ocr"]
        e[field] = v["text"]
        fn.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        n += 1
    print(n, "fields changed in", a.run)


if __name__ == "__main__":
    main()
