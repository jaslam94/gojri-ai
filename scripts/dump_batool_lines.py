"""Dump mixed Latin + Batool-PUA lines from a dictionary page.

Batool runs are printed right-to-left as hex codes. Latin is left as-is.
Used to grow data/decode/batool_pua_seed.json against gold.

  py -3 scripts/dump_batool_lines.py
  py -3 scripts/dump_batool_lines.py 26
"""

from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "decode" / "batool_pua_seed.json"


def load_map() -> dict[str, str]:
    data = json.loads(SEED.read_text(encoding="utf-8"))
    return data["map"]


Y_GAP = 14.0  # Nastaliq diagonals split PDF lines; cluster nearby y into rows.
WORD_GAP = 1.0  # x gap (px) between RTL glyphs that marks a word space.


def page_chars(page: fitz.Page) -> list[tuple[float, float, float, str, str, int]]:
    data = page.get_text("rawdict", flags=0)
    chars = []
    for block in data["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                font = span.get("font", "")
                for ch in span["chars"]:
                    x0, y0, x1, y1 = ch["bbox"]
                    chars.append((y0, x0, x1, font, ch["c"], ord(ch["c"])))
    chars.sort(key=lambda t: (t[0], -t[1]))
    return chars


def cluster_rows(chars: list) -> list[tuple[float, list]]:
    if not chars:
        return []
    rows: list[tuple[float, list]] = []
    cur: list = [chars[0]]
    for item in chars[1:]:
        if item[0] - cur[-1][0] > Y_GAP:
            ys = [t[0] for t in cur]
            rows.append((sum(ys) / len(ys), [(t[1], t[2], t[3], t[4], t[5]) for t in cur]))
            cur = [item]
        else:
            cur.append(item)
    ys = [t[0] for t in cur]
    rows.append((sum(ys) / len(ys), [(t[1], t[2], t[3], t[4], t[5]) for t in cur]))
    return rows


def is_combining_mark(text: str) -> bool:
    return bool(text) and all(unicodedata.category(ch) in {"Mn", "Mc"} for ch in text)


def merge_marks(
    items: list[tuple[float, float, str]],
) -> list[tuple[float, float, str]]:
    """Attach each combining mark to the nearest host letter by x.

    After RTL sort a mark may sit before or after its letter. Unicode
    needs letter then mark.
    """
    n = len(items)
    host_of: dict[int, int] = {}
    for i, (x0, x1, text) in enumerate(items):
        if not is_combining_mark(text):
            continue
        mx = (x0 + x1) / 2
        best: int | None = None
        best_d: float | None = None
        for j, (lx0, lx1, lt) in enumerate(items):
            if is_combining_mark(lt):
                continue
            if min(lx0, lx1) <= mx <= max(lx0, lx1):
                d = 0.0
            else:
                d = min(abs(mx - lx0), abs(mx - lx1))
            if best_d is None or d < best_d:
                best_d = d
                best = j
        if best is not None:
            host_of[i] = best

    merged: list[tuple[float, float, str]] = []
    for i, (x0, x1, text) in enumerate(items):
        if is_combining_mark(text):
            if i not in host_of:
                merged.append((x0, x1, text))
            continue
        marks = [items[k][2] for k in range(n) if host_of.get(k) == i]
        merged.append((x0, x1, text + "".join(marks)))
    return merged


def _is_mark_code(key: str, pua_map: dict[str, str]) -> bool:
    text = pua_map.get(key, "")
    return is_combining_mark(text)


def _neighbor_letter(
    run: list[tuple[float, float, int]],
    pua_map: dict[str, str],
    i: int,
    step: int,
) -> tuple[int, str, str] | None:
    j = i + step
    while 0 <= j < len(run):
        key = f"{run[j][2]:04X}"
        text = pua_map.get(key, f"[{key}]")
        if text == "" or _is_mark_code(key, pua_map):
            j += step
            continue
        return j, key, text
    return None


def map_code(
    run: list[tuple[float, float, int]],
    pua_map: dict[str, str],
    i: int,
) -> str | None:
    """Map one Batool code. Some letters need the next/previous letter.

    Gold (dict_alif): آبلائے, نھیں, مهارو, اپ ھُدرو.
    """
    key = f"{run[i][2]:04X}"
    base = pua_map.get(key, f"[{key}]")
    if base == "":
        return None
    prev = _neighbor_letter(run, pua_map, i, -1)
    nxt = _neighbor_letter(run, pua_map, i, 1)
    prev_text = prev[2] if prev else ""
    next_text = nxt[2] if nxt else ""
    next_key = nxt[1] if nxt else ""

    if key == "F031" and prev and prev[1] == "F0F1":
        return None
    if key == "F0F1" and next_key == "F031":
        if prev_text.startswith("ا") or prev_text.startswith("آ"):
            return "ئے"
        return "ائے"
    if key == "F060":
        if prev_text.startswith("ن") and next_text.startswith("ی"):
            return "ھ"
        if prev_text.startswith("م") and next_text.startswith("ا"):
            return "ه"
    if key == "F061" and next_text.startswith("د"):
        return "ھ"
    return base


def decode_batool_run(run: list[tuple[float, float, int]], pua_map: dict[str, str]) -> str:
    run = sorted(run, key=lambda t: -t[0])
    items: list[tuple[float, float, str]] = []
    for i, (x0, x1, _o3) in enumerate(run):
        text = map_code(run, pua_map, i)
        if text is None:
            continue
        items.append((x0, x1, text))
    merged = merge_marks(items)
    decoded = []
    prev_x0 = None
    for x0, x1, text in merged:
        if prev_x0 is not None and (prev_x0 - x1) > WORD_GAP:
            decoded.append(" ")
        decoded.append(text)
        prev_x0 = x0
    return "".join(decoded)


def fmt_line(chars, pua_map: dict[str, str], wrap_batool: bool = True) -> str:
    chars = sorted(chars, key=lambda t: t[0])
    parts = []
    i = 0
    while i < len(chars):
        _x0, _x1, font, c, o = chars[i]
        if "Batool" in font or (0xE000 <= o <= 0xF8FF):
            run = []
            while i < len(chars):
                x0, x1, font2, c2, o2 = chars[i]
                if "Batool" in font2 or (0xE000 <= o2 <= 0xF8FF):
                    run.append((x0, x1, o2))
                    i += 1
                else:
                    break
            text = decode_batool_run(run, pua_map)
            parts.append("{" + text + "}" if wrap_batool else text)
        else:
            buf = []
            while i < len(chars):
                _x0b, _x1b, font2, c2, o2 = chars[i]
                if "Batool" in font2 or (0xE000 <= o2 <= 0xF8FF):
                    break
                buf.append(c2)
                i += 1
            parts.append("".join(buf))
    return "".join(parts)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    page_1idx = 25
    if len(sys.argv) > 1:
        page_1idx = int(sys.argv[1])
    pua_map = load_map()
    pdf = ROOT / "pdfs/anjumshanasi/Gojri-English-Dictionary.pdf"
    doc = fitz.open(pdf)
    if page_1idx == 25:
        gold = (ROOT / "data/gold/transcriptions/dict_alif/dict_alif_gold.txt").read_text(
            encoding="utf-8"
        )
        print("=== gold ===")
        print(gold)
    print(f"=== decoded page {page_1idx} (known map) / [CODE] unknown ===")
    rows = cluster_rows(page_chars(doc[page_1idx - 1]))
    for y, chars in rows:
        print(f"y={y:6.1f}  {fmt_line(chars, pua_map)}")
    unknown = set()
    seen = set()
    for _y, chars in rows:
        for _x0, _x1, font, c, o in chars:
            if "Batool" in font:
                key = f"{o:04X}"
                seen.add(key)
                if key not in pua_map:
                    unknown.add(key)
    print(f"\nunknown codes ({len(unknown)}):", " ".join(sorted(unknown)))
    print(f"page Batool codes ({len(seen)}), table size {len(pua_map)}")


if __name__ == "__main__":
    main()
