"""Score the OCR text of ocr_prose_pages.py against a speaker's review (build_prose_review.py, review_marks.json).

Truth of a row: the corrected text when the row is marked "wrong", the OCR text when marked "ok". "unsure" rows are skipped.
Same-letter rules for scoring (orthography-decisions memory): ك=ک, ه=ہ, ݨ=ݩ; Persian and Arabic-Indic digits are the same.
Punctuation spacing rule (user, 2026-11-16): a space follows ۔ and ، ; the rule is applied to OCR and truth alike.
Three errors, scored apart: letters (marks, spaces and punctuation removed), marks (the mark sequence), spaces.
Run: py -3 -X utf8 scripts/ocr_eval/score_prose_review.py data/reviews/prose-banjara-dildarya/review_marks.json [--post]
--post applies the punctuation rule to the OCR text before scoring (the truth always gets it).
"""
import argparse
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402

SAME = str.maketrans({"ك": "ک", "ه": "ہ", "ݨ": "ݩ", "٠": "۰", "١": "۱", "٢": "۲", "٣": "۳", "٤": "۴", "٥": "۵", "٦": "۶", "٧": "۷", "٨": "۸", "٩": "۹"})


def punct_rule(s):
    return re.sub(r"([۔،])(?=[^\s۔،])", r"\1 ", s)


def norm(s):
    return re.sub(r"\s+", " ", s.replace("\t", " ")).strip().translate(SAME)


def split(s):
    letters = "".join(c for c in s if unicodedata.category(c)[0] not in "MZPC" and not c.isspace())
    marks = "".join(c for c in s if unicodedata.category(c).startswith("M"))
    nomarks = "".join(c for c in s if not unicodedata.category(c).startswith("M"))
    return letters, marks, nomarks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("marks")
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--run", help="score another OCR run folder (<run>/<book>/dpi300/page_NNN.json) against the same truth; rows missing from it are skipped")
    args = ap.parse_args()
    m = json.load(open(args.marks, encoding="utf-8"))
    if args.run:
        new = {}
        for jf in Path(args.run).glob("*/dpi*/page_*.json"):
            j = json.loads(jf.read_text(encoding="utf-8"))
            for r in j["rows"]:
                new[f"{jf.parts[-3]}|{j['page']}|{r['row']}"] = r["text"]
        # the truth is what the speaker wrote (corrected text when "wrong", the old OCR text when "ok"); the run is scored against it
        m = {k: {**v, "text": v["text"] if v["m"] == "wrong" else v["ocr"], "m": "wrong", "ocr": new[k]} for k, v in m.items() if k in new and v["m"] != "unsure"}
    st = collections.defaultdict(lambda: collections.Counter())
    for k, v in m.items():
        if v["m"] == "unsure":
            continue
        book, page, _ = k.split("|")
        truth = norm(punct_rule(v["text"] if v["m"] == "wrong" else v["ocr"]))
        ocr = norm(punct_rule(v["ocr"]) if args.post else v["ocr"])
        lt, mt, nt = split(truth)
        lo, mo, no = split(ocr)
        el, em = O.ed(lo, lt), O.ed(mo, mt)
        es = max(0, O.ed(no, nt) - el)  # edits beyond the letter edits: space and punctuation edits
        for key in ((book, int(page)), ("ALL", 0), (book, 0)):
            c = st[key]
            c["rows"] += 1
            c["wrong"] += v["m"] == "wrong"
            c["let_err"] += el
            c["let_n"] += len(lt)
            c["mark_err"] += em
            c["mark_n"] += len(mt)
            c["sp_err"] += es
            c["sp_n"] += nt.count(" ")
            c["rows_let"] += el > 0
            c["rows_mark"] += em > 0
            c["rows_sp"] += es > 0
    print("rule applied to OCR:", args.post)
    for key in sorted(st, key=lambda x: (x[0] == "ALL", x)):
        c = st[key]
        name = f"{key[0]} p{key[1]}" if key[1] else f"{key[0]} (all)"
        print(f"{name:20s} rows {c['rows']:3d} wrong {c['wrong']:3d} | letters {100 * c['let_err'] / max(c['let_n'], 1):5.1f}% "
              f"({c['rows_let']} rows) | marks {100 * c['mark_err'] / max(c['mark_n'], 1):5.1f}% of {c['mark_n']} "
              f"({c['rows_mark']} rows) | spaces {c['sp_err']} edits on {c['sp_n']} spaces ({c['rows_sp']} rows)")


if __name__ == "__main__":
    main()
