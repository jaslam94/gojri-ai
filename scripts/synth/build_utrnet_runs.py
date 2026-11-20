"""Cut the Arabic-script runs out of the real dictionary line crops, with one label per run (UTRNet fine-tune data).

UTRNet only reads the Arabic-script runs of a page (English is cut away first), so it must be trained on runs, not on
whole lines. A run is a group of neighbouring Batool-font glyphs in the PDF (same rule as scripts/utrnet_arabic_eval.py).
The label of a run is the matching Arabic-script part of the line label: the line text is cut at every English
letter, digit or bracket, and the Arabic parts are paired with the PDF runs from left to right (the line label is in
visual left-to-right order: headword first, a synonym or example sentence after the English).
A line is used only when the number of Arabic parts equals the number of PDF runs. Leading and trailing punctuation
of a part is cut off (the print may or may not hold it in the Batool font).

Sources:  labels_merged_clean.jsonl (11,126 lines; the 200 reviewed lines are not in it)  -> train / val
          labels_review_test.jsonl  (the 200 lines the speaker checked, text_fix)        -> test (never trained on)
Split:    validation = about 3% of the pages and test = --test-pages whole pages that hold no reviewed line (whole pages, so no
          leak between neighbouring lines); the rest trains. test_seen.tsv holds the 200 reviewed lines (their pages
          also hold training lines: a weaker test, kept to compare with earlier numbers). The script fails if a val or
          test page appears in train.
Output:   <out>/img/*.png, <out>/{train,val,test}.tsv with columns: file, label, left_margin_px, right_margin_px, page_line.
          Each crop keeps up to MARGIN px of the line on each side; the margins are stored so training can trim them at random.

Run: py -3 -X utf8 scripts/synth/build_utrnet_runs.py --out data/utrnet-ft
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(1, str(ROOT / "scripts" / "synth"))

import fitz  # noqa: E402
from PIL import Image  # noqa: E402

import dump_batool_lines as D  # noqa: E402
import merge_decode_letters as M  # noqa: E402
import mine_batool_pairs as MB  # noqa: E402

MARGIN = 3
ARABIC_LETTER = re.compile(r"[ؠ-يٮ-ۓەۮ-ۿ]")
EDGE = re.compile(r"^[^ؠ-ۿ]+|[^ؠ-ۿ]+$")


def arabic_parts(text):
    """Arabic-script parts of a line label, in text order. English letters, digits and brackets end a part."""
    out = []
    for m in re.finditer(r"[؀-ۿ][؀-ۿ ]*", text):
        p = EDGE.sub("", m.group(0)).strip()
        p = re.sub(r" +", " ", p)
        if ARABIC_LETTER.search(p):
            out.append(p)
    return out


def arabic_runs(bb):
    runs, cur = [], []
    for x0, x1, font, _c, o in sorted(bb["chars"], key=lambda t: t[0]):
        if "Batool" in font or 0xE000 <= o <= 0xF8FF:
            cur.append((x0, x1))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [(min(a for a, _ in r), max(b for _, b in r)) for r in runs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--val-share", type=float, default=0.03)
    ap.add_argument("--test-pages", type=int, default=25)
    ap.add_argument("--seed", type=int, default=20261110)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "img").mkdir(parents=True, exist_ok=True)
    base = ROOT / "data" / "synth" / "real_pairs"
    doc = fitz.open(M.PDF)
    pua = D.load_map()
    clean = [json.loads(line) for line in (base / "labels_merged_clean.jsonl").open(encoding="utf-8")]
    review = [json.loads(line) for line in (ROOT / "data" / "reviews" / "dictionary-200-lines" / "labels_review_test.jsonl").open(encoding="utf-8")]

    boxes = {}

    def line_boxes(page):
        if page not in boxes:
            labels = M.pass2_labels(page)
            rows = MB.cluster_rows_full(MB.page_chars_full(doc[page - 1]))
            texts = [re.sub(r"\s+", " ", D.fmt_line(bb["chars"], pua, wrap_batool=False)).strip() for _y, bb in rows]
            keep = str(page) in labels
            boxes[page] = [bb for (_y, bb), t in zip(rows, texts) if t and (keep or t != str(page))]
        return boxes[page]

    random.seed(args.seed)
    pages = sorted({int(r["page_line"][5:9]) for r in clean})
    val_pages = set(random.sample(pages, max(1, round(len(pages) * args.val_share))))
    review_pages = {int(r["page_line"][5:9]) for r in review}
    test_pool = sorted(set(pages) - val_pages - review_pages)
    test_pages = set(random.sample(test_pool, min(args.test_pages, len(test_pool))))
    stats = {"lines": 0, "folio": 0, "no_arabic": 0, "count_mismatch": 0, "box_missing": 0, "runs": 0}
    rows_out = {"train": [], "val": [], "test": [], "test_seen": []}

    def handle(r, text, split):
        stats["lines"] += 1
        if r.get("folio"):
            stats["folio"] += 1
            return
        page, line = int(r["page_line"][5:9]), int(r["page_line"].split(":L")[1])
        try:
            bb = line_boxes(page)[line - 1]
        except IndexError:
            stats["box_missing"] += 1
            return
        parts = arabic_parts(text)
        runs = arabic_runs(bb)
        if not parts or not runs:
            stats["no_arabic"] += 1
            return
        if len(parts) != len(runs):
            stats["count_mismatch"] += 1
            return
        img = Image.open(base / r["image"]).convert("L")
        rx0 = max(0, int((bb["x0"] - MB.PAD_PT) * MB.ZOOM))
        # the line label is in left-to-right order (headword at the left), the same order as the runs sorted by x
        for k, ((x0, x1), label) in enumerate(zip(sorted(runs), parts)):
            a0, b0 = int(x0 * MB.ZOOM - rx0), int(x1 * MB.ZOOM - rx0)
            a, b = max(0, a0 - MARGIN), min(img.width, b0 + MARGIN)
            if b0 - a0 < 12:
                continue
            name = f"{r['page_line'].replace(':', '_')}_{k + 1}.png"
            img.crop((a, 0, b, img.height)).save(out / "img" / name)
            rows_out[split].append((name, label, a0 - a, b - b0, r["page_line"]))
            stats["runs"] += 1

    for r in clean:
        pg = int(r["page_line"][5:9])
        handle(r, r["text"], "val" if pg in val_pages else "test" if pg in test_pages else "train")
    for r in review:
        handle(r, r.get("text_fix") or r["text"], "test_seen")
    for split, rs in rows_out.items():
        (out / f"{split}.tsv").write_text(
            "".join(f"{n}\t{lab}\t{lm}\t{rm}\t{pl}\n" for n, lab, lm, rm, pl in rs), encoding="utf-8")
    page_of = lambda rows: {int(x[4][5:9]) for x in rows}  # noqa: E731
    leak = {"val": page_of(rows_out["val"]) & page_of(rows_out["train"]), "test": page_of(rows_out["test"]) & page_of(rows_out["train"]),
            "test_vs_val": page_of(rows_out["test"]) & page_of(rows_out["val"])}
    print(stats)
    print({k: len(v) for k, v in rows_out.items()}, "val pages:", len(val_pages), "test pages:", len(test_pages))
    print("page overlap (must all be 0):", {k: len(v) for k, v in leak.items()})
    print("test_seen pages also in train:", len(page_of(rows_out["test_seen"]) & page_of(rows_out["train"])), "of", len(page_of(rows_out["test_seen"])))
    if any(leak.values()):
        raise SystemExit("page leak between splits")


if __name__ == "__main__":
    main()
