"""Dump NOORIN/NOORIC PUA lines from Kahawat-Kosh (two columns).

Keys are FONT:CODE (example NOORIN85:F08A). Do not use the Batool table.

  py -3 scripts/dump_noorin_lines.py
  py -3 scripts/dump_noorin_lines.py 50
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "decode" / "noorin_pua_seed.json"
PDF = ROOT / "pdfs/anjumshanasi/Kahawat-Kosh.pdf"
GOLD = ROOT / "data/gold/transcriptions/kahawat_kosh/kahawat_kosh_gold.txt"

Y_GAP = 12.0
COL_SPLIT = 240.0
WORD_GAP = 1.2


def is_overlay_font(font: str) -> bool:
    fam = font_family(font).upper()
    return fam.startswith("NOORIC") or fam == "NOORIN86"


def font_family(font: str) -> str:
    name = font.split("+")[-1]
    return name.split(",")[0]


def is_noorin(font: str) -> bool:
    fam = font_family(font).upper()
    return fam.startswith("NOORIN") or fam.startswith("NOORIC")


def load_map() -> dict[str, str]:
    if not SEED.exists():
        return {}
    return json.loads(SEED.read_text(encoding="utf-8")).get("map", {})


def page_chars(page: fitz.Page) -> list[tuple[float, float, float, str, int]]:
    data = page.get_text("rawdict", flags=0)
    chars = []
    for block in data["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                font = span.get("font", "")
                for ch in span["chars"]:
                    x0, y0, x1, _y1 = ch["bbox"]
                    chars.append((y0, x0, x1, font, ord(ch["c"])))
    chars.sort(key=lambda t: (t[0], -t[1]))
    return chars


def attach_overlays(
    rows: list[tuple[float, list]], overlays: list, max_dy: float = 18.0
) -> list[list]:
    """Each overlay joins only the nearest base row."""
    out = [list(row) for _y, row in rows]
    ys = [y for y, _row in rows]
    if not ys:
        return out
    for ov in overlays:
        best_i = 0
        best_d = abs(ov[0] - ys[0])
        for i, y in enumerate(ys[1:], start=1):
            d = abs(ov[0] - y)
            if d < best_d:
                best_d = d
                best_i = i
        if best_d <= max_dy:
            out[best_i].append(ov)
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


def map_key(font: str, o: int) -> str:
    return f"{font_family(font)}:{o:04X}"


def nearest_base_index(run: list, i: int) -> int | None:
    """Index of nearest non-overlay glyph to overlay i."""
    _y, x0, x1, _font, _o = run[i]
    cx = (x0 + x1) / 2
    best = None
    best_d = None
    for j, (_yj, xj0, xj1, fontj, _oj) in enumerate(run):
        if j == i:
            continue
        if is_overlay_font(fontj):
            continue
        jcx = (xj0 + xj1) / 2
        d = abs(jcx - cx)
        if best_d is None or d < best_d:
            best_d = d
            best = j
    return best


def base_has_nuqta(run: list, base_i: int) -> bool:
    _y, bx0, bx1, _font, _o = run[base_i]
    pad = 8.0
    bases = [j for j, item in enumerate(run) if not is_overlay_font(item[3])]
    for j, (_yj, nx0, nx1, fontj, _oj) in enumerate(run):
        if font_family(fontj).upper() != "NOORIN86":
            continue
        if bx1 + pad >= nx0 and nx1 + pad >= bx0:
            return True
        nearest = nearest_base_index(run, j)
        if nearest is None:
            continue
        hosts = {nearest}
        if nearest in bases:
            pos = bases.index(nearest)
            for step in (1, 2):
                if pos + step < len(bases):
                    hosts.add(bases[pos + step])
        if base_i in hosts:
            return True
    return False


def neighbor_base_keys(run: list, i: int, pua_map: dict[str, str]) -> tuple[str | None, str | None]:
    """Previous and next base keys, skipping overlays and empty maps."""
    prev = None
    for item in reversed(run[:i]):
        if is_overlay_font(item[3]):
            continue
        k = map_key(item[3], item[4])
        if pua_map.get(k) == "":
            continue
        prev = k
        break
    nxt = None
    for item in run[i + 1 :]:
        if is_overlay_font(item[3]):
            continue
        k = map_key(item[3], item[4])
        if pua_map.get(k) == "":
            continue
        nxt = k
        break
    return prev, nxt


def immediate_prev_base_key(run: list, i: int) -> str | None:
    """Previous base key, skipping overlays only (keeps empty-mapped joiners)."""
    for item in reversed(run[:i]):
        if is_overlay_font(item[3]):
            continue
        return map_key(item[3], item[4])
    return None


def kar_r_before(run: list, i: int) -> bool:
    """True when run[i] immediately follows ک+ر (F067 then F05A)."""
    for j in range(i - 1, -1, -1):
        if is_overlay_font(run[j][3]):
            continue
        if map_key(run[j][3], run[j][4]) == "NOORIN01:F05A":
            return immediate_prev_base_key(run, j) == "NOORIN01:F067"
        return False
    return False


def base_keys_before(run: list, i: int, pua_map: dict[str, str], n: int) -> list[str]:
    """Last n base keys before index i, skipping overlays and empty flat maps."""
    out: list[str] = []
    for item in reversed(run[:i]):
        if is_overlay_font(item[3]):
            continue
        k = map_key(item[3], item[4])
        if pua_map.get(k) == "":
            continue
        out.append(k)
        if len(out) == n:
            break
    return out


def base_keys_before_full_row(
    run: list, i: int, row_all: list | None, pua_map: dict[str, str], n: int
) -> list[str]:
    """Like base_keys_before, but uses the full clustered row when split by column."""
    if row_all is None:
        return base_keys_before(run, i, pua_map, n)
    cur = run[i]
    row_run = sorted(
        [c for c in row_all if not is_overlay_font(c[3])],
        key=lambda t: -t[1],
    )
    idx = next((j for j, c in enumerate(row_run) if c is cur), None)
    if idx is None:
        return base_keys_before(run, i, pua_map, n)
    return base_keys_before(row_run, idx, pua_map, n)


def base_keys_after(run: list, i: int, pua_map: dict[str, str], n: int) -> list[str]:
    """Next n base keys after index i, skipping overlays and empty flat maps."""
    out: list[str] = []
    for item in run[i + 1 :]:
        if is_overlay_font(item[3]):
            continue
        k = map_key(item[3], item[4])
        if pua_map.get(k) == "":
            continue
        out.append(k)
        if len(out) == n:
            break
    return out


def lookup_text(
    run: list, i: int, pua_map: dict[str, str], row_all: list | None = None
) -> str | None:
    _y, _x0, _x1, font, o = run[i]
    key = map_key(font, o)
    if is_overlay_font(font):
        if key not in pua_map:
            return None
        return pua_map[key]
    nuqta = base_has_nuqta(run, i)
    if key == "NOORIN48:F0E2":
        return "پ" if nuqta else "و"
    if key == "NOORIN81:F037":
        return "پڑ" if nuqta else "پر"
    if key == "NOORIN01:F075":
        return "گ" if nuqta else "ک"
    if key == "NOORIN82:F08C":
        return "غ" if nuqta else "ع"
    if key == "NOORIN05:F083":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN48:F0E3":
            return "ہو"
        if nxt in ("NOORIN01:F05C", "NOORIN48:F0E2"):
            return "ہون"
        return pua_map.get(key, "ہون")
    if key == "NOORIN05:F04B":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN48:F0E3":
            return "منا"
        if nxt == "NOORIN05:F084":
            return ""
        return pua_map.get(key, "اپنی")
    if key == "NOORIN01:F068":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        # چھوڑ and جوڑن already contain ڑ.
        if prev in ("NOORIN07:F067", "NOORIN81:F08E"):
            return ""
        if ip == "NOORIN05:F04E":
            return ""
        return pua_map.get(key, "ڑ")
    if key == "NOORIN82:F063":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F09C":
            return "یا"
        if prev == "NOORIN81:F025":
            return "یار"
        if prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return "بت"
        if prev == "NOORIN04:F0DB" and nxt == "NOORIN01:F099":
            return "یر"
        if nxt == "NOORIN85:F08A":
            return ""
        if prev == "NOORIN01:F07A":
            return "یا"
        return pua_map.get(key, "یار")
    if key == "NOORIN01:F099":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN82:F063" and nxt == "NOORIN34:F023":
            return " یا"
        if nxt == "NOORIN34:F023" and prev != "NOORIN82:F063":
            return "د"
        return pua_map.get(key)
    if key == "NOORIN34:F023":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F099" and nxt == "NOORIN05:F083":
            return "دشمنی"
        if prev == "NOORIN85:F08A" and nxt in (
            "NOORIN82:F099",
            "NOORIN01:F058",
        ):
            return "شمنی"
        if prev == "NOORIN01:F099" and nxt in (
            "NOORIN63:F0C5",
            "NOORIN63:F0C2",
            "NOORIN01:F0D4",
            None,
        ):
            return "شمنی"
        return ""
    if key == "NOORIN01:F05A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F061":
            return ""
        if nxt == "NOORIN41:F076" and prev == "NOORIN63:F0B0":
            return ""
        if nxt == "NOORIN06:F056":
            return "ا"
        if nxt == "NOORIN56:F0DD":
            return "ا"
        if nxt == "NOORIN82:F038":
            return "ا"
        if prev == "NOORIN04:F0DB" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "ر")
    if key == "NOORIN01:F051":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN06:F056":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN01:F057":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN52:F099":
            return "آ"
        return pua_map.get(key, "آپ")
    if key == "NOORIN85:F0BB":
        return pua_map.get(key, "تیا")
    if key == "NOORIN06:F056":
        return pua_map.get(key, "ٹھا")
    if key == "NOORIN52:F099":
        return pua_map.get(key, "سمجھ")
    if key == "NOORIN01:F07A":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F05D":
            return ""
        if prev == "NOORIN89:F031":
            return ""
        if prev == "NOORIN01:F079":
            before = base_keys_before(run, i, pua_map, 2)
            if len(before) >= 2 and before[1] == "NOORIN14:F0B7":
                return ""
        return pua_map.get(key, "ھ")
    if key == "NOORIN01:F079":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN14:F0B7":
            return ""
        if prev == "NOORIN27:F076":
            return ""
        if prev == "NOORIN25:F0A9":
            return ""
        return pua_map.get(key, "ے")
    if key == "NOORIN89:F031":
        return pua_map.get(key, "نجھی")
    if key == "NOORIN01:F067":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN06:F05E":
            return "ری"
        if prev == "NOORIN57:F044" and nxt == "NOORIN82:F038":
            return "تے "
        return pua_map.get(key, "ک")
    if key == "NOORIN57:F044":
        after = base_keys_after(run, i, pua_map, 2)
        if after[:2] == ["NOORIN01:F067", "NOORIN82:F038"]:
            return "پھٹکڑی "
        return pua_map.get(key, "ت")
    if key == "NOORIN57:F061":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN82:F038":
            return "چوکھا"
        return pua_map.get(key, "ای")
    if key == "NOORIN14:F07D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F040" and nxt in (
            "NOORIN82:F097", "NOORIN82:F02A", "NOORIN22:F037",
        ):
            return "کہ"
        if ip == "NOORIN63:F0D1" and nxt == "NOORIN22:F037":
            return "لا"
        if prev == "NOORIN82:F03A" and nxt == "NOORIN15:F0D1":
            return "لا"
        return pua_map.get(key, "")
    if key == "NOORIN15:F0D1":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN14:F07D":
            return "لگے "
        return pua_map.get(key)
    if key == "NOORIN01:F056":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        before = base_keys_before(run, i, pua_map, 2)
        if (
            prev == "NOORIN01:F05A"
            and nxt == "NOORIN63:F0C3"
            and len(before) == 2
            and before[0] == "NOORIN01:F05A"
            and before[1] == "NOORIN04:F0DB"
        ):
            return ""
        return pua_map.get(key, "ں")
    if key == "NOORIN01:F09D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN57:F05A" and nxt == "NOORIN17:F041":
            return "و"
        if ip == "NOORIN12:F0E2" and nxt == "NOORIN01:F077":
            return "ڈال"
        if ip == "NOORIN57:F021" and nxt == "NOORIN01:F077":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN08:F04A":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN04:F0DB":
            return "سخت"
        return pua_map.get(key, "س")
    if key == "NOORIN81:F05D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F07A":
            return "جدو"
        return pua_map.get(key, "جد")
    if key == "NOORIN82:F068":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F05D":
            return "ید"
        return pua_map.get(key)
    if key == "NOORIN82:F09E":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F05D":
            return "کہ"
        return pua_map.get(key)
    if key == "NOORIN81:F061":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F05A":
            return ""
        if nxt == "NOORIN04:F02C":
            return pua_map.get(key, "یر")
        return pua_map.get(key, "یر")
    if key == "NOORIN04:F02C":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F061":
            return "یںپ"
        if prev == "NOORIN81:F06C":
            return "یںپ"
        return pua_map.get(key, "ریںپ")
    if key == "NOORIN48:F0DE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN56:F0D8":
            return pua_map.get(key, "ق")
        if prev == "NOORIN01:F07A":
            before = base_keys_before(run, i, pua_map, 2)
            if len(before) >= 2 and before[1] == "NOORIN01:F067":
                if nxt == "NOORIN63:F0D1":
                    return "ل"
                if nxt in ("NOORIN57:F031", "NOORIN82:F03B"):
                    return "ڑ"
                if nxt == "NOORIN85:F08A":
                    return "و"
        return pua_map.get(key, "ق")
    if key == "NOORIN63:F0B0":
        return pua_map.get(key, "فی")
    if key == "NOORIN81:F07B":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F07B":
            for j in range(i + 1, len(run)):
                if is_overlay_font(run[j][3]):
                    continue
                k2 = map_key(run[j][3], run[j][4])
                if k2 == "NOORIN01:F07B":
                    _p2, n2 = neighbor_base_keys(run, j, pua_map)
                    if n2 == "NOORIN16:F023":
                        return "خو"
                    break
        return pua_map.get(key, "خا")
    if key == "NOORIN01:F07B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN61:F0CE":
            return ""
        if prev == "NOORIN05:F06E":
            return ""
        if nxt == "NOORIN16:F023":
            return "اہ"
        if prev == "NOORIN16:F023":
            return "اہ"
        if prev == "NOORIN25:F0BA" and nxt == "NOORIN63:F0E2":
            return "ہ"
        return pua_map.get(key, "ر")
    if key == "NOORIN06:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN26:F032":
            return "ٹھو"
        if prev == "NOORIN01:F09F":
            return "ھو"
        if prev in ("NOORIN56:F0CE", "NOORIN82:F02A") and nxt == "NOORIN82:F099":
            return "ٹھو"
        if prev == "NOORIN06:F0D1" and nxt == "NOORIN63:F0D1":
            return ""
        if nxt == "NOORIN11:F033" and prev in (None, "NOORIN63:F0C3"):
            return "جو ٹھو "
        if prev is None and nxt == "NOORIN01:F065":
            return "ٹھوڈی"
        if prev is None and nxt == "NOORIN82:F099":
            return "ٹھوکرے جا"
        if prev == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return "ٹھوکرے جا"
        if prev is None and nxt == "NOORIN01:F075":
            return "ٹھو"
        if prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F075":
            return "ٹھو"
        if prev in (None, "NOORIN01:F0D4") and nxt == "NOORIN63:F0C3":
            return "جوٹھو"
        if prev == "NOORIN63:F0C3" and nxt == "NOORIN14:F0A3":
            return "جوٹھو"
        if prev == "NOORIN63:F0C3" and nxt == "NOORIN85:F08A":
            return "جھوٹو"
        if prev == "NOORIN76:F084" and nxt == "NOORIN01:F03A":
            return "جھوٹو"
        if prev == "NOORIN01:F0A5":
            return "رٹھو"
        if prev == "NOORIN01:F05A" and nxt == "NOORIN63:F0F1":
            return "اٹھو"
        # Do not use R-column colon as prev for L-column F05E (false ٹوٹھو).
        if prev is None and nxt == "NOORIN01:F06B":
            return "جھوٹو ا"
        if prev is None and nxt == "NOORIN01:F03A":
            return "ھو"
        if prev == "NOORIN01:F065":
            return "ھوا"
        return None
    if key == "NOORIN01:F065":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN06:F05E":
            return "ڈ"
        if nxt == "NOORIN82:F038":
            return "ڈ"
        if nxt == "NOORIN01:F05A":
            after = base_keys_after(run, i, pua_map, 2)
            if after[:2] == ["NOORIN01:F05A", "NOORIN82:F038"]:
                return "ڈ"
        if prev == "NOORIN06:F05E":
            return ""
        return pua_map.get(key, "ڈر")
    if key == "NOORIN82:F099":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN06:F05E":
            for j in range(i - 1, -1, -1):
                if is_overlay_font(run[j][3]):
                    continue
                if map_key(run[j][3], run[j][4]) == "NOORIN06:F05E":
                    p2, _n2 = neighbor_base_keys(run, j, pua_map)
                    if p2 in (None, "NOORIN01:F03A"):
                        return ""
                    break
        return pua_map.get(key)
    if key == "NOORIN01:F07D":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN82:F040":
            return "ے"
        before = base_keys_before(run, i, pua_map, 2)
        if (
            len(before) >= 2
            and before[0] == "NOORIN82:F099"
            and before[1] == "NOORIN06:F05E"
        ):
            for j in range(i - 1, -1, -1):
                if is_overlay_font(run[j][3]):
                    continue
                if map_key(run[j][3], run[j][4]) == "NOORIN06:F05E":
                    p2, _n2 = neighbor_base_keys(run, j, pua_map)
                    if p2 in (None, "NOORIN01:F03A"):
                        return ""
                    break
        return pua_map.get(key, "پدے")
    if key == "NOORIN57:F031":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN12:F042":
            return "بو"
        return pua_map.get(key, "")
    if key == "NOORIN12:F042":
        return pua_map.get(key, "لیں")
    if key == "NOORIN82:F074":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev in (
            "NOORIN01:F058",
            "NOORIN81:F082",
            "NOORIN81:F046",
            "NOORIN63:F0E2",
            "NOORIN81:F036",
            "NOORIN85:F08A",
            "NOORIN82:F02A",
        ) or (prev is None and nxt == "NOORIN01:F03A"):
            return "یہ"
        if prev == "NOORIN57:F05A":
            return "ی"
        if prev == "NOORIN01:F07A":
            if nxt == "NOORIN15:F055":
                return "یہ"
            if nxt == "NOORIN01:F05A":
                for j in range(i + 1, len(run)):
                    if is_overlay_font(run[j][3]):
                        continue
                    k2 = map_key(run[j][3], run[j][4])
                    if k2 == "NOORIN01:F05A":
                        _p2, n2 = neighbor_base_keys(run, j, pua_map)
                        if n2 == "NOORIN22:F037":
                            return "یہ"
                        break
            return "ویہ"
        return None
    if key == "NOORIN81:F021":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        # Same 4.9px با-shape. Drop alif before ے (سے، کیے، بے).
        if prev == "NOORIN81:F06C":
            return "بی"
        if nxt == "NOORIN01:F079":
            return "ب" if prev is None else ""
        if nxt == "NOORIN85:F08A":
            return "با"
        return pua_map.get(key, "با")
    if key == "NOORIN81:F027":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F07B":
            for j in range(i - 1, -1, -1):
                if is_overlay_font(run[j][3]):
                    continue
                if map_key(run[j][3], run[j][4]) == "NOORIN01:F07B":
                    p2, _ = neighbor_base_keys(run, j, pua_map)
                    if p2 == "NOORIN05:F06E":
                        return "بر"
                break
        return pua_map.get(key, "ز")
    if key == "NOORIN13:F0A8":
        if not nuqta:
            return pua_map.get(key)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F05A" and nxt == "NOORIN01:F079":
            return "ہ"
        if prev == "NOORIN01:F053" and nxt == "NOORIN01:F079":
            return "س"
        return pua_map.get(key, "س")
    if key == "NOORIN08:F081":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F05A" and nxt == "NOORIN01:F079":
            return ""
        if prev == "NOORIN01:F077" and nxt == "NOORIN01:F056":
            return "ا"
        return None
    if key == "NOORIN09:F051":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F07D":
            return "چھوڑ"
        return pua_map.get(key, "ٹھنڈ")
    if key == "NOORIN04:F058":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN63:F0C6":
            return "بچا"
        return pua_map.get(key, "بچ")
    if key == "NOORIN12:F0E2":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN12:F07B":
            return "بال"
        return pua_map.get(key, "گھی")
    if key == "NOORIN12:F07B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN12:F0E2":
            return "وں"
        if nxt == "NOORIN01:F07D":
            return "گھڑے"
        if nxt == "NOORIN04:F02C":
            return "گھڑیں"
        return pua_map.get(key, "گھڑی")
    if key == "NOORIN12:F0BE":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN82:F063":
            return "لیا"
        return pua_map.get(key, "ل")
    if key == "NOORIN14:F07A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev is None:
            return "ر"
        if prev == "NOORIN89:F031" and nxt == "NOORIN01:F0D4":
            return " ہنڈی"
        if prev == "NOORIN12:F0E1":
            if nxt == "NOORIN01:F07A":
                return "نو"
            return "ن"
        if prev == "NOORIN63:F0C5":
            return "ہنڈ"
        if prev == "NOORIN01:F057" and nxt == "NOORIN12:F0E1":
            return "ن"
        if prev == "NOORIN01:F05A" and nxt in (
            "NOORIN01:F0A5",
            "NOORIN63:F0C3",
        ):
            return ""
        return None
    if key == "NOORIN14:F0F7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F07A":
            return ""
        if prev == "NOORIN63:F0C5" and nxt in (
            "NOORIN01:F03A",
            "NOORIN57:F044",
        ):
            return ""
        if prev == "NOORIN01:F05A" and nxt in (
            "NOORIN57:F044",
            "NOORIN63:F0C3",
            "NOORIN01:F03A",
            "NOORIN01:F058",
            "NOORIN01:F05A",
        ):
            return ""
        if prev == "NOORIN01:F0D4" and nxt == "NOORIN04:F02C":
            return ""
        if prev == "NOORIN82:F026" and nxt == "NOORIN01:F05A":
            return ""
        if prev == "NOORIN14:F0BE" and nxt == "NOORIN01:F05A":
            return ""
        if prev == "NOORIN14:F0F7" and nxt == "NOORIN01:F07D":
            return "ا"
        if prev is None and nxt != "NOORIN14:F0F7":
            return ""
        if prev is None and nxt == "NOORIN14:F0F7":
            return ""
        if prev == "NOORIN48:F0E4":
            return ""
        if prev == "NOORIN01:F06B" and nxt == "NOORIN12:F079":
            return "ے"
        if prev == "NOORIN57:F05E" and nxt == "NOORIN09:F096":
            return ""
        if prev == "NOORIN01:F05A" and nxt == "NOORIN81:F059":
            return ""
        if prev == "NOORIN59:F0F1" and nxt == "NOORIN62:F0D8":
            return ""
        if prev == "NOORIN19:F0D3" and nxt == "NOORIN01:F05A":
            return ""
        if prev == "NOORIN01:F056" and nxt == "NOORIN57:F0B7":
            return ""
        if prev == "NOORIN10:F072" and nxt == "NOORIN01:F07D":
            return ""
        if prev == "NOORIN01:F0D4" and nxt is None:
            return ""
        if prev == "NOORIN48:F0E3" and nxt == "NOORIN01:F07D":
            return ""
        if prev == "NOORIN63:F0C4" and nxt == "NOORIN01:F05A":
            return ""
        if prev == "NOORIN59:F0F1" and nxt == "NOORIN82:F099":
            return ""
        if prev == "NOORIN01:F056" and nxt == "NOORIN81:F082":
            return ""
        return None
    if key == "NOORIN10:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN63:F0C5":
            return "ہی"
        if prev == "NOORIN63:F0C3" and nxt == "NOORIN22:F037":
            return ""
        if prev == "NOORIN63:F0C3":
            return "ہی"
        if prev == "NOORIN06:F091" and nxt == "NOORIN14:F0F7":
            return "ا"
        if prev == "NOORIN01:F079" and nxt == "NOORIN63:F0BB":
            return "اک"
        if prev == "NOORIN57:F044" and nxt == "NOORIN01:F03A":
            return "ہی"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0DB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN48:F0E2" and nxt == "NOORIN01:F05A":
            return "ن"
        if prev == "NOORIN48:F0E2" and nxt is None:
            return ""
        if prev == "NOORIN82:F02A" and nxt == "NOORIN48:F0EC":
            return "ے"
        if prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F03A":
            return ""
        if prev == "NOORIN01:F075" and nxt == "NOORIN01:F03A":
            return ""
        if prev == "NOORIN01:F056" and nxt == "NOORIN01:F058":
            return "،"
        if prev == "NOORIN01:F07B" and nxt == "NOORIN01:F07A":
            return "د"
        if prev == "NOORIN01:F07A" and nxt == "NOORIN01:F079":
            return ""
        if prev == "NOORIN63:F0E2" and nxt == "NOORIN01:F067":
            return "ا"
        if prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F07A":
            return ""
        if prev == "NOORIN01:F077" and nxt == "NOORIN01:F0D4":
            return ""
        if prev == "NOORIN77:F0B3" and nxt == "NOORIN01:F03A":
            return ""
        if prev == "NOORIN63:F0DF" and nxt == "NOORIN01:F03A":
            return ""
        if prev == "NOORIN08:F03F" and nxt is None:
            return ""
        if prev == "NOORIN57:F044" and nxt == "NOORIN05:F083":
            return ""
        if prev == "NOORIN01:F056" and nxt == "NOORIN01:F05A":
            return ""
        if prev == "NOORIN05:F084" and nxt == "NOORIN05:F083":
            return ""
        if prev == "NOORIN63:F0C4" and nxt == "NOORIN57:F05A":
            return ""
        if prev == "NOORIN72:F0C1" and nxt == "NOORIN01:F0D4":
            return ""
        if prev == "NOORIN63:F0C6" and nxt == "NOORIN11:F033":
            return ""
        if nxt == "NOORIN01:F0D4":
            return ""
        if nxt == "NOORIN01:F03A":
            return ""
        if prev == "NOORIN27:F098" and nxt == "NOORIN83:F0D9":
            return "بیری"
        if prev == "NOORIN08:F04A" and nxt == "NOORIN82:F063":
            return "ب"
        if prev == "NOORIN17:F041" and nxt == "NOORIN01:F05A":
            return ""
        if prev is None and nxt is None:
            return ""
        return None
    if key == "NOORIN81:F0A2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F07A":
            return ""
        if prev == "NOORIN81:F071" and nxt == "NOORIN48:F0EC":
            return "ضر ہ"
        if prev == "NOORIN57:F022" and nxt == "NOORIN01:F067":
            return "ضرر "
        return None
    if key == "NOORIN82:F038":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F067":
            if nxt == "NOORIN57:F061":
                return "رنگ "
            if nxt == "NOORIN01:F067":
                return "ھ"
            if nxt in ("NOORIN63:F0D1", "NOORIN01:F065"):
                return "ھ"
            if nxt == "NOORIN63:F0C3":
                return "و"
            if nxt == "NOORIN09:F0F1":
                return "ھ"
            if nxt == "NOORIN81:F0A2":
                return "ھ"
        if prev == "NOORIN63:F0E2" and nxt == "NOORIN07:F067":
            return "ر"
        if prev == "NOORIN81:F021" and nxt in (
            "NOORIN01:F03A",
            "NOORIN63:F0C3",
            "NOORIN01:F058",
        ):
            return "نگ"
        if prev == "NOORIN01:F0AF" and nxt == "NOORIN01:F03A":
            return "نگ"
        if prev == "NOORIN01:F09F":
            return "نگ"
        if prev == "NOORIN01:F065":
            return "نگ"
        if prev == "NOORIN85:F08A" and nxt == "NOORIN01:F067":
            return "نگ"
        if prev == "NOORIN63:F0BB" and nxt == "NOORIN16:F071":
            return "نگ"
        if prev == "NOORIN01:F05A":
            return "نگ"
        if prev is None and nxt == "NOORIN01:F03A":
            return ""
        return None
    if key == "NOORIN14:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN85:F08A" and nxt == "NOORIN01:F079":
            return "ھیان"
        return pua_map.get(key, "ھ")
    if key == "NOORIN82:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN11:F033":
            if nxt == "NOORIN01:F07D":
                return "د"
            return "دے"
        if prev == "NOORIN83:F0E1":
            return "دے"
        if prev is None and nxt == "NOORIN01:F03A":
            return "دے"
        return None
    if key == "NOORIN59:F0F0":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN12:F076":
            return ""
        return pua_map.get(key)
    if key == "NOORIN57:F049":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN12:F076":
            return ""
        return pua_map.get(key, "لو")
    if key == "NOORIN18:F0A9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F057":
            return " اپنی"
        return pua_map.get(key, " پئی")
    if key == "NOORIN01:F062":
        return pua_map.get(key, "طرح")
    if key == "NOORIN08:F053":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F062":
            return "س"
        return None
    if key == "NOORIN12:F076":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        # گھاٹو / گھاٹا / گھا / گھائی / گھوڑ family; also بھوک.
        if nxt == "NOORIN81:F04E":
            return "گھا"
        if nxt == "NOORIN63:F0C3":
            return "گھا"
        if nxt == "NOORIN59:F0F0":
            return "گھوڑو"
        if nxt == "NOORIN57:F04B":
            return "گھائی"
        if nxt == "NOORIN01:F05E":
            return "گھا"
        if nxt == "NOORIN01:F059":
            return "ک"
        if prev == "NOORIN01:F056":
            return "گھاٹو "
        if prev == "NOORIN01:F07A" and nxt == "NOORIN57:F049":
            return "گھاٹو "
        if prev in ("NOORIN63:F0E2", "NOORIN05:F084") and nxt == "NOORIN57:F049":
            return "گھاٹو"
        if prev == "NOORIN63:F0C3" and nxt in (
            "NOORIN57:F049",
            "NOORIN01:F03A",
        ):
            return "گھاٹو"
        if prev in ("NOORIN48:F0F0", "NOORIN63:F0D0") or (
            prev == "NOORIN01:F07A" and nxt == "NOORIN01:F059"
        ):
            return "ک"
        if prev is None and nxt == "NOORIN81:F04E":
            return "گھا"
        return None
    if key == "NOORIN01:F05E":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F076":
            return "ٹ"
        return pua_map.get(key, "")
    if key == "NOORIN63:F0F0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F068" and nxt and nxt.endswith(":F06A"):
            return "ں"
        return pua_map.get(key, "من")
    if key == "NOORIN08:F06A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN05:F083":
            return "سکو"
        if prev == "NOORIN22:F037":
            return "اسکو"
        if prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return "اسکو"
        return pua_map.get(key, "اس")
    if key == "NOORIN06:F06A":
        return pua_map.get(key, "اس")
    if key == "NOORIN81:F09C":
        return pua_map.get(key, "صد")
    if key == "NOORIN82:F09A":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN48:F0EC":
            return "کڑی"
        if nxt == "NOORIN81:F07B":
            return "کھڑ"
        return pua_map.get(key, "کڑ")
    if key == "NOORIN56:F0DD":
        return pua_map.get(key, "صل")
    if key == "NOORIN05:F056":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN82:F02A" and nxt == "NOORIN11:F033":
            return "و"
        if prev == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C5":
            return "و"
        if prev == "NOORIN63:F0C7":
            return "و"
        if prev is None and nxt == "NOORIN01:F0D4":
            return "و"
        return pua_map.get(key, "پھل")
    if key == "NOORIN01:F0A7":
        return pua_map.get(key, "ر")
    if key == "NOORIN06:F06E":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F07D":
            return "لئے"
        return pua_map.get(key, "و")
    if key == "NOORIN27:F076":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN05:F04A":
            return "پنو نقصان"
        return pua_map.get(key, "نقصان")
    if key == "NOORIN05:F06E":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN05:F084":
            return "تباہی"
        if nxt == "NOORIN01:F07B":
            after = base_keys_after(run, i, pua_map, 2)
            if len(after) >= 2 and after[1] == "NOORIN81:F027":
                return "تباہ"
            return "تباہ"
        return pua_map.get(key, "تبا")
    if key == "NOORIN05:F084":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN05:F06E":
            return ""
        return pua_map.get(key, "گہنو")
    if key == "NOORIN81:F06C":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN48:F0F0":
            return "چڑ"
        return pua_map.get(key, "چر")
    if key == "NOORIN17:F081":
        if immediate_prev_base_key(run, i) == "NOORIN82:F026":
            return "تھی"
        return pua_map.get(key, "ھی")
    if key == "NOORIN25:F0A9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        inx = None
        for item in run[i + 1 :]:
            if is_overlay_font(item[3]):
                continue
            inx = map_key(item[3], item[4])
            break
        if prev == "NOORIN01:F067":
            return "ے"
        if prev == "NOORIN63:F0C5":
            if inx == "NOORIN01:F068":
                return "ڑ"
            return "ے"
        if prev == "NOORIN48:F0E2":
            return "ے"
        if prev == "NOORIN82:F03A":
            return "ی"
        if prev == "NOORIN01:F056":
            return "بھی"
        if prev == "NOORIN63:F0C3":
            return "ئ"
        if prev == "NOORIN06:F0BD":
            return "ے"
        if prev == "NOORIN63:F0E0":
            return ""
        if prev is None and inx == "NOORIN01:F056":
            return "وں"
        return pua_map.get(key, "ے")
    if key == "NOORIN13:F0FA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev in ("NOORIN63:F0C6", "NOORIN57:F058"):
            return "نماز"
        if prev == "NOORIN04:F02C":
            return "اں"
        if prev == "NOORIN63:F0C5":
            return "ے"
        if prev == "NOORIN01:F0D4":
            return ""
        if prev == "NOORIN01:F029":
            return "گ"
        if prev == "NOORIN57:F044":
            return "ے"
        if prev in ("NOORIN16:F07E", "NOORIN85:F0BE"):
            return ""
        if prev is None:
            return ""
        return pua_map.get(key, "ے")
    if key == "NOORIN01:F071":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN56:F0E7":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN81:F099":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F099":
            return ""
        if prev == "NOORIN01:F073":
            return ""
        if prev == "NOORIN01:F075":
            return "ڑ"
        if prev in ("NOORIN01:F07A", "NOORIN57:F059"):
            return "ڈ"
        if prev == "NOORIN81:F083":
            return "د"
        return pua_map.get(key, "ڈ")
    if key == "NOORIN09:F09A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        inx = None
        for item in run[i + 1 :]:
            if is_overlay_font(item[3]):
                continue
            inx = map_key(item[3], item[4])
            break
        if prev == "NOORIN01:F057" and inx == "NOORIN59:F0F1":
            return ""
        if prev == "NOORIN63:F0C5":
            return "ے"
        if prev == "NOORIN01:F057":
            return "ے"
        if prev == "NOORIN01:F07B":
            return "بلا"
        if prev == "NOORIN01:F07D":
            return "ا"
        if prev == "NOORIN82:F02A":
            return "ے"
        if prev == "NOORIN63:F0C6":
            return "و"
        if prev == "NOORIN63:F0D3":
            return "ے"
        if prev in ("NOORIN12:F0BF", "NOORIN01:F068"):
            return ""
        if prev is None:
            return ""
        return pua_map.get(key, "ے")
    if key == "NOORIN82:F02D":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F05A":
            return "ند"
        if prev == "NOORIN63:F0E2":
            return "ں"
        if prev == "NOORIN63:F0BB":
            return "ند"
        if prev in ("NOORIN09:F04A", "NOORIN07:F0EC"):
            return ""
        return pua_map.get(key, "ند")
    if key == "NOORIN54:F02A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F067":
            return "ے"
        if prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return ""
        if prev in ("NOORIN63:F0CF", "NOORIN07:F0A7", "NOORIN01:F03A") and nxt == "NOORIN01:F05A":
            return ""
        if prev is None and nxt == "NOORIN01:F05A":
            return ""
        if prev == "NOORIN01:F0D4" and nxt == "NOORIN08:F0B8":
            return ""
        if nxt == "NOORIN01:F05A":
            return "ے"
        return pua_map.get(key, "ے")
    if key == "NOORIN05:F061":
        before = base_keys_before(run, i, pua_map, 8)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN07:F071" or "NOORIN36:F081" in before or "NOORIN13:F035" in before:
            return "پیدا"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0D7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        inx = None
        for item in run[i + 1 :]:
            if is_overlay_font(item[3]):
                continue
            inx = map_key(item[3], item[4])
            break
        if prev == "NOORIN04:F0B8":
            return "ے"
        if ip == "NOORIN82:F02A" and inx == "NOORIN81:F021":
            return "ی"
        if ip == "NOORIN82:F02A" and nxt == "NOORIN01:F056":
            return "ں"
        if prev in ("NOORIN82:F04A", "NOORIN05:F0E5", "NOORIN70:F096") and nxt == "NOORIN01:F056":
            return ""
        if prev == "NOORIN81:F046":
            return ""
        if prev == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return "ے"
        return pua_map.get(key, "ے")
    if key == "NOORIN05:F0DF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        before = base_keys_before_full_row(run, i, row_all, pua_map, 8)
        if nxt == "NOORIN82:F099":
            if "NOORIN07:F0F4" in before or prev == "NOORIN01:F03B":
                return "تنگ"
            return "پھر"
        if nxt == "NOORIN05:F083" and prev == "NOORIN17:F0F2":
            return "تنگ"
        return pua_map.get(key, "")
    if key == "NOORIN57:F060":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F077" and nxt == "NOORIN77:F071":
            return "چن"
        return pua_map.get(key, "")
    if key == "NOORIN43:F0C3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        inx = None
        for item in run[i + 1 :]:
            if is_overlay_font(item[3]):
                continue
            inx = map_key(item[3], item[4])
            break
        if nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN05:F083" and nxt == "NOORIN57:F044":
            return "و"
        if prev == "NOORIN82:F099" and inx == "NOORIN81:F036":
            return "و"
        if prev == "NOORIN82:F099" and nxt == "NOORIN57:F044":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN05:F051":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev is None:
            return ""
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN85:F08A":
            return ""
        if prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F063":
            return "پھر"
        if prev == "NOORIN01:F03A" and nxt == "NOORIN01:F05A":
            return "پھر"
        if prev == "NOORIN01:F056" and nxt == "NOORIN48:F0E2":
            return "چ"
        if prev == "NOORIN22:F037" and nxt == "NOORIN04:F02D":
            return "و"
        if prev == "NOORIN57:F044" and nxt == "NOORIN01:F068":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN19:F03E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev is None and nxt == "NOORIN01:F07A":
            return "ب"
        if prev == "NOORIN01:F03A":
            if nxt == "NOORIN81:F036":
                return "پ"
            if nxt == "NOORIN85:F08A":
                return "د"
            if nxt == "NOORIN01:F07A":
                return "ھ"
            if nxt == "NOORIN01:F05A":
                return ""
            if nxt == "NOORIN04:F02D":
                return "و"
        if prev == "NOORIN01:F07A" and nxt == "NOORIN63:F0DF":
            return "پ"
        if prev == "NOORIN01:F056" and nxt == "NOORIN59:F0F0":
            return "ہ"
        if prev == "NOORIN01:F07A" and nxt == "NOORIN59:F0F0":
            return "ہ"
        if prev == "NOORIN82:F096" and nxt == "NOORIN01:F09B":
            return "د"
        if prev == "NOORIN01:F05C" and nxt == "NOORIN57:F044":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN82:F07E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F071":
            return "ق"
        if ip == "NOORIN48:F0EC" and nxt == "NOORIN01:F05A":
            return "ق"
        if ip == "NOORIN57:F037" and nxt == "NOORIN14:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F068":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN01:F03A":
            return "ں"
        if ip == "NOORIN85:F08A" and nxt == "NOORIN05:F084":
            return "ے"
        if ip == "NOORIN50:F071" and nxt == "NOORIN01:F058":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN61:F0CE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07B":
            return "دین"
        if ip == "NOORIN57:F022" and nxt == "NOORIN05:F084":
            return "د"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C6":
            return "دے"
        if ip == "NOORIN57:F044" and nxt == "NOORIN63:F0C6":
            return "ے"
        if ip == "NOORIN82:F0AA" and nxt == "NOORIN01:F067":
            return "ھ"
        if ip in ("NOORIN81:F036", "NOORIN50:F09B") and nxt == "NOORIN11:F087":
            return "ھیل"
        return pua_map.get(key, "")
    if key == "NOORIN08:F0F1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and nxt == "NOORIN63:F0C3":
            return "ے"
        if ip == "NOORIN57:F022":
            if nxt == "NOORIN48:F0EC":
                return " د"
            if nxt in ("NOORIN82:F099", "NOORIN63:F0C2"):
                return " دے"
        if ip == "NOORIN57:F044" and nxt == "NOORIN63:F0C5":
            return "ے"
        if ip == "NOORIN01:F03A":
            if nxt == "NOORIN01:F057":
                return ""
            if nxt in ("NOORIN82:F099", "NOORIN81:F028"):
                return " دے"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN82:F099":
            return " دے"
        if ip == "NOORIN41:F076" and nxt == "NOORIN01:F057":
            return " دے"
        if prev is None and nxt in (
            "NOORIN63:F0C3",
            "NOORIN63:F0C5",
            "NOORIN81:F028",
            "NOORIN01:F057",
            "NOORIN82:F072",
        ):
            return " دے"
        return pua_map.get(key, "")
    if key == "NOORIN15:F02E":
        return pua_map.get(key, "")
    if key == "NOORIN10:F088":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN82:F09A":
            return ""
        if prev is None and nxt == "NOORIN82:F09A":
            return ""
        if prev is None and nxt == "NOORIN22:F038":
            return "ب"
        if ip == "NOORIN01:F079" and nxt == "NOORIN01:F056":
            return "ی"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F059":
            return "ی"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F06C":
            return ""
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN01:F059":
            return " عاء"
        if ip == "NOORIN21:F0B3" and nxt == "NOORIN01:F059":
            return "عاء"
        if ip == "NOORIN21:F0B3" and nxt == "NOORIN04:F0B6":
            return "اء"
        if ip in ("NOORIN04:F0B6", "NOORIN01:F03A", "NOORIN01:F058") and nxt in (
            "NOORIN01:F059",
            "NOORIN04:F0B6",
        ):
            return "اء"
        return pua_map.get(key, "")
    if key == "NOORIN16:F08C":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN67:F0F0":
        return pua_map.get(key, "")
    if key == "NOORIN04:F0EA":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and neighbor_base_keys(run, i, pua_map)[1] == "NOORIN11:F0AD":
            return "ی"
        if ip == "NOORIN81:F037":
            _prev, nxt = neighbor_base_keys(run, i, pua_map)
            if nxt == "NOORIN01:F056":
                return "ا"
        if ip == "NOORIN01:F03A":
            _prev, nxt = neighbor_base_keys(run, i, pua_map)
            if nxt == "NOORIN63:F0D1":
                return "دھ"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0B4":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip is None:
            return "ہ"
        if ip == "NOORIN05:F043" and nxt == "NOORIN82:F091":
            return "ہ"
        if nxt == "NOORIN01:F060" and ip in ("NOORIN63:F0C3", "NOORIN59:F0F1"):
            return "ئ"
        return pua_map.get(key, "")
    if key == "NOORIN43:F042":
        ip = immediate_prev_base_key(run, i)
        if ip is None:
            return "ا"
        if ip == "NOORIN63:F0BB":
            return "م"
        return pua_map.get(key, "")
    if key == "NOORIN89:F036":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F058" and ip in ("NOORIN01:F067", "NOORIN16:F0C8"):
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN12:F031":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F056":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN05:F05E":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN81:F024" and nxt == "NOORIN01:F057":
            return "ا"
        if ip in ("NOORIN01:F07A", "NOORIN01:F07E") and nxt == "NOORIN63:F0E2":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN82:F0B5":
        return pua_map.get(key, "")
    if key == "NOORIN16:F07E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07B":
            return "ہ"
        if prev == "NOORIN63:F0C6" and nxt == "NOORIN25:F072":
            return "ہ"
        if prev == "NOORIN63:F0C1" and nxt == "NOORIN01:F05A":
            return "ہ"
        if prev == "NOORIN01:F067" and nxt is None:
            return "ے"
        if prev == "NOORIN01:F056" and nxt == "NOORIN82:F063":
            return "ے"
        if ip == "NOORIN01:F0D4":
            return ""
        if prev == "NOORIN56:F0D1" and nxt in ("NOORIN01:F03A", "NOORIN01:F058"):
            return ""
        if prev in ("NOORIN30:F03F", "NOORIN07:F027") or ip == "NOORIN01:F069":
            return ""
        if ip is None:
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F0EC":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip is None:
            return "ے"
        if ip == "NOORIN82:F063" and nxt == "NOORIN63:F0E0":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN10:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F03A":
            return "ے"
        if prev == "NOORIN01:F075" and nxt == "NOORIN81:F024":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN82:F037":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN57:F044" and nxt == "NOORIN81:F065":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN17:F05E":
        return pua_map.get(key, "")
    if key == "NOORIN13:F0C3":
        return pua_map.get(key, "")
    if key == "NOORIN81:F0AD":
        return pua_map.get(key, "")
    if key == "NOORIN08:F073":
        return pua_map.get(key, "")
    if key == "NOORIN10:F0D2":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F05A" and nxt in (
            "NOORIN63:F0D1",
            "NOORIN85:F08A",
            "NOORIN01:F0A5",
            "NOORIN08:F099",
            "NOORIN18:F09E",
            "NOORIN15:F0D3",
        ):
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN63:F0D3":
        return pua_map.get(key, "")
    if key == "NOORIN32:F061":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F099":
            return "ی"
        if ip == "NOORIN81:F059":
            before = []
            for j in range(i - 1, -1, -1):
                if is_overlay_font(run[j][3]):
                    continue
                before.append(map_key(run[j][3], run[j][4]))
                if len(before) == 2:
                    break
            if len(before) >= 2 and before[1] == "NOORIN11:F059":
                return "ں"
            return "ی"
        if ip == "NOORIN01:F078":
            return "نی"
        if ip == "NOORIN05:F083":
            return "ی"
        if ip == "NOORIN01:F061":
            return "ی"
        if ip == "NOORIN63:F0D1":
            return "ے"
        if ip == "NOORIN15:F04E":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F073":
        return pua_map.get(key, "")
    if key == "NOORIN12:F0D6":
        return pua_map.get(key, "")
    if key == "NOORIN18:F09E":
        return pua_map.get(key, "")
    if key == "NOORIN81:F057":
        return pua_map.get(key, "")
    if key == "NOORIN07:F0ED":
        return pua_map.get(key, "")
    if key == "NOORIN12:F0BF":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and kar_r_before(run, i):
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN89:F05A":
        return pua_map.get(key, "")
    if key == "NOORIN05:F063":
        ip = immediate_prev_base_key(run, i)
        if ip is None or ip == "NOORIN05:F063":
            return ""
        if ip == "NOORIN05:F045":
            return "یر"
        if ip in (
            "NOORIN05:F043",
            "NOORIN01:F075",
            "NOORIN63:F0C6",
            "NOORIN63:F0C3",
            "NOORIN05:F084",
            "NOORIN01:F0D4",
            "NOORIN63:F0BB",
            "NOORIN81:F036",
            "NOORIN63:F0D1",
            "NOORIN01:F07E",
            "NOORIN04:F02C",
            "NOORIN82:F071",
            "NOORIN01:F029",
        ):
            return ""
        if ip in ("NOORIN01:F056", "NOORIN16:F07D", "NOORIN17:F0F2"):
            return "یر"
        if ip == "NOORIN01:F07B":
            return ""
        return pua_map.get(key, "یر")
    if key == "NOORIN04:F0E9":
        return pua_map.get(key, "")
    if key == "NOORIN04:F0CE":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CE":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN20:F06E":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN63:F0F3":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F066" and nxt == "NOORIN30:F06C":
            return "د"
        if ip == "NOORIN01:F066":
            return ""
        if ip == "NOORIN01:F05A" and nxt in ("NOORIN01:F05A", "NOORIN01:F067"):
            return "د"
        if ip == "NOORIN15:F06C":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F063":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN63:F0F1" and nxt == "NOORIN15:F06C":
            return "ڑ"
        if ip == "NOORIN63:F0F1" and nxt == "NOORIN81:F021":
            return ""
        if prev in ("NOORIN01:F07A", "NOORIN01:F07E") or ip in (
            "NOORIN01:F07A",
            "NOORIN01:F07E",
        ):
            return "و"
        if ip is None:
            return ""
        if ip in ("NOORIN01:F0AF", "NOORIN05:F0E2", "NOORIN82:F025"):
            return ""
        if ip == "NOORIN01:F05A" and nxt == "NOORIN07:F071":
            return "و"
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F0B8":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN81:F021" and nxt == "NOORIN01:F056":
            return "ا"
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN82:F064":
            return "ب"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN82:F054":
            return "ب"
        if ip == "NOORIN01:F056" and nxt == "NOORIN82:F085":
            return "ب"
        if ip == "NOORIN01:F07D" and nxt == "NOORIN82:F085":
            return "ب"
        if ip == "NOORIN56:F0CE":
            return ""
        if ip == "NOORIN01:F029" and nxt == "NOORIN82:F085":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F04E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F068":
            if ip is None:
                return "کار"
            if prev == "NOORIN63:F0BB":
                return "ر"
            return pua_map.get(key, "")
        return pua_map.get(key, "")
    if key == "NOORIN15:F06C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN63:F0F1" and nxt == "NOORIN01:F078":
            return "ے"
        if prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F078":
            return "غ"
        if prev == "NOORIN11:F058" and nxt == "NOORIN01:F06B":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN44:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN22:F037":
            if nxt in ("NOORIN01:F058", "NOORIN57:F044"):
                return "رہندے"
            if nxt is None:
                return "گرتو"
        if prev == "NOORIN56:F0D0" and nxt == "NOORIN22:F037":
            return "گرتو"
        return pua_map.get(key, "")
    if key == "NOORIN29:F04F":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A":
            return "ہ"
        if ip == "NOORIN01:F067":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN15:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0D1":
            return ""
        if ip is None and nxt == "NOORIN57:F044":
            return "و"
        if ip is None and nxt == "NOORIN63:F0F1":
            return "و"
        if prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F056":
            return "و"
        if prev == "NOORIN22:F037" and nxt == "NOORIN57:F044":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN07:F0A7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05B" and nxt == "NOORIN01:F05D":
            return "و"
        if ip == "NOORIN01:F078" and nxt in ("NOORIN81:F059", "NOORIN07:F0BB"):
            return "یں"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN57:F043":
            return "ی"
        if ip == "NOORIN81:F0A7" and nxt in ("NOORIN54:F02A", "NOORIN82:F03A"):
            return "ح"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN57:F043":
            return "ی"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN82:F099":
            return " "
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN01:F057":
            return ""
        if ip == "NOORIN82:F02A" and nxt == "NOORIN01:F057":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN26:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and nxt == "NOORIN01:F056":
            return "و"
        if ip == "NOORIN01:F05C" and nxt == "NOORIN57:F044":
            return "ں"
        if ip == "NOORIN14:F07A" and nxt == "NOORIN01:F057":
            return "و"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN01:F07A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN69:F085":
        return "۔"
    if key == "NOORIN23:F074":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return "ے"
        if ip == "NOORIN81:F028" and nxt == "NOORIN82:F099":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN28:F0F1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and nxt in (
            "NOORIN81:F08E",
            "NOORIN82:F099",
            "NOORIN63:F0C1",
        ):
            return "،"
        if ip == "NOORIN01:F03A" and nxt in ("NOORIN82:F02A", "NOORIN01:F057"):
            return " "
        if ip == "NOORIN57:F044" and nxt in ("NOORIN82:F099", "NOORIN22:F037"):
            return " "
        if ip == "NOORIN82:F074" and nxt == "NOORIN82:F02A":
            return " "
        if ip == "NOORIN01:F07D" and nxt == "NOORIN01:F07A":
            return " "
        return pua_map.get(key, "")
    if key == "NOORIN35:F0C6":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F05A":
            if nxt == "NOORIN81:F021":
                return "ب"
            if nxt == "NOORIN81:F0AA":
                return " "
            if nxt is None:
                return "ے"
            if nxt == "NOORIN06:F027":
                return "ے"
            if nxt == "NOORIN81:F036":
                return "ے"
            if nxt == "NOORIN48:F0E3":
                return "ے"
            if nxt == "NOORIN81:F059":
                return "ن"
            if nxt == "NOORIN22:F037":
                return "ے"
            if nxt == "NOORIN01:F05A":
                return "ے"
            if nxt == "NOORIN01:F07A":
                return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN11:F051":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN63:F0C3", "NOORIN63:F0CD") and nxt == "NOORIN01:F07A":
            return "ے"
        if ip == "NOORIN41:F076" and nxt == "NOORIN01:F05A":
            return " "
        if ip == "NOORIN82:F030" and nxt == "NOORIN82:F099":
            return " "
        if ip == "NOORIN01:F056" and nxt == "NOORIN01:F05A":
            return " "
        if ip == "NOORIN01:F05D" and nxt == "NOORIN63:F0C6":
            return " "
        return pua_map.get(key, "")
    if key == "NOORIN41:F032":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN08:F024" and nxt == "NOORIN48:F0E2":
            return "و"
        if ip == "NOORIN61:F0D5" and nxt == "NOORIN48:F0E3":
            return "و"
        if ip == "NOORIN06:F08F" and nxt == "NOORIN01:F07A":
            return "و"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN82:F02A" and nxt == "NOORIN63:F0C2":
            return "ے"
        if ip == "NOORIN01:F061" and nxt == "NOORIN48:F0E3":
            return "و"
        if ip == "NOORIN82:F064" and nxt == "NOORIN48:F0E3":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN06:F0E5":
        return "ے"
    if key == "NOORIN08:F03F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN04:F0DB":
            return ""
        if ip is None and nxt == "NOORIN81:F021":
            return "ا"
        if ip is None and nxt == "NOORIN01:F029":
            return ""
        if ip == "NOORIN48:F0E3" and nxt == "NOORIN63:F0C5":
            return "ے"
        if ip == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return ""
        if ip == "NOORIN82:F02A" and nxt == "NOORIN06:F027":
            return "و"
        if ip == "NOORIN81:F036" and nxt == "NOORIN01:F099":
            return "ا"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN85:F08A":
            return " "
        if ip == "NOORIN01:F03A" and nxt == "NOORIN81:F021":
            return "ا"
        if ip == "NOORIN82:F038" and nxt == "NOORIN82:F02A":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN30:F044":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN81:F093":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN19:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt in ("NOORIN63:F0C3", "NOORIN63:F0C5"):
            return ""
        if ip is None and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN48:F0EC":
            return "ا"
        if ip == "NOORIN82:F02A" and nxt == "NOORIN05:F083":
            return "ا"
        if ip == "NOORIN05:F04B" and nxt == "NOORIN82:F063":
            return "ا"
        if ip == "NOORIN07:F071" and nxt == "NOORIN82:F099":
            return "وں"
        if ip == "NOORIN82:F03A" and nxt == "NOORIN82:F099":
            return "اں"
        if ip == "NOORIN27:F095" and nxt == "NOORIN17:F0E7":
            return "ا"
        if ip == "NOORIN01:F058" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN41:F0AF":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN31:F06F":
        return "و"
    if key == "NOORIN08:F0B0":
        return "،"
    if key == "NOORIN63:F0B5":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0F1":
            return "ٹ"
        return pua_map.get(key, "")
    if key == "NOORIN18:F02B":
        ip = immediate_prev_base_key(run, i)
        if ip is None:
            return "ا"
        if ip in ("NOORIN48:F0F0", "NOORIN01:F03A", "NOORIN17:F0F2"):
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F083":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip in ("NOORIN01:F0D4", "NOORIN81:F064", "NOORIN81:F083") and nxt == "NOORIN01:F056":
            return "و"
        if ip is None:
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F096":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip in ("NOORIN01:F0D4", "NOORIN01:F05D") and nxt == "NOORIN07:F067":
            return " "
        if ip == "NOORIN16:F08B":
            return "،"
        if ip is None:
            if nxt == "NOORIN01:F05A":
                return "ر"
            if nxt in ("NOORIN82:F02A", "NOORIN01:F099"):
                return "ن"
            if nxt == "NOORIN63:F0C3":
                return "ک"
            if nxt in ("NOORIN63:F0BB", "NOORIN08:F0E0"):
                return "ک"
            return " "
        if ip == "NOORIN82:F071" and nxt == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN14:F0F7":
            return " "
        return pua_map.get(key, "")
    if key == "NOORIN50:F071":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN81:F0A2":
            return "ھ"
        if nxt == "NOORIN01:F058" and ip == "NOORIN17:F0C5":
            return "ی"
        if nxt == "NOORIN47:F095":
            return ""
        if nxt is None:
            return "ے"
        if ip is None:
            if nxt in ("NOORIN47:F08D", "NOORIN63:F0E2"):
                return "ے"
            if nxt == "NOORIN83:F0D7":
                return " "
        if nxt == "NOORIN57:F044":
            return " "
        return pua_map.get(key, "")
    if key == "NOORIN04:F0AB":
        return "ے"
    if key == "NOORIN04:F0B6":
        return "۔"
    if key == "NOORIN04:F02A":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN82:F08A" and nxt in ("NOORIN01:F058", "NOORIN63:F0B8", "NOORIN48:F0EC"):
            return "ے"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN57:F021":
            return "ی"
        if ip == "NOORIN15:F0C6" and nxt == "NOORIN01:F07A":
            return "ے"
        if ip == "NOORIN01:F031" and nxt == "NOORIN01:F065":
            return "ی"
        return pua_map.get(key, "")
    if key in ("NOORIN01:F032", "NOORIN01:F039", "NOORIN01:F031", "NOORIN01:F030"):
        return ""
    if key == "NOORIN54:F0AB":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F067":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN24:F0D6":
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN01:F065", "NOORIN01:F09F"):
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0F4":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN63:F0D1":
            return "ر"
        if ip == "NOORIN01:F065":
            return "ڑ"
        return pua_map.get(key, "")
    if key == "NOORIN57:F062":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F0D4":
            return "ی"
        if ip == "NOORIN01:F067":
            return "و"
        if ip == "NOORIN01:F0A7" and nxt == "NOORIN63:F0D1":
            return "و"
        if ip == "NOORIN01:F0A7" and nxt in ("NOORIN01:F057", "NOORIN63:F0C3"):
            return "ہ"
        if ip == "NOORIN01:F0A7":
            return ""
        if ip == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F037":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN14:F0C5":
            return "ی"
        if ip == "NOORIN81:F036":
            return "ے"
        if ip == "NOORIN57:F061":
            return "ئ"
        if ip == "NOORIN06:F027":
            return "ھ"
        if ip in ("NOORIN01:F03A", None) and nxt in (
            "NOORIN01:F07A",
            "NOORIN63:F0C9",
        ):
            return "ی"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C9":
            return "ی"
        if ip == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F07D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev is None:
            return "غ"
        if ip == "NOORIN01:F057" and nxt == "NOORIN01:F021":
            return "ک"
        if prev == "NOORIN01:F075":
            return "ڑ"
        if prev == "NOORIN14:F0BE":
            return "ے"
        if ip == "NOORIN01:F069" and nxt == "NOORIN01:F029":
            return "ک"
        if ip == "NOORIN01:F03A":
            return "غ"
        return pua_map.get(key, "")
    if key == "NOORIN01:F0AD":
        return "ے"
    if key == "NOORIN39:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN46:F037":
            return "ل"
        if prev == "NOORIN19:F0A9":
            return "ل"
        if ip == "NOORIN01:F05A" and nxt in ("NOORIN63:F0DF", "NOORIN01:F077"):
            return "پ"
        if ip is None and nxt == "NOORIN63:F0E0":
            return "ے"
        if ip in ("NOORIN01:F05C", "NOORIN01:F06C") and nxt == "NOORIN11:F087":
            return "ن"
        if ip == "NOORIN05:F04A" and nxt == "NOORIN63:F0DF":
            return "پ"
        if nxt == "NOORIN01:F077" and ip in ("NOORIN82:F02A", "NOORIN14:F0B4"):
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN13:F033":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN13:F0B6":
            return ""
        if ip in ("NOORIN14:F0B9", "NOORIN08:F0D1", "NOORIN82:F0A5"):
            return "و"
        if ip == "NOORIN81:F059" and nxt == "NOORIN01:F0D4":
            return "ے"
        if ip == "NOORIN81:F059" and nxt == "NOORIN01:F058":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN15:F02B":
        ip = immediate_prev_base_key(run, i)
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F05A" and nxt in ("NOORIN11:F033", "NOORIN12:F079"):
            return "ڑ"
        if ip == "NOORIN17:F03E":
            return "ڑ"
        if ip == "NOORIN85:F08A":
            return "ے"
        if ip == "NOORIN01:F07A":
            return "ے"
        if ip == "NOORIN81:F036":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN66:F04F":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F078":
            return "اں"
        if ip in ("NOORIN63:F0C3", "NOORIN82:F03A", "NOORIN81:F064", "NOORIN22:F037"):
            return ""
        return pua_map.get(key, "")

    if key == "NOORIN74:F0A2":
        return "ں"
    if key == "NOORIN57:F05F":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN63:F0C5":
            return "کی"
        if nxt == "NOORIN63:F0D1":
            return "لارہنو"
        if nxt == "NOORIN22:F037":
            return "نہیں"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0B3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2":
            return "زھز"
        if ip == "NOORIN01:F056" and nxt == "NOORIN01:F07D":
            return "پ"
        if ip == "NOORIN63:F0C3":
            return "ھ"
        if ip == "NOORIN57:F04B":
            return "ھ"
        if ip == "NOORIN04:F02C" and nxt == "NOORIN04:F02C":
            return ""
        if ip == "NOORIN81:F040":
            return "ھ"
        if ip is None and nxt == "NOORIN81:F037":
            return "پ"
        return pua_map.get(key, "")
    if key == "NOORIN11:F0A7":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065":
            return "ں"
        if ip == "NOORIN59:F0F6":
            return "نا"
        if ip in ("NOORIN01:F03A", None):
            return "ن"
        return pua_map.get(key, "ن")
    if key == "NOORIN14:F045":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F02D" and nxt == "NOORIN01:F067":
            return "اک"
        if ip in ("NOORIN52:F0F2", "NOORIN01:F028") and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN01:F057" and nxt == "NOORIN01:F058":
            return "ے"
        if ip == "NOORIN57:F075" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F056" and nxt == "NOORIN01:F07A":
            return "ں"
        if ip == "NOORIN81:F030" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN72:F0B4" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN01:F021":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and nxt == "NOORIN01:F028":
            return ""
        if ip in (
            "NOORIN01:F06C", "NOORIN59:F0F1", "NOORIN06:F037",
            "NOORIN01:F079", "NOORIN01:F07B", "NOORIN82:F099",
        ):
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN48:F0F6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F03B":
            return "ے"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN29:F052":
            return "ں"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN63:F0C6":
            return "ک"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN01:F057":
            return "آ"
        return pua_map.get(key, "")
    if key == "NOORIN06:F029":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F07B":
            return "ھ"
        if ip == "NOORIN63:F0E2":
            return "ر"
        if ip == "NOORIN63:F0C5":
            return "ت"
        if ip == "NOORIN57:F022":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN10:F08F":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN82:F08A":
            return "قد"
        if nxt == "NOORIN82:F064":
            return "ریب"
        return pua_map.get(key, "ریب")
    if key == "NOORIN56:F0DC":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F073":
            return "فر"
        if nxt == "NOORIN82:F099":
            return "کر"
        return pua_map.get(key, "")
    if key == "NOORIN08:F06D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F053":
            return "ر"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN85:F08A":
            return "ہ"
        if ip in ("NOORIN01:F051", "NOORIN01:F068"):
            return "ہ"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C9":
            return "گ"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN76:F027":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F040" and nxt == "NOORIN14:F0A3":
            return "ک"
        if ip == "NOORIN11:F059" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN17:F0E1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN08:F057" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN08:F057":
            return "ن"
        if ip == "NOORIN01:F07D" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0B0":
            return "ف"
        return pua_map.get(key, "")
    if key == "NOORIN61:F08C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E2" and nxt == "NOORIN01:F0D4":
            return "،"
        if ip == "NOORIN05:F084" and nxt == "NOORIN01:F03A":
            return ":"
        if nxt in ("NOORIN01:F058", None):
            return "۔"
        return pua_map.get(key, "۔")
    if key == "NOORIN06:F0E4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and nxt == "NOORIN82:F099":
            return "ے"
        if ip == "NOORIN01:F057" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN16:F0C9":
            return "ھ"
        if ip == "NOORIN01:F05D" and nxt == "NOORIN06:F090":
            return "ے"
        if ip == "NOORIN01:F05D" and nxt == "NOORIN01:F0D4":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN57:F042":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F082" and nxt == "NOORIN01:F03A":
            return "یر"
        if ip == "NOORIN81:F082" and nxt in ("NOORIN85:F08A", "NOORIN56:F0CE"):
            return "دی"
        if ip == "NOORIN82:F03B":
            return "ال"
        if ip == "NOORIN01:F067":
            return "ون"
        return pua_map.get(key, "")
    if key == "NOORIN73:F0EE":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN12:F042":
            return "بول"
        if nxt == "NOORIN01:F07A":
            return "ھ"
        if nxt == "NOORIN01:F05A":
            return "ر"
        if nxt == "NOORIN89:F079":
            return "خ"
        return pua_map.get(key, "")
    if key == "NOORIN16:F06E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN17:F0E7" and nxt == "NOORIN63:F0C5":
            return "کی"
        if ip == "NOORIN17:F0E7":
            return "ما"
        if ip == "NOORIN01:F057":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN22:F098":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3":
            return "ے"
        if ip is None and nxt == "NOORIN63:F0E0":
            return "ے"
        if ip in (None, "NOORIN63:F0C5") and nxt == "NOORIN57:F059":
            return "ب"
        if ip == "NOORIN63:F0BB":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN57:F077":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044":
            return "و"
        if ip == "NOORIN08:F04A":
            return "ت"
        if ip == "NOORIN01:F078":
            return "ع"
        if ip == "NOORIN63:F0C5":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN41:F0B1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F065":
            return "ہ"
        if ip == "NOORIN01:F07B":
            return "ر"
        if ip in ("NOORIN82:F02A", "NOORIN05:F056"):
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN82:F05E":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059":
            return "نا"
        return pua_map.get(key, "نا")
    if key == "NOORIN05:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F074":
            return "ک"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN63:F0B9":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN57:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056":
            return "ت"
        if ip == "NOORIN57:F04A":
            return "ی"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN12:F0F3":
            return "و"
        if ip is None:
            return "د"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN18:F0A9":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN05:F0EA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN13:F0E6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN17:F0EC":
            return "ے"
        if ip == "NOORIN01:F067":
            return "ے"
        if ip == "NOORIN01:F07A":
            return "ی"
        if ip == "NOORIN01:F053":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN11:F06D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A":
            return "ی" if nxt == "NOORIN63:F0E2" else "ھ"
        if ip == "NOORIN81:F024" and nxt == "NOORIN05:F084":
            return "ب"
        if ip == "NOORIN81:F024":
            return "ے"
        if ip == "NOORIN81:F030":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN57:F064":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CE" and nxt == "NOORIN01:F0D4":
            return "و"
        if ip == "NOORIN56:F0CE":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN15:F050":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F0D4":
            return "ی"
        if nxt == "NOORIN01:F058":
            return "و"
        if nxt == "NOORIN01:F066":
            return "ا"
        if nxt == "NOORIN01:F07A":
            return "ے"
        if nxt == "NOORIN16:F06F":
            return "ن"
        return pua_map.get(key, "")
    if key == "NOORIN05:F082":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067":
            return "ر"
        if ip == "NOORIN81:F06D":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN17:F097":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN05:F084", "NOORIN57:F044", "NOORIN06:F044"):
            return "ب"
        if ip == "NOORIN82:F04A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN08:F0BA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN01:F0A7":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN82:F095":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F027":
            return "ن"
        if ip == "NOORIN82:F095" and nxt == "NOORIN81:F059":
            return "ن"
        return pua_map.get(key, "ن")
    if key == "NOORIN76:F084":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3":
            return "و"
        if ip == "NOORIN19:F025":
            return "ں"
        if ip == "NOORIN57:F044":
            return "و"
        if ip == "NOORIN01:F067":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN58:F0ED":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F04B":
            return "ل"
        if ip == "NOORIN81:F036":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN10:F029":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F079":
            return "و"
        if ip == "NOORIN63:F0D1":
            return "و"
        if ip == "NOORIN01:F067":
            return "ے"
        if ip == "NOORIN81:F0AD":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0E2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056":
            return "د"
        return pua_map.get(key, "د")
    if key == "NOORIN17:F083":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F030" and nxt == "NOORIN01:F05A":
            return "ک"
        if ip == "NOORIN82:F030" and nxt == "NOORIN22:F037":
            return "ند"
        if ip == "NOORIN82:F030":
            return "ند"
        if ip == "NOORIN01:F065":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN31:F083":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN17:F0F2":
            return "ہ"
        if ip == "NOORIN01:F056":
            return "ں"
        if ip in ("NOORIN82:F0AA", "NOORIN01:F079"):
            return "ئ"
        if ip == "NOORIN01:F077":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN48:F0E9":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A":
            return "ش"
        return pua_map.get(key, "ش")
    if key == "NOORIN16:F0B2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and nxt == "NOORIN63:F0C3":
            return "د"
        if ip == "NOORIN85:F08A" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN81:F025":
            return "ڈ"
        return pua_map.get(key, "")
    if key == "NOORIN05:F099":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A":
            return "ے"
        if ip in ("NOORIN31:F07D", "NOORIN81:F021"):
            return "ا"
        if ip is None or ip == "NOORIN01:F0D4":
            return "ا"
        if ip == "NOORIN63:F0C3":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN19:F0C2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN63:F0D1":
            return "ر"
        if ip is None and nxt == "NOORIN63:F0C2":
            return "ے"
        if ip == "NOORIN01:F0D4" and nxt in ("NOORIN63:F0D1", "NOORIN81:F061"):
            return "د" if nxt == "NOORIN81:F061" else "ر"
        if ip == "NOORIN01:F077" and nxt == "NOORIN81:F061":
            return "د"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0C2":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN13:F076":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A":
            return "ے"
        if ip == "NOORIN01:F09B":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0C9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB":
            return "ں"
        if ip == "NOORIN63:F0C7":
            return "ں"
        if ip == "NOORIN57:F044" and nxt == "NOORIN25:F077":
            return "ے"
        if ip == "NOORIN57:F044":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN14:F033":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN32:F085":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059":
            return "ال"
        return pua_map.get(key, "ب")
    if key == "NOORIN63:F031":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E3":
            return "ر"
        if ip == "NOORIN01:F056":
            return "ز"
        if ip == "NOORIN63:F0C5":
            return "ے"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN82:F063":
            return "ر"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0E2":
            return "ے"
        if ip == "NOORIN01:F03A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN82:F041":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A":
            return "ل"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN22:F037":
            return "ں"
        if ip == "NOORIN04:F02C":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN51:F0EF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN01:F07A":
            return "م"
        if ip is None and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN48:F0E4":
            return "ی"
        if ip == "NOORIN57:F044":
            return "و"
        if ip == "NOORIN05:F04B":
            return "ہ"
        if ip == "NOORIN01:F07B":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN07:F051":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F077":
            return "ی"
        if ip == "NOORIN59:F0F1":
            return "ے"
        if ip == "NOORIN05:F04A":
            return "ی"
        if ip is None:
            return "ی"
        return pua_map.get(key, "ے")
    if key == "NOORIN08:F07C":
        return pua_map.get(key, "ے")
    if key == "NOORIN10:F0CB":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "ر")
    if key == "NOORIN11:F030":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None:
            return "ے"
        if ip == "NOORIN28:F070":
            return "ے"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN82:F02A":
            return "ن"
        if ip == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F07E":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN11:F04F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN63:F0F2":
            return "ا"
        if ip in ("NOORIN01:F03A", None):
            return "ہ"
        if ip == "NOORIN05:F04B":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN29:F05B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN17:F0EC":
            return "ت"
        if ip == "NOORIN18:F076":
            return "ہ"
        if ip == "NOORIN01:F079":
            return "ب"
        if ip == "NOORIN01:F077":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN63:F0DE":
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN57:F031", "NOORIN39:F065", "NOORIN81:F024"):
            return "ے"
        return "ر"
    if key == "NOORIN34:F024":
        return pua_map.get(key, "ق")
    if key == "NOORIN83:F0CB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN34:F024" and nxt == "NOORIN81:F036":
            return "پاس"
        return pua_map.get(key, "۔")


    if key == "NOORIN82:F0A2":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F040":
            return "ت"
        if ip in ("NOORIN15:F024", "NOORIN57:F044", "NOORIN15:F059"):
            return "ت"
        if ip == "NOORIN41:F076":
            return "ر"
        if ip == "NOORIN01:F067":
            return "ے"
        if ip is None:
            return "ت"
        if ip == "NOORIN80:F031":
            return "ک"
        if ip == "NOORIN06:F0D6":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN20:F0F1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F0C7":
            return " "
        if ip == "NOORIN63:F0C6":
            return "،"
        if ip == "NOORIN01:F079" and nxt == "NOORIN01:F03A":
            return " "
        return pua_map.get(key, "")
    if key == "NOORIN85:F083":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN11:F033":
            return "ت"
        if ip == "NOORIN63:F0F1":
            return "ر"
        if nxt is None:
            return ""
        if ip == "NOORIN48:F0F0":
            return "ں"
        if ip == "NOORIN10:F0CD":
            return "ھ"
        if ip == "NOORIN09:F09A":
            return "ی"
        if ip == "NOORIN15:F098":
            return "ں"
        if ip == "NOORIN01:F065":
            return "ی"
        if ip == "NOORIN81:F059" and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN13:F0A5":
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN63:F0BB", "NOORIN01:F075"):
            return " پر"
        return "ر"
    if key == "NOORIN21:F0AD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0DD":
            return "ت"
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN01:F07A":
            return "ھے"
        if ip == "NOORIN06:F05F":
            return "د"
        if ip == "NOORIN05:F04B":
            return ""
        if ip is None:
            return "ل"
        if ip == "NOORIN01:F077":
            return "ن"
        if ip == "NOORIN82:F02A" and nxt == "NOORIN14:F0EA":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN82:F070":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0D1" and neighbor_base_keys(run, i, pua_map)[1] == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN05:F0B0":
            return "ہو"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0F3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN01:F053", "NOORIN32:F0B3"):
            return "د"
        if ip == "NOORIN63:F0CD":
            return "ر"
        if ip == "NOORIN01:F05A":
            if nxt == "NOORIN01:F067":
                return "ک"
            if nxt == "NOORIN01:F056":
                return "ں"
        if ip in ("NOORIN56:F0CE", "NOORIN01:F051"):
            return "گ"
        if ip == "NOORIN01:F0D4":
            if nxt == "NOORIN11:F096":
                return "ب"
            if nxt == "NOORIN09:F062":
                return "ھ"
        if ip == "NOORIN36:F0B7":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0C9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F088":
            return "ئ"
        if ip == "NOORIN01:F07E":
            return "ب"
        if ip is None:
            if nxt == "NOORIN01:F05A":
                return "ر"
            if nxt in ("NOORIN63:F0CD", "NOORIN48:F0E4"):
                return "گ"
            if nxt == "NOORIN63:F0BB":
                return "ک"
            if nxt == "NOORIN82:F02A":
                return "س"
        if ip == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN01:F06C":
            return "ں"
        if ip in ("NOORIN59:F0F0", "NOORIN12:F088"):
            return "ئ"
        return pua_map.get(key, "")
    if key == "NOORIN12:F074":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and nxt == "NOORIN01:F03A":
            return ":"
        if ip == "NOORIN04:F0C8":
            return "،"
        if ip == "NOORIN01:F05A":
            return "۔"
        if ip in ("NOORIN48:F0E9", "NOORIN21:F0EC"):
            return "ن"
        if ip is None and nxt == "NOORIN01:F03A":
            return "ن"
        return pua_map.get(key, "")
    if key == "NOORIN06:F08D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F079" and nxt == "NOORIN48:F0E2":
            return "و"
        if ip == "NOORIN01:F079" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN01:F07E" and nxt == "NOORIN48:F0E3":
            return "نی"
        if ip == "NOORIN82:F02A":
            return "ے"
        if ip == "NOORIN57:F068":
            if nxt == "NOORIN08:F06E":
                return "سے"
            return "ے"
        if ip == "NOORIN01:F067" and nxt == "NOORIN48:F0E3":
            return "نی"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0EC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN85:F08A":
            if nxt == "NOORIN01:F03A":
                return "د:"
            if nxt in ("NOORIN01:F058", "NOORIN01:F0D4"):
                return "د"
        if prev == "NOORIN06:F05D":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN61:F03B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6":
            return "درج"
        if ip == "NOORIN82:F053":
            return "ت"
        if ip in ("NOORIN01:F07E", "NOORIN01:F028", "NOORIN82:F02A") and nxt in (
            "NOORIN63:F0C2",
            "NOORIN01:F03A",
        ):
            return ":"
        if ip == "NOORIN57:F044":
            return "کھ"
        if ip == "NOORIN01:F07B":
            return "ل"
        if ip == "NOORIN11:F02C":
            return "("
        return pua_map.get(key, "")
    if key == "NOORIN19:F03F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F058":
            return "۔"
        if ip is None and nxt == "NOORIN01:F05A":
            return "ر"
        if nxt == "NOORIN81:F067":
            return " "
        if nxt == "NOORIN85:F08A":
            return "د"
        if nxt == "NOORIN11:F059":
            return " "
        if nxt == "NOORIN01:F029":
            return "("
        if nxt == "NOORIN01:F03A":
            return " "
        return pua_map.get(key, "")
    if key == "NOORIN52:F0B9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt is None:
            return "ر"
        if ip == "NOORIN01:F058":
            return "ھے"
        if nxt == "NOORIN57:F044":
            return "تھے"
        if nxt == "NOORIN27:F086":
            return "تھے"
        if nxt == "NOORIN81:F021":
            return "ب"
        if nxt == "NOORIN05:F083":
            return "ہو"
        if ip is None:
            return "تھے"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0C1":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt is None:
            return ""
        if ip is None:
            if nxt == "NOORIN04:F0BD":
                return "ر"
            if nxt == "NOORIN63:F0D1":
                return "لا"
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN63:F0D1":
            return "لا"
        if ip == "NOORIN01:F0D4":
            return " "
        if nxt == "NOORIN06:F046":
            return "ل"
        if ip == "NOORIN81:F036":
            return "کے"
        return pua_map.get(key, "")
    if key == "NOORIN11:F02E":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0D0":
            return "و"
        if ip in ("NOORIN81:F021", "NOORIN18:F08D", "NOORIN05:F059", "NOORIN01:F028"):
            return "ہ"
        if ip == "NOORIN63:F0CD":
            return "کے"
        if neighbor_base_keys(run, i, pua_map)[1] == "NOORIN01:F03A":
            return ":"
        if ip == "NOORIN56:F0CE":
            return "لو"
        if ip == "NOORIN01:F029":
            return ":"
        return pua_map.get(key, "")
    if key == "NOORIN51:F0C2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN05:F083":
            return "ہوں"
        if nxt in ("NOORIN63:F0E2", "NOORIN82:F02A"):
            return "نال"
        if nxt == "NOORIN57:F069":
            return "یار"
        if nxt == "NOORIN82:F063":
            return "ی"
        if nxt == "NOORIN85:F068":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0A9":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip is None:
            if nxt == "NOORIN63:F0BB":
                return "ک"
            if nxt == "NOORIN04:F0CC":
                return "ب"
            if nxt in ("NOORIN48:F0E4", "NOORIN82:F02A"):
                return "س"
        if ip == "NOORIN01:F079":
            return "ھ"
        if ip == "NOORIN63:F0E1":
            return "م"
        if ip == "NOORIN57:F044":
            return "پ"
        if ip == "NOORIN63:F0C6":
            return "چ"
        return pua_map.get(key, "")
    if key == "NOORIN41:F02D":
        return "ے"
    if key == "NOORIN19:F0DF":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip is None:
            if nxt == "NOORIN85:F08A":
                return "دل"
            if nxt == "NOORIN63:F0C5":
                return "کی"
            if nxt == "NOORIN63:F0E2":
                return "ماں"
            if nxt == "NOORIN82:F02A":
                return "نام"
            if nxt == "NOORIN18:F076":
                return ""
        if ip == "NOORIN01:F021":
            return "ر"
        if ip == "NOORIN57:F044":
            return "ھ"
        if ip == "NOORIN63:F0C3":
            return ""
        if ip == "NOORIN01:F0D4":
            return "کو"
        return pua_map.get(key, "")
    if key == "NOORIN07:F0BB":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN19:F0B9" and neighbor_base_keys(run, i, pua_map)[1] == "NOORIN22:F037":
            return "نہیں"
        if ip in ("NOORIN81:F083", "NOORIN26:F06B"):
            return "ہوننو"
        return "ہونی"
    if key == "NOORIN18:F072":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3":
            return "ئ"
        if ip == "NOORIN01:F05A":
            return "نی"
        return pua_map.get(key, "")
    if key == "NOORIN81:F084":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F0D4":
            return "،"
        if ip is None:
            if nxt == "NOORIN81:F036":
                return "پر"
            if nxt == "NOORIN05:F064":
                return "ھی"
            if nxt == "NOORIN27:F02E":
                return ""
        if nxt == "NOORIN81:F027":
            return "ز"
        if ip == "NOORIN63:F0C5":
            return "ب"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN06:F0BD":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN22:F037":
            return "نی"
        if ip == "NOORIN82:F02A" and nxt == "NOORIN15:F041":
            return "نا"
        if prev == "NOORIN48:F0EB" or prev == "NOORIN35:F0B0":
            return "ں"
        if nxt == "NOORIN63:F0C5":
            return "کیر"
        if nxt == "NOORIN25:F0A9":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN63:F0D2":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB":
            return "ئ"
        if ip == "NOORIN01:F056":
            return "ئ"
        if ip == "NOORIN01:F07E":
            return "اے"
        return pua_map.get(key, "")
    if key == "NOORIN83:F0E2":
        return ""
    if key == "NOORIN81:F062":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt in ("NOORIN82:F099", "NOORIN57:F044"):
            return "کر"
        if nxt == "NOORIN01:F07A":
            return "ھے"
        return ""
    if key == "NOORIN17:F0E7":
        ip = immediate_prev_base_key(run, i)
        if ip is None and neighbor_base_keys(run, i, pua_map)[1] == "NOORIN41:F0AB":
            return "فی"
        if ip in ("NOORIN48:F0E4", "NOORIN82:F074", "NOORIN63:F0BB", "NOORIN14:F0A3"):
            return "ما"
        if ip == "NOORIN14:F0A3":
            return "ما"
        return pua_map.get(key, "")
    if key == "NOORIN08:F05E":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F06B":
            return "ما"
        return ""
    if key == "NOORIN14:F0EA":
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN07:F04B", "NOORIN23:F040"):
            return "ں"
        if ip == "NOORIN85:F08A" and neighbor_base_keys(run, i, pua_map)[1] == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN85:F08A" and neighbor_base_keys(run, i, pua_map)[1] == "NOORIN01:F03A":
            return "ں:"
        return pua_map.get(key, "")
    if key == "NOORIN63:F0EF":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN81:F090":
            if nxt == "NOORIN11:F059":
                return "ی"
            if nxt == "NOORIN01:F05A":
                return "ر"
            if nxt == "NOORIN14:F090":
                return "ان"
            if nxt == "NOORIN05:F083":
                return "ہ"
            if nxt == "NOORIN82:F099":
                return "کر"
        if ip is None:
            if nxt == "NOORIN82:F099":
                return "کر"
            return ""
        if ip == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F04E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN01:F0CC":
            if nxt in ("NOORIN01:F05A", "NOORIN17:F0F2"):
                return "رو"
            if nxt == "NOORIN01:F067":
                return "ہ"
        if ip is None and nxt == "NOORIN01:F05A":
            return "ر"
        if nxt == "NOORIN01:F05A" and immediate_prev_base_key(run, i) == "NOORIN11:F087":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN49:F0A9":
        return "ے"
    if key == "NOORIN21:F0DC":
        ip = immediate_prev_base_key(run, i)
        if ip is None:
            return "ھ"
        if ip == "NOORIN01:F03A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN08:F09D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt in ("NOORIN81:F036", "NOORIN05:F083", "NOORIN01:F03A", "NOORIN01:F058"):
            if nxt == "NOORIN01:F058":
                return "۔"
            return "پہ"
        return pua_map.get(key, "")
    if key == "NOORIN15:F0D8":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN63:F0C5":
            return "ر"
        if nxt == "NOORIN81:F06D":
            return "چ"
        if nxt == "NOORIN82:F063":
            return "یار"
        if nxt == "NOORIN82:F099":
            return "کر"
        return pua_map.get(key, "")
    if key == "NOORIN14:F02C":
        if neighbor_base_keys(run, i, pua_map)[1] == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN53:F027":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F058":
            return "۔"
        if nxt == "NOORIN01:F07A":
            return "،"
        return pua_map.get(key, "")
    if key == "NOORIN15:F086":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN63:F0C5":
            return "کی"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN81:F036":
            return "ں"
        if ip == "NOORIN01:F03A":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN05:F0B0":
        return "پھر"
    if key == "NOORIN15:F06B":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN82:F063" and nxt == "NOORIN48:F0E3":
            return "نی"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN07:F067":
            return "چھوڑ"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN48:F0E2":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN81:F0C4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN82:F02A":
            return "نال"
        return "کی"
    if key == "NOORIN30:F043":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN22:F037":
            return "ئ"
        if nxt == "NOORIN01:F05D":
            return "ت"
        if nxt == "NOORIN11:F033":
            return "کھ"
        if nxt == "NOORIN04:F04D":
            return "،"
        if nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F0B2":
        return "ر"
    if key == "NOORIN13:F035":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN01:F05C":
            return "و"
        if ip == "NOORIN01:F056" and nxt == "NOORIN01:F077":
            return "ل"
        if ip == "NOORIN21:F0D2":
            return "و"
        if ip == "NOORIN01:F070" and nxt == "NOORIN85:F031":
            return ""
        if ip == "NOORIN57:F044" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN82:F087":
            return "قات"
        return pua_map.get(key, "")
    if key == "NOORIN80:F031":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F05A" and immediate_prev_base_key(run, i) == "NOORIN01:F07A":
            return "ے"
        return ""
    if key == "NOORIN57:F068":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN01:F07A":
            return "ئے"
        if ip == "NOORIN05:F04A":
            return "ں"
        if ip is None or ip == "NOORIN01:F03A":
            return "و"
        if ip in ("NOORIN05:F084", "NOORIN59:F0F1", "NOORIN22:F037"):
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN13:F0EA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN04:F073":
            return "،"
        if nxt == "NOORIN01:F03A":
            return ":"
        if nxt == "NOORIN57:F049":
            return "لو"
        if ip == "NOORIN57:F064":
            return "،"
        return pua_map.get(key, "")
    if key == "NOORIN29:F03C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F06B":
            return "س"
        if nxt == "NOORIN56:F0CF":
            return "تے"
        return pua_map.get(key, "")
    if key == "NOORIN26:F0F4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F06F":
            return "کر"
        if nxt == "NOORIN01:F070":
            return "چ"
        return pua_map.get(key, "")
    if key == "NOORIN21:F064":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A":
            return "د"
        if ip == "NOORIN57:F040":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0EF":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F075" and nxt == "NOORIN01:F067":
            return "کھ"
        if ip == "NOORIN81:F059" and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN01:F051":
            return "ب"
        if ip == "NOORIN63:F0BB" and nxt == "NOORIN09:F094":
            return "ب"
        if ip == "NOORIN01:F053":
            return "ک"
        if ip == "NOORIN01:F058":
            return "کر"
        if ip == "NOORIN01:F03A":
            return "من"
        return pua_map.get(key, "")
    if key == "NOORIN16:F074":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN82:F03A" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN81:F082":
            if nxt == "NOORIN01:F057":
                return "آپ"
            if nxt == "NOORIN01:F07A":
                return "ھے"
            if nxt == "NOORIN01:F058":
                return "۔"
        if ip == "NOORIN01:F057":
            return "س"
        return pua_map.get(key, "")
    if key == "NOORIN14:F082":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and neighbor_base_keys(run, i, pua_map)[1] == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN01:F051" and neighbor_base_keys(run, i, pua_map)[1] == "NOORIN48:F0E2":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN21:F0D7":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN82:F0B1":
            return "کے"
        if ip == "NOORIN57:F044":
            return "ر"
        if ip == "NOORIN01:F03A":
            return "ھ"
        if ip == "NOORIN01:F0D4":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN06:F0BB":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip is None and nxt == "NOORIN63:F0C3":
            return "کو"
        if ip is None and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN01:F079" and nxt == "NOORIN72:F0B4":
            return "کے"
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN48:F0E3":
            return "نی"
        if ip == "NOORIN48:F0E3":
            return "نی"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN16:F05F":
        return ""
    if key == "NOORIN57:F02E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN16:F05F":
            if nxt == "NOORIN01:F05A":
                return "رت"
            if nxt == "NOORIN01:F066":
                return "زمیدرک"
            if nxt == "NOORIN01:F058":
                return ""
            if nxt == "NOORIN05:F084":
                return "گہنو"
            if nxt == "NOORIN85:F08A":
                return "زیادہ"
            if nxt == "NOORIN04:F0B4":
                return "رئی"
        return pua_map.get(key, "")
    if key == "NOORIN08:F099":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None:
            if nxt == "NOORIN05:F084":
                return "گہنو"
            if nxt == "NOORIN01:F058":
                return "۔"
            if nxt == "NOORIN82:F02A":
                return "گہنورھ"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN05:F084":
            return "گہنو"
        if ip == "NOORIN10:F0D2" and nxt == "NOORIN05:F084":
            return "گہنو"
        if ip == "NOORIN48:F0E2" and nxt == "NOORIN01:F058":
            return "۔"
        if ip == "NOORIN48:F0E2" and nxt == "NOORIN01:F03A":
            return ""
        if ip is None and nxt == "NOORIN05:F084":
            return "گہنو"
        if ip == "NOORIN82:F02A" and nxt == "NOORIN52:F099":
            return "نا"
        return pua_map.get(key, "")
    if key == "NOORIN26:F0B9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F058":
            return "۔"
        if nxt == "NOORIN01:F067":
            return "کان"
        if nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")

    if key == "NOORIN05:F048":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and nxt == "NOORIN01:F05A":
            return "رت"
        if ip == "NOORIN63:F0E0" and nxt == "NOORIN01:F07A":
            return "ے"
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN01:F03A":
            return ":"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0B4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and nxt == "NOORIN82:F02A":
            return "ھ"
        if ip == "NOORIN01:F028" and nxt == "NOORIN16:F071":
            return "م"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN15:F0C7":
            return "ر"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F043":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN01:F05D", "NOORIN63:F0C9") and nxt == "NOORIN48:F0E3":
            return "نی"
        if ip == "NOORIN63:F0C9" and nxt == "NOORIN01:F079":
            return "ے"
        if ip is None and nxt == "NOORIN01:F07D":
            return "پ"
        return pua_map.get(key, "")
    if key == "NOORIN41:F041":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN63:F0C3", "NOORIN63:F0BB") and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN57:F044" and nxt == "NOORIN81:F059":
            return "ن"
        return pua_map.get(key, "")
    if key == "NOORIN56:F0CC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0F1" and nxt in ("NOORIN63:F0C3", "NOORIN81:F024"):
            return "کو"
        if ip == "NOORIN01:F067" and nxt == "NOORIN01:F067":
            return "کو"
        return pua_map.get(key, "")
    if key == "NOORIN09:F0BF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and nxt == "NOORIN82:F03A":
            return "ے"
        if ip == "NOORIN05:F084" and nxt == "NOORIN05:F083":
            return "ے"
        if ip == "NOORIN81:F036" and nxt == "NOORIN82:F099":
            return "ے"
        if ip == "NOORIN57:F022" and nxt == "NOORIN01:F07A":
            return "ے"
        if ip == "NOORIN26:F088" and nxt == "NOORIN01:F07A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN82:F096":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F037" and nxt == "NOORIN01:F03A":
            return ":"
        if ip == "NOORIN01:F079" and nxt == "NOORIN05:F084":
            return "د"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F09B":
            return "د"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F058":
            return ":"
        return pua_map.get(key, "")
    if key == "NOORIN13:F036":
        return pua_map.get(key, "")
    if key == "NOORIN04:F04F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN18:F0A9" and nxt == "NOORIN48:F0E3":
            return "نی"
        return pua_map.get(key, "")
    if key == "NOORIN05:F06B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and nxt == "NOORIN01:F07A":
            return "ں"
        if ip == "NOORIN01:F07C" and nxt == "NOORIN48:F0EC":
            return "ے"
        if ip == "NOORIN37:F0A2" and nxt == "NOORIN01:F03A":
            return ":"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F03A":
            return "ے"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN01:F067":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN11:F02B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN01:F07C":
            return "ھ"
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN01:F07C":
            return "ے"
        if ip == "NOORIN72:F0C1" and nxt == "NOORIN01:F07C":
            return "ھ"
        if ip == "NOORIN59:F0F0" and nxt == "NOORIN77:F0B3":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN07:F0AA":
        return pua_map.get(key, "رے")
    if key == "NOORIN64:F0D8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and nxt in ("NOORIN89:F079", "NOORIN14:F0F7"):
            return ""
        if ip is None:
            return ""
        if ip == "NOORIN01:F05A" and nxt == "NOORIN82:F02A":
            return "ناں"
        return pua_map.get(key, "")
    if key == "NOORIN49:F061":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN01:F076", "NOORIN57:F044") and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F058" and nxt is None:
            return ""
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F054":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN83:F0DE" and nxt == "NOORIN48:F0EC":
            return "موتر"
        return pua_map.get(key, "")
    if key == "NOORIN57:F03F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F071" and nxt == "NOORIN81:F0A4":
            return "حا"
        if ip is None and nxt == "NOORIN81:F059":
            return "نوتھا"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN81:F059":
            return "نوتھا"
        if ip == "NOORIN81:F071" and nxt == "NOORIN63:F0C5":
            return "حا"
        return pua_map.get(key, "")
    if key == "NOORIN22:F056":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and nxt == "NOORIN81:F024":
            return "ے"
        if ip == "NOORIN11:F087" and nxt == "NOORIN01:F057":
            return "ے"
        if ip == "NOORIN22:F037" and nxt == "NOORIN01:F099":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN05:F064":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F049" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN48:F0E4" and nxt == "NOORIN81:F036":
            return "و"
        if ip == "NOORIN01:F067" and nxt == "NOORIN82:F053":
            return "ھی"
        if ip == "NOORIN59:F0F0" and nxt == "NOORIN63:F0C3":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0F3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None:
            return ""
        if ip == "NOORIN57:F044" and nxt == "NOORIN81:F030":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN25:F0EB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN01:F057":
            return "ے"
        if ip == "NOORIN01:F03B" and nxt == "NOORIN63:F0E2":
            return "ما"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0C5":
            return "کی"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0BB":
            return "کا"
        if ip == "NOORIN01:F06C" and nxt == "NOORIN05:F083":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN41:F09B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return "کر"
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN15:F095":
            return "کھ"
        return pua_map.get(key, "")
    if key == "NOORIN13:F0BB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F073":
            return "ف"
        if ip == "NOORIN01:F053" and nxt == "NOORIN01:F073":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN38:F0BD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E2" and nxt == "NOORIN01:F099":
            return "دو"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F03A":
            return "د"
        if ip == "NOORIN48:F0E2" and nxt == "NOORIN85:F08A":
            return "د"
        if ip == "NOORIN05:F084" and nxt == "NOORIN01:F0D4":
            return "دو"
        return pua_map.get(key, "")
    if key == "NOORIN06:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN01:F03A", "NOORIN57:F044", "NOORIN01:F05A") and nxt == "NOORIN63:F0C3":
            return "کو"
        if ip is None and nxt == "NOORIN63:F0C5":
            return "کو"
        return pua_map.get(key, "")
    if key == "NOORIN07:F0DC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN56:F0E0":
            return "بر"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F074":
            return "ق"
        return pua_map.get(key, "")
    if key == "NOORIN06:F04C":
        return pua_map.get(key, "")
    if key == "NOORIN15:F0DB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C6":
            return "کے"
        return pua_map.get(key, "")
    if key == "NOORIN19:F046":
        return pua_map.get(key, "ک")
    if key == "NOORIN14:F099":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN67:F0D5":
            return "تو"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN14:F060":
            return "تو"
        return pua_map.get(key, "")
    if key == "NOORIN07:F068":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F030" and nxt == "NOORIN82:F02A":
            return "ے"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN75:F084":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN01:F079", "NOORIN63:F0E2", "NOORIN82:F03A", "NOORIN01:F0D4"):
            return "ناں"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0F9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and nxt == "NOORIN01:F067":
            return "ے"
        if ip == "NOORIN01:F09F" and nxt == "NOORIN82:F03A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN14:F02D":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F06C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and nxt == "NOORIN11:F087":
            return "نو"
        if ip == "NOORIN01:F076" and nxt == "NOORIN11:F087":
            return "نو"
        if ip is None and nxt == "NOORIN11:F087":
            return "نو"
        if ip == "NOORIN08:F042" and nxt == "NOORIN01:F067":
            return "ہ"
        if ip == "NOORIN57:F044" and nxt == "NOORIN17:F0F2":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN14:F039":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and nxt == "NOORIN82:F099":
            return "پ"
        if ip == "NOORIN82:F02A" and nxt == "NOORIN63:F0C6":
            return "کے"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05C" and nxt == "NOORIN01:F05C":
            return "و"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F067":
            return "ک"
        if ip is None and nxt == "NOORIN01:F05B":
            return "ب"
        return pua_map.get(key, "")
    if key == "NOORIN06:F07C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F040" and nxt == "NOORIN63:F0E3":
            return "تا"
        if ip == "NOORIN81:F040" and nxt == "NOORIN06:F027":
            return "ت"
        if ip == "NOORIN81:F040" and nxt == "NOORIN81:F024":
            return "ت"
        if ip == "NOORIN81:F040" and nxt == "NOORIN57:F044":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0B4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and nxt == "NOORIN01:F03A":
            return "ڑ"
        if ip is None and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN82:F03A" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN26:F07B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN60:F0A4" and nxt == "NOORIN81:F059":
            return "نئے"
        if ip == "NOORIN59:F0F1" and nxt == "NOORIN01:F029":
            return "نئے"
        if ip == "NOORIN85:F0B6" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F068" and nxt == "NOORIN81:F04A":
            return "تک"
        if ip == "NOORIN31:F0B9" and nxt == "NOORIN63:F0E2":
            return "ماں"
        if ip == "NOORIN01:F07E" and nxt == "NOORIN81:F082":
            return "سا"
        if ip == "NOORIN01:F05E" and nxt == "NOORIN63:F0E2":
            return "ماں"
        return pua_map.get(key, "")
    if key == "NOORIN01:F03F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN82:F063", "NOORIN63:F0C6", "NOORIN14:F090") and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F068" and nxt == "NOORIN82:F033":
            return "غ"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0BE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and nxt == "NOORIN01:F057":
            return "و"
        if ip == "NOORIN57:F044" and nxt == "NOORIN01:F057":
            return "آ"
        if ip == "NOORIN05:F04A" and nxt == "NOORIN48:F0E2":
            return "و"
        if ip is None and nxt == "NOORIN48:F0E2":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN26:F024":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E2" and nxt == "NOORIN82:F02A":
            return "نا"
        if ip is None and nxt == "NOORIN63:F0D1":
            return "لانی"
        if ip is None and nxt == "NOORIN63:F0BB":
            return "کا"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN63:F0D1":
            return "لانی"
        return pua_map.get(key, "")
    if key == "NOORIN10:F094":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and nxt in ("NOORIN01:F058", "NOORIN01:F03A", "NOORIN82:F03B"):
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN01:F05F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and nxt == "NOORIN23:F0CF":
            return "سے"
        if ip == "NOORIN63:F0DF" and nxt is None:
            return "سے"
        return pua_map.get(key, "")
    if key == "NOORIN27:F04D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F05D" and nxt == "NOORIN48:F0E3":
            return "ت"
        if ip is None and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F065":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0A7" and nxt == "NOORIN82:F033":
            return "غ"
        if ip == "NOORIN01:F067" and nxt == "NOORIN63:F0BB":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN16:F0C8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN82:F03A":
            return "اک"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN82:F03B":
            return "اک"
        if ip is None and nxt == "NOORIN82:F03B":
            return "اک"
        return pua_map.get(key, "")
    if key == "NOORIN15:F032":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F077":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN08:F0E0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F075" and nxt == "NOORIN01:F05D":
            return "ت"
        if ip == "NOORIN01:F07E" and nxt == "NOORIN01:F07A":
            return ""
        if ip == "NOORIN57:F044" and nxt == "NOORIN85:F08A":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN23:F0F0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F067":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN70:F052":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and nxt == "NOORIN01:F067":
            return "ے"
        if ip == "NOORIN07:F059" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN26:F031":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN48:F0E4":
            return "سے"
        if ip == "NOORIN01:F072" and nxt == "NOORIN48:F0E4":
            return "سے"
        if ip == "NOORIN01:F07B" and nxt == "NOORIN48:F0E2":
            return "و"
        if ip == "NOORIN41:F09C" and nxt == "NOORIN48:F0E4":
            return "سے"
        return pua_map.get(key, "")
    if key == "NOORIN17:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F05A":
            return "ے"
        if ip == "NOORIN63:F0C9" and nxt == "NOORIN82:F099":
            return "ے"
        if ip == "NOORIN08:F057" and nxt == "NOORIN63:F0C5":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN15:F041":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and nxt == "NOORIN01:F03A":
            return "آ"
        if ip == "NOORIN06:F0BD" and nxt == "NOORIN01:F03A":
            return "آ"
        return pua_map.get(key, "")
    if key == "NOORIN06:F0C3":
        return pua_map.get(key, "")
    if key == "NOORIN72:F0B4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN06:F0BB", "NOORIN48:F0E3", "NOORIN01:F056") and nxt == "NOORIN63:F0C5":
            return "کیا"
        if ip == "NOORIN01:F067" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0C0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN63:F0BB", "NOORIN57:F044") and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN49:F08D":
        return pua_map.get(key, "ک")
    if key == "NOORIN14:F0E2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F0BE" and nxt == "NOORIN01:F056":
            return "غ"
        if ip == "NOORIN81:F0BE" and nxt == "NOORIN01:F05D":
            return "تو"
        return pua_map.get(key, "")
    if key == "NOORIN01:F0A3":
        return pua_map.get(key, "")
    if key == "NOORIN37:F057":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN61:F08B" and nxt == "NOORIN48:F0EC":
            return "ے"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F094":
        return pua_map.get(key, "ر")
    if key == "NOORIN18:F085":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F075":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN10:F03D":
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN01:F067", "NOORIN63:F0C2"):
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN01:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F0DC" and nxt == "NOORIN01:F059":
            return "ء"
        return pua_map.get(key, "")
    if key == "NOORIN57:F057":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN09:F094" and nxt == "NOORIN63:F0C6":
            return "ک"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0C6":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN59:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and nxt in ("NOORIN83:F0F3", "NOORIN63:F0BB", "NOORIN63:F0C3"):
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN45:F096":
        _prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "ں")
    if key == "NOORIN82:F069":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and nxt == "NOORIN01:F07C":
            return "ے"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN13:F063":
            return "ر"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN28:F0F8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN82:F02A":
            return "ناس"
        if ip == "NOORIN85:F08A" and nxt == "NOORIN01:F05B":
            return "رد"
        return pua_map.get(key, "")
    if key == "NOORIN18:F076":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and nxt == "NOORIN01:F068":
            return "ے"
        if ip == "NOORIN82:F04A" and nxt == "NOORIN05:F083":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN11:F097":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN48:F0E3":
            return "ے"
        if ip == "NOORIN01:F077" and nxt == "NOORIN63:F0E2":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN13:F0B1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and nxt == "NOORIN85:F08A":
            return "د"
        if ip == "NOORIN01:F067" and nxt == "NOORIN50:F076":
            return "د"
        if ip == "NOORIN04:F02C" and nxt == "NOORIN63:F0BB":
            return "ک"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F05A":
            return "را"
        return pua_map.get(key, "")
    if key == "NOORIN57:F058":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN81:F021":
            return "با"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN04:F0C8":
            return "بھو"
        return pua_map.get(key, "")
    if key == "NOORIN81:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F099":
            return "ڈ"
        return pua_map.get(key, "")
    if key == "NOORIN81:F081":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F06B" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN63:F0C6" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0BE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F058" and nxt == "NOORIN81:F071":
            return "حال"
        if ip is None and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F07E" and nxt == "NOORIN81:F071":
            return "حال"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0C4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and nxt == "NOORIN63:F0E2":
            return "آ"
        if ip == "NOORIN01:F067" and nxt == "NOORIN85:F08A":
            return "آ"
        if ip == "NOORIN01:F067" and nxt == "NOORIN01:F057":
            return "آ"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0CB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0D0" and nxt == "NOORIN01:F03A":
            return "رد"
        if ip == "NOORIN57:F022" and nxt == "NOORIN63:F0BB":
            return "رد"
        return pua_map.get(key, "")


    if key == "NOORIN07:F0B8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and nxt == "NOORIN01:F07D":
            return "ر"
        if ip == "NOORIN01:F06C" and nxt == "NOORIN08:F08B":
            return "ش"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0D1":
            return "و"
        if ip == "NOORIN57:F022" and nxt == "NOORIN63:F0E2":
            return "ما"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN44:F041":
            return "و"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F0D4":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN01:F06D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F07B" and nxt == "NOORIN82:F099":
            return "و"
        if ip == "NOORIN10:F0EF" and nxt == "NOORIN82:F02A":
            return ""
        if ip is None and nxt is None:
            return ""
        if ip == "NOORIN81:F07B" and nxt == "NOORIN01:F057":
            return "ر"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0C3":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN15:F0D3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN63:F0BB", "NOORIN01:F06B", "NOORIN01:F03A", "NOORIN01:F028",
                  "NOORIN57:F044") and nxt in ("NOORIN01:F056", "NOORIN57:F04B"):
            return "ں"
        if ip == "NOORIN17:F03E" and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "ں")
    if key == "NOORIN04:F068":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN57:F044" and nxt == "NOORIN01:F07A":
            return "د"
        if ip == "NOORIN01:F056" and nxt in ("NOORIN01:F03A", "NOORIN01:F058"):
            return "ے"
        if ip is None and nxt == "NOORIN63:F0CD":
            return ""
        if ip == "NOORIN81:F024" and nxt == "NOORIN63:F0C5":
            return "ب"
        return pua_map.get(key, "")
    if key == "NOORIN16:F0A3":
        return pua_map.get(key, "")
    if key == "NOORIN16:F056":
        return "ے"
    if key == "NOORIN11:F046":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN57:F059", "NOORIN01:F067") and nxt in (
            "NOORIN01:F0AD", "NOORIN81:F021",
        ):
            return "ے"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN57:F022":
            return "سے"
        if ip == "NOORIN11:F087" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN54:F0CB":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN11:F0DC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F030" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN15:F098" and nxt == "NOORIN01:F03A":
            return "و"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN57:F044":
            return "و"
        if ip == "NOORIN63:F0C2" and nxt == "NOORIN01:F03A":
            return "ے"
        if ip == "NOORIN01:F076" and nxt == "NOORIN01:F03A":
            return "ر"
        if ip == "NOORIN57:F043" and nxt == "NOORIN01:F029":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN56:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN63:F0C6", "NOORIN01:F03A") and nxt == "NOORIN01:F056":
            return "ں"
        if ip is None and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "ں")
    if key == "NOORIN15:F0D0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN61:F08C", "NOORIN56:F0D0") and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN22:F037" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN82:F0AA" and nxt == "NOORIN48:F0F0":
            return "ھ"
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN81:F06C":
            return "چ"
        return pua_map.get(key, "")
    if key == "NOORIN10:F051":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN01:F07A":
            return "ما"
        if ip == "NOORIN22:F037" and nxt == "NOORIN82:F063":
            return "ی"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN16:F0C0" and nxt == "NOORIN01:F07D":
            return "پ"
        if ip is None and nxt in ("NOORIN81:F06D", "NOORIN81:F036"):
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F0E2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F053" and nxt == "NOORIN63:F02C":
            return "ا"
        if ip == "NOORIN01:F053" and nxt == "NOORIN81:F0A4":
            return "ط"
        if ip == "NOORIN81:F036" and nxt == "NOORIN01:F03A":
            return "پ"
        if ip == "NOORIN01:F05A" and nxt in ("NOORIN63:F0C9", "NOORIN06:F046"):
            return "گ"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F0E0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and nxt == "NOORIN82:F02A":
            return "نا"
        if ip == "NOORIN57:F044" and nxt == "NOORIN85:F08A":
            return "دا"
        if ip is None and nxt == "NOORIN81:F086":
            return ""
        if ip == "NOORIN82:F09E" and nxt == "NOORIN63:F0C2":
            return "ت"
        if ip == "NOORIN01:F07C" and nxt == "NOORIN63:F0C5":
            return "کی"
        if ip == "NOORIN01:F079" and nxt == "NOORIN63:F0E2":
            return "مار"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0BC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F043" and nxt == "NOORIN01:F056":
            return "ں"
        if ip is None and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN82:F03A" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN63:F0C2" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN07:F098":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN57:F044" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN01:F077" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN59:F0F1" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN63:F0C4" and nxt == "NOORIN06:F027":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN03:F0F9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN14:F0A3" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN82:F071" and nxt == "NOORIN05:F083":
            return "ہ"
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN81:F0AC":
            return "ع"
        return pua_map.get(key, "")
    if key == "NOORIN13:F02B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN13:F0A8" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F03A" and nxt in ("NOORIN56:F0CF", "NOORIN89:F079"):
            return "ڈ"
        if ip == "NOORIN01:F058" and nxt == "NOORIN56:F0CF":
            return "تے"
        if ip == "NOORIN81:F024" and nxt == "NOORIN82:F02A":
            return "نا"
        return pua_map.get(key, "")
    if key == "NOORIN29:F0F8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and nxt == "NOORIN01:F057":
            return "کر"
        if ip == "NOORIN85:F08A" and nxt == "NOORIN01:F03A":
            return "د"
        if ip == "NOORIN85:F08A" and nxt == "NOORIN57:F037":
            return "کر"
        if ip == "NOORIN85:F08A" and nxt == "NOORIN81:F065":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0E7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and nxt in ("NOORIN01:F07B", "NOORIN82:F02A"):
            return "ر"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN05:F084" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN13:F024":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN07:F059" and nxt in ("NOORIN01:F05A", "NOORIN82:F02A"):
            return "رم"
        if ip == "NOORIN25:F0A9" and nxt == "NOORIN01:F03A":
            return "بھی"
        if ip in ("NOORIN81:F065", "NOORIN07:F059") and nxt in (
            "NOORIN83:F0DB", "NOORIN81:F040", "NOORIN63:F0C3",
        ):
            return "چا"
        return pua_map.get(key, "")
    if key == "NOORIN59:F0EC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F087" and nxt == "NOORIN01:F067":
            return "کر"
        if ip == "NOORIN82:F087" and nxt == "NOORIN05:F083":
            return "کر"
        if ip == "NOORIN14:F0BC" and nxt == "NOORIN01:F067":
            return "کر"
        return pua_map.get(key, "کر")
    if key == "NOORIN36:F0D2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN15:F0C9" and nxt == "NOORIN01:F058":
            return "ے"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN81:F08E":
            return "جوڑنگو"
        if ip in ("NOORIN82:F02A", "NOORIN22:F0AB") and nxt == "NOORIN01:F03A":
            return "ے"
        if ip == "NOORIN59:F0F0" and nxt == "NOORIN81:F036":
            return "ئی"
        if ip == "NOORIN22:F0AB" and nxt == "NOORIN01:F07A":
            return "تے"
        return pua_map.get(key, "")
    if key == "NOORIN81:F06E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN83:F0E0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F02E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN01:F05D" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN20:F06B" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip is None and nxt == "NOORIN01:F067":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN41:F0AB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and nxt == "NOORIN01:F03A":
            return "ک"
        if ip == "NOORIN57:F044" and nxt == "NOORIN81:F027":
            return "زر"
        if ip == "NOORIN63:F0C6" and nxt == "NOORIN01:F03A":
            return "ما"
        if ip == "NOORIN63:F0C5" and nxt is None:
            return "کی"
        if ip == "NOORIN63:F0B0" and nxt == "NOORIN01:F0D4":
            return "ی"
        if ip == "NOORIN16:F0BB" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F04D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F04A" and nxt == "NOORIN01:F077":
            return "لی"
        if ip is None and nxt == "NOORIN05:F084":
            return "گہنو"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN82:F02E":
            return "ے"
        if ip == "NOORIN63:F0C6" and nxt == "NOORIN82:F02E":
            return "ے"
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN01:F077":
            return "ل"
        if ip == "NOORIN63:F0BB" and nxt == "NOORIN01:F077":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN06:F090":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN01:F067" and nxt in ("NOORIN01:F0D4", "NOORIN01:F058", "NOORIN01:F056"):
            return "ے"
        if ip == "NOORIN01:F05D" and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN08:F032":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and nxt == "NOORIN01:F03A":
            return "ک"
        if ip == "NOORIN81:F046" and nxt == "NOORIN01:F067":
            return "و"
        if ip == "NOORIN19:F05B" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN01:F056" and nxt == "NOORIN01:F056":
            return "ں"
        if ip is None and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN82:F03A" and nxt == "NOORIN01:F0D4":
            return "،"
        return pua_map.get(key, "")
    if key == "NOORIN11:F0CE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F077" and nxt in ("NOORIN01:F07A", "NOORIN01:F078"):
            return "ھ"
        if ip == "NOORIN82:F04A" and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN63:F0C6" and nxt == "NOORIN01:F078":
            return "ر"
        if ip == "NOORIN82:F02A" and nxt == "NOORIN01:F078":
            return "ن"
        if ip == "NOORIN63:F0C4" and nxt == "NOORIN05:F084":
            return "سے"
        return pua_map.get(key, "")
    if key == "NOORIN82:F0A5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN63:F0CD", "NOORIN81:F08E") and nxt == "NOORIN01:F0D4":
            return "،"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN63:F0C3":
            return "وا"
        if ip == "NOORIN01:F067" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN01:F03A":
            return "و"
        if ip == "NOORIN82:F030" and nxt == "NOORIN70:F052":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN25:F05A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN07:F071" and nxt == "NOORIN01:F067":
            return "چ"
        if ip == "NOORIN63:F0CF" and nxt == "NOORIN01:F067":
            return "ک"
        return pua_map.get(key, "ک")
    if key == "NOORIN15:F0C7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F053" and nxt == "NOORIN04:F02C":
            return "ر"
        if ip == "NOORIN14:F0B4" and nxt == "NOORIN82:F097":
            return "ک"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F057":
            return "آ"
        if ip == "NOORIN17:F095" and nxt == "NOORIN82:F03A":
            return "ن"
        if ip == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return "ھی"
        if ip == "NOORIN01:F061" and nxt == "NOORIN01:F058":
            return "چ"
        return pua_map.get(key, "")
    if key == "NOORIN72:F0A2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F058" and nxt == "NOORIN81:F059":
            return "ن"
        if ip == "NOORIN81:F036" and nxt == "NOORIN22:F037":
            return "ن"
        if ip in ("NOORIN57:F05A", "NOORIN01:F03A") and nxt == "NOORIN63:F0C3":
            return "ک"
        if ip == "NOORIN01:F07A" and nxt == "NOORIN82:F03A":
            return "ے"
        if ip is None and nxt == "NOORIN63:F0C3":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN05:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F05D":
            return "ت"
        if ip == "NOORIN77:F0B3" and nxt == "NOORIN01:F067":
            return "چ"
        if ip == "NOORIN63:F0CD" and nxt == "NOORIN01:F067":
            return "و"
        if ip is None and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN01:F059" and nxt == "NOORIN01:F067":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN06:F060":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and nxt == "NOORIN57:F044":
            return "ہ"
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN81:F06D":
            return "و"
        if ip == "NOORIN01:F09F" and nxt == "NOORIN05:F084":
            return "ر"
        if ip == "NOORIN01:F065" and nxt == "NOORIN82:F03A":
            return "ر"
        if ip == "NOORIN05:F083" and nxt in ("NOORIN57:F044", "NOORIN01:F03A"):
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN22:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and nxt in (
            "NOORIN63:F0C1", "NOORIN01:F058", "NOORIN01:F0D4", "NOORIN81:F059",
        ):
            return "د"
        return pua_map.get(key, "د")
    if key == "NOORIN15:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt in (
            "NOORIN01:F065", "NOORIN04:F0CC", "NOORIN81:F071",
        ):
            return "ڈ"
        if ip == "NOORIN57:F05A" and nxt == "NOORIN01:F067":
            return "کھ"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN12:F03F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F066" and nxt in (
            "NOORIN82:F099", "NOORIN05:F083", "NOORIN82:F063", "NOORIN01:F058",
        ):
            return "ز"
        return pua_map.get(key, "ز")
    if key == "NOORIN82:F0B4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN63:F0C2":
            return "تو"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN63:F0C5":
            return "کی"
        return pua_map.get(key, "")
    if key == "NOORIN27:F095":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt is None:
            return "ر"
        if ip == "NOORIN01:F053" and nxt == "NOORIN14:F0A3":
            return "ک"
        if ip == "NOORIN01:F05A" and nxt in ("NOORIN01:F058", "NOORIN59:F0F0"):
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN48:F0EF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F037" and nxt == "NOORIN05:F083":
            return "ہ"
        if ip == "NOORIN81:F06D" and nxt in ("NOORIN01:F057", "NOORIN63:F0C1"):
            return "ے"
        if ip == "NOORIN01:F068" and nxt == "NOORIN85:F08A":
            return "دا"
        if ip == "NOORIN85:F08A" and nxt == "NOORIN05:F083":
            return "د"
        if ip == "NOORIN06:F046" and nxt is None:
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN17:F03E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and nxt == "NOORIN01:F056":
            return "ں"
        if ip is None and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN26:F088" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "ں")
    if key == "NOORIN01:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021" and nxt == "NOORIN11:F05A":
            return "ے"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN26:F031":
            return "ے"
        if ip is None and nxt is None:
            return ""
        if ip == "NOORIN01:F05A" and nxt in ("NOORIN06:F046", "NOORIN85:F08A"):
            return "ل"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN81:F036":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN81:F03A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt in (
            "NOORIN01:F057", "NOORIN01:F0D4", "NOORIN28:F0A9", "NOORIN63:F0F1",
            "NOORIN22:F037", "NOORIN01:F058",
        ):
            return "ر"
        return pua_map.get(key, "ر")
    if key == "NOORIN83:F0CD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN34:F03A", "NOORIN34:F039", "NOORIN34:F038") and nxt in (
            "NOORIN63:F0E2", "NOORIN01:F03A", "NOORIN22:F037", "NOORIN05:F083",
        ):
            return "ما"
        return pua_map.get(key, "")
    if key == "NOORIN53:F0CC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt in (
            "NOORIN85:F08A", "NOORIN82:F097", "NOORIN04:F0AF",
        ):
            return "ب"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN82:F097":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN67:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F075" and nxt == "NOORIN31:F07D":
            return "کہ"
        if ip == "NOORIN01:F03A" and nxt in ("NOORIN63:F0DF", "NOORIN63:F0C1"):
            return "پ"
        if ip == "NOORIN63:F0BB" and nxt == "NOORIN05:F084":
            return "گ"
        if ip == "NOORIN57:F044" and nxt == "NOORIN82:F02A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0F2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F075" and nxt == "NOORIN81:F059":
            return "ن"
        if ip == "NOORIN06:F027" and nxt == "NOORIN81:F059":
            return "ن"
        if ip == "NOORIN51:F0C8" and nxt == "NOORIN81:F059":
            return "ن"
        if ip == "NOORIN48:F0E2" and nxt == "NOORIN81:F059":
            return "ن"
        if ip == "NOORIN01:F056" and nxt == "NOORIN63:F0C6":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and nxt == "NOORIN63:F0C3":
            return "ت"
        if ip == "NOORIN63:F0E2" and nxt in ("NOORIN01:F05A", "NOORIN01:F058"):
            return "ر"
        if ip is None and nxt in ("NOORIN81:F040", "NOORIN63:F0C3"):
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F0CB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F06D" and nxt in ("NOORIN01:F067", "NOORIN01:F028"):
            return "ے"
        if ip == "NOORIN85:F08A" and nxt == "NOORIN01:F067":
            return "کھ"
        if ip == "NOORIN01:F068" and nxt == "NOORIN01:F03A":
            return "ڑ"
        if ip == "NOORIN81:F06D" and nxt == "NOORIN57:F044":
            return "ے"
        if ip == "NOORIN01:F065" and nxt == "NOORIN01:F03A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN05:F059":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN66:F046":
            return ""
        if ip == "NOORIN01:F029" and nxt == "NOORIN01:F075":
            return "ک"
        if ip == "NOORIN01:F078" and nxt == "NOORIN01:F075":
            return "ک"
        if ip == "NOORIN01:F075" and nxt == "NOORIN01:F075":
            return "ک"
        if ip == "NOORIN48:F0E4" and nxt == "NOORIN72:F0C1":
            return "چ"
        if ip == "NOORIN81:F021" and nxt == "NOORIN82:F03A":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN81:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and nxt in ("NOORIN01:F05A", "NOORIN01:F07A"):
            return "و"
        if ip is None and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN01:F077":
            return "ل"
        if ip == "NOORIN82:F087" and nxt == "NOORIN01:F07D":
            return "پ"
        return pua_map.get(key, "")
    if key == "NOORIN05:F0EF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F028" and nxt == "NOORIN63:F0E2":
            return "ما"
        if ip == "NOORIN81:F040" and nxt == "NOORIN01:F03A":
            return "تا"
        if ip == "NOORIN82:F05D" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN63:F0C3" and nxt == "NOORIN01:F03A":
            return "اک"
        if ip == "NOORIN82:F03A" and nxt == "NOORIN63:F0E2":
            return "ما"
        return pua_map.get(key, "")
    if key == "NOORIN08:F043":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and nxt in ("NOORIN59:F0F0", "NOORIN82:F02A"):
            return "ئی"
        if ip is None and nxt in ("NOORIN82:F02A", "NOORIN82:F025"):
            return ""
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN59:F0F0":
            return "ئی"
        return pua_map.get(key, "")
    if key == "NOORIN08:F0D1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F079":
            return "ے"
        if ip is None and nxt == "NOORIN01:F067":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN57:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN15:F0D1":
            return ""
        if ip == "NOORIN05:F084" and nxt == "NOORIN81:F059":
            return "نس"
        if ip == "NOORIN81:F027" and nxt == "NOORIN63:F0C3":
            return "ی"
        if ip == "NOORIN48:F0E4" and nxt == "NOORIN15:F0D1":
            return "نس"
        if ip == "NOORIN63:F0F1" and nxt == "NOORIN31:F0B9":
            return "ٹر"
        return pua_map.get(key, "")
    if key == "NOORIN19:F054":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05D" and nxt == "NOORIN82:F063":
            return "ی"
        if ip == "NOORIN22:F037" and nxt == "NOORIN63:F0C2":
            return "تو"
        if ip == "NOORIN82:F02A" and nxt == "NOORIN48:F0E2":
            return "و"
        if ip is None and nxt == "NOORIN48:F0E2":
            return "و"
        if ip == "NOORIN01:F079" and nxt in ("NOORIN01:F058", "NOORIN01:F07A"):
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN14:F078":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return "ر"
        if ip in ("NOORIN56:F0CE", "NOORIN63:F0C7") and nxt in (
            "NOORIN82:F02A", "NOORIN01:F03A",
        ):
            return "نا"
        if ip == "NOORIN57:F049" and nxt == "NOORIN01:F0D4":
            return "لو"
        return pua_map.get(key, "")
    if key == "NOORIN16:F0BE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN63:F0C6":
            return "کے"
        if ip == "NOORIN01:F075" and nxt == "NOORIN63:F0C6":
            return "کے"
        if ip == "NOORIN01:F0D4" and nxt is None:
            return "کے"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0C6":
            return "کے"
        if ip == "NOORIN82:F063" and nxt == "NOORIN63:F0C6":
            return "کے"
        return pua_map.get(key, "کے")
    if key == "NOORIN04:F07A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F070" and nxt == "NOORIN01:F067":
            return "کت"
        return pua_map.get(key, "کت")
    if key == "NOORIN29:F0C8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and nxt == "NOORIN01:F03A":
            return "ے"
        if ip == "NOORIN82:F03A" and nxt == "NOORIN01:F058":
            return "کر"
        if ip == "NOORIN81:F071" and nxt == "NOORIN57:F022":
            return "ق"
        if ip == "NOORIN63:F0C9" and nxt == "NOORIN01:F058":
            return "ے"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN15:F0E8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN46:F09A" and nxt == "NOORIN63:F0D1":
            return "لا"
        if ip == "NOORIN82:F03A" and nxt == "NOORIN11:F033":
            return "کھ"
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN01:F07B":
            return "ی"
        if ip is None and nxt in ("NOORIN63:F0C3", "NOORIN62:F042", "NOORIN63:F0C6"):
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN07:F04B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F046" and nxt in (None, "NOORIN01:F03A", "NOORIN85:F08A"):
            return "و"
        return pua_map.get(key, "و")
    if key == "NOORIN14:F0AF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0E4" and nxt == "NOORIN59:F0F0":
            return "ئی"
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN59:F0F0":
            return "ما"
        if ip == "NOORIN01:F05A" and nxt in (
            "NOORIN01:F056", "NOORIN81:F030", "NOORIN63:F0C3",
        ):
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN13:F0B6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN62:F0D7":
            return "ر"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN01:F0D4":
            return "ے"
        if ip == "NOORIN63:F0C5" and nxt == "NOORIN48:F0E3":
            return "نی"
        if ip == "NOORIN26:F0C9" and nxt == "NOORIN48:F0E3":
            return "چ"
        return pua_map.get(key, "")
    if key == "NOORIN15:F027":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN01:F029", "NOORIN01:F079") and nxt == "NOORIN01:F067":
            return "کر"
        if ip == "NOORIN57:F044" and nxt == "NOORIN01:F067":
            return "ت"
        if ip == "NOORIN01:F060" and nxt == "NOORIN01:F067":
            return "کر"
        if ip is None and nxt == "NOORIN01:F067":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0DC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt in (
            "NOORIN01:F036", "NOORIN06:F027", None, "NOORIN48:F0E4", "NOORIN81:F099",
        ):
            return "ر"
        return pua_map.get(key, "ر")
    if key == "NOORIN27:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F067":
            return "کھ"
        return pua_map.get(key, "کھ")
    if key == "NOORIN02:F073":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and nxt in (
            "NOORIN01:F05A", "NOORIN83:F0E1", "NOORIN08:F0DE", "NOORIN63:F0B8",
        ):
            return "رد"
        if ip == "NOORIN81:F046" and nxt == "NOORIN25:F075":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN08:F090":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN13:F02A" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip is None and nxt == "NOORIN05:F083":
            return "ہ"
        if ip == "NOORIN63:F0C6" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F060" and nxt == "NOORIN01:F0D4":
            return "،"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN63:F0E2":
            return "ما"
        return pua_map.get(key, "")
    if key == "NOORIN14:F084":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and nxt in ("NOORIN01:F058", "NOORIN14:F090"):
            return "ے"
        if ip == "NOORIN81:F065" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN81:F046" and nxt == "NOORIN13:F04E":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN55:F0E5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F077" and nxt == "NOORIN05:F083":
            return "ل"
        if ip == "NOORIN01:F058" and nxt == "NOORIN01:F07A":
            return "ہر"
        if ip == "NOORIN05:F04A" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F0D4":
            return "،"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN56:F0EE":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN50:F0F4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip in ("NOORIN63:F0E2", "NOORIN82:F06B") and nxt == "NOORIN01:F070":
            return "ما"
        if ip == "NOORIN08:F057" and nxt == "NOORIN01:F070":
            return "م"
        if ip == "NOORIN81:F036" and nxt == "NOORIN01:F070":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN46:F037":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN11:F090" and nxt == "NOORIN57:F075":
            return "سر"
        if ip == "NOORIN82:F043" and nxt == "NOORIN81:F036":
            return "پ"
        if ip == "NOORIN63:F0C5" and nxt in ("NOORIN63:F0D1", "NOORIN82:F097"):
            return "ل"
        if ip == "NOORIN82:F043" and nxt == "NOORIN01:F07A":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0F7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN63:F0BB":
            return "ک"
        if ip == "NOORIN63:F0C0" and nxt == "NOORIN82:F099":
            return "ے"
        if ip == "NOORIN48:F0E4" and nxt == "NOORIN63:F0BB":
            return "ک"
        if ip == "NOORIN01:F07C" and nxt == "NOORIN05:F083":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0B8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN57:F044":
            return "ت"
        if ip in ("NOORIN01:F029", "NOORIN82:F099", "NOORIN01:F03A") and nxt in (
            "NOORIN01:F0D4", "NOORIN01:F028", "NOORIN01:F029",
        ):
            return "،"
        return pua_map.get(key, "")
    if key == "NOORIN54:F0CB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and nxt == "NOORIN63:F0F1":
            return "م"
        if ip == "NOORIN48:F0E4" and nxt == "NOORIN15:F0B4":
            return "س"
        if ip == "NOORIN05:F0E0" and nxt == "NOORIN57:F075":
            return "ر"
        if ip == "NOORIN11:F046" and nxt == "NOORIN63:F0DF":
            return "پ"
        if ip == "NOORIN63:F0C9" and nxt == "NOORIN05:F083":
            return "ے"
        return pua_map.get(key, "")

    if key == "NOORIN89:F07A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN82:F063":
            return "یار"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F02A":
            return "نا"
        return pua_map.get(key, "")
    if key == "NOORIN11:F0AD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F0EA" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F058":
            return "یے"
        if ip == "NOORIN08:F065" and prev == "NOORIN01:F05A" and nxt == "NOORIN81:F059":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN35:F06B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F1" and prev == "NOORIN59:F0F1" and nxt == "NOORIN63:F0C3":
            return "نو"
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN81:F059":
            return "نو"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0C9":
            return "گ"
        return pua_map.get(key, "")
    if key == "NOORIN13:F0D0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F053" and prev == "NOORIN01:F053" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F05D":
            return "ت"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F05D":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN06:F09E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN01:F09D":
            return "ڑے"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A":
            return "یر"
        return pua_map.get(key, "")
    if key == "NOORIN56:F0E7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0F1" and prev == "NOORIN63:F0F1" and nxt == "NOORIN81:F036":
            return "ت"
        if ip == "NOORIN82:F08C" and prev == "NOORIN82:F08C" and nxt == "NOORIN81:F06D":
            return "ض"
        return pua_map.get(key, "")
    if key == "NOORIN10:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F077":
            return "ل"
        if ip == "NOORIN48:F0E3" and prev == "NOORIN48:F0E3" and nxt == "NOORIN01:F077":
            return "ل"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F077":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN25:F098":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN05:F083":
            return "ہون"
        if nxt == "NOORIN12:F088":
            return "گئی"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN56:F0D8":
            return "شوق"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN12:F088":
            return "گئی"
        return pua_map.get(key, "")
    if key == "NOORIN07:F055":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN57:F037":
            return "ہئے"
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN63:F0DF":
            return "پوڑ"
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F0D4":
            return "پوڑ"
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F07A":
            return "پوڑ"
        return pua_map.get(key, "")
    if key == "NOORIN05:F045":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN05:F063":
            return "یر"
        if nxt == "NOORIN01:F059":
            return "ء"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN08:F0A7":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F03A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN85:F08A":
            return "دھیک"
        if ip == "NOORIN63:F0C9" and prev == "NOORIN63:F0C9" and nxt == "NOORIN01:F058":
            return "گ"
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN04:F0C8" and prev == "NOORIN04:F0C8" and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN27:F094":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07A":
            return "ھے"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN82:F09E":
            return ""
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN82:F09E":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F062":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F087" and prev == "NOORIN82:F087" and nxt == "NOORIN82:F099":
            return "قا"
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3":
            return "کو"
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0B4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0F1" and prev == "NOORIN63:F0F1" and nxt == "NOORIN22:F037":
            return "ن"
        if ip == "NOORIN63:F0F1" and prev == "NOORIN63:F0F1" and nxt == "NOORIN85:F08A":
            return "دین"
        if ip == "NOORIN63:F0F1" and prev == "NOORIN63:F0F1" and nxt == "NOORIN01:F057":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0FA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN07:F0AA":
            return "رے"
        if ip == "NOORIN81:F082" and prev == "NOORIN81:F082" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021":
            return ""
        if ip == "NOORIN57:F031" and prev == "NOORIN63:F0C3" and nxt == "NOORIN63:F0C6":
            return "کے"
        return pua_map.get(key, "")
    if key == "NOORIN76:F0F9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN21:F083":
            return "ڑ"
        if nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN06:F021":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN82:F063":
            return "یار"
        if ip == "NOORIN06:F027" and prev == "NOORIN06:F027" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN82:F030" and prev == "NOORIN82:F030" and nxt == "NOORIN82:F099":
            return "کر"
        return pua_map.get(key, "")
    if key == "NOORIN29:F0F9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F030" and prev == "NOORIN57:F030" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN06:F084" and prev == "NOORIN06:F084" and nxt == "NOORIN81:F082":
            return ""
        if ip == "NOORIN04:F0BD" and prev == "NOORIN04:F0BD" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F0A9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F0" and prev == "NOORIN59:F0F0" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN05:F083":
            return "ہون"
        if ip == "NOORIN48:F0E2" and prev == "NOORIN48:F0E2" and nxt == "NOORIN82:F02A":
            return "نا"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN57:F044":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0EE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN63:F0C3":
            return "ک"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F067":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN08:F035":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F028":
            return "ے"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN85:F08A":
            return "ے"
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN01:F057":
            return "ے"
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F0E2":
        return pua_map.get(key, "ل")
    if key == "NOORIN63:F0DA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN05:F083":
            return "ہون"
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN57:F044":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN35:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN48:F0EB":
            return "ہم"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN81:F059":
            return "ے"
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F09B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F031" and prev == "NOORIN04:F02C" and nxt == "NOORIN63:F0D1":
            return "لاو"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN81:F040":
            return "ت"
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F0D4":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0E6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F0B8" and prev == "NOORIN04:F0B8" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN63:F0BB":
            return "ا"
        if ip == "NOORIN82:F03B" and prev == "NOORIN82:F03B" and nxt == "NOORIN01:F0D4":
            return "وا"
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN21:F0A2":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN78:F082":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E3" and prev == "NOORIN63:F0E3" and nxt == "NOORIN01:F057":
            return "چ"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0BB":
            return "کاہ"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F02A":
            return "نا"
        if ip == "NOORIN07:F028" and prev == "NOORIN07:F028" and nxt == "NOORIN82:F02A":
            return "نا"
        return pua_map.get(key, "")
    if key == "NOORIN07:F0F2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05B":
            return "ب"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0B6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F02A":
            return "نا"
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN05:F083":
            return "ہو"
        return pua_map.get(key, "")
    if key == "NOORIN04:F057":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F0D4":
            return "،"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A":
            return ""
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN56:F0CE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0F9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F05A" and prev == "NOORIN57:F05A" and nxt == "NOORIN01:F03A":
            return "ج"
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN01:F03A":
            return "ج"
        return pua_map.get(key, "")
    if key == "NOORIN27:F086":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN06:F027" and prev == "NOORIN06:F027" and nxt == "NOORIN01:F07A":
            return "ھر"
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F06E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F059" and prev == "NOORIN01:F059" and nxt == "NOORIN01:F07A":
            return "ء"
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN22:F037":
            return "ن"
        if ip == "NOORIN57:F075" and prev == "NOORIN57:F075" and nxt == "NOORIN01:F05A":
            return "ر"
        if nxt == "NOORIN05:F083":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN16:F0E3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN85:F08A":
            return "د"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F03A":
            return "ن"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN07:F06B":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN07:F037":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F09C" and prev == "NOORIN81:F09C" and nxt == "NOORIN01:F057":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F057":
            return "آپو"
        if ip == "NOORIN63:F0E0" and prev == "NOORIN63:F0E0" and nxt == "NOORIN01:F057":
            return "آپنی"
        if ip == "NOORIN08:F05E" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F057":
            return "آپنی"
        return pua_map.get(key, "")
    if key == "NOORIN12:F06F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F07C":
            return "ھ"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F053":
            return "ھ"
        if ip == "NOORIN04:F02C" and prev == "NOORIN04:F02C" and nxt == "NOORIN01:F07C":
            return "ھ"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F07C":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN09:F07A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN81:F0C3":
            return "ف"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F065":
            return "ڈر"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN82:F02A":
            return "نا"
        return pua_map.get(key, "")
    if key == "NOORIN18:F048":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN22:F037":
            return "ن"
        if ip == "NOORIN81:F0A4" and prev == "NOORIN81:F0A4" and nxt == "NOORIN82:F099":
            return "کر"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN82:F099":
            return "کر"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0E2":
            return "مان"
        return pua_map.get(key, "")
    if key == "NOORIN66:F04B":
        return pua_map.get(key, "")
    if key == "NOORIN17:F071":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN57:F044":
            return "ر"
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN01:F0D4":
            return "ر"
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F025":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN63:F0E2":
            return "ماس"
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN22:F037":
            return "ماس"
        return pua_map.get(key, "")
    if key == "NOORIN09:F026":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN41:F076" and prev == "NOORIN41:F076" and nxt == "NOORIN01:F03A":
            return ""
        if nxt == "NOORIN01:F062":
            return "طرح"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F062":
            return "طرح"
        if ip == "NOORIN18:F0A9" and prev == "NOORIN18:F0A9" and nxt == "NOORIN07:F0B2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN61:F0D5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F057":
            return "آپد"
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN48:F0E3":
            return "ون"
        return pua_map.get(key, "")
    if key == "NOORIN67:F0D5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F05A":
            return "ر"
        if nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN17:F0F1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN81:F082" and prev == "NOORIN81:F082" and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN20:F02D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN10:F0F5":
            return ""
        if nxt == "NOORIN63:F0C2":
            return "تو"
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN82:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN20:F02D" and prev == "NOORIN20:F02D" and nxt == "NOORIN82:F03A":
            return ""
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN04:F0C7":
            return "ک"
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F08B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F1" and prev == "NOORIN59:F0F1" and nxt == "NOORIN01:F05A":
            return "ے"
        if ip == "NOORIN01:F079" and prev == "NOORIN01:F079" and nxt == "NOORIN63:F0C6":
            return "ے"
        if ip == "NOORIN63:F0C4" and prev == "NOORIN63:F0C4" and nxt == "NOORIN63:F0C6":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0AA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E2" and prev == "NOORIN48:F0E2" and nxt == "NOORIN01:F06B":
            return "س"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN83:F0D6":
            return "ہمت"
        if nxt == "NOORIN83:F0D6":
            return "ہمت"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN85:F08A":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN15:F024":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN10:F0E2":
            return "د"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN81:F021":
            return "ے"
        if ip == "NOORIN82:F043" and prev == "NOORIN82:F043" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN15:F02A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN63:F0C7":
            return "گا"
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return "ے"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F067":
            return "ڈر"
        return pua_map.get(key, "")
    if key == "NOORIN07:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN82:F02A":
            return "نا"
        if nxt == "NOORIN54:F053":
            return ""
        if ip == "NOORIN88:F035" and prev == "NOORIN88:F035" and nxt == "NOORIN01:F0D4":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN11:F05A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN06:F05F":
            return "ے"
        if nxt == "NOORIN11:F05A":
            return ""
        if ip == "NOORIN11:F05A" and prev == "NOORIN11:F05A" and nxt == "NOORIN19:F055":
            return ""
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN48:F0E2":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN19:F047":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN06:F027" and prev == "NOORIN06:F027" and nxt == "NOORIN57:F044":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN26:F066":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F077":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN42:F03B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F04A" and prev == "NOORIN57:F04A" and nxt == "NOORIN63:F0C1":
            return "ک"
        if ip == "NOORIN76:F065" and prev == "NOORIN76:F065" and nxt == "NOORIN81:F082":
            return "سا"
        if nxt == "NOORIN63:F0BB":
            return "کا"
        if ip == "NOORIN75:F0CB" and prev == "NOORIN75:F0CB" and nxt == "NOORIN82:F099":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN17:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F028" and prev == "NOORIN81:F028" and nxt == "NOORIN11:F059":
            return "ے"
        if ip == "NOORIN01:F07D" and prev == "NOORIN01:F07D" and nxt == "NOORIN63:F0CD":
            return "گو"
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN81:F059":
            return "نئے"
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F03A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN63:F0E2":
            return "ما"
        if nxt == "NOORIN01:F03A":
            return "ما"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN22:F037":
            return "ک"
        if ip == "NOORIN59:F0F0" and prev == "NOORIN59:F0F0" and nxt == "NOORIN05:F083":
            return "ئی"
        return pua_map.get(key, "")
    if key == "NOORIN20:F069":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F02A":
            return "ر"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN81:F083":
            return "ر"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN81:F036":
            return "پ"
        return pua_map.get(key, "")
    if key == "NOORIN75:F043":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN82:F03A":
            return "نہ"
        if nxt == "NOORIN81:F030":
            return "انی"
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN12:F07B":
            return "گھڑ"
        return pua_map.get(key, "")
    if key == "NOORIN81:F047":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN10:F02E":
            return "ے"
        if ip == "NOORIN57:F037" and prev == "NOORIN57:F037" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F073":
            return "ف"
        if nxt == "NOORIN63:F0BB":
            return "کالا"
        return pua_map.get(key, "")
    if key == "NOORIN22:F038":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0F2":
            return "ما"
        if nxt == "NOORIN05:F083":
            return "ہ"
        if ip == "NOORIN01:F05D" and prev == "NOORIN01:F05D" and nxt == "NOORIN01:F078":
            return "م"
        if ip == "NOORIN57:F04A" and prev == "NOORIN57:F04A" and nxt == "NOORIN05:F083":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0BF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F05A":
            return "ر"
        if nxt == "NOORIN04:F02C":
            return "ر"
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN63:F0BB":
            return "کا"
        return pua_map.get(key, "")
    if key == "NOORIN20:F03B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0E2":
            return "ما"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN63:F0E2":
            return "ما"
        return pua_map.get(key, "")
    if key == "NOORIN16:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F075" and prev == "NOORIN01:F075" and nxt == "NOORIN01:F077":
            return "ل"
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN56:F0D1" and prev == "NOORIN56:F0D1" and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F077":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN17:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0D1" and prev == "NOORIN63:F0D1" and nxt == "NOORIN01:F057":
            return "لا"
        if ip == "NOORIN63:F0D1" and prev == "NOORIN63:F0D1" and nxt == "NOORIN74:F032":
            return "لا"
        if ip == "NOORIN63:F0D1" and prev == "NOORIN63:F0D1" and nxt == "NOORIN01:F0D4":
            return "لا"
        return pua_map.get(key, "")
    if key == "NOORIN19:F058":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F058":
            return "ں"
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN01:F058":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0C7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0C3":
            return "کو"
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN63:F0C3":
            return "یار"
        if ip == "NOORIN10:F0F5" and prev == "NOORIN10:F0F5" and nxt == "NOORIN04:F0B8":
            return "ک"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0C4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F1" and prev == "NOORIN59:F0F1" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F058":
            return "ے"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F0D4":
            return "ے"
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN82:F02A":
            return "نا"
        return pua_map.get(key, "")
    if key == "NOORIN06:F091":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN10:F0DB" and prev == "NOORIN10:F0DB" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN48:F0E3" and prev == "NOORIN48:F0E3" and nxt == "NOORIN14:F0F7":
            return "نی"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN81:F036":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0E7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN63:F0B8":
            return "ت"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN04:F05E":
            return "ے"
        if nxt == "NOORIN63:F0B8":
            return "قوف"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F08C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN05:F04F" and prev == "NOORIN05:F04F" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN42:F0B2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E0" and prev == "NOORIN63:F0E0" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN05:F08A" and prev == "NOORIN05:F08A" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN48:F0E3" and prev == "NOORIN48:F0E3" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F0D4":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN82:F034":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F043" and prev == "NOORIN82:F043" and nxt == "NOORIN85:F08A":
            return "د"
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN85:F08A":
            return "د"
        if ip == "NOORIN63:F0E3" and prev == "NOORIN63:F0E3" and nxt == "NOORIN85:F08A":
            return "ی"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F05A":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN11:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F024" and prev == "NOORIN81:F024" and nxt == "NOORIN01:F067":
            return "ب"
        if ip == "NOORIN63:F0F1" and prev == "NOORIN63:F0F1" and nxt == "NOORIN01:F03A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN65:F075":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN11:F02C":
            return "کنڈ"
        if ip == "NOORIN59:F0F0" and prev == "NOORIN59:F0F0" and nxt == "NOORIN82:F09A":
            return "کڑ"
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN11:F02C":
            return "کنڈ"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F09F":
            return "ڈھو"
        return pua_map.get(key, "")
    if key == "NOORIN07:F056":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F058":
            return "ں"
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F0D4":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN69:F0A5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F070" and prev == "NOORIN57:F070" and nxt == "NOORIN01:F077":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN82:F02E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F0D4":
            return "ے"
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN63:F0C3":
            return "ے"
        if nxt == "NOORIN09:F07D":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F065":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN66:F046":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F058":
            return "ھ"
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN01:F058":
            return "ر"
        if ip == "NOORIN12:F079" and prev == "NOORIN12:F079" and nxt == "NOORIN12:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F0A6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F07B":
            return "ر"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F0D4":
            return "ے"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F07C":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0E9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN48:F0EC":
            return "ے"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN05:F083":
            return "ہ"
        if ip == "NOORIN01:F07C" and prev == "NOORIN01:F07C" and nxt == "NOORIN12:F043":
            return "ھ"
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN05:F0F0":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN81:F086":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN07:F067":
            return "ے"
        if nxt == "NOORIN08:F036":
            return "ے"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN06:F0CD":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN05:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F0D4":
            return "کی"
        if nxt == "NOORIN05:F0E0":
            return "گ"
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN57:F05A":
            return "ج"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F0A7":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN81:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F04A":
            return "تک"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN81:F04A":
            return "تک"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C3":
            return "کو"
        if ip == "NOORIN01:F06B" and prev == "NOORIN01:F06B" and nxt == "NOORIN81:F04A":
            return "تک"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0BE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN56:F0D1":
            return "ے"
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN57:F044":
            return "ت"
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN01:F058":
            return "د"
        if ip == "NOORIN63:F0C4" and prev == "NOORIN63:F0C4" and nxt == "NOORIN14:F0F7":
            return "کھ"
        return pua_map.get(key, "")
    if key == "NOORIN02:F09F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F070" and prev == "NOORIN57:F070" and nxt == "NOORIN08:F08B":
            return "و"
        if ip == "NOORIN57:F070" and prev == "NOORIN57:F070" and nxt == "NOORIN01:F057":
            return "و"
        if ip == "NOORIN57:F070" and prev == "NOORIN57:F070" and nxt == "NOORIN05:F083":
            return "و"
        if ip == "NOORIN57:F070" and prev == "NOORIN57:F070" and nxt == "NOORIN01:F058":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN16:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN48:F0F0":
            return "ھ"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN01:F07C":
            return "ھ"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN48:F0F0":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN85:F027":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F077":
            return "ل"
        if ip == "NOORIN81:F083" and prev == "NOORIN81:F083" and nxt == "NOORIN01:F077":
            return "ل"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F077":
            return "ک"
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN01:F077":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN09:F062":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN19:F097" and prev == "NOORIN19:F097" and nxt == "NOORIN82:F099":
            return "ے"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F02A":
            return "نال"
        if ip == "NOORIN59:F0F0" and prev == "NOORIN59:F0F0" and nxt == "NOORIN01:F0D4":
            return "ئی"
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN01:F0D4":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN06:F05D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN85:F08A":
            return "د"
        if nxt == "NOORIN06:F05D":
            return "گ"
        if ip == "NOORIN06:F05D" and prev == "NOORIN06:F05D" and nxt == "NOORIN63:F0CD":
            return "گ"
        return pua_map.get(key, "")
    if key == "NOORIN35:F0C4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F023" and prev == "NOORIN82:F023" and nxt == "NOORIN81:F021":
            return "ہ"
        if ip == "NOORIN21:F083" and prev == "NOORIN21:F083" and nxt == "NOORIN63:F0E2":
            return "ما"
        return pua_map.get(key, "")
    if key == "NOORIN08:F0B8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN09:F095":
            return "ر"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN19:F025":
            return "ر"
        if ip == "NOORIN01:F0A7" and prev == "NOORIN01:F0A7" and nxt == "NOORIN22:F037":
            return "ے"
        if ip == "NOORIN54:F02A" and prev == "NOORIN54:F02A" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F06B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN01:F03A":
            return "ر"
        if ip == "NOORIN11:F02C" and prev == "NOORIN11:F02C" and nxt == "NOORIN05:F083":
            return "ہ"
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return "دھ"
        if nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN82:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05D" and prev == "NOORIN01:F05D" and nxt == "NOORIN81:F021":
            return "ت"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F02A":
            return "ر"
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN63:F0E2":
            return "ما"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN63:F0DF":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN82:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F03A":
            return "د"
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN09:F094":
            return "د"
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN09:F051":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN15:F05A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F079":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN11:F09B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05D":
            return "ت"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F05D":
            return "ت"
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN59:F0F1":
            return "ئے"
        return pua_map.get(key, "")
    if key == "NOORIN08:F042":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN04:F0B8":
            return "ے"
        if nxt == "NOORIN01:F067":
            return "ک"
        if nxt == "NOORIN63:F0BB":
            return "کا"
        if ip == "NOORIN01:F076" and prev == "NOORIN01:F076" and nxt == "NOORIN11:F087":
            return "گ"
        return pua_map.get(key, "")
    if key == "NOORIN68:F0D9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F0D4":
            return "ے"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F058":
            return "ے"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN05:F084":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN81:F05F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN09:F051":
            return "ٹھ"
        if ip == "NOORIN01:F05D" and prev == "NOORIN01:F05D" and nxt == "NOORIN81:F021":
            return "ت"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN81:F082":
            return "سا"
        return pua_map.get(key, "")
    if key == "NOORIN14:F06E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN06:F05F" and prev == "NOORIN06:F05F" and nxt == "NOORIN82:F099":
            return "ی"
        if ip == "NOORIN01:F075" and prev == "NOORIN01:F075" and nxt == "NOORIN63:F0C5":
            return "ے"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return "و"
        if ip == "NOORIN35:F0D0" and prev == "NOORIN35:F0D0" and nxt == "NOORIN63:F0C5":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0F4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F058":
            return "ے"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return "ے"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN63:F0C3":
            return "ے"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN85:F08A":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN12:F038":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN57:F044":
            return "د"
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F0D4":
            return "د"
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN08:F04D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0C3":
            return "ی"
        if nxt == "NOORIN06:F027":
            return "ی"
        if nxt == "NOORIN57:F044":
            return "ی"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN08:F0BF":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN06:F054":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F030" and prev == "NOORIN81:F030" and nxt == "NOORIN01:F03A":
            return "و"
        if ip == "NOORIN57:F037" and prev == "NOORIN57:F037" and nxt == "NOORIN57:F037":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0AD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN06:F046" and prev == "NOORIN06:F046" and nxt == "NOORIN16:F06F":
            return "ی"
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F03A":
            return "و"
        if ip == "NOORIN06:F046" and prev == "NOORIN06:F046" and nxt == "NOORIN01:F0D4":
            return "ی"
        if ip == "NOORIN01:F068" and prev == "NOORIN01:F068" and nxt == "NOORIN01:F03A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN04:F04D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN63:F0D1":
            return "ہ"
        if ip == "NOORIN30:F043" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F0D4":
            return "ی"
        if ip == "NOORIN30:F043" and nxt == "NOORIN01:F03A":
            return "ی"
        if ip == "NOORIN30:F043" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN07:F08A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F02A":
            return "ی"
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN82:F02A":
            return "ی"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN82:F02A":
            return "ی"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN21:F083":
            return "ڑ"
        return pua_map.get(key, "")
    if key == "NOORIN62:F0C1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F053":
            return "گ"
        if ip == "NOORIN01:F07E" and prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F053":
            return "گ"
        if ip == "NOORIN82:F081" and prev == "NOORIN82:F081" and nxt == "NOORIN82:F053":
            return "گ"
        return pua_map.get(key, "")
    if key == "NOORIN05:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C3":
            return "ی"
        if nxt == "NOORIN63:F0C2":
            return "ی"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN63:F0C3":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN11:F0C7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN05:F083":
            return "د"
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN82:F053":
            return "دھ"
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN48:F0F0":
            return "دھ"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN81:F082":
            return "،"
        return pua_map.get(key, "")
    if key == "NOORIN08:F0CE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F079":
            return "و"
        if nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F079":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN16:F05E":
        return pua_map.get(key, "و")
    if key == "NOORIN13:F084":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F090" and prev == "NOORIN83:F0E1" and nxt == "NOORIN63:F0C3":
            return "ے"
        if ip == "NOORIN07:F0EC" and prev == "NOORIN01:F067" and nxt == "NOORIN63:F0C5":
            return "ے"
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN82:F02A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN62:F0D8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F025" and prev == "NOORIN82:F025" and nxt == "NOORIN01:F03A":
            return "ی"
        if ip == "NOORIN82:F030" and prev == "NOORIN82:F030" and nxt == "NOORIN63:F0C2":
            return "ا"
        if ip == "NOORIN81:F087" and prev == "NOORIN81:F087" and nxt == "NOORIN01:F028":
            return "ا"
        if ip == "NOORIN14:F0F7" and prev == "NOORIN14:F0F7" and nxt == "NOORIN82:F099":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN48:F0E8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN48:F0E8":
            return "ا"
        if ip == "NOORIN48:F0E8" and prev == "NOORIN48:F0E8" and nxt == "NOORIN63:F0C6":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN82:F086":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F09F" and prev == "NOORIN81:F09F" and nxt == "NOORIN81:F094":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN12:F03B":
        return pua_map.get(key, "ر")
    if key == "NOORIN22:F0AB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN81:F021":
            return "ر"
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN63:F0C3":
            return "ر"
        if nxt == "NOORIN01:F07A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN49:F025":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F05A":
            return "ا"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F05A":
            return "ا"
        if ip == "NOORIN01:F07E" and prev == "NOORIN81:F060" and nxt == "NOORIN48:F0E4":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN51:F0F0":
        return pua_map.get(key, "خ")
    if key == "NOORIN14:F079":
        return pua_map.get(key, "پ")
    if key == "NOORIN15:F074":
        return pua_map.get(key, "ا")
    if key == "NOORIN07:F0E3":
        return pua_map.get(key, "ہ")
    if key == "NOORIN01:F04C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN51:F0F3" and prev == "NOORIN51:F0F3" and nxt == "NOORIN63:F0CD":
            return "ک"
        if ip == "NOORIN01:F05B" and prev == "NOORIN01:F05B" and nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN13:F063" and prev == "NOORIN13:F063" and nxt == "NOORIN63:F0CD":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN83:F0F3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F5" and prev == "NOORIN01:F067" and nxt == "NOORIN82:F02A":
            return "ک"
        if ip == "NOORIN01:F079" and prev == "NOORIN01:F079" and nxt == "NOORIN01:F034":
            return "ک"
        if ip == "NOORIN01:F06C" and prev == "NOORIN01:F06C" and nxt == "NOORIN63:F0BB":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN82:F021":
        return pua_map.get(key, "ن")
    if key == "NOORIN11:F0A6":
        return pua_map.get(key, "ا")
    if key == "NOORIN13:F069":
        return pua_map.get(key, "ج")
    if key == "NOORIN46:F07C":
        return pua_map.get(key, "ب")
    if key == "NOORIN06:F0AC":
        return pua_map.get(key, "ے")
    if key == "NOORIN48:F044":
        return pua_map.get(key, "ے")
    if key == "NOORIN11:F0EE":
        return pua_map.get(key, "ں")
    if key == "NOORIN25:F048":
        return pua_map.get(key, "ی")
    if key == "NOORIN15:F0B4":
        return pua_map.get(key, "و")
    if key == "NOORIN81:F055":
        return pua_map.get(key, "ی")
    if key == "NOORIN04:F0AA":
        return pua_map.get(key, "ک")
    if key == "NOORIN11:F058":
        return pua_map.get(key, "ک")
    if key == "NOORIN28:F049":
        return pua_map.get(key, "ے")
    if key == "NOORIN15:F0F8":
        return pua_map.get(key, "ھ")
    if key == "NOORIN01:F0CC":
        return pua_map.get(key, "ک")
    if key == "NOORIN30:F03F":
        return pua_map.get(key, "ر")
    if key == "NOORIN12:F08C":
        return pua_map.get(key, "ب")
    if key == "NOORIN25:F077":
        return pua_map.get(key, "ں")
    if key == "NOORIN24:F0EE":
        return pua_map.get(key, "ھ")
    if key == "NOORIN82:F08F":
        return pua_map.get(key, "ھ")
    if key == "NOORIN76:F05E":
        return pua_map.get(key, "ا")
    if key == "NOORIN81:F0B1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F022" and prev == "NOORIN57:F022" and nxt == "NOORIN57:F043":
            return "ر"
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN08:F057" and prev == "NOORIN08:F057" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN10:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F051" and prev == "NOORIN01:F067" and nxt == "NOORIN57:F061":
            return "ک"
        if ip == "NOORIN01:F028" and prev == "NOORIN01:F028" and nxt == "NOORIN57:F044":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN29:F05C":
        return pua_map.get(key, "ر")
    if key == "NOORIN53:F096":
        return pua_map.get(key, "ہ")
    if key == "NOORIN31:F09B":
        return pua_map.get(key, "ے")
    if key == "NOORIN66:F0A9":
        return pua_map.get(key, "ت")
    if key == "NOORIN07:F0A4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F07B" and prev == "NOORIN81:F07B" and nxt == "NOORIN63:F0E2":
            return "ا"
        if ip == "NOORIN81:F07B" and prev == "NOORIN81:F07B" and nxt == "NOORIN01:F07A":
            return "ا"
        if ip == "NOORIN81:F07B" and prev == "NOORIN81:F07B" and nxt == "NOORIN22:F037":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN21:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN63:F0E2":
            return "ر"
        if nxt == "NOORIN01:F067":
            return "ک"
        if ip == "NOORIN82:F071" and prev == "NOORIN82:F071" and nxt == "NOORIN05:F083":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN57:F04C":
        return pua_map.get(key, "س")
    if key == "NOORIN17:F025":
        return pua_map.get(key, "د")
    if key == "NOORIN22:F06C":
        return pua_map.get(key, "ر")
    if key == "NOORIN28:F0A9":
        return pua_map.get(key, "ں")
    if key == "NOORIN06:F0D4":
        return pua_map.get(key, "د")
    if key == "NOORIN25:F04D":
        return pua_map.get(key, "ھ")
    if key == "NOORIN33:F039":
        return pua_map.get(key, "ے")
    if key == "NOORIN37:F06B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F03F" and nxt == "NOORIN63:F0E6":
            return "س"
        if ip == "NOORIN01:F07E" and prev == "NOORIN82:F099" and nxt == "NOORIN81:F083":
            return "س"
        if nxt == "NOORIN74:F0A2":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN53:F0B6":
        return pua_map.get(key, "ں")
    if key == "NOORIN18:F0A2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F057":
            return "ا"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return "ا"
        if ip == "NOORIN64:F0D8" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F0DE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return "ے"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F029":
            return "ے"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN63:F0C5":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN49:F0A4":
        return pua_map.get(key, "ا")
    if key == "NOORIN29:F052":
        return pua_map.get(key, "ں")
    if key == "NOORIN22:F024":
        return pua_map.get(key, "و")
    if key == "NOORIN22:F065":
        return pua_map.get(key, "و")
    if key == "NOORIN06:F0CD":
        return pua_map.get(key, "و")
    if key == "NOORIN01:F0A9":
        return pua_map.get(key, "ھ")
    if key == "NOORIN09:F079":
        return pua_map.get(key, "ں")
    if key == "NOORIN56:F0E0":
        return pua_map.get(key, "ہ")
    if key == "NOORIN10:F0E6":
        return pua_map.get(key, "ی")
    if key == "NOORIN21:F0A6":
        return pua_map.get(key, "")
    if key == "NOORIN04:F0D5":
        return pua_map.get(key, "س")
    if key == "NOORIN85:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN73:F0EE" and prev == "NOORIN63:F0F1" and nxt == "NOORIN82:F03A":
            return "ن"
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN82:F099":
            return "ن"
        if ip == "NOORIN48:F0EC" and prev == "NOORIN48:F0EC" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F0E5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE":
            return "چ"
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN81:F082":
            return "س"
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN22:F037":
            return "چ"
        return pua_map.get(key, "")
    if key == "NOORIN11:F0AA":
        return pua_map.get(key, "آ")
    if key == "NOORIN05:F0D3":
        return pua_map.get(key, "ش")
    if key == "NOORIN09:F0A6":
        return pua_map.get(key, "ا")
    if key == "NOORIN01:F03B":
        return pua_map.get(key, "ر")
    if key == "NOORIN43:F065":
        return pua_map.get(key, "ا")
    if key == "NOORIN18:F06B":
        return pua_map.get(key, "ا")
    if key == "NOORIN04:F0E8":
        return pua_map.get(key, "پ")
    if key == "NOORIN24:F04F":
        return pua_map.get(key, "ک")
    if key == "NOORIN15:F04F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN63:F0E2":
            return "د"
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F0D4":
            return "د"
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F067":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN21:F0EC":
        return pua_map.get(key, "س")
    if key == "NOORIN58:F0AA":
        return pua_map.get(key, "ں")
    if key == "NOORIN16:F08B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN81:F065":
            return "د"
        if ip == "NOORIN81:F065" and prev == "NOORIN81:F065" and nxt == "NOORIN01:F0D4":
            return "ا"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN57:F075":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN11:F096":
        return pua_map.get(key, "ا")
    if key == "NOORIN46:F06B":
        return pua_map.get(key, "و")
    if key == "NOORIN42:F0F0":
        return pua_map.get(key, "ں")
    if key == "NOORIN05:F055":
        return pua_map.get(key, "ر")
    if key == "NOORIN12:F09F":
        return pua_map.get(key, "س")
    if key == "NOORIN35:F0B9":
        return pua_map.get(key, "ر")
    if key == "NOORIN31:F081":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F02C" and prev == "NOORIN04:F02C" and nxt == "NOORIN01:F07A":
            return "ق"
        if nxt == "NOORIN59:F0F0":
            return "ق"
        if ip == "NOORIN06:F027" and prev == "NOORIN06:F027" and nxt == "NOORIN59:F0F0":
            return "ق"
        return pua_map.get(key, "")
    if key == "NOORIN12:F0B7":
        return pua_map.get(key, "و")
    if key == "NOORIN10:F095":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN08:F069" and prev == "NOORIN08:F069" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN24:F048":
        return pua_map.get(key, "ک")
    if key == "NOORIN50:F038":
        return pua_map.get(key, "ر")
    if key == "NOORIN18:F06D":
        return pua_map.get(key, "ھ")
    if key == "NOORIN37:F077":
        return pua_map.get(key, "ا")
    if key == "NOORIN15:F055":
        return pua_map.get(key, "ھ")
    if key == "NOORIN67:F04B":
        return pua_map.get(key, "ھ")
    if key == "NOORIN24:F0B1":
        return pua_map.get(key, "ک")
    if key == "NOORIN05:F0ED":
        return pua_map.get(key, "پ")
    if key == "NOORIN09:F0AD":
        return pua_map.get(key, "و")
    if key == "NOORIN04:F034":
        return pua_map.get(key, "د")
    if key == "NOORIN14:F0DE":
        return pua_map.get(key, "ھ")
    if key == "NOORIN08:F0A8":
        return pua_map.get(key, "")
    if key == "NOORIN12:F0C9":
        return pua_map.get(key, "ے")
    if key == "NOORIN57:F038":
        return pua_map.get(key, "ر")
    if key == "NOORIN81:F08C":
        return pua_map.get(key, "")
    if key == "NOORIN18:F03A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN41:F076" and prev == "NOORIN41:F076" and nxt == "NOORIN82:F099":
            return "ے"
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN04:F0B6":
            return "ے"
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN85:F08A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN12:F084":
        return pua_map.get(key, "")
    if key == "NOORIN19:F055":
        return pua_map.get(key, "ر")
    if key == "NOORIN47:F068":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E1" and prev == "NOORIN06:F027" and nxt == "NOORIN04:F02D":
            return "ل"
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN48:F0E2":
            return "و"
        if ip == "NOORIN12:F0D6" and prev == "NOORIN01:F07A" and nxt == "NOORIN48:F0E2":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN07:F0A1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN16:F071":
            return "س"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN81:F083":
            return "س"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN16:F071":
            return "م"
        return pua_map.get(key, "")
    if key == "NOORIN06:F0D7":
        return pua_map.get(key, "ی")
    if key == "NOORIN37:F06E":
        return pua_map.get(key, "ہ")
    if key == "NOORIN82:F085":
        return pua_map.get(key, "غ")
    if key == "NOORIN09:F09D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN16:F0A3" and prev == "NOORIN01:F0D4" and nxt == "NOORIN82:F099":
            return ""
        if ip == "NOORIN63:F0DF" and prev == "NOORIN63:F0DF" and nxt == "NOORIN63:F0D1":
            return ""
        if ip == "NOORIN16:F0A3" and prev == "NOORIN05:F084" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F024":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN48:F0E2":
            return ""
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN81:F071":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F043":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN01:F077":
            return ""
        if ip == "NOORIN01:F099" and prev == "NOORIN01:F099" and nxt == "NOORIN63:F0E2":
            return ""
        if ip == "NOORIN01:F09D" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F022":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN01:F03A":
            return ""
        if nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0D3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN83:F0D6":
            return ""
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN83:F0D6":
            return ""
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN83:F0D6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F04F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN63:F0F1":
            return ""
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN06:F027":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN54:F053":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN07:F049" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F05D" and prev == "NOORIN01:F05D" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F048":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN07:F048":
            return ""
        if ip == "NOORIN07:F048" and prev == "NOORIN07:F048" and nxt == "NOORIN01:F029":
            return ""
        if nxt == "NOORIN04:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN49:F0C3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F1" and prev == "NOORIN59:F0F1" and nxt == "NOORIN82:F03A":
            return ""
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN63:F0C3":
            return ""
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN69:F0A4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN01:F0A7" and prev == "NOORIN01:F0A7" and nxt == "NOORIN85:F08A":
            return ""
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F029":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F028" and prev == "NOORIN01:F028" and nxt == "NOORIN01:F06B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F093":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN59:F0F0":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0C5":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F048":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0CF" and prev == "NOORIN63:F0CF" and nxt == "NOORIN01:F0D4":
            return ""
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F0D6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0A6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E6" and prev == "NOORIN63:F0E6" and nxt == "NOORIN08:F04E":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN08:F04E":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F04E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0A6" and prev == "NOORIN63:F0A6" and nxt == "NOORIN01:F0D4":
            return ""
        if ip == "NOORIN63:F0A6" and prev == "NOORIN63:F0A6" and nxt == "NOORIN63:F0CD":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F097":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN82:F099":
            return ""
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN26:F0C9":
            return ""
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F067":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN48:F0E4":
            return ""
        if nxt == "NOORIN48:F0E4":
            return ""
        if ip == "NOORIN05:F063" and prev == "NOORIN05:F063" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0BC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0E2":
            return ""
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN05:F083":
            return ""
        if ip == "NOORIN12:F079" and prev == "NOORIN12:F079" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F079":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F099" and prev == "NOORIN01:F099" and nxt == "NOORIN82:F030":
            return ""
        if ip == "NOORIN01:F099" and prev == "NOORIN01:F099" and nxt == "NOORIN82:F02A":
            return ""
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F048":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN04:F0AF":
            return ""
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F08B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN66:F04C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN12:F088":
            return ""
        if ip == "NOORIN01:F068" and prev == "NOORIN01:F068" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F0F3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN16:F06F":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F092":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN82:F02A":
            return ""
        if nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN24:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F048":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F069" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F067":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F081":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F03A":
            return ""
        if nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F063":
            return ""
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN62:F02F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN29:F07E":
            return ""
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN77:F071":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F07E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN62:F02F" and prev == "NOORIN62:F02F" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN82:F02D" and prev == "NOORIN82:F02D" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0DC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return ""
        if nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F04F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F02C" and prev == "NOORIN04:F02C" and nxt == "NOORIN04:F02C":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0D8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F067":
            return ""
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F073":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F066" and prev == "NOORIN01:F066" and nxt == "NOORIN06:F027":
            return ""
        if ip == "NOORIN81:F046" and prev == "NOORIN81:F046" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN03:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F071" and prev == "NOORIN81:F071" and nxt == "NOORIN82:F02A":
            return ""
        if ip == "NOORIN81:F071" and prev == "NOORIN81:F071" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN18:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN39:F07C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C4" and prev == "NOORIN63:F0C4" and nxt == "NOORIN05:F084":
            return ""
        if ip == "NOORIN59:F0F1" and prev == "NOORIN59:F0F1" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F06E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F099" and prev == "NOORIN01:F099" and nxt == "NOORIN01:F07A":
            return ""
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F06B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E0" and prev == "NOORIN63:F0E0" and nxt == "NOORIN63:F0E2":
            return ""
        if ip == "NOORIN16:F0E3" and prev == "NOORIN63:F0E2" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F06C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0C3":
            return ""
        if nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F065":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN81:F037":
            return ""
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F0B4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0DB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F021":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F031":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN12:F088":
            return ""
        if ip == "NOORIN19:F025" and prev == "NOORIN19:F025" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F0D6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN09:F0D6":
            return ""
        if ip == "NOORIN09:F0D6" and prev == "NOORIN09:F0D6" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F090":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F029":
            return ""
        if nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F065":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN04:F0A9" and prev == "NOORIN63:F0C6" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F095":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05C" and prev == "NOORIN01:F05C" and nxt == "NOORIN05:F0E5":
            return ""
        if ip == "NOORIN01:F075" and prev == "NOORIN01:F075" and nxt == "NOORIN82:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN18:F047":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F0C1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F0D4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F076":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F048":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN56:F0DA":
            return ""
        if ip == "NOORIN01:F07D" and prev == "NOORIN01:F07D" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F0DC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return ""
        if nxt == "NOORIN63:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F081":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN05:F083":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN51:F059":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F067" and nxt == "NOORIN52:F099":
            return ""
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN56:F0CE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN22:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E2" and prev == "NOORIN48:F0E2" and nxt == "NOORIN52:F099":
            return ""
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F068":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN40:F0A7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN65:F081":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F036":
            return ""
        if nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN53:F03E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN06:F027" and prev == "NOORIN06:F027" and nxt == "NOORIN81:F040":
            return ""
        if ip == "NOORIN82:F043" and prev == "NOORIN82:F043" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN76:F0DF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F05B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F079" and prev == "NOORIN01:F079" and nxt == "NOORIN48:F0E2":
            return ""
        if ip == "NOORIN01:F06E" and prev == "NOORIN01:F06E" and nxt == "NOORIN48:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F029":
            return ""
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0B3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F059":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN04:F0B6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0D5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F0E6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F065":
            return ""
        if ip == "NOORIN01:F07E" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN60:F05B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0E4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN05:F084":
            return ""
        if ip == "NOORIN01:F066" and prev == "NOORIN01:F066" and nxt == "NOORIN05:F084":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F097":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F0E2" and prev == "NOORIN12:F0E2" and nxt == "NOORIN63:F0C3":
            return ""
        if nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN27:F082":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F04E" and prev == "NOORIN81:F04E" and nxt == "NOORIN06:F027":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN59:F08C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C9" and prev == "NOORIN63:F0C9" and nxt == "NOORIN48:F0E3":
            return ""
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN89:F079" and prev == "NOORIN89:F079" and nxt == "NOORIN01:F07A":
            return ""
        if ip == "NOORIN89:F079" and prev == "NOORIN89:F079" and nxt == "NOORIN63:F0C2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F090":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0F2" and prev == "NOORIN63:F0F2" and nxt == "NOORIN81:F021":
            return ""
        if ip == "NOORIN01:F028" and prev == "NOORIN01:F028" and nxt == "NOORIN81:F021":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F0A8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN81:F059":
            return ""
        if ip == "NOORIN63:F0D1" and prev == "NOORIN63:F0D1" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN79:F0DB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F0D4":
            return ""
        if ip == "NOORIN01:F051" and prev == "NOORIN06:F027" and nxt == "NOORIN82:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN01:F063":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F099":
            return ""
        return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F050":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN08:F065" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F07A":
            return ""
        if ip == "NOORIN63:F0C7" and prev == "NOORIN63:F0C7" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0B5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F024":
            return ""
        if ip == "NOORIN57:F043" and prev == "NOORIN57:F043" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN43:F082":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F067" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F02B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F06A" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F067":
            return ""
        if ip == "NOORIN57:F06A" and prev == "NOORIN01:F03A" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F068":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN82:F03A":
            return ""
        if ip == "NOORIN51:F0C2" and prev == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F064":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN62:F057":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN83:F0D9":
            return ""
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN12:F079" and prev == "NOORIN12:F079" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN40:F08B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F07A":
            return ""
        if ip == "NOORIN13:F04E" and prev == "NOORIN13:F04E" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F09F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN22:F037":
            return ""
        if nxt == "NOORIN06:F046":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F032":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN04:F0D2":
            return ""
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F0E9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F056":
            return ""
        if nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0D5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F088":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F07A":
            return ""
        if nxt == "NOORIN17:F03E":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN76:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN06:F027":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F098":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F082" and prev == "NOORIN81:F082" and nxt == "NOORIN05:F083":
            return ""
        if ip == "NOORIN81:F082" and prev == "NOORIN81:F082" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F0DD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F067":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0E9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07D" and prev == "NOORIN01:F07D" and nxt == "NOORIN01:F03A":
            return ""
        if nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN17:F0EC":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F027":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0BB":
            return ""
        if ip == "NOORIN14:F052" and prev == "NOORIN14:F052" and nxt == "NOORIN04:F0BD":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN70:F096":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F099":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F057":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F074":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN81:F065":
            return ""
        if nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F0EA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN01:F067":
            return ""
        if ip == "NOORIN48:F0E3" and prev == "NOORIN48:F0E3" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F0FA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F067":
            return ""
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN63:F0E0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F08F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN63:F0DF":
            return ""
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN83:F0D9":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN27:F02E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F022" and prev == "NOORIN57:F022" and nxt == "NOORIN07:F071":
            return ""
        if ip == "NOORIN81:F084" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F058":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F056":
            return ""
        if nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F023":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F068" and prev == "NOORIN01:F068" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0AE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN01:F07A":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F09A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN13:F02A" and prev == "NOORIN13:F02A" and nxt == "NOORIN63:F0C5":
            return ""
        if nxt == "NOORIN63:F0BB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F068":
            return ""
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN52:F09B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN76:F02B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F04A" and prev == "NOORIN05:F04A" and nxt == "NOORIN27:F076":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F022" and prev == "NOORIN57:F022" and nxt == "NOORIN01:F067":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0AF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN21:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0E2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN06:F0AF" and prev == "NOORIN06:F0AF" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN06:F0AF" and prev == "NOORIN06:F0AF" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F0AC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN56:F0CE":
            return ""
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F0C5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F058":
            return ""
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F073":
            return ""
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F06B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F0D4":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN07:F0BB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0EE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F06A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0A7" and prev == "NOORIN01:F0A7" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F08F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F0D4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F067":
            return ""
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F08A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F0D5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F063":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F045":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F043" and prev == "NOORIN05:F043" and nxt == "NOORIN63:F0CD":
            return ""
        if nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN85:F028":
            return ""
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN35:F05B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F1" and prev == "NOORIN59:F0F1" and nxt == "NOORIN82:F02A":
            return ""
        if ip == "NOORIN08:F040" and prev == "NOORIN57:F044" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F03D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F1" and prev == "NOORIN59:F0F1" and nxt == "NOORIN82:F02A":
            return ""
        if ip == "NOORIN01:F07D" and prev == "NOORIN01:F07D" and nxt == "NOORIN48:F0E4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F054":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F0B8" and prev == "NOORIN01:F0D4" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F050":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN81:F036":
            return ""
        if ip == "NOORIN15:F059" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN35:F071":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F03A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN07:F071":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F08E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07C":
            return ""
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN01:F07C":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F06F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F05D":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN65:F0A5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F02E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0C3":
            return ""
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F04C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN12:F0F5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN10:F04C" and prev == "NOORIN10:F04C" and nxt == "NOORIN81:F07B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F068":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN79:F071":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return ""
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN08:F07C":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F061":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN82:F099":
            return ""
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN68:F0D2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0AB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN59:F0F1" and prev == "NOORIN59:F0F1" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F043":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F077":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN17:F0F2" and prev == "NOORIN17:F0F2" and nxt == "NOORIN01:F07A":
            return ""
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F0F4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN72:F0C1" and prev == "NOORIN72:F0C1" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN72:F0C1" and prev == "NOORIN72:F0C1" and nxt == "NOORIN01:F03B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F0EB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN04:F02B" and prev == "NOORIN04:F02B" and nxt == "NOORIN06:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F048":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F059" and prev == "NOORIN57:F059" and nxt == "NOORIN01:F056":
            return "و"
        if ip == "NOORIN57:F073" and nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F0B6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F081" and prev == "NOORIN82:F081" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN82:F081" and prev == "NOORIN82:F081" and nxt == "NOORIN07:F067":
            return "سے"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F056":
            return "اں"
        return pua_map.get(key, "")
    if key == "NOORIN60:F0AD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN01:F058":
            return "۔"
        return pua_map.get(key, "")
    if key == "NOORIN13:F031":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN47:F08D":
            return ""
        if nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN56:F0ED":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN85:F08A":
            return "ل"
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN41:F02D":
            return "ے"
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN05:F083":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN08:F0A7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F05D":
            return "ا"
        if ip == "NOORIN05:F045" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN63:F0E0" and prev == "NOORIN63:F0E0" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN65:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN57:F044":
            return "ا"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F058":
            return "۔"
        return pua_map.get(key, "")
    if key == "NOORIN85:F086":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0D1" and prev == "NOORIN63:F0D1" and nxt == "NOORIN81:F024":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F099":
            return "و"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN04:F0AF":
            return "ٹی"
        return pua_map.get(key, "")
    if key == "NOORIN08:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN01:F07A":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN28:F042":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F028" and prev == "NOORIN01:F028" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN07:F0ED" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN17:F0F2" and prev == "NOORIN17:F0F2" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F0E1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F057":
            return "وں"
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN17:F07B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN63:F0C5":
            return "و"
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F05A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F079" and prev == "NOORIN01:F079" and nxt == "NOORIN01:F099":
            return "ل"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN56:F0CE":
            return "س"
        if nxt == "NOORIN56:F0CE":
            return "س"
        return pua_map.get(key, "")
    if key == "NOORIN57:F069":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN21:F075" and prev == "NOORIN63:F0C1":
            return ""
        if ip == "NOORIN51:F0C2" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return "ں"
        if ip == "NOORIN63:F0C1" and prev == "NOORIN63:F0C1" and nxt == "NOORIN82:F099":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN81:F029":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return "و"
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN85:F08A":
            return "ل"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN85:F08A":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN47:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN63:F0C5":
            return "و"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F02A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN82:F029":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN63:F0C5":
            return "و"
        if ip == "NOORIN01:F069" and prev == "NOORIN82:F02A" and nxt == "NOORIN01:F05A":
            return "و"
        if ip == "NOORIN01:F066" and prev == "NOORIN01:F066" and nxt == "NOORIN85:F08A":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN05:F033":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return "و"
        if ip == "NOORIN04:F02C" and prev == "NOORIN04:F02C" and nxt == "NOORIN05:F084":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN05:F083":
            return "ہ"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return "و"
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN57:F044":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN35:F0D0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F075" and prev == "NOORIN01:F075" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN85:F08A":
            return "ل"
        if nxt == "NOORIN85:F028":
            return ""
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN35:F05B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F082":
            return ""
        if nxt == "NOORIN05:F083":
            return "ہ"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN83:F0D9":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F09B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F081" and prev == "NOORIN82:F081" and nxt == "NOORIN82:F03A":
            return "س"
        if ip == "NOORIN82:F081" and prev == "NOORIN82:F081" and nxt == "NOORIN01:F028":
            return ""
        if ip == "NOORIN82:F081" and prev == "NOORIN82:F081" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN81:F098":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0C5":
            return "و"
        if nxt == "NOORIN01:F067":
            return "و"
        if nxt == "NOORIN01:F029":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN27:F06A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F058":
            return "۔"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C6":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN08:F0F0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0C3":
            return "و"
        if nxt == "NOORIN63:F0C5":
            return "و"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN26:F0C9":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0D6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F06E" and prev == "NOORIN01:F06E" and nxt == "NOORIN63:F0BB":
            return "ھ"
        if ip == "NOORIN01:F06E" and prev == "NOORIN01:F06E" and nxt == "NOORIN82:F025":
            return "ھ"
        if ip == "NOORIN13:F0E9" and prev == "NOORIN13:F0E9" and nxt == "NOORIN01:F067":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN07:F042":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F0C3" and prev == "NOORIN81:F0C3" and nxt == "NOORIN81:F037":
            return "ھ"
        if ip == "NOORIN81:F0C3" and prev == "NOORIN81:F0C3" and nxt == "NOORIN82:F03A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN82:F0A8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F087" and prev == "NOORIN82:F087" and nxt == "NOORIN06:F027":
            return "ا"
        if nxt == "NOORIN63:F0D1":
            return "و"
        if nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN41:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F07A":
            return "د"
        if nxt == "NOORIN77:F071":
            return "و"
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN01:F068":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN76:F0AD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F03A":
            return ""
        if nxt == "NOORIN81:F037":
            return "ھ"
        if ip == "NOORIN81:F037" and prev == "NOORIN81:F037" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN27:F09A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C7":
            return ""
        if nxt == "NOORIN01:F03A":
            return ""
        if nxt == "NOORIN01:F057":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F02F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN57:F075":
            return "و"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F067":
            return "و"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN20:F068":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN25:F05B":
            return ""
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN63:F0C9":
            return ""
        if ip == "NOORIN06:F027" and prev == "NOORIN06:F027" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN01:F02F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F02F":
            return ""
        if ip == "NOORIN01:F02F" and prev == "NOORIN01:F02F" and nxt == "NOORIN01:F02F":
            return ""
        if ip == "NOORIN01:F02F" and prev == "NOORIN01:F02F":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F077":
            return "و"
        if ip == "NOORIN01:F053" and prev == "NOORIN01:F053" and nxt == "NOORIN63:F0E0":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN81:F0AE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F090" and prev == "NOORIN83:F0E1" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN10:F029" and nxt == "NOORIN63:F0E2":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN05:F0AE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05A":
            return "و"
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN01:F05A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN01:F0C4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN82:F063":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN24:F043":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F02A" and prev == "NOORIN01:F067" and nxt == "NOORIN63:F0BB":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN61:F0BF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and prev is None and nxt is None:
            return ""
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F0D4":
            return "گل"
        return pua_map.get(key, "")
    if key == "NOORIN13:F07E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F06A" and prev == "NOORIN54:F05E" and nxt == "NOORIN01:F0D4":
            return "گل"
        if ip == "NOORIN05:F070" and prev == "NOORIN05:F070" and nxt == "NOORIN82:F03A":
            return "س"
        return pua_map.get(key, "")
    if key == "NOORIN81:F03E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN83:F0DE" and prev == "NOORIN01:F0D4" and nxt == "NOORIN06:F0C0":
            return ""
        if ip == "NOORIN83:F0DE" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F058":
            return "۔"
        return pua_map.get(key, "")
    if key == "NOORIN08:F03B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F058":
            return "۔"
        return pua_map.get(key, "")
    if key == "NOORIN01:F038":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F036" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F059":
            return ""
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN01:F07C":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN18:F043":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F077":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN01:F037":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN01:F059":
            return ""
        if ip == "NOORIN81:F040" and prev == "NOORIN81:F040" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F0E7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F077":
            return "و"
        if ip == "NOORIN01:F07E" and prev == "NOORIN81:F060" and nxt == "NOORIN01:F077":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN07:F04F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F078":
            return "و"
        if nxt == "NOORIN01:F056":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN14:F059":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F02A":
            return "و"
        if nxt == "NOORIN85:F08A":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN62:F0D7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN13:F0B6" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F028":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN71:F08B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F053" and prev == "NOORIN01:F053" and nxt == "NOORIN01:F09F":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0CE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN06:F027":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN14:F065":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0DF" and prev == "NOORIN63:F0DF" and nxt == "NOORIN63:F0CD":
            return ""
        if ip == "NOORIN63:F0C7" and prev == "NOORIN63:F0C7" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0BE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN14:F0F1" and nxt == "NOORIN01:F077":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN33:F0F3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN14:F0F1":
            return ""
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN14:F0F1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0F1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN33:F0F3" and prev == "NOORIN33:F0F3" and nxt == "NOORIN06:F0BE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0A7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F05A":
            return "و"
        if ip == "NOORIN06:F027" and prev == "NOORIN06:F027" and nxt == "NOORIN01:F0D4":
            return "گل"
        return pua_map.get(key, "")
    if key == "NOORIN38:F087":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F079" and prev == "NOORIN01:F079" and nxt == "NOORIN01:F058":
            return "۔"
        if ip == "NOORIN07:F0ED" and nxt == "NOORIN01:F058":
            return "۔"
        return pua_map.get(key, "")
    if key == "NOORIN58:F031":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F075" and prev == "NOORIN01:F075" and nxt == "NOORIN01:F056":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN23:F0D7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C1" and prev == "NOORIN63:F0C1" and nxt == "NOORIN01:F077":
            return "و"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN63:F0BB":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN06:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN06:F070" and prev == "NOORIN06:F070" and nxt == "NOORIN82:F08A":
            return ""
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN64:F043":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F06B":
            return ""
        if ip == "NOORIN09:F0F5" and prev == "NOORIN09:F0F5" and nxt == "NOORIN01:F06B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F05D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067":
            return ""
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F056":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN81:F058":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN63:F0C5":
            return "و"
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN82:F02A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN09:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN48:F0EC":
            return "ے"
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN64:F043":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0BD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN81:F059":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN09:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F06A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return "و"
        if ip == "NOORIN57:F06A" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F05A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN23:F0F4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN82:F063":
            return "و"
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F099":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN14:F05C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F06B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F091":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN10:F0B4" and prev == "NOORIN82:F074" and nxt == "NOORIN81:F021":
            return "ے"
        if ip == "NOORIN10:F0B4" and prev == "NOORIN05:F043" and nxt == "NOORIN63:F0E2":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN12:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN17:F0F8" and prev == "NOORIN17:F0F8" and nxt == "NOORIN63:F0BB":
            return "و"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN05:F083":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN75:F022":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F082" and prev == "NOORIN81:F082" and nxt == "NOORIN01:F05A":
            return "و"
        if ip == "NOORIN81:F082" and prev == "NOORIN81:F082" and nxt == "NOORIN63:F0BB":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN51:F0D1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F06B" and prev == "NOORIN01:F06B" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN57:F022" and prev == "NOORIN57:F022" and nxt == "NOORIN01:F05A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN05:F0D0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN09:F08B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN10:F067":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C2" and prev == "NOORIN63:F0C2" and nxt == "NOORIN01:F056":
            return "و"
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN02:F070":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0E8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN01:F05B":
            return ""
        if ip == "NOORIN81:F0A7" and prev == "NOORIN81:F0A7" and nxt == "NOORIN13:F069":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN61:F027":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05C" and prev == "NOORIN01:F05C" and nxt == "NOORIN01:F0D4":
            return "گل"
        if nxt == "NOORIN82:F02A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN27:F05C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F04B" and prev == "NOORIN05:F04B" and nxt == "NOORIN01:F0D4":
            return "گل"
        return pua_map.get(key, "")
    if key == "NOORIN09:F04A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F02D":
            return "ل"
        return pua_map.get(key, "")
    if key == "NOORIN19:F0BA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F079" and prev == "NOORIN12:F079" and nxt == "NOORIN57:F075":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F0B5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN01:F05A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN15:F0E4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F0AA" and prev == "NOORIN82:F0AA" and nxt == "NOORIN01:F09B":
            return "ل"
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN08:F09E":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0CC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F0C8" and prev == "NOORIN04:F0C8" and nxt == "NOORIN63:F0C5":
            return "و"
        if ip == "NOORIN01:F051" and nxt == "NOORIN01:F029":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN31:F059":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F083" and prev == "NOORIN05:F083" and nxt == "NOORIN01:F058":
            return "۔"
        if ip == "NOORIN06:F056" and prev == "NOORIN06:F056" and nxt == "NOORIN01:F0D4":
            return "گل"
        return pua_map.get(key, "")
    if key == "NOORIN12:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F058":
            return "۔"
        if ip == "NOORIN04:F0C8" and prev == "NOORIN04:F0C8" and nxt == "NOORIN05:F084":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F025":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F06C":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F082":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN01:F056":
            return "ں"
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F056":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN15:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN81:F059":
            return "و"
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN83:F0DB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F062":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN81:F059":
            return "و"
        if ip == "NOORIN14:F02D" and prev == "NOORIN01:F05A" and nxt == "NOORIN07:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F05D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN82:F03A":
            return "س"
        if ip == "NOORIN05:F0CD" and prev == "NOORIN05:F0CD" and nxt == "NOORIN01:F067":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN06:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN48:F0EC":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN29:F0ED":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN81:F027":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0D2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F029":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F066":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN14:F04C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067":
            return ""
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F0D6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN01:F028":
            return ""
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN63:F0C2":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN10:F06C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E0" and prev == "NOORIN63:F0E0" and nxt == "NOORIN01:F05A":
            return "و"
        if nxt == "NOORIN81:F059":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN17:F079":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F099" and prev == "NOORIN01:F099" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN01:F09F" and prev == "NOORIN01:F09F" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN02:F06A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE":
            return ""
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F058":
            return "۔"
        return pua_map.get(key, "")
    if key == "NOORIN55:F0E6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN57:F061":
            return ""
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN36:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN48:F0E2":
            return ""
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN48:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0F3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F058":
            return "۔"
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F04A" and prev == "NOORIN57:F04A" and nxt == "NOORIN01:F07B":
            return "و"
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F077":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN29:F047":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F060" and prev == "NOORIN01:F060" and nxt == "NOORIN01:F067":
            return "ں"
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F077":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN66:F02F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN48:F0E3" and prev == "NOORIN48:F0E3" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F045":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN22:F037":
            return "س"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN21:F02D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN21:F02D":
            return ""
        if ip == "NOORIN21:F02D" and prev == "NOORIN21:F02D" and nxt == "NOORIN01:F05A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN10:F0C7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN01:F0A5" and prev == "NOORIN01:F0A5" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F073":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F08E" and prev == "NOORIN81:F08E" and nxt == "NOORIN01:F0D4":
            return "گل"
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN63:F0CD":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN17:F0E1" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F07A":
            return "ھ"
        if ip == "NOORIN05:F0CD" and prev == "NOORIN05:F0CD" and nxt == "NOORIN01:F0D4":
            return "گل"
        return pua_map.get(key, "")
    if key == "NOORIN46:F038":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN48:F0EC":
            return "ے"
        if nxt == "NOORIN82:F03B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F057":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN22:F037":
            return "س"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F057":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F074":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F08A" and prev == "NOORIN82:F08A" and nxt == "NOORIN01:F058":
            return "۔"
        return pua_map.get(key, "")
    if key == "NOORIN12:F066":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F029":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F0A1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07D" and prev == "NOORIN01:F07D" and nxt == "NOORIN63:F0BB":
            return "و"
        if nxt == "NOORIN07:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN49:F05D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F024" and prev == "NOORIN57:F024" and nxt == "NOORIN01:F079":
            return "ے"
        if ip == "NOORIN24:F02C" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F079":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0C3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F075" and prev == "NOORIN01:F075" and nxt == "NOORIN14:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F052":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN50:F087":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F075" and prev == "NOORIN01:F075" and nxt == "NOORIN81:F082":
            return ""
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN09:F0F1":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN27:F039":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0F1":
            return "و"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN83:F0D6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F061":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN57:F044":
            return "ا"
        if ip == "NOORIN56:F0D9" and prev == "NOORIN56:F0D9" and nxt == "NOORIN01:F05A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN11:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F024" and prev == "NOORIN81:F024" and nxt == "NOORIN01:F058":
            return "۔"
        return pua_map.get(key, "")
    if key == "NOORIN20:F023":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F067" and nxt == "NOORIN14:F0C5":
            return ""
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN63:F0C5":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN08:F0D9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F075":
            return "و"
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN59:F0F0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F05A":
            return "و"
        if ip == "NOORIN32:F085" and prev == "NOORIN32:F085" and nxt == "NOORIN63:F0D1":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN06:F053":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN82:F063":
            return "و"
        if nxt == "NOORIN01:F067":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN21:F0CE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN85:F08A":
            return "ل"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN81:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F067":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN19:F03F" and prev == "NOORIN82:F03A" and nxt == "NOORIN01:F0D4":
            return "گل"
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return "ں"
        return pua_map.get(key, "")
    if key == "NOORIN04:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN63:F0BB":
            return "و"
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F0D4":
            return "گل"
        return pua_map.get(key, "")
    if key == "NOORIN29:F0C4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN07:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN19:F062" and prev == "NOORIN19:F062" and nxt == "NOORIN01:F03A":
            return ""
        if ip == "NOORIN17:F0EC" and prev == "NOORIN17:F0EC" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F0D2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN48:F0E3":
            return "و"
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN05:F083":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN10:F07C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F028" and prev == "NOORIN01:F028" and nxt == "NOORIN01:F05D":
            return "ا"
        if ip == "NOORIN01:F078" and prev == "NOORIN01:F078" and nxt == "NOORIN01:F05D":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN15:F0C4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3":
            return ""
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F058":
            return "۔"
        return pua_map.get(key, "")
    if key == "NOORIN61:F038":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F07D":
            return "و"
        if ip == "NOORIN08:F0B0" and prev == "NOORIN08:F0B0" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN25:F04E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05D" and prev == "NOORIN01:F05D" and nxt == "NOORIN01:F05A":
            return "و"
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F0AA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return "و"
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN05:F083":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN14:F060":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F068" and prev == "NOORIN01:F068" and nxt == "NOORIN82:F02A":
            return "و"
        if ip == "NOORIN14:F099" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0C5":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN11:F074":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F051" and prev == "NOORIN01:F0D4" and nxt == "NOORIN72:F0C1":
            return ""
        if ip == "NOORIN01:F051" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0C1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F0B9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN53:F096":
            return ""
        if ip == "NOORIN63:F05B" and prev == "NOORIN63:F05B" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F05D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN01:F06B":
            return ""
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0A8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN16:F0A3" and prev == "NOORIN63:F0C6" and nxt == "NOORIN81:F036":
            return ""
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN64:F090":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F0E1" and prev == "NOORIN12:F0E1" and nxt == "NOORIN63:F0C2":
            return ""
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F04B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN56:F0CF":
            return ""
        if nxt == "NOORIN01:F029":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F02F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F087" and prev == "NOORIN82:F087" and nxt == "NOORIN81:F0BE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN39:F0D5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0BA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN08:F07C":
            return ""
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0DC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN57:F043":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN03:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F0B4":
        return pua_map.get(key, "")
    if key == "NOORIN22:F026":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN82:F037" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN24:F08A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F03B" and prev == "NOORIN82:F03B" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F090":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return ""
        if ip == "NOORIN01:F07E" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN22:F064":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0C5":
            return ""
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0ED":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        return pua_map.get(key, "")
    if key == "NOORIN23:F0EC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN82:F038":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0FC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN83:F0FB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0FB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN83:F0FC" and prev == "NOORIN83:F0FC":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F086":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN59:F0F7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0C0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F03E" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN56:F0E4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0F1" and prev == "NOORIN63:F0F1" and nxt == "NOORIN59:F0F0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN54:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN57:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN72:F0BD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F05A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN35:F0AF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN16:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F07A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN35:F0AF" and prev == "NOORIN35:F0AF" and nxt == "NOORIN13:F070":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN16:F07A" and prev == "NOORIN16:F07A" and nxt == "NOORIN63:F0BB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN75:F045":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F075" and prev == "NOORIN57:F075":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN01:F035":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F028" and prev == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F059":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN71:F052":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F092":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN34:F041":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F041":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN09:F0B7" and prev == "NOORIN09:F0B7" and nxt == "NOORIN01:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0A9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN56:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN51:F0F3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F04A" and prev == "NOORIN05:F04A" and nxt == "NOORIN63:F0CD":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F0AF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN81:F040":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F06D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F0F4" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F065":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN01:F034":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN83:F0F3" and prev == "NOORIN01:F079" and nxt == "NOORIN01:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F063":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F069" and prev == "NOORIN01:F05A" and nxt == "NOORIN63:F0CD":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN51:F09F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN07:F059" and prev == "NOORIN07:F059" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F041":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F05A" and prev == "NOORIN57:F05A" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN63:F0C2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F090":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F06B" and prev == "NOORIN01:F06B" and nxt == "NOORIN57:F075":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN82:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN50:F076":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN13:F0B1" and prev == "NOORIN01:F067" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F09B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN24:F092":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F079" and prev == "NOORIN01:F079" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F0DE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN02:F073" and prev == "NOORIN01:F07A" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN36:F050":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN13:F04E":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F078":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN75:F033":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F03F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F06B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN39:F065":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F0BD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN14:F0E3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0E3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F0BD" and prev == "NOORIN05:F0BD" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F0C9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F043" and prev == "NOORIN57:F043" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F0F2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F092":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN82:F06B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F029":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN72:F08A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F02D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F061":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN71:F05F":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN71:F05F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN20:F061" and prev == "NOORIN20:F061" and nxt == "NOORIN82:F053":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F0F8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F053" and prev == "NOORIN82:F053" and nxt == "NOORIN63:F0BB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN16:F076":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F076":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F072" and prev == "NOORIN04:F072" and nxt == "NOORIN01:F05B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0BD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN32:F063":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F063":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F0BD" and prev == "NOORIN12:F0BD" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN01:F043":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F078":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F03B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F078" and prev == "NOORIN01:F078" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F071":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F038":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0B9" and prev == "NOORIN63:F0B9" and nxt == "NOORIN82:F06B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F09B" and prev == "NOORIN01:F09B" and nxt == "NOORIN56:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN80:F057":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN53:F0B5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN56:F0D8":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0EE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F02C" and prev == "NOORIN04:F02C" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F0E2" and prev == "NOORIN01:F053" and nxt == "NOORIN48:F0EC":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN56:F0F7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0A8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN72:F099":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F04B" and prev == "NOORIN05:F04B" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F052":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F0A9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F077":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F0B8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F0F7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0EC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN33:F04C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F068":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F0FB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F037" and prev == "NOORIN57:F037" and nxt == "NOORIN01:F057":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F034":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E2" and prev == "NOORIN48:F0E2" and nxt == "NOORIN08:F06E":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN18:F09A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F046" and prev == "NOORIN81:F046" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN35:F0D4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F0CC" and prev == "NOORIN04:F0CC":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN58:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F02D" and prev == "NOORIN04:F02D" and nxt == "NOORIN82:F025":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0CB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN56:F0CE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F0B3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN81:F05D":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F08F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F03D" and prev == "NOORIN81:F03D" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F07A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F05D" and prev == "NOORIN81:F05D" and nxt == "NOORIN01:F057":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F08D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN34:F024":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0EC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F0B6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN55:F085":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN48:F0EB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F064":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F061" and prev == "NOORIN57:F061" and nxt == "NOORIN06:F046":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN45:F0AE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F0EE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E6" and prev == "NOORIN63:F0E6" and nxt == "NOORIN04:F042":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F042":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0EE" and prev == "NOORIN48:F0EE" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F088":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN37:F0A2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F09E" and prev == "NOORIN82:F09E" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0C7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F09C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN57:F04B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F029":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F043" and prev == "NOORIN57:F043" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F0B5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F04A" and prev == "NOORIN57:F04A" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN45:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0E7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F048":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C7" and prev == "NOORIN63:F0C7" and nxt == "NOORIN12:F0E1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN27:F0A3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN62:F084":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E0" and prev == "NOORIN63:F0E0" and nxt == "NOORIN81:F021":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F063":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN63:F0C1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0BA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F0C3" and prev == "NOORIN81:F0C3" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F027":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN14:F0DC" and prev == "NOORIN85:F08A" and nxt == "NOORIN48:F0F0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F037":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN02:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN10:F067" and prev == "NOORIN01:F07B" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F0E0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F062":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F06F":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F053":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F0E8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F075" and prev == "NOORIN01:F075" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0E8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN38:F053" and prev == "NOORIN38:F053" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN53:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN62:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CF" and prev == "NOORIN56:F0CF" and nxt == "NOORIN57:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0B3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F058":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN82:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F086":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C4" and prev == "NOORIN63:F0C4" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F0DA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN81:F028" and nxt == "NOORIN14:F090":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F08C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN07:F059" and prev == "NOORIN07:F059" and nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F04F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN56:F0CE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F075":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0CE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F04F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F0E6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F076" and prev == "NOORIN01:F076" and nxt == "NOORIN83:F0D5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0D5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN34:F0E6" and prev == "NOORIN34:F0E6" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN68:F025":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F02D" and prev == "NOORIN04:F02D" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F088":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F033":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F046":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F0BE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F0F7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F022" and prev == "NOORIN57:F022" and nxt == "NOORIN81:F071":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F0C7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN07:F071":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F056":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN57:F030":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F0DA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F084" and prev == "NOORIN05:F084" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F0CB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E4" and prev == "NOORIN48:F0E4" and nxt == "NOORIN81:F06D":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN74:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN11:F033" and prev == "NOORIN11:F033" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F0B5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F045":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F04A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F0D9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F05D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0D1" and prev == "NOORIN63:F0D1" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F031":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN13:F035" and prev == "NOORIN01:F070" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN73:F081":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN12:F0BE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN64:F059":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F09B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F023":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0BF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN41:F09C" and prev == "NOORIN41:F09C" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F030":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F063":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0BC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN78:F0C8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F028" and prev == "NOORIN85:F028" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN52:F0AD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN68:F0AD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F09D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN05:F084":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F02F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0E3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN17:F0F2" and prev == "NOORIN17:F0F2" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0CE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F087":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN62:F042":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN15:F0E8" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN05:F084":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0F3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN35:F045":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F077":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN50:F099":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN50:F09B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN11:F087":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN22:F055":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F07A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F051":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN06:F046":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F063":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F068":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F02A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F05C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F025":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F0C7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN83:F0D6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN68:F0F8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN16:F06F" and prev == "NOORIN16:F06F" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F063":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F035":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN57:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F0B1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN07:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN65:F09D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05D" and prev == "NOORIN01:F05D" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F071":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN13:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F087":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN18:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F069" and prev == "NOORIN13:F0FA" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F0AC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F085":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F06B" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN76:F0CE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN83:F0DB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN43:F069":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E0" and prev == "NOORIN63:F0E0" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F055":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN81:F024":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F04D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN38:F08A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05D" and prev == "NOORIN01:F05D" and nxt == "NOORIN01:F029":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F077":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN82:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN89:F030":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F062":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F029":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN36:F099":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN61:F08B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F095" and prev == "NOORIN82:F095" and nxt == "NOORIN48:F0EC":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN43:F09C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F060" and prev == "NOORIN01:F060" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F021":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F0A4" and prev == "NOORIN81:F0A4" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0EB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0CD" and prev == "NOORIN63:F0CD" and nxt == "NOORIN26:F0C9":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN76:F059":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F053":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F03E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F0DE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN06:F027" and prev == "NOORIN06:F027" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F03C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN47:F08D":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN69:F067":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN63:F0C2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0C1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F05B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F05A" and prev == "NOORIN57:F05A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F0D3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN14:F0F7":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F0BC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F06B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F04C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN75:F0CB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN56:F0F0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN21:F075" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F0BB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN81:F09F":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN65:F0B8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F06C" and prev == "NOORIN01:F06C" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F0FA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN11:F033":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F07C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F062":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN63:F0C2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN22:F06F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN63:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN69:F0B6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN17:F0EC":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F0EF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN66:F04F" and prev == "NOORIN82:F03A" and nxt == "NOORIN01:F068":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F0E6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F037" and prev == "NOORIN57:F037" and nxt == "NOORIN06:F027":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F04F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0F1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB" and nxt == "NOORIN06:F027":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F056":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0D9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN88:F035":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN27:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0F2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN22:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0CD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F046":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN22:F05C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN76:F03B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN11:F096" and prev == "NOORIN11:F096" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F02D" and prev == "NOORIN04:F02D" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F08C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F053" and prev == "NOORIN82:F053" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0C8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F079" and prev == "NOORIN01:F079" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN55:F0A6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN80:F0DC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F021" and prev == "NOORIN57:F021" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F06F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN05:F055":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0DA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN82:F04C":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F04C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN83:F0DA" and prev == "NOORIN83:F0DA" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F02E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F047" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0D7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0ED":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F0C8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F1" and prev == "NOORIN59:F0F1" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN53:F073":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F0F4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0EC" and prev == "NOORIN48:F0EC" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F0A6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F075" and prev == "NOORIN57:F075" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F0DE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0DF" and prev == "NOORIN63:F0DF":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN61:F02E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F085":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F040":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F09B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN12:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0E2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F024":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05F" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F065":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F06B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F022" and prev == "NOORIN57:F022" and nxt == "NOORIN81:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN37:F0AD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F072":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN16:F07E" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F0FA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN48:F09C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F041":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN10:F028" and prev == "NOORIN82:F04F" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F0B5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN53:F0EC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E0" and prev == "NOORIN63:F0E0" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0A8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F0E9" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F0D1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F045":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN05:F035":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F033":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F03D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F029" and prev == "NOORIN01:F029" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F0F2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN66:F064":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F068":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0F9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0F1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F0EB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F092":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F065" and prev == "NOORIN81:F065":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F0DE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN01:F03E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F0E3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F09B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0E1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN12:F079" and prev == "NOORIN12:F079" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F023":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN23:F0CB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F0CB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN11:F023" and prev == "NOORIN11:F023" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN22:F0AE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F09D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN14:F057":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN63:F0BB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F0D2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05C":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F07D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F05B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F053":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F097":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05D" and prev == "NOORIN01:F05D" and nxt == "NOORIN01:F05D":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F022":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F03B" and prev == "NOORIN82:F03B" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN24:F0E4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F063" and prev == "NOORIN05:F063" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN56:F0DA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN21:F048" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F02D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F058" and prev == "NOORIN01:F058" and nxt == "NOORIN19:F025":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F053":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F0A3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F036" and prev == "NOORIN81:F036" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F067":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F034":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN63:F0BB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN27:F0DA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F0A2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN81:F036":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN38:F055":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F093":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN45:F06C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C9" and prev == "NOORIN63:F0C9" and nxt == "NOORIN82:F063":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN64:F0CE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F056":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F085":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN85:F0BE" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F0B5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN89:F03B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN22:F08C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F096":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN57:F049":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F0C8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F077":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN21:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E0" and prev == "NOORIN63:F0E0" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F026":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN82:F03B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN56:F086":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F07B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0E3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F097":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F059" and prev == "NOORIN81:F059" and nxt == "NOORIN01:F060":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F08D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN83:F0E1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F08E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN63:F0CF":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN45:F034":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F084":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F082":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN74:F032":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN17:F036" and prev == "NOORIN63:F0D1" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN27:F083":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0F2" and prev == "NOORIN63:F0F2" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0EF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F06A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F0A7" and prev == "NOORIN81:F0A7" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F055":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0CD" and prev == "NOORIN63:F0CD" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F024":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F0C0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07D":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0E6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN69:F046":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN85:F0BE" and nxt == "NOORIN07:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F094":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F062":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F099" and prev == "NOORIN82:F099" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F056":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0C2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F032":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN06:F027":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN56:F0F3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN58:F078":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN83:F0D7":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F028":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN60:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E3" and prev == "NOORIN48:F0E3" and nxt == "NOORIN83:F0D7":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN50:F0DB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F067" and nxt == "NOORIN63:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN46:F0ED":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F03A" and prev == "NOORIN82:F03A" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN38:F0C4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F0BB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN36:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F076" and prev == "NOORIN01:F076" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN28:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F03C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN44:F085":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F083":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN81:F065":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN72:F0B5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN82:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0CD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F05A" and prev == "NOORIN57:F05A" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F06E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F069" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0F1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F069":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F0" and prev == "NOORIN59:F0F0" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F021":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN16:F071" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0F7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F025":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F0E1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F04B" and prev == "NOORIN57:F04B" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F0E2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F035":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN56:F0E8":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN35:F058":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F067":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F0B8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F0B8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN40:F0B7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F079":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F051" and prev == "NOORIN01:F056" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN70:F070":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F0E1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN08:F057" and prev == "NOORIN08:F057" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN58:F05B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN04:F0B8":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F07D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02E" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F05E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0E2" and prev == "NOORIN63:F0E2" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN54:F084":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN15:F0C9":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN59:F0ED":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F09B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN40:F02E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F0A7":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F0C8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN57:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN58:F0E8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN04:F0C8":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0D7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E3" and prev == "NOORIN48:F0E3" and nxt == "NOORIN12:F07B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F058":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0C5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN56:F0CE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F042":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F099" and prev == "NOORIN01:F099" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN54:F04D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN35:F05C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F030" and prev == "NOORIN82:F030" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F06C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F025" and prev == "NOORIN82:F025" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F050":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN05:F083" and prev == "NOORIN05:F083" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F04E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F085":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN63:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN15:F05F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F08A" and prev == "NOORIN82:F08A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F063":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0BB" and prev == "NOORIN63:F0BB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN43:F04C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F068":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN59:F074":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F032":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F047":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F09D" and nxt == "NOORIN63:F0BB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F06E":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F08C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F038" and prev == "NOORIN01:F065" and nxt == "NOORIN59:F0F0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F0BD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F021" and prev == "NOORIN81:F021" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F0D0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN41:F049":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN56:F0CE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN44:F095":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F037":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN48:F0E3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F0BC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN49:F0A3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN07:F071":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN14:F0A4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN83:F0D6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F033":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F061":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F057":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F031":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN60:F0A4" and prev == "NOORIN60:F0A4" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F08F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F060" and prev == "NOORIN01:F060" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F039":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN35:F06C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E3" and prev == "NOORIN48:F0E3" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN16:F0EF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F042":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN22:F037":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN51:F0E4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN26:F0C5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN48:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN24:F066":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F0D5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F082" and prev == "NOORIN81:F082" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN53:F0BB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN64:F06F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F079" and nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN81:F0A1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F034":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN82:F099":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F08A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F063" and prev == "NOORIN82:F063" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN70:F023":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN64:F0BB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CE" and prev == "NOORIN56:F0CE" and nxt == "NOORIN01:F09B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN19:F08D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN08:F04A" and prev == "NOORIN08:F04A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN20:F097":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F052":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F05A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F022" and prev == "NOORIN57:F022" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F088":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F097" and prev == "NOORIN82:F097" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F086" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN64:F0E2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F028" and prev == "NOORIN85:F028" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F065":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F039" and prev == "NOORIN57:F039" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F060":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F079" and prev == "NOORIN01:F079" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0C3":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F029":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN47:F095":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN50:F071" and prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN27:F0E5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F021":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F05F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F0C9" and prev == "NOORIN57:F044" and nxt == "NOORIN05:F084":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN74:F0C7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F09B" and prev == "NOORIN01:F09B" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN08:F041":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C6" and prev == "NOORIN63:F0C6" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN46:F09A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN37:F0E4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07D" and prev == "NOORIN01:F07D" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F0D8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN01:F07A" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN75:F057":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN35:F0E9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN28:F049" and prev == "NOORIN28:F049" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN36:F081":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN52:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F057" and prev == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN51:F050":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F0" and prev == "NOORIN59:F0F0" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN53:F050":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05B" and prev == "NOORIN01:F05B" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0FA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F0CC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN43:F042" and nxt == "NOORIN59:F0F0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F02A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN08:F07C":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F026":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0AB":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F057" and prev == "NOORIN01:F057" and nxt == "NOORIN01:F07D":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN41:F0C9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN59:F0F0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F06B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0D1" and prev == "NOORIN56:F0D1" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN17:F0AC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F03A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN25:F058":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN08:F0E8" and prev == "NOORIN08:F0E8" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN56:F0D7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN81:F082":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN02:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0D1" and prev == "NOORIN63:F0D1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F073":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F0AE":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07B" and prev == "NOORIN01:F07B" and nxt == "NOORIN85:F0B6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN36:F024":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN05:F0F0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F066":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C5" and prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F065":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F058":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN85:F08A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F08F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F039" and prev == "NOORIN57:F039" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F075":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN41:F0FA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F0DD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F090":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN81:F0AC" and prev == "NOORIN81:F0AC" and nxt == "NOORIN82:F02A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN85:F039":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN41:F076" and prev == "NOORIN41:F076" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN24:F033":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN18:F0A9" and prev == "NOORIN18:F0A9" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN66:F0B5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN04:F088" and prev == "NOORIN04:F088" and nxt == "NOORIN56:F0CE":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN49:F093":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F06E" and prev == "NOORIN01:F06E" and nxt == "NOORIN48:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F089":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN82:F02A" and prev == "NOORIN82:F02A" and nxt == "NOORIN63:F0E6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN09:F0E2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN68:F0D2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN14:F061" and prev == "NOORIN01:F056" and nxt == "NOORIN63:F0DF":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN18:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C3" and prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F023":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F05F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F065" and prev == "NOORIN01:F065" and nxt == "NOORIN83:F0CF":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0CF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN34:F05F" and prev == "NOORIN34:F05F" and nxt == "NOORIN01:F079":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN05:F087":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F077" and prev == "NOORIN01:F077" and nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN10:F02B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07B":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN58:F0F8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F078":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN83:F0EF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN83:F0DB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN26:F0C9":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN23:F0B0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN59:F0F0" and prev == "NOORIN59:F0F0" and nxt == "NOORIN04:F0AF":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN53:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F0D4" and prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN49:F057":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN63:F0BB":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F04B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN62:F03C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN22:F037" and prev == "NOORIN22:F037" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F0C0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F056":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN42:F07A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN56:F0CF":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN24:F0E0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN48:F0E3" and prev == "NOORIN48:F0E3" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN29:F0FA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F0C6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0C6":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN30:F050":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F094":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN72:F0C1" and prev == "NOORIN72:F0C1" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN51:F037":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F03A" and prev == "NOORIN01:F03A" and nxt == "NOORIN01:F07A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN22:F0E7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F05A" and prev == "NOORIN01:F05A" and nxt == "NOORIN05:F084":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F022":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN11:F033":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN38:F0E4":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN01:F05A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN54:F046":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and nxt == "NOORIN01:F0D4":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN04:F026":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0D1" and prev == "NOORIN63:F0D1" and nxt == "NOORIN63:F0C1":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN57:F025":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F066" and prev == "NOORIN01:F066" and nxt == "NOORIN01:F028":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN34:F038":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN82:F043" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN31:F041":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F056" and prev == "NOORIN01:F056" and nxt == "NOORIN01:F03A":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN44:F096":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN85:F08A" and prev == "NOORIN85:F08A" and nxt == "NOORIN01:F058":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN24:F022":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN63:F0C3":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F0E1":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN63:F0C1" and prev == "NOORIN63:F0C1" and nxt == "NOORIN81:F059":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN76:F087":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07E" and prev == "NOORIN82:F043" and nxt == "NOORIN59:F0F0":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN84:F044":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN05:F083":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN07:F0B2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN09:F026" and prev == "NOORIN18:F0A9" and nxt == "NOORIN57:F044":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN32:F07B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F07A" and prev == "NOORIN01:F07A" and nxt == "NOORIN05:F084":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN06:F0EA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN57:F044" and prev == "NOORIN57:F044" and nxt == "NOORIN63:F0C5":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN74:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN01:F067" and prev == "NOORIN01:F067" and nxt == "NOORIN17:F0EC":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN82:F0A6":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN01:F056" and nxt == "NOORIN01:F05A":
            return "کو"
        if prev == "NOORIN57:F044" and nxt == "NOORIN01:F067":
            return "ت"
        if ip is None and nxt == "NOORIN01:F067":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN81:F077":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        before = base_keys_before(run, i, pua_map, 8)
        if nxt == "NOORIN01:F05A":
            if ip == "NOORIN57:F04B":
                return "ش"
            if prev == "NOORIN05:F04B":
                return "ف"
        if prev == "NOORIN76:F084" and nxt == "NOORIN01:F05A":
            return pua_map.get(key, "")
        if ip is None and nxt == "NOORIN01:F05A":
            return "ش"
        if prev == "NOORIN01:F03A" and nxt == "NOORIN01:F05A":
            return "ش"
        if prev == "NOORIN63:F0C4" and nxt == "NOORIN10:F0C2":
            return "شر"
        if prev == "NOORIN81:F060" and nxt == "NOORIN81:F0C3":
            return pua_map.get(key, "")
        if prev == "NOORIN01:F077" and nxt == "NOORIN01:F05A":
            if "NOORIN01:F09B" in before:
                return "ح"
            if any(k == "NOORIN81:F077" for k in before):
                return "شر"
            return pua_map.get(key, "")
        return pua_map.get(key, "")
    if key == "NOORIN82:F0AD":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN82:F063":
            return "ی"
        if ip is None and nxt == "NOORIN01:F03A":
            return pua_map.get(key, "")
        if prev == "NOORIN01:F067" and nxt == "NOORIN01:F0D4":
            return pua_map.get(key, "")
        if prev == "NOORIN01:F07A" and nxt == "NOORIN01:F079":
            return pua_map.get(key, "")
        if prev == "NOORIN01:F07A" and nxt == "NOORIN16:F078":
            return pua_map.get(key, "")
        if prev == "NOORIN01:F07A" and nxt == "NOORIN01:F056":
            return "ا"
        if prev == "NOORIN01:F028" and nxt == "NOORIN01:F03A":
            return pua_map.get(key, "")
        if prev == "NOORIN81:F036" and nxt is None:
            return pua_map.get(key, "")
        return pua_map.get(key, "")
    if key == "NOORIN07:F086":
        return pua_map.get(key, "")
    if key == "NOORIN57:F06A":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN57:F044" and nxt == "NOORIN09:F02B":
            return "ھ"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN09:F02B":
            return "د"
        return pua_map.get(key, "")
    if key == "NOORIN81:F0B2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        after = base_keys_after(run, i, pua_map, 6)
        if prev == "NOORIN83:F0E1" and nxt == "NOORIN01:F028":
            return pua_map.get(key, "")
        if prev == "NOORIN63:F0E3" and nxt == "NOORIN56:F0DF":
            return pua_map.get(key, "")
        if ip is None and nxt == "NOORIN56:F0D8":
            return "ب"
        if prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F074":
            return "ئی"
        if prev == "NOORIN06:F027" and any(k == "NOORIN65:F0B8" for k in after):
            return "ہ"
        if prev == "NOORIN83:F0E1" and nxt == "NOORIN14:F090":
            return pua_map.get(key, "")
        return pua_map.get(key, "")
    if key == "NOORIN22:F041":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN85:F08A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN01:F0AF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if nxt == "NOORIN82:F030":
            return "ز"
        if ip is None and nxt == "NOORIN01:F03A":
            return pua_map.get(key, "")
        if prev == "NOORIN23:F0EC" and nxt == "NOORIN82:F038":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN52:F0F2":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        before = base_keys_before(run, i, pua_map, 6)
        if nxt == "NOORIN01:F05A" and any(k == "NOORIN11:F0A7" for k in before):
            return "ب"
        if ip is None:
            return pua_map.get(key, "")
        if prev == "NOORIN48:F0E2" and nxt == "NOORIN63:F0C3":
            return "ہ"
        if prev == "NOORIN01:F028" and nxt == "NOORIN14:F045":
            return pua_map.get(key, "")
        if any(k == "NOORIN14:F079" for k in before) and nxt == "NOORIN01:F065":
            return "پ"
        return pua_map.get(key, "")
    if key == "NOORIN21:F075":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        before = base_keys_before(run, i, pua_map, 5)
        if prev == "NOORIN59:F0F1" and nxt == "NOORIN01:F03A":
            return "ے"
        if prev == "NOORIN17:F071" and nxt == "NOORIN21:F075":
            return "ؤ"
        if prev == "NOORIN63:F0C1" and nxt == "NOORIN21:F075":
            return "ا"
        if prev == "NOORIN21:F075" and nxt == "NOORIN21:F075":
            return "ز"
        if prev == "NOORIN01:F03A" and nxt == "NOORIN21:F075":
            return "و"
        if prev == "NOORIN21:F075" and nxt == "NOORIN01:F0D4":
            if any(k == "NOORIN17:F071" for k in before):
                return pua_map.get(key, "")
            return "ہ"
        if prev == "NOORIN21:F075" and nxt == "NOORIN08:F035":
            return "ہ"
        if prev == "NOORIN08:F05E" and nxt == "NOORIN21:F075":
            return "و"
        if prev == "NOORIN21:F075" and nxt == "NOORIN56:F0F0":
            return "ن"
        if prev == "NOORIN21:F075" and nxt == "NOORIN01:F03A":
            return pua_map.get(key, "")
        if prev == "NOORIN21:F075" and nxt == "NOORIN57:F069":
            return "ز"
        return pua_map.get(key, "")
    if key == "NOORIN51:F096":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if (ip is None or prev == "NOORIN01:F03A") and nxt == "NOORIN57:F044":
            return "ا"
        if prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F0D4":
            return "ے"
        if prev == "NOORIN63:F0C5":
            return pua_map.get(key, "")
        if prev == "NOORIN82:F063" and nxt == "NOORIN82:F02A":
            return pua_map.get(key, "")
        if ip is None or prev == "NOORIN01:F03A":
            return pua_map.get(key, "")
        return pua_map.get(key, "")
    if key == "NOORIN53:F036":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        before = base_keys_before(run, i, pua_map, 5)
        if prev == "NOORIN63:F0C5" and nxt == "NOORIN01:F067":
            return "ہ"
        if nxt != "NOORIN01:F067":
            return pua_map.get(key, "")
        if any(k == "NOORIN05:F04D" for k in before):
            return "ہ"
        if any(k == "NOORIN06:F027" for k in before):
            return "ا"
        if prev == "NOORIN01:F03A":
            if any(k == "NOORIN01:F05A" for k in before[:3]):
                return "ا"
            return "ی"
        if prev in ("NOORIN01:F058", "NOORIN05:F04B") or ip is None:
            return "ی"
        if any(k == "NOORIN14:F033" for k in before):
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN21:F088":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        before = base_keys_before(run, i, pua_map, 6)
        if prev == "NOORIN01:F07A" and nxt == "NOORIN81:F036":
            return "و"
        if prev == "NOORIN81:F083" and nxt == "NOORIN01:F07A":
            return "اں"
        if prev == "NOORIN63:F0C1" and nxt == "NOORIN81:F036":
            return "پ"
        if prev == "NOORIN47:F0EB" and nxt == "NOORIN01:F056":
            return "ا"
        if ip == "NOORIN01:F029" and nxt == "NOORIN01:F056":
            return "یو"
        if prev == "NOORIN81:F040" and nxt == "NOORIN63:F0C5":
            return pua_map.get(key, "")
        if nxt == "NOORIN63:F0C5" and any(k == "NOORIN10:F094" for k in before):
            return pua_map.get(key, "")
        if ip is None and nxt in ("NOORIN01:F029", "NOORIN01:F07A"):
            return pua_map.get(key, "")
        return pua_map.get(key, "")
    if key == "NOORIN24:F02C":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN24:F02C":
            if nxt == "NOORIN49:F05D":
                return "ئ"
            return "ی"
        if prev == "NOORIN01:F03A" and nxt == "NOORIN24:F02C":
            return "ا"
        if prev == "NOORIN01:F05A" and nxt == "NOORIN56:F0CE":
            return "س"
        if prev == "NOORIN01:F05A":
            return "ک"
        if prev == "NOORIN01:F067" and nxt == "NOORIN24:F02C":
            return "ک"
        if prev == "NOORIN08:F034" and nxt == "NOORIN81:F021":
            return "ک"
        return pua_map.get(key, "")
    if key == "NOORIN20:F082":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None and nxt == "NOORIN01:F057":
            return "ی"
        if prev == "NOORIN01:F03A" and nxt == "NOORIN01:F07A":
            return "ی"
        if prev in ("NOORIN81:F021", "NOORIN57:F022") and nxt in (
            "NOORIN01:F0D4",
            "NOORIN01:F03A",
        ):
            return "ش"
        if prev == "NOORIN05:F043":
            return "ڑ"
        if prev == "NOORIN01:F074" and nxt == "NOORIN82:F03A":
            return "ب"
        if prev == "NOORIN01:F078" and nxt == "NOORIN05:F083":
            return "ے"
        if prev == "NOORIN06:F0BC" and nxt == "NOORIN05:F083":
            return "ب"
        if prev == "NOORIN10:F0F3" and nxt == "NOORIN82:F03A":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0DA":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if ip is None:
            return "ی"
        if prev == "NOORIN63:F0C3" and nxt == "NOORIN01:F07A":
            return "ئی"
        if prev == "NOORIN01:F07A" and nxt == "NOORIN01:F07A":
            return "ے"
        if prev == "NOORIN01:F07B":
            return pua_map.get(key, "")
        if prev == "NOORIN01:F07A" and nxt == "NOORIN82:F063":
            return "ی"
        if prev == "NOORIN04:F048":
            return "یا"
        if prev == "NOORIN57:F044" and nxt == "NOORIN01:F07A":
            return "ھ"
        return pua_map.get(key, "")
    if key == "NOORIN04:F0B9":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN01:F056" and nxt == "NOORIN85:F08A":
            return "گ"
        if ip is None or prev == "NOORIN01:F03A":
            if nxt == "NOORIN82:F063":
                return "ف"
        if prev == "NOORIN01:F07A" and nxt == "NOORIN05:F083":
            return "ا"
        if prev == "NOORIN01:F0D4" and nxt == "NOORIN01:F099":
            return "ڑ"
        return pua_map.get(key, "")
    if key == "NOORIN08:F092":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        before = base_keys_before(run, i, pua_map, 5)
        if prev == "NOORIN85:F08A" and nxt == "NOORIN01:F0D4":
            if any(k == "NOORIN82:F02A" for k in before):
                return pua_map.get(key, "")
            return "ہ"
        if prev == "NOORIN85:F08A" and nxt == "NOORIN01:F058":
            return "ھ"
        if prev == "NOORIN01:F0A5" and nxt == "NOORIN01:F0D4":
            return "ہ"
        if prev == "NOORIN85:F08A" and nxt == "NOORIN01:F03A":
            return "ہ"
        return pua_map.get(key, "")
    if key == "NOORIN09:F0E5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        before = base_keys_before(run, i, pua_map, 5)
        if prev == "NOORIN12:F079" and nxt == "NOORIN63:F0C6":
            return pua_map.get(key, "")
        if prev == "NOORIN12:F079":
            return "ے"
        if prev == "NOORIN63:F0C6" and nxt == "NOORIN01:F03A":
            return "ے"
        if prev == "NOORIN01:F059":
            return "ے"
        if prev == "NOORIN01:F07A" and any(k == "NOORIN01:F056" for k in before):
            return "ن"
        if prev == "NOORIN12:F0C7" and nxt == "NOORIN01:F07A":
            return "ر"
        if ip is None and nxt == "NOORIN01:F07A":
            return "ر"
        if prev == "NOORIN34:F037" and nxt == "NOORIN48:F0E3":
            return "ا"
        return pua_map.get(key, "")
    if key == "NOORIN32:F05F":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        if prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F07A":
            return "ہ"
        if prev == "NOORIN63:F0C3" and nxt in ("NOORIN05:F083", "NOORIN57:F061"):
            return "ئی"
        if prev == "NOORIN56:F0CE" and nxt == "NOORIN57:F044":
            return "ت"
        if prev == "NOORIN48:F0E3" and nxt == "NOORIN05:F083":
            return "ں"
        if ip is None and nxt == "NOORIN01:F07A":
            return "ہم"
        return pua_map.get(key, "")
    if key == "NOORIN14:F0DC":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        before = base_keys_before(run, i, pua_map, 5)
        if prev == "NOORIN85:F08A" or ip == "NOORIN85:F08A":
            return "ے"
        if prev == "NOORIN63:F0E6" or ip == "NOORIN63:F0E6":
            return "ے"
        if nxt == "NOORIN82:F02A" and any(k == "NOORIN01:F03A" for k in before):
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN12:F06B":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        before = base_keys_before(run, i, pua_map, 2)
        if ip == "NOORIN05:F04A" and nxt == "NOORIN01:F07B":
            if len(before) >= 2 and before[1] == "NOORIN01:F057":
                return "پ"
        if prev == "NOORIN63:F0C5" and nxt == "NOORIN16:F085":
            return "ے"
        if prev == "NOORIN85:F08A" and nxt == "NOORIN01:F07B":
            return "ی"
        if prev == "NOORIN01:F077" and nxt == "NOORIN57:F061":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN63:F0BE":
        return pua_map.get(key, "")
    if key == "NOORIN12:F024":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        before = base_keys_before(run, i, pua_map, 5)
        if prev == "NOORIN01:F05A" and nxt == "NOORIN01:F0D4":
            if any(k == "NOORIN14:F0C5" for k in before):
                return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN14:F091":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        before = base_keys_before(run, i, pua_map, 2)
        if prev == "NOORIN14:F0C5" and nxt == "NOORIN01:F07A":
            return "د"
        if prev == "NOORIN01:F05A" and nxt == "NOORIN01:F058":
            return ""
        if prev == "NOORIN01:F067":
            if nxt == "NOORIN48:F0EC":
                return "و"
            if nxt in ("NOORIN81:F030", "NOORIN82:F03B"):
                return ""
            if nxt in ("NOORIN01:F058", "NOORIN01:F0D4"):
                return "ے"
            if nxt == "NOORIN01:F03A":
                if len(before) >= 2 and before[1] == "NOORIN82:F03A":
                    return "و"
                if len(before) >= 2 and before[1] == "NOORIN63:F0C6":
                    return ""
                return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN10:F05D":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        before = base_keys_before(run, i, pua_map, 2)
        if nxt == "NOORIN01:F067":
            if (
                len(before) >= 2
                and before[0] == "NOORIN05:F04A"
                and before[1] == "NOORIN01:F05A"
            ):
                return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN56:F0FA":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN85:F08A" and nxt == "NOORIN01:F07A":
            return "ھ"
        if prev == "NOORIN57:F044" and nxt == "NOORIN01:F067":
            return "ی"
        if prev == "NOORIN63:F0C4" and nxt == "NOORIN01:F05A":
            return "ر"
        if ip == "NOORIN01:F067" and nxt == "NOORIN01:F067":
            return "ی"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F067":
            return "ی"
        if ip == "NOORIN01:F028" and nxt == "NOORIN01:F067":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN57:F027":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN63:F0C6":
            return "ں"
        if ip == "NOORIN01:F03A" and nxt == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "")
    if key == "NOORIN19:F034":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip is None and nxt == "NOORIN04:F02B":
            return "گ"
        if prev == "NOORIN63:F0C3" and nxt == "NOORIN04:F02B":
            return "ے"
        if prev == "NOORIN63:F0C5" and nxt == "NOORIN04:F02B":
            return "ے"
        if ip == "NOORIN01:F056" and nxt == "NOORIN82:F03A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN08:F065":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F077" or prev == "NOORIN01:F077":
            if nxt == "NOORIN01:F077":
                return "ے"
            if nxt == "NOORIN01:F056":
                return "و"
        if ip == "NOORIN01:F05A" or prev == "NOORIN01:F05A":
            if nxt == "NOORIN11:F0AD":
                return "ے"
        if ip == "NOORIN01:F051" and nxt == "NOORIN28:F050":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN59:F0EB":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN63:F0D1" or prev == "NOORIN63:F0D1":
            if nxt == "NOORIN01:F07A":
                return "ھ"
            if nxt == "NOORIN63:F0DF":
                return "ھ"
            if nxt == "NOORIN01:F05A":
                return "ر"
            if nxt == "NOORIN57:F037":
                return "ہ"
            if nxt == "NOORIN09:F094":
                return "ب"
            if nxt == "NOORIN01:F057":
                return "آ"
            if nxt in ("NOORIN57:F044", "NOORIN01:F05D"):
                return ""
        return pua_map.get(key, "")
    if key == "NOORIN13:F052":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN81:F0BE" or prev == "NOORIN81:F0BE":
            if nxt == "NOORIN81:F071":
                return "ر"
            if nxt == "NOORIN63:F0E2":
                return "ا"
            if nxt == "NOORIN63:F0C2":
                return "ت"
            if nxt == "NOORIN01:F07A":
                return "ھ"
        if ip == "NOORIN82:F08C" or prev == "NOORIN82:F08C":
            if nxt == "NOORIN01:F067":
                return ""
        if ip == "NOORIN10:F08F" or prev == "NOORIN10:F08F":
            if nxt == "NOORIN82:F08A":
                return ""
        return pua_map.get(key, "")
    if key == "NOORIN12:F041":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN01:F067" or prev == "NOORIN01:F067":
            if nxt == "NOORIN63:F0C2":
                return "ر"
        if nxt in (
            "NOORIN85:F08A",
            "NOORIN01:F07A",
            "NOORIN01:F057",
            "NOORIN63:F0C3",
        ):
            return ""
        if ip is None:
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN63:F0AF":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN81:F0A7" and nxt == "NOORIN01:F056":
            return "ی"
        if ip == "NOORIN01:F05A" and nxt == "NOORIN01:F05A":
            return ""
        if ip == "NOORIN63:F0E2" and nxt == "NOORIN16:F0E3":
            return "ی"
        return pua_map.get(key, "")
    if key == "NOORIN15:F0F5":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F07A":
            return "ت"
        return pua_map.get(key, "")
    if key == "NOORIN81:F02F":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F077" or ip == "NOORIN01:F077":
            return "وں"
        if ip == "NOORIN05:F08A" and nxt == "NOORIN63:F0C5":
            return "توں"
        if ip == "NOORIN05:F08A" and nxt == "NOORIN01:F057":
            return "توں"
        if ip == "NOORIN05:F08A" and nxt == "NOORIN63:F0C2":
            return ""
        if ip == "NOORIN63:F0C2":
            return "ں"
        if ip in ("NOORIN01:F078", "NOORIN01:F07B"):
            return ""
        if ip == "NOORIN49:F0A3":
            return "کی"
        return pua_map.get(key, "")
    if key == "NOORIN10:F047":
        return pua_map.get(key, "")
    if key == "NOORIN14:F068":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN08:F0E8":
            return "ی"
        if ip == "NOORIN82:F02A":
            return "ں"
        if ip in (None, "NOORIN06:F027"):
            return "ی"
        if ip == "NOORIN14:F068":
            return ""
        if ip == "NOORIN01:F065" and nxt == "NOORIN01:F03A":
            return "ی"
        if ip == "NOORIN63:F0F1" and nxt == "NOORIN01:F056":
            return ""
        if ip == "NOORIN63:F0C9" and nxt == "NOORIN48:F0E3":
            return "ا"
        if ip == "NOORIN12:F023" and nxt == "NOORIN82:F02A":
            return "ی"
        if ip == "NOORIN01:F0D4" and nxt == "NOORIN63:F0E2":
            return ""
        return pua_map.get(key, "")
    if key == "NOORIN11:F048":
        ip = immediate_prev_base_key(run, i)
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if ip == "NOORIN05:F043" and nxt == "NOORIN63:F0C3":
            return ""
        if ip == "NOORIN01:F067" and nxt == "NOORIN01:F056":
            return "ا"
        if ip == "NOORIN63:F0C6" and nxt == "NOORIN01:F07A":
            return "و"
        if ip == "NOORIN63:F0C9" and nxt == "NOORIN01:F056":
            return "ا"
        if nxt == "NOORIN01:F067" and ip != "NOORIN01:F067":
            return "و"
        if ip == "NOORIN19:F025" and nxt == "NOORIN01:F07A":
            return "و"
        if ip == "NOORIN01:F05D" and nxt == "NOORIN01:F056":
            return ""
        if nxt == "NOORIN01:F065":
            return "و"
        return pua_map.get(key, "")
    if key == "NOORIN15:F059":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN56:F0CE":
            return ""
        if ip == "NOORIN01:F07A":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN10:F021":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN16:F07E":
            return "ے"
        return pua_map.get(key, "")
    if key == "NOORIN01:F060":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN10:F0B4":
            for j in range(i - 1, -1, -1):
                if is_overlay_font(run[j][3]):
                    continue
                if map_key(run[j][3], run[j][4]) == "NOORIN10:F0B4":
                    f0b4_ip = immediate_prev_base_key(run, j)
                    if f0b4_ip in ("NOORIN63:F0C3", "NOORIN59:F0F1"):
                        return "ی"
                    break
        return pua_map.get(key, "ج")
    if key == "NOORIN01:F059":
        ip = immediate_prev_base_key(run, i)
        if ip == "NOORIN10:F088":
            for j in range(i - 1, -1, -1):
                if is_overlay_font(run[j][3]):
                    continue
                if map_key(run[j][3], run[j][4]) == "NOORIN10:F088":
                    f088_out = lookup_text(run, j, pua_map, row_all)
                    if f088_out and f088_out != "ی":
                        return ""
                    break
        return pua_map.get(key, "ء")
    if key == "NOORIN08:F0E8":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        inx = None
        for item in run[i + 1 :]:
            if is_overlay_font(item[3]):
                continue
            inx = map_key(item[3], item[4])
            break
        if prev == "NOORIN04:F0CC":
            return "شیر"
        if prev == "NOORIN01:F05D":
            return "شیر"
        if prev in ("NOORIN48:F0E4", "NOORIN57:F022"):
            return "ش"
        if prev == "NOORIN14:F068":
            return "ک"
        if prev == "NOORIN63:F0BB" and nxt == "NOORIN01:F03A":
            return "یر"
        if prev == "NOORIN63:F0BB":
            return "ش"
        if prev == "NOORIN01:F05A" and nxt == "NOORIN01:F056":
            return "وں"
        if prev == "NOORIN01:F058" and nxt == "NOORIN01:F05A":
            return "ش"
        if prev in ("NOORIN01:F029", "NOORIN67:F04B"):
            return "ش"
        if prev == "NOORIN04:F02C":
            return "ش"
        if prev == "NOORIN63:F0C5":
            return "ر"
        if prev is None and inx == "NOORIN01:F05A":
            return "ش"
        if prev is None:
            return "شیر"
        return pua_map.get(key, "یر")
    if key == "NOORIN57:F021":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F06C":
            return "بی"
        if prev == "NOORIN16:F078":
            return "ب"
        if prev == "NOORIN01:F09F":
            return "بی"
        if prev == "NOORIN57:F021":
            return ""
        if prev == "NOORIN57:F022":
            return ""
        if prev == "NOORIN04:F02A":
            return "ی"
        if prev == "NOORIN85:F08A":
            return "ے"
        if prev == "NOORIN10:F0C2":
            return "س"
        if prev == "NOORIN82:F02A":
            return "ہ"
        if prev == "NOORIN04:F0B8":
            return "ب"
        if prev == "NOORIN01:F065":
            return "ے"
        if prev == "NOORIN01:F05A":
            return "ر"
        return pua_map.get(key, "ب")
    if key == "NOORIN44:F041":
        return pua_map.get(key, "لگنی")
    if key == "NOORIN22:F0AA":
        return pua_map.get(key, "پہلا")
    if key == "NOORIN81:F0A7":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F07B":
            return "تر"
        if nxt == "NOORIN01:F062":
            return "دی"
        return pua_map.get(key, "طر")
    if key == "NOORIN63:F0DD":
        return pua_map.get(key, "لم")
    if key == "NOORIN17:F0D2":
        return pua_map.get(key, "لحاظ")
    if key == "NOORIN01:F070":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN17:F0D2":
            return ""
        return pua_map.get(key)
    if key == "NOORIN01:F06F":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN17:F0D2":
            return ""
        return pua_map.get(key)
    if key == "NOORIN15:F0C9":
        return pua_map.get(key, "لکھ")
    if key == "NOORIN81:F064":
        return pua_map.get(key, "جگ")
    if key == "NOORIN08:F094":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN01:F058" and nxt == "NOORIN08:F08B":
            return ""
        if prev == "NOORIN85:F08A":
            before = base_keys_before(run, i, pua_map, 2)
            if nxt == "NOORIN01:F03A":
                return "سنی"
            if len(before) >= 2 and before[1] == "NOORIN63:F0C9":
                return "سنی"
            return "ے"
        return pua_map.get(key, "ے")
    if key == "NOORIN25:F05B":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        inx = None
        for item in run[i + 1 :]:
            if is_overlay_font(item[3]):
                continue
            inx = map_key(item[3], item[4])
            break
        if inx == "NOORIN48:F0E3":
            return "بن" if prev is None else "بیگا"
        if prev is None and inx == "NOORIN01:F067":
            return "بیگا"
        if prev is None and inx == "NOORIN82:F02A":
            return "بنا"
        if prev == "NOORIN57:F044" and inx == "NOORIN01:F067":
            return ""
        if prev == "NOORIN85:F08A" and inx == "NOORIN48:F0E2":
            return "گ"
        if inx == "NOORIN82:F02A":
            if prev in ("NOORIN01:F0D4", "NOORIN01:F07B"):
                return "گ"
            if prev is None or prev == "NOORIN01:F03A":
                return "بنا"
        if inx == "NOORIN82:F03A":
            return "بنا"
        if inx == "NOORIN48:F0E2" and prev == "NOORIN01:F07D":
            return "گ"
        if inx == "NOORIN01:F067" and prev == "NOORIN63:F0C5":
            return "ی"
        return pua_map.get(key, "گا")
    if key == "NOORIN43:F092":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        inx = None
        for item in run[i + 1 :]:
            if is_overlay_font(item[3]):
                continue
            inx = map_key(item[3], item[4])
            break
        if prev == "NOORIN81:F060" and inx == "NOORIN01:F067":
            return "ا"
        if prev == "NOORIN63:F0C5" and inx == "NOORIN01:F03A":
            return "نیند"
        if prev == "NOORIN05:F04B" and inx == "NOORIN56:F0CE":
            return "نیند"
        if prev == "NOORIN05:F04B" and inx == "NOORIN81:F059":
            return "نین"
        if ip is None and inx == "NOORIN01:F057":
            return "نیند"
        if prev == "NOORIN63:F0C5" and inx == "NOORIN56:F0CE":
            return "نیند"
        if prev == "NOORIN01:F03A" and inx == "NOORIN01:F07A":
            return "نین"
        if prev == "NOORIN01:F07A" and inx == "NOORIN01:F057":
            return "ند"
        if prev == "NOORIN57:F044" and inx == "NOORIN01:F07A":
            return "د"
        if prev == "NOORIN01:F0D4" and inx == "NOORIN01:F05A":
            return "ین"
        return pua_map.get(key, "نین")
    if key == "NOORIN81:F059":
        if immediate_prev_base_key(run, i) == "NOORIN43:F092":
            return "د"
        return pua_map.get(key, "ن")
    if key == "NOORIN21:F053":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        inx = None
        for item in run[i + 1 :]:
            if is_overlay_font(item[3]):
                continue
            inx = map_key(item[3], item[4])
            break
        if prev == "NOORIN57:F039":
            return "نے"
        if prev == "NOORIN18:F0A9":
            return "نبھا"
        if prev in ("NOORIN01:F067", "NOORIN01:F07B", "NOORIN01:F07E"):
            return "نے"
        if prev == "NOORIN22:F037" and inx == "NOORIN63:F0C2":
            return ""
        if prev == "NOORIN01:F07A" and inx == "NOORIN48:F0E2":
            return "و"
        if prev == "NOORIN82:F02A" and inx == "NOORIN01:F079":
            return "ڑ"
        if prev == "NOORIN01:F077" and inx == "NOORIN48:F0E2":
            return "ل"
        if prev == "NOORIN57:F044" and inx == "NOORIN59:F0EE":
            return "وں"
        if prev in ("NOORIN63:F0E2",):
            return "نے"
        return pua_map.get(key, "نے")
    if key == "NOORIN08:F096":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN63:F0C6":
            return "سہارے"
        if prev == "NOORIN01:F05D":
            return "ھک"
        if prev == "NOORIN01:F07D":
            return "سہارہ"
        if prev in ("NOORIN63:F0C3", "NOORIN89:F079"):
            return "و"
        if prev == "NOORIN57:F022":
            return ""
        if prev == "NOORIN01:F067":
            return "ھ"
        if prev == "NOORIN01:F07A":
            return "ی"
        if prev == "NOORIN01:F05A":
            return "ا"
        if prev == "NOORIN81:F036":
            return "ے"
        if prev == "NOORIN82:F02A":
            return "ھ"
        if prev == "NOORIN57:F049":
            return "ے"
        if prev == "NOORIN14:F0A3":
            return "ے"
        return pua_map.get(key, "ک")
    if key == "NOORIN57:F076":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        ip = immediate_prev_base_key(run, i)
        inx = None
        for item in run[i + 1 :]:
            if is_overlay_font(item[3]):
                continue
            inx = map_key(item[3], item[4])
            break
        if prev == "NOORIN63:F0C3" and inx == "NOORIN04:F02D":
            return "ر"
        if prev == "NOORIN08:F057":
            return "ر"
        if prev == "NOORIN56:F0CF" and inx == "NOORIN12:F088":
            return "ھ"
        if prev is None and inx == "NOORIN63:F0C6":
            return "سڑ"
        if prev == "NOORIN01:F077" and inx == "NOORIN48:F0E2":
            return "سڑ"
        if prev is None and inx == "NOORIN01:F079":
            return "سڑ"
        if prev is None and inx == "NOORIN82:F063":
            return ""
        if prev == "NOORIN01:F03A" and inx == "NOORIN82:F063":
            return ""
        if prev == "NOORIN01:F029" and inx == "NOORIN01:F07D":
            return "پ"
        if prev == "NOORIN12:F079" and inx == "NOORIN01:F07D":
            return "پ"
        if prev is None and inx == "NOORIN18:F08D":
            return ""
        if prev == "NOORIN01:F07D" and inx == "NOORIN18:F08D":
            return ""
        return pua_map.get(key, "سڑ")
    if key == "NOORIN83:F0E0":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN81:F064":
            if prev in ("NOORIN57:F044", "NOORIN57:F05A"):
                return "ے"
            return ""
        return pua_map.get(key)
    if key == "NOORIN56:F0DF":
        prev, nxt = neighbor_base_keys(run, i, pua_map)
        if nxt == "NOORIN01:F077":
            return "اصو"
        if nxt == "NOORIN63:F0E0":
            return "اصولی"
        if nxt == "NOORIN63:F0DF":
            return "اصولو"
        if nxt == "NOORIN01:F067":
            if prev == "NOORIN81:F0B2":
                return "صور"
            return "صورت"
        if nxt in ("NOORIN01:F058", None):
            return "صور"
        return None
    if key == "NOORIN63:F0DF":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN56:F0DF":
            return ""
        return pua_map.get(key)
    if key == "NOORIN63:F0E0":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN56:F0DF":
            return ""
        return pua_map.get(key)
    if key == "NOORIN63:F0B8":
        prev, _nxt = neighbor_base_keys(run, i, pua_map)
        if prev == "NOORIN81:F09C":
            return "قہ"
        return pua_map.get(key, "قو")
    if key == "NOORIN83:F0DE":
        # Joiner before NOORIN81 *ل ligatures (پل/بل/تل/ٹل/اٹل).
        return ""
    if key in (
        "NOORIN81:F02E",
        "NOORIN81:F03E",
        "NOORIN81:F04C",
        "NOORIN81:F054",
    ):
        if immediate_prev_base_key(run, i) == "NOORIN83:F0DE":
            if key == "NOORIN81:F02E":
                return "بل"
            if key == "NOORIN81:F03E":
                return "پل"
            if key == "NOORIN81:F04C":
                return "تل"
            # F054: موت اٹل vs کم ٹل
            prev_skip, _ = neighbor_base_keys(run, i, pua_map)
            if prev_skip == "NOORIN01:F05A":
                return "اٹل"
            return "ٹل"
        return pua_map.get(key)
    if key not in pua_map:
        return None
    return pua_map[key]


def fmt_run(chars: list, pua_map: dict[str, str], row_all: list | None = None) -> str:
    run = sorted(chars, key=lambda t: -t[1])
    parts = []
    prev_x0 = None
    for i, (y, x0, x1, font, o) in enumerate(run):
        text = lookup_text(run, i, pua_map, row_all)
        if text == "":
            continue
        if prev_x0 is not None and (prev_x0 - x1) > WORD_GAP:
            parts.append(" ")
        if text is None:
            parts.append(f"[{map_key(font, o)}]")
        else:
            parts.append(text)
        prev_x0 = x0
    return "".join(parts)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    page_1idx = 50
    if len(sys.argv) > 1:
        page_1idx = int(sys.argv[1])
    pua_map = load_map()
    doc = fitz.open(PDF)
    if page_1idx == 50 and GOLD.exists():
        print("=== gold ===")
        print(GOLD.read_text(encoding="utf-8"))
    print(f"=== decoded page {page_1idx} (NOORIN FONT:CODE) ===")
    chars = page_chars(doc[page_1idx - 1])
    ascii_chars = [c for c in chars if not is_noorin(c[3]) and c[4] < 128]
    if ascii_chars:
        print("ascii:", "".join(chr(c[4]) for c in ascii_chars))
    noorin = [c for c in chars if is_noorin(c[3])]
    base = [c for c in noorin if not is_overlay_font(c[3])]
    overlays = [c for c in noorin if is_overlay_font(c[3])]
    rows = cluster_rows(base)
    attached = attach_overlays(rows, overlays)
    for (y, _row), row_all in zip(rows, attached):
        left = [c for c in row_all if c[1] < COL_SPLIT]
        right = [c for c in row_all if c[1] >= COL_SPLIT]
        if right:
            print(f"y={y:6.1f} R {fmt_run(right, pua_map, row_all)}")
        if left:
            print(f"y={y:6.1f} L {fmt_run(left, pua_map, row_all)}")
    seen = {map_key(f, o) for _y, _x0, _x1, f, o in noorin}
    unk = sorted(k for k in seen if k not in pua_map)
    print(f"\npage keys {len(seen)} mapped {len(seen) - len(unk)} unknown {len(unk)}")
    print("unknown:", " ".join(unk[:80]))


if __name__ == "__main__":
    main()
