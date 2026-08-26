"""Shared helpers for the Quran GID decode table.

UrduTypesetting / ArabicTypesetting ToUnicode is broken for joining
forms. Use get_texttrace GIDs. Key is FONT:GID. Do not mix with
Batool or NOORIN tables.

  py -3 scripts/dump_quran_gids.py 17
"""

from __future__ import annotations

import json
import os
import sys
import unicodedata
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "decode" / "quran_gid_seed.json"
PDF = ROOT / "pdfs/QURANIC_TRANSLATION_in_GOJRI_by_Dr_Rafiq.pdf"

Y_GAP = 10.0
WORD_GAP = 1.2

KEEP_FONTS = (
    "urdutypesetting",
    "arabictypesetting",
    "traditionalarabic",
)


def font_family(font: str) -> str:
    name = font.split("+")[-1]
    return name.split(",")[0]


def is_keep_font(font: str) -> bool:
    fam = font_family(font).lower()
    return any(k in fam for k in KEEP_FONTS)


def map_key(font: str, gid: int) -> str:
    return f"{font_family(font)}:{gid}"


def load_map() -> dict[str, str]:
    if not SEED.exists():
        return {}
    return json.loads(SEED.read_text(encoding="utf-8")).get("map", {})


def is_good_ucs(ucs: int) -> bool:
    if ucs is None or ucs < 0 or ucs > 0x10FFFF:
        return False
    if ucs in (0xFFFD, 0xFFFF):
        return False
    if 32 <= ucs < 127:
        return True
    if 0x0600 <= ucs <= 0x06FF or 0x0750 <= ucs <= 0x077F:
        return True
    if 0x08A0 <= ucs <= 0x08FF:
        return True
    if 0xFB50 <= ucs <= 0xFDFF or 0xFE70 <= ucs <= 0xFEFF:
        return True
    if ucs in (0x200C, 0x200D, 0x200E, 0x200F, 0x061C):
        return True
    return False


def ucs_to_text(ucs: int) -> str:
    ch = chr(ucs)
    if 0xFB50 <= ucs <= 0xFDFF or 0xFE70 <= ucs <= 0xFEFF:
        return unicodedata.normalize("NFKC", ch)
    return ch


_TRACE_KEEP: list = []


def page_glyphs(page: fitz.Page) -> list[tuple]:
    """(y0, x0, x1, y1, font, gid, ucs) from texttrace.

    Keep the raw trace list alive. Deleting it can crash PyMuPDF
    during garbage collection. Callers that scan many pages must
    run in a short-lived process and exit with os._exit.
    """
    out = []
    spans = page.get_texttrace()
    _TRACE_KEEP.append(spans)
    for sp in spans:
        font = str(sp.get("font") or "")
        for ch in sp.get("chars") or []:
            try:
                ucs = int(ch[0])
                gid = int(ch[1])
                bbox = ch[3]
                x0 = float(bbox[0])
                y0 = float(bbox[1])
                x1 = float(bbox[2])
                y1 = float(bbox[3])
            except Exception:
                continue
            out.append((y0, x0, x1, y1, font, gid, ucs))
    out.sort(key=lambda t: (t[0], -t[1]))
    return out


def cluster_rows(chars: list) -> list[tuple[float, list]]:
    if not chars:
        return []
    rows: list[tuple[float, list]] = []
    cur = [chars[0]]
    for item in chars[1:]:
        if item[0] - cur[-1][0] > Y_GAP:
            ys = [t[0] for t in cur]
            rows.append((sum(ys) / len(ys), cur))
            cur = [item]
        else:
            cur.append(item)
    ys = [t[0] for t in cur]
    rows.append((sum(ys) / len(ys), cur))
    return rows


NUQTA_MAX_W = 0.4
TOOTH = set("بتثنپٹيیےئ")


def is_arabic_letter_ucs(ucs: int) -> bool:
    if not is_good_ucs(ucs):
        return False
    ch = chr(ucs)
    return unicodedata.category(ch).startswith("L") and (
        "\u0600" <= ch <= "\u06ff" or "\u0750" <= ch <= "\u077f"
    )


def lookup_text(font: str, gid: int, ucs: int, gid_map: dict[str, str]) -> str | None:
    key = map_key(font, gid)
    if key in gid_map:
        return gid_map[key]
    if is_keep_font(font):
        if is_good_ucs(ucs):
            return ucs_to_text(ucs)
        return None
    if ucs in (0xFFFD, 0xFFFF) or ucs < 0 or ucs > 0x10FFFF:
        return None
    ch = chr(ucs)
    if 0xFB50 <= ucs <= 0xFDFF or 0xFE70 <= ucs <= 0xFEFF:
        return unicodedata.normalize("NFKC", ch)
    if ch.isprintable() or ch.isspace():
        return ch
    return None


def is_combining_mark(text: str) -> bool:
    return bool(text) and all(unicodedata.category(ch) in {"Mn", "Mc"} for ch in text)


def nuqta_plan(run: list, gid_map: dict[str, str]) -> tuple[set[int], dict[int, str]]:
    """Zero-width Arabic letters are dots. They name the next host glyph."""
    skip: set[int] = set()
    override: dict[int, str] = {}
    for i, (_y0, x0, x1, _y1, font, gid, ucs) in enumerate(run):
        if (x1 - x0) >= NUQTA_MAX_W:
            continue
        if not is_keep_font(font) or not is_arabic_letter_ucs(ucs):
            continue
        letter = ucs_to_text(ucs)
        for j in range(i + 1, len(run)):
            _hy0, _hx0, _hx1, _hy1, hfont, hgid, hucs = run[j]
            if not is_keep_font(hfont):
                continue
            htext = lookup_text(hfont, hgid, hucs, gid_map)
            if htext == " ":
                continue
            if htext is None or htext == "" or (htext[0] in TOOTH):
                override[j] = letter
            skip.add(i)
            break
    return skip, override


def merge_marks(items: list[tuple[float, float, str]]) -> list[tuple[float, float, str]]:
    n = len(items)
    host_of: dict[int, int] = {}
    for i, (x0, x1, text) in enumerate(items):
        if not is_combining_mark(text):
            continue
        cx = (x0 + x1) / 2
        best = None
        best_d = None
        for j, (hx0, hx1, htext) in enumerate(items):
            if is_combining_mark(htext):
                continue
            hcx = (hx0 + hx1) / 2
            d = abs(hcx - cx)
            if best_d is None or d < best_d:
                best_d = d
                best = j
        if best is not None:
            host_of[i] = best
    merged: list[tuple[float, float, str]] = []
    extras: dict[int, str] = {}
    for i, host in host_of.items():
        extras[host] = extras.get(host, "") + items[i][2]
    for i, (x0, x1, text) in enumerate(items):
        if i in host_of:
            continue
        merged.append((x0, x1, text + extras.get(i, "")))
    return merged


def fmt_row(row: list, gid_map: dict[str, str]) -> str:
    run = sorted(row, key=lambda t: -t[1])
    skip, override = nuqta_plan(run, gid_map)
    pieces: list[tuple[float, float, str]] = []
    prev_x0 = None
    for i, (_y0, x0, x1, _y1, font, gid, ucs) in enumerate(run):
        if i in skip:
            continue
        if i in override:
            text = override[i]
        else:
            text = lookup_text(font, gid, ucs, gid_map)
        if text == "":
            continue
        if prev_x0 is not None and (prev_x0 - x1) > WORD_GAP:
            if not (text and is_combining_mark(text)):
                pieces.append((x0, x1, " "))
        if text is None:
            pieces.append((x0, x1, f"[{map_key(font, gid)}]"))
        else:
            pieces.append((x0, x1, text))
        prev_x0 = x0
    merged = merge_marks(pieces)
    return "".join(t for _x0, _x1, t in merged)


def decode_page(page: fitz.Page, gid_map: dict[str, str]) -> str:
    rows = cluster_rows(page_glyphs(page))
    lines = []
    for _y, row in rows:
        text = fmt_row(row, gid_map).strip()
        if text:
            lines.append(text)
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    page_1idx = 17
    if len(sys.argv) > 1:
        page_1idx = int(sys.argv[1])
    gid_map = load_map()
    doc = fitz.open(PDF)
    page = doc[page_1idx - 1]
    print(f"=== decoded page {page_1idx} (GID table {len(gid_map)}) ===")
    print(decode_page(page, gid_map))
    glyphs = page_glyphs(page)
    keep = [g for g in glyphs if is_keep_font(g[4])]
    seen = {map_key(f, gid) for _y0, _x0, _x1, _y1, f, gid, _u in keep}
    unk = sorted(k for k in seen if k not in gid_map)
    print(f"page keep-keys {len(seen)} mapped {len(seen) - len(unk)} unknown {len(unk)}")
    print("unknown:", " ".join(unk[:60]), flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
