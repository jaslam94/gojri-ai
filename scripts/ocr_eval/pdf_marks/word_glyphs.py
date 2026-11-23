"""Put the shadda of the whole-word PDF glyphs into an OCR run (Kahawat-Kosh).

Shadda is drawn only inside two whole-word glyphs (found 2026-11-15, see LOG.md):
  NOORIN41,Bold gid 89 = اللّٰہ (shadda and small alef), 72 uses
  NOORIN61,Bold gid 10 = بللّی (shadda on the second lam), 2 uses
Speaker ruling 2026-11-23: write اللہ as printed, with the shadda and the small alef.

Method (no model, no letter change except the mark): the page trace (data/ocr/pdfmarks-work/trace, from dump_trace.py) lists the
glyph positions. Each glyph goes to the nearest printed row of an entry (idiom = right of the column line, meaning = left).
Per field: if the number of glyphs equals the number of matching words in the OCR text, every match gets the marks. If the numbers
differ (the OCR misread the word), the field is left as it is and listed in word_glyph_flags.json for the speaker.

Run: py -3 -X utf8 scripts/ocr_eval/pdf_marks/word_glyphs.py data/ocr/kahawat-final data/ocr/kahawat-final2
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TRACE = ROOT / "data/ocr/pdfmarks-work/trace"
PT2PX = 200 / 72
ALLAH = "اللّٰہ"                      # ا ل ل U+0651 U+0670 ہ
ALLAH_RE = re.compile("ا" + "ل" * 2 + "[ّٰ]*" + "[ہھه]")
BILLI_RE = re.compile("بللی")
GLYPHS = {("NOORIN41,Bold", 89): (ALLAH_RE, ALLAH), ("NOORIN61,Bold", 10): (BILLI_RE, "بللّی")}


def main(src, dst):
    src, dst = Path(src), Path(dst)
    dst.mkdir(parents=True, exist_ok=True)
    stat, flags = collections.Counter(), []
    for f in sorted(src.glob("page_*.json")):
        info = json.loads(f.read_text(encoding="utf-8"))
        n = int(f.stem.split("_")[1])
        if info.get("kind") == "entries":
            tr = json.loads((TRACE / f"p{n - 1}.json").read_text(encoding="utf-8"))
            xb = info["line"][1]
            seen, per = set(), collections.Counter()   # per[(entry, field, glyph key)] = number of glyphs
            for fn, gid, uc, ox, oy, bb, size in tr:
                if (fn, gid) not in GLYPHS or (fn, gid, ox, oy) in seen:
                    continue
                seen.add((fn, gid, ox, oy))
                x, y = ox * PT2PX, oy * PT2PX
                best = None
                for ei, e in enumerate(info["entries"]):
                    for field, rk in (("idiom", "yr"), ("meaning", "yl")):
                        if (field == "idiom") != (x >= xb):
                            continue
                        for ya, yb in e.get(rk) or []:
                            d = 0 if ya <= y <= yb else min(abs(y - ya), abs(y - yb))
                            if best is None or d < best[0]:
                                best = (d, ei, field)
                if best and best[0] <= 14:
                    per[(best[1], best[2], (fn, gid))] += 1
                else:
                    stat["glyph not placed"] += 1
            for (ei, field, key), k in sorted(per.items()):
                e = info["entries"][ei]
                rx, new = GLYPHS[key]
                m = len(rx.findall(e[field]))
                if m == k:
                    e[field + "_pre_word_glyph"] = e[field]
                    e[field] = rx.sub(new, e[field])
                    stat["fields fixed"] += 1
                    stat["words fixed"] += k
                else:
                    stat["fields flagged"] += 1
                    flags.append({"page": n, "entry": ei, "field": field, "glyph": key[0] + ":" + str(key[1]), "glyphs": k, "text matches": m, "text": e[field]})
        (dst / f.name).write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
    (dst / "word_glyph_flags.json").write_text(json.dumps(flags, ensure_ascii=False, indent=1), encoding="utf-8")
    print(dict(stat))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
