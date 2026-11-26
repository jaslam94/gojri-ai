"""Fix گ read for ک under a pesh, with the PDF's own glyphs (2026-11-26).

Problem: in the print, a pesh over ک looks like the second stroke of گ. UTRNet reads گ for ک in most of these cases (random rows: 10 گُ outputs, 3 right).
Lead: in Banjara and Dil-Darya (NOORIN fonts) the PDF draws a real گ with pesh with the glyph NOORIC,Bold 60 beside the pesh glyph NOORIC,Bold 49
(within 5 pt in x and 14 pt in y: the stroke sits 2 to 11 pt above the pesh). In 8 of 8 true گُ cases glyph 60 sits at a pesh; in 0 of 8 true کُ cases. Rule (row level, because UTRNet gives no x per letter here):
  a = number of گ with a pesh in the OCR row; b = number of pesh glyphs (49) with a glyph 60 near them.
  b == 0 and the row has at least a pesh glyphs: every گُ becomes کُ. Otherwise the text stays (b >= a keeps; 0 < b < a is only counted).
Only text changes; nothing else. Input and output are run folders (<run>/<book>/dpi300/page_NNN.json).

  py -3 -X utf8 scripts/ocr_eval/pdf_marks/gaf_fix.py dump --book Banjara --pages 12 150 300     (at most 6 pages per call; pymupdf crashes after more)
  py -3 -X utf8 scripts/ocr_eval/pdf_marks/gaf_fix.py fix --run data/ocr/prose-aws-full2 --out data/ocr/prose-gaffix --trace-dir <dir>
"""
import argparse
import glob
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PESH = ("NOORIC,Bold", 49)
GAF = ("NOORIC,Bold", 60)
NEAR = 5.0  # pt
GAF_PESH = re.compile("گ([ً-ْٰؔ؎]*ُ)")


def dump(book, pages, trace_dir):
    import fitz
    doc = fitz.open(glob.glob(str(ROOT / f"pdfs/**/{book}.pdf"), recursive=True)[0])
    Path(trace_dir).mkdir(parents=True, exist_ok=True)
    for p in pages:
        g = list(dict.fromkeys((s["font"].split("+")[-1], ch[1], round(ch[2][0], 2), round(ch[2][1], 2))
                               for s in doc[p - 1].get_texttrace() for ch in s["chars"]))
        (Path(trace_dir) / f"{book}_{p}.json").write_text(json.dumps(g), encoding="utf-8")


def row_counts(glyphs, row):
    """(pesh glyphs in the row, pesh glyphs with a glyph 60 near them)."""
    y0, y1, x0, x1 = (row[k] * 72 / 300 for k in ("y0", "y1", "x0", "x1"))
    inrow = [g for g in glyphs if y0 - 4 <= g[3] <= y1 + 4 and x0 - 4 <= g[2] <= x1 + 4]
    pesh = [g for g in inrow if (g[0], g[1]) == PESH]
    gaf = [g for g in inrow if (g[0], g[1]) == GAF]
    return len(pesh), sum(any(abs(p[2] - q[2]) < NEAR and abs(p[3] - q[3]) < 14 for q in gaf) for p in pesh)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dump")
    d.add_argument("--book", required=True)
    d.add_argument("--pages", type=int, nargs="+", required=True)
    d.add_argument("--trace-dir", required=True)
    f = sub.add_parser("fix")
    f.add_argument("--run", required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--trace-dir", required=True)
    a = ap.parse_args()
    if a.cmd == "dump":
        dump(a.book, a.pages, a.trace_dir)
        return
    stats = {"rows_with_gaf_pesh": 0, "rows_changed": 0, "letters_changed": 0, "kept": 0, "ambiguous_rows": 0, "no_trace": 0, "few_pesh_glyphs": 0}
    shutil.copytree(a.run, a.out, dirs_exist_ok=True)
    for fn in glob.glob(f"{a.out}/*/dpi300/page_*.json"):
        j = json.loads(Path(fn).read_text(encoding="utf-8"))
        book = Path(fn).parts[-3]
        todo = [r for r in j["rows"] if GAF_PESH.search(r["text"])]
        if not todo:
            continue
        tf = Path(a.trace_dir) / f"{book}_{j['page']}.json"
        if not tf.exists():
            stats["no_trace"] += len(todo)
            continue
        glyphs = [tuple(x) for x in json.loads(tf.read_text(encoding="utf-8"))]
        for r in todo:
            n = len(GAF_PESH.findall(r["text"]))
            stats["rows_with_gaf_pesh"] += 1
            npesh, b = row_counts(glyphs, r)
            if npesh < n:
                stats["few_pesh_glyphs"] += 1
            elif b == 0:
                r["text_before_gaf_fix"] = r["text"]
                r["text"] = GAF_PESH.sub(lambda m: "ک" + m.group(1), r["text"])
                stats["rows_changed"] += 1
                stats["letters_changed"] += n
            elif b >= n:
                stats["kept"] += 1
            else:
                stats["ambiguous_rows"] += 1
        Path(fn).write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats))


if __name__ == "__main__":
    sys.exit(main())
