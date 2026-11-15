"""Score a Kahawat-Kosh OCR run against the cards a Gojri speaker marked in the review page.

Truth: a card marked OK keeps the OCR text it showed, a card marked Wrong takes the speaker's fixed text, Unsure is
skipped. Each card is matched to an entry of the run in --ocr-dir by PDF page and best idiom match (the entry's y can
move between runs, for example when a section-letter box is removed).
If the speaker's text runs past the end of the OCR text (an older crop also showed the next entry's row, and the speaker
typed it in), the extra tail is cut from the truth before scoring and counted as "tail cut".

Metrics (on Arabic-script letters; see kraken_compare.py): letter error, mark (zer) error, word-break errors, and one
class per field: exact, space only, marks only, letters, no entry found.
Run: py -3 -X utf8 scripts/ocr_eval/score_marks.py --marks <review_marks.json> --sample <review/sample.json>
        --ocr-dir data/ocr/kahawat-gpu4 [--show 20]
"""
import argparse
import difflib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402
from kraken_compare import base, marks_of, space_errors  # noqa: E402


def trim_tail(truth, ocr, min_cut=6):
    """Cut the part of the truth that lies after the last letter the OCR text shares with it. Returns (text, letters cut)."""
    lt, lo = base(truth), base(ocr)
    sm = difflib.SequenceMatcher(None, lt, lo, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size]
    if not blocks:
        return truth, 0
    end = blocks[-1].a + blocks[-1].size
    cut = len(lt) - end
    if cut < min_cut:
        return truth, 0
    n = 0
    for k, ch in enumerate(truth):
        if ch in " ":
            continue
        if base(ch):
            n += 1
        if n == end:
            j = k + 1
            while j < len(truth) and (base(truth[j]) == "" and truth[j] != " "):
                j += 1  # keep marks that follow the last letter
            return truth[:j], cut
    return truth, 0


def best_entry(entries, truth_idiom, truth_meaning):
    best, score = None, 9.0
    ti, tm = base(truth_idiom), base(truth_meaning)
    for e in entries:
        oi, om = base(e["idiom"]), base(e["meaning"])
        a = O.ed(ti[: len(oi) + 4], oi) / max(len(oi), 1)
        b = O.ed(tm[: len(om) + 4], om) / max(len(om), 1)
        s = a + b
        if s < score:
            best, score = e, s
    return (best, score) if best is not None and score < 1.2 else (None, score)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marks", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--ocr-dir", required=True)
    ap.add_argument("--show", type=int, default=0, help="print this many fields with letter errors")
    args = ap.parse_args()
    sample = json.loads(Path(args.sample).read_text(encoding="utf-8"))
    marks = json.loads(Path(args.marks).read_text(encoding="utf-8"))
    pages = {}
    rows = []
    for i, m in sorted(marks.items(), key=lambda x: int(x[0])):
        if m["m"] == "unsure":
            continue
        s = sample[int(i)]
        truth = (m["idiom"], m["meaning"]) if m["m"] == "wrong" else (s["idiom"], s["meaning"])
        p = s["page"]
        if p not in pages:
            f = Path(args.ocr_dir) / f"page_{p:03d}.json"
            info = json.loads(f.read_text(encoding="utf-8"))
            pages[p] = info.get("entries", []) if info["kind"] == "entries" else []
        e, _ = best_entry(pages[p], *truth)
        for fi, field in enumerate(("idiom", "meaning")):
            r = {"card": int(i) + 1, "page": p, "field": field, "mark": m["m"], "truth": truth[fi], "ocr": e[field] if e else None}
            if e:
                t, cut = trim_tail(truth[fi], e[field])
                bt, bo = base(t), base(e[field])
                r.update(tail_cut=cut, n_letters=len(bt), letter_ed=O.ed(bt, bo), n_marks=len(marks_of(t)),
                         mark_ed=O.ed(marks_of(t), marks_of(e[field])), trimmed=t)
                if m["m"] == "wrong":
                    r["sp"] = space_errors(t, e[field])
                if r["letter_ed"]:
                    r["cls"] = "letters"
                elif r["mark_ed"]:
                    r["cls"] = "marks only"
                elif m["m"] == "wrong" and (r["sp"][0] + r["sp"][1]):
                    r["cls"] = "space only"
                else:
                    r["cls"] = "exact"
            else:
                r["cls"] = "no entry found"
            rows.append(r)
    ok = [r for r in rows if r["ocr"] is not None]
    nl = sum(r["n_letters"] for r in ok)
    le = sum(r["letter_ed"] for r in ok)
    nm = sum(r["n_marks"] for r in ok)
    me = sum(r["mark_ed"] for r in ok)
    sp = [r["sp"] for r in ok if "sp" in r]
    cls = {}
    for r in rows:
        cls[r["cls"]] = cls.get(r["cls"], 0) + 1
    print(f"{args.ocr_dir}: {len(rows)} fields, classes {cls}, tail cut in {sum(1 for r in ok if r['tail_cut'])} fields")
    print(f"letters {nl}, letter error {100 * le / max(nl, 1):.1f}% | marks in truth {nm}, mark error {me} ({100 * me / max(nm, 1):.0f}%) | "
          f"word breaks {sum(x[2] for x in sp)}, missing {sum(x[0] for x in sp)}, extra {sum(x[1] for x in sp)} (Wrong cards)")
    for r in [r for r in rows if r["cls"] in ("letters", "no entry found")][: args.show]:
        print(r["card"], r["field"], r["cls"], r.get("letter_ed"))
        print("   T:", r.get("trimmed", r["truth"]))
        print("   O:", r["ocr"])
    (Path(args.ocr_dir) / "score_marks.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
