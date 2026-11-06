"""Build the local dictionary review tool in data/review/.

Two checks for a native Gojri speaker:
  1. Table check: one card per Batool PUA code (160). Glyph crop from the PDF,
     the table's Unicode output, and example words in context.
  2. Line sample: 200 lines drawn evenly across the book from
     data/synth/real_pairs/labels_clean.jsonl, each as a crop beside its label.

Read-only against data/synth/real_pairs/, data/decode/ and the PDF. Everything
new goes to data/review/ (gitignored).

  py -3 -X utf8 scripts/review/build_review.py
  py -3 -X utf8 scripts/review/build_review.py --seed 20261103 --lines 200
"""

from __future__ import annotations

import argparse
import io
import json
import random
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from dump_batool_lines import (  # noqa: E402
    WORD_GAP,
    cluster_rows,
    decode_batool_run,
    is_combining_mark,
    load_map,
    map_code,
    page_chars,
)

PDF = ROOT / "pdfs" / "anjumshanasi" / "Gojri-English-Dictionary.pdf"
PAIRS = ROOT / "data" / "synth" / "real_pairs"
DECODE_OUT = ROOT / "data" / "decode" / "out" / "gojri-english-dictionary"
OUT = ROOT / "data" / "review"
TEMPLATE = Path(__file__).resolve().parent / "review_template.html"

FIRST_PAGE, LAST_PAGE = 25, 498
GLYPH_ZOOM = 16.0  # 1152 DPI, glyph crops
WORD_ZOOM = 8.0  # 576 DPI, word-in-context crops
EXAMPLES_PER_CODE = 8
MAX_CTX_WIDTH_PT = 150.0

# Rules that live in dump_batool_lines.map_code. Shown on the card so the
# reviewer knows the output depends on neighbours.
RULE_NOTES = {
    "F0F1": "Context rule: when F031 follows, this pair gives ائے (or ئے if an alef is just before it).",
    "F031": "Context rule: right after F0F1 this code gives nothing. The pair gives ائے.",
    "F060": "Context rule: ہ normally. Between ن and ی it gives ھ. Between م and ا it gives ه.",
    "F061": "Context rule: ه normally. Before د it gives ھ.",
}


# ---------------------------------------------------------------- decode

def decode_run_traced(run: list, pua_map: dict[str, str]):
    """Same output as dump_batool_lines.decode_batool_run, plus which code
    made which characters. run items: (x0, x1, ord, tbbox).

    Returns words: dict(text, parts=[(src_idx, start, end)], srcs=[idx]) where
    src_idx indexes the returned `ordered` list (run sorted right to left).
    """
    ordered = sorted(run, key=lambda t: -t[0])
    items: list[list] = []  # [x0, x1, text, parts]
    for i, (x0, x1, _o, _bb) in enumerate(ordered):
        text = map_code(ordered, pua_map, i)
        if text is None:
            if items:
                items[-1][3].append((i, ""))
            continue
        items.append([x0, x1, text, [(i, text)]])

    n = len(items)
    host_of: dict[int, int] = {}
    for i, (x0, x1, text, _p) in enumerate(items):
        if not is_combining_mark(text):
            continue
        mx = (x0 + x1) / 2
        best, best_d = None, None
        for j, (lx0, lx1, lt, _lp) in enumerate(items):
            if is_combining_mark(lt):
                continue
            if min(lx0, lx1) <= mx <= max(lx0, lx1):
                d = 0.0
            else:
                d = min(abs(mx - lx0), abs(mx - lx1))
            if best_d is None or d < best_d:
                best_d, best = d, j
        if best is not None:
            host_of[i] = best

    merged = []
    for i, (x0, x1, text, parts) in enumerate(items):
        if is_combining_mark(text):
            if i not in host_of:
                merged.append((x0, x1, text, list(parts)))
            continue
        all_parts = list(parts)
        full = text
        for k in range(n):
            if host_of.get(k) == i:
                full += items[k][2]
                all_parts.extend(items[k][3])
        merged.append((x0, x1, full, all_parts))

    words: list[dict] = []
    cur: dict | None = None
    prev_x0 = None
    for x0, x1, text, parts in merged:
        if prev_x0 is not None and (prev_x0 - x1) > WORD_GAP:
            cur = None
        if cur is None:
            cur = {"text": "", "parts": [], "srcs": []}
            words.append(cur)
        pos = len(cur["text"])
        # host text comes first in `full`; spans follow part order.
        offset = pos
        for src, ptxt in parts:
            cur["parts"].append((src, offset, offset + len(ptxt)))
            cur["srcs"].append(src)
            offset += len(ptxt)
        cur["text"] += text
        prev_x0 = x0
    return ordered, words


def is_batool_char(font: str, o: int) -> bool:
    return "Batool" in font or (0xE000 <= o <= 0xF8FF)


def raw_boxes(page: fitz.Page) -> dict:
    """(code, x0 rounded) -> list of (y0, bbox) for Batool glyphs, from rawdict.

    The same call the production decoder uses. get_texttrace gives the same
    boxes (see texttrace_check) but this PyMuPDF build crashes after about 55
    get_texttrace calls in one process, so it cannot scan 474 pages.
    """
    out: dict = defaultdict(list)
    for block in page.get_text("rawdict", flags=0)["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if "Batool" not in span.get("font", ""):
                    continue
                for ch in span["chars"]:
                    bb = tuple(ch["bbox"])
                    out[(ord(ch["c"]), round(bb[0], 1))].append((bb[1], bb))
    return out


def texttrace_check(doc: fitz.Document, pages: list[int]) -> dict:
    """Compare rawdict boxes with get_texttrace boxes on a few pages.
    Keep the page list under ~50: more calls crash this PyMuPDF build."""
    worst, missing, total = 0.0, 0, 0
    for pn in pages:
        page = doc[pn - 1]
        raw = raw_boxes(page)
        for span in page.get_texttrace():
            if "Batool" not in span["font"]:
                continue
            for code, _gid, _origin, bbox in span["chars"]:
                total += 1
                cands = raw.get((code, round(bbox[0], 1)))
                if not cands:
                    missing += 1
                    continue
                best = min(
                    max(abs(a - b) for a, b in zip(bb, bbox)) for _y, bb in cands
                )
                worst = max(worst, best)
    return {"pages": len(pages), "glyphs": total, "unmatched": missing,
            "max_box_diff_pt": round(worst, 3)}


def scan_book(doc: fitz.Document, pua_map: dict[str, str]):
    """Decode every body page with tracing. Returns per-code stats + instances."""
    stats: dict[str, dict] = defaultdict(lambda: {"count": 0, "pages": set()})
    instances: dict[str, list] = defaultdict(list)
    mismatches = 0
    fallback_boxes = 0
    total_runs = 0
    for page_no in range(FIRST_PAGE, LAST_PAGE + 1):
        page = doc[page_no - 1]
        boxes = raw_boxes(page)
        per_code_page = defaultdict(int)
        for row_y, chars in cluster_rows(page_chars(page)):
            chars = sorted(chars, key=lambda t: t[0])
            i = 0
            while i < len(chars):
                x0, x1, font, _c, o = chars[i]
                if not is_batool_char(font, o):
                    i += 1
                    continue
                run = []
                while i < len(chars) and is_batool_char(chars[i][2], chars[i][4]):
                    cx0, cx1, _f, _c2, co = chars[i]
                    cands = boxes.get((co, round(cx0, 1)), [])
                    if cands:
                        _y0, bb = min(cands, key=lambda c: abs(c[0] - row_y))
                    else:
                        fallback_boxes += 1
                        bb = (cx0, row_y, cx1, row_y + 12.0)
                    run.append((cx0, cx1, co, bb))
                    i += 1
                total_runs += 1
                ordered, words = decode_run_traced(run, pua_map)
                prod = decode_batool_run([(a, b, c) for a, b, c, _bb in run], pua_map)
                if " ".join(w["text"] for w in words) != prod:
                    mismatches += 1
                for wi, w in enumerate(words):
                    for src, start, end in w["parts"]:
                        code = f"{ordered[src][2]:04X}"
                        stats[code]["count"] += 1
                        stats[code]["pages"].add(page_no)
                        if per_code_page[code] >= 3:
                            continue  # keep at most 3 per code per page
                        per_code_page[code] += 1
                        left = words[wi - 1] if wi > 0 else None
                        right = words[wi + 1] if wi + 1 < len(words) else None
                        # decode order is reading order (right to left)
                        triple = [x for x in (left, w, right) if x]
                        ctx_text = " ".join(x["text"] for x in triple)
                        shift = len(left["text"]) + 1 if left else 0
                        boxes_ctx = [ordered[s][3] for x in triple for s in x["srcs"]]
                        cx = (
                            min(b[0] for b in boxes_ctx),
                            min(b[1] for b in boxes_ctx),
                            max(b[2] for b in boxes_ctx),
                            max(b[3] for b in boxes_ctx),
                        )
                        instances[code].append(
                            {
                                "page": page_no,
                                "glyph": ordered[src][3],
                                "out": w["text"][start:end],
                                "word": w["text"],
                                "wlen": len(w["text"]),
                                "ctx": ctx_text,
                                "hl": (shift + start, shift + end),
                                "ctx_box": cx,
                            }
                        )
    return stats, instances, {
        "runs": total_runs,
        "decode_mismatches": mismatches,
        "box_fallbacks": fallback_boxes,
    }


# ---------------------------------------------------------------- crops

def render_clip(page: fitz.Page, rect: fitz.Rect, zoom: float):
    rect = rect & page.rect
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return img, pix.x, pix.y


def save_glyph_crop(doc, inst, path: Path) -> None:
    """Wide side padding: Nastaliq ink often sticks out of the advance box.
    The red box shows where this code's own box sits."""
    gx0, gy0, gx1, gy1 = inst["glyph"]
    rect = fitz.Rect(gx0 - 6.0, gy0 - 2.0, gx1 + 6.0, gy1 + 2.0)
    img, ox, oy = render_clip(doc[inst["page"] - 1], rect, GLYPH_ZOOM)
    ImageDraw.Draw(img).rectangle(
        [gx0 * GLYPH_ZOOM - ox, gy0 * GLYPH_ZOOM - oy, gx1 * GLYPH_ZOOM - ox, gy1 * GLYPH_ZOOM - oy],
        outline=(220, 30, 30),
        width=2,
    )
    img.save(path, optimize=True)


def save_word_crop(doc, inst, path: Path) -> None:
    x0, y0, x1, y1 = inst["ctx_box"]
    rect = fitz.Rect(x0 - 3.0, y0 - 2.0, x1 + 3.0, y1 + 2.0)
    page = doc[inst["page"] - 1]
    img, ox, oy = render_clip(page, rect, WORD_ZOOM)
    gx0, gy0, gx1, gy1 = inst["glyph"]
    draw = ImageDraw.Draw(img)
    draw.rectangle(
        [gx0 * WORD_ZOOM - ox, gy0 * WORD_ZOOM - oy, gx1 * WORD_ZOOM - ox, gy1 * WORD_ZOOM - oy],
        outline=(220, 30, 30),
        width=2,
    )
    img.save(path, optimize=True)


def pick_examples(insts: list, rng: random.Random, k: int) -> list:
    good = [
        i
        for i in insts
        if 2 <= i["wlen"] <= 10 and (i["ctx_box"][2] - i["ctx_box"][0]) <= MAX_CTX_WIDTH_PT
    ] or insts
    if not good:
        return []
    chosen: list = []
    by_out: dict[str, list] = defaultdict(list)
    for i in good:
        by_out[i["out"]].append(i)
    for o in sorted(by_out, key=lambda o: -len(by_out[o]))[:4]:
        chosen.append(rng.choice(by_out[o]))
    pool = sorted(good, key=lambda i: i["page"])
    for b in range(k):
        if len(chosen) >= k:
            break
        lo, hi = b * len(pool) // k, (b + 1) * len(pool) // k
        used = {c["page"] for c in chosen}
        window = pool[lo:hi]
        cands = [i for i in window if i["page"] not in used] or window
        if cands:
            pick = rng.choice(cands)
            if pick not in chosen:
                chosen.append(pick)
    # fill up if buckets collided
    for i in rng.sample(pool, min(len(pool), 3 * k)):
        if len(chosen) >= k:
            break
        if i not in chosen:
            chosen.append(i)
    return chosen[:k]


def build_table_cards(doc, pua_map, seed: int) -> tuple[list, dict]:
    print("scanning book for code instances ...", flush=True)
    stats, instances, health = scan_book(doc, pua_map)
    spread = [FIRST_PAGE + k * (LAST_PAGE - FIRST_PAGE) // 39 for k in range(40)]
    health["texttrace_check"] = texttrace_check(doc, spread)
    print("scan health:", health, flush=True)
    tdir = OUT / "table"
    tdir.mkdir(parents=True, exist_ok=True)
    cards = []
    total_uses = sum(s["count"] for s in stats.values())
    for code in sorted(pua_map, key=lambda c: -stats[c]["count"] if c in stats else 1):
        rng = random.Random(f"{seed}:{code}")
        st = stats.get(code, {"count": 0, "pages": set()})
        exs = pick_examples(instances.get(code, []), rng, EXAMPLES_PER_CODE)
        glyph_img = None
        if exs:
            glyph_img = f"table/{code}_glyph.png"
            save_glyph_crop(doc, exs[0], OUT / glyph_img)
        ex_out = []
        for n, inst in enumerate(exs):
            rel = f"table/{code}_ex{n + 1}.png"
            save_word_crop(doc, inst, OUT / rel)
            ex_out.append(
                {
                    "img": rel,
                    "page": inst["page"],
                    "ctx": inst["ctx"],
                    "hl": list(inst["hl"]),
                    "out": inst["out"],
                }
            )
        cards.append(
            {
                "code": code,
                "out": pua_map[code],
                "out_hex": " ".join(f"U+{ord(ch):04X}" for ch in pua_map[code]),
                "uses": st["count"],
                "pages": len(st["pages"]),
                "share": round(100.0 * st["count"] / total_uses, 3) if total_uses else 0,
                "rule": RULE_NOTES.get(code, ""),
                "glyph": glyph_img,
                "examples": ex_out,
            }
        )
    health["total_glyph_uses"] = total_uses
    health["codes_without_examples"] = [c["code"] for c in cards if not c["examples"]]
    return cards, health


# ---------------------------------------------------------------- lines

def nonblank(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def stratified_sample(rows: list[dict], n: int, seed: int) -> list[dict]:
    """Cut the book (in page order) into n strata of equal line count and draw
    one random line from each. Spreads the sample evenly over all pages and
    gives every line almost the same chance."""

    def key(r):
        page, line = r["page_line"].split(":")
        return int(page.split("-")[1]), int(line[1:])

    rows = sorted(rows, key=key)
    rng = random.Random(seed)
    picked = []
    for s in range(n):
        lo, hi = s * len(rows) // n, (s + 1) * len(rows) // n
        picked.append(rng.choice(rows[lo:hi]))
    return picked


def build_line_sample(n: int, seed: int) -> tuple[list, dict]:
    rows = [
        json.loads(ln)
        for ln in (PAIRS / "labels_clean.jsonl").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    assert not any(r.get("folio") for r in rows), "labels_clean should hold no folio rows"
    picked = stratified_sample(rows, n, seed)
    ldir = OUT / "lines"
    ldir.mkdir(parents=True, exist_ok=True)
    out = []
    raw_hints = 0
    for idx, r in enumerate(picked, 1):
        page_key, line_key = r["page_line"].split(":")
        k = int(line_key[1:])
        src = PAIRS / r["image"]
        dst_rel = f"lines/{Path(r['image']).name}"
        shutil.copyfile(src, OUT / dst_rel)
        raw_lines = nonblank(DECODE_OUT / f"{page_key}.txt")
        pass2_lines = nonblank(DECODE_OUT / f"{page_key}-pass2.txt")
        raw = raw_lines[k - 1] if len(raw_lines) == len(pass2_lines) and k <= len(raw_lines) else None
        raw_hints += raw is not None
        out.append(
            {
                "n": idx,
                "page_line": r["page_line"],
                "page": int(page_key.split("-")[1]),
                "line": k,
                "img": dst_rel,
                "w": r["width_px"],
                "h": r["height_px"],
                "label": r["text"],
                "raw": raw,
            }
        )
    health = {
        "pool_rows": len(rows),
        "sample": len(out),
        "distinct_pages": len({o["page"] for o in out}),
        "with_raw_decode": raw_hints,
    }
    return out, health


# ---------------------------------------------------------------- main

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261103)
    ap.add_argument("--lines", type=int, default=200)
    ap.add_argument("--skip-table", action="store_true", help="rebuild the line sample only")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    pua_map = load_map()
    doc = fitz.open(PDF)

    if args.skip_table and (OUT / "table_cards.json").exists():
        cards = json.loads((OUT / "table_cards.json").read_text(encoding="utf-8"))
        table_health = {"reused": True}
    else:
        cards, table_health = build_table_cards(doc, pua_map, args.seed)
        (OUT / "table_cards.json").write_text(
            json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    lines, line_health = build_line_sample(args.lines, args.seed)
    (OUT / "line_sample.json").write_text(
        json.dumps(
            {"seed": args.seed, "method": "stratified, one line per equal-size stratum of "
             "labels_clean.jsonl in page order", "lines": lines},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )

    payload = {
        "built": datetime.now().isoformat(timespec="seconds"),
        "seed": args.seed,
        "table": cards,
        "lines": lines,
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", data)
    (OUT / "index.html").write_text(html, encoding="utf-8")

    report = {"table": table_health, "lines": line_health}
    (OUT / "build_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=1))
    print("open:", OUT / "index.html")


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    import os
    os._exit(0)  # PyMuPDF get_texttrace leaks refs and aborts at shutdown
