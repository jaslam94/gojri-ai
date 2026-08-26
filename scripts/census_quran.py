"""Census Quran (font, GID) keys and seed maps from good ToUnicode values.

A GID is seeded only when its ToUnicode value is a real Arabic / ASCII /
presentation character on almost every occurrence.

Scans run in short child processes. PyMuPDF texttrace can crash this
process if many pages stay in one Python session.

  py -3 scripts/census_quran.py 17 17
  py -3 scripts/census_quran.py 1 80 --write-seed
  py -3 scripts/census_quran.py 1 717 --write-seed
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_quran_gids import (
    PDF,
    ROOT,
    SEED,
    is_good_ucs,
    is_keep_font,
    map_key,
    page_glyphs,
    ucs_to_text,
)

BATCH = 15


def parse_args() -> tuple[int, int, bool, bool, Path | None]:
    start, end, write, worker = 17, 17, False, False
    out: Path | None = None
    args = sys.argv[1:]
    if "--write-seed" in args:
        write = True
        args = [a for a in args if a != "--write-seed"]
    if "--worker" in args:
        worker = True
        args = [a for a in args if a != "--worker"]
    if "--out" in args:
        i = args.index("--out")
        out = Path(args[i + 1])
        args = args[:i] + args[i + 2 :]
    if len(args) >= 2:
        start, end = int(args[0]), int(args[1])
    elif len(args) == 1:
        start = end = int(args[0])
    return start, end, write, worker, out


def harvest(start: int, end: int) -> dict:
    doc = fitz.open(PDF)
    end = min(end, doc.page_count)
    ucs_of: dict[str, Counter[int]] = defaultdict(Counter)
    inst = Counter()
    first_page: dict[str, int] = {}
    for page_1idx in range(start, end + 1):
        for _y0, _x0, _x1, _y1, font, gid, ucs in page_glyphs(doc[page_1idx - 1]):
            if not is_keep_font(font):
                continue
            key = map_key(font, gid)
            inst[key] += 1
            ucs_of[key][ucs] += 1
            first_page.setdefault(key, page_1idx)
    return {
        "inst": dict(inst),
        "ucs_of": {k: dict(v) for k, v in ucs_of.items()},
        "first_page": first_page,
    }


def merge_harvest(
    inst: Counter,
    ucs_of: dict[str, Counter[int]],
    first_page: dict[str, int],
    part: dict,
) -> None:
    for key, n in part["inst"].items():
        inst[key] += n
    for key, counts in part["ucs_of"].items():
        for u_s, n in counts.items():
            ucs_of[key][int(u_s)] += n
    for key, page in part["first_page"].items():
        prev = first_page.get(key)
        if prev is None or page < prev:
            first_page[key] = page


def run_worker(start: int, end: int) -> dict:
    out = ROOT / "data" / "decode" / f"_tmp_quran_census_{start}_{end}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        str(start),
        str(end),
        "--worker",
        "--out",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    data = json.loads(out.read_text(encoding="utf-8"))
    out.unlink(missing_ok=True)
    return data


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    start, end, write, worker, out = parse_args()
    if worker:
        import os

        assert out is not None
        data = harvest(start, end)
        out.write_text(json.dumps(data), encoding="utf-8")
        sys.stdout.flush()
        os._exit(0)

    doc = fitz.open(PDF)
    end = min(end, doc.page_count)
    doc.close()

    inst: Counter = Counter()
    ucs_of: dict[str, Counter[int]] = defaultdict(Counter)
    first_page: dict[str, int] = {}
    for batch_start in range(start, end + 1, BATCH):
        batch_end = min(batch_start + BATCH - 1, end)
        print(f"...pages {batch_start}-{batch_end}", flush=True)
        part = run_worker(batch_start, batch_end)
        merge_harvest(inst, ucs_of, first_page, part)

    existing = {}
    evidence = {}
    if SEED.exists():
        seed_data = json.loads(SEED.read_text(encoding="utf-8"))
        existing = seed_data.get("map", {})
        evidence = seed_data.get("evidence", {})

    seeded = dict(existing)
    new = 0
    for key, counts in ucs_of.items():
        total = sum(counts.values())
        good = [(u, n) for u, n in counts.most_common() if is_good_ucs(u)]
        if not good:
            continue
        u, n = good[0]
        if n / total < 0.9:
            continue
        text = ucs_to_text(u)
        if key in seeded:
            continue
        seeded[key] = text
        evidence[key] = (
            f"auto ToUnicode U+{u:04X} n={n}/{total} first_p{first_page[key]:03d}"
        )
        new += 1

    mapped_n = sum(inst[k] for k in inst if k in seeded)
    unk_n = sum(inst[k] for k in inst if k not in seeded)
    unk_keys = [k for k in inst if k not in seeded]
    total_inst = mapped_n + unk_n
    pct = (100.0 * mapped_n / total_inst) if total_inst else 0.0
    print(f"pages {start}-{end}")
    print(f"unique keep keys {len(inst)} seeded {len(seeded)} new {new}")
    print(f"still unknown unique {len(unk_keys)}")
    print(f"instances mapped {mapped_n} unknown {unk_n} mapped_pct {pct:.1f}")
    once = sum(1 for k in unk_keys if inst[k] == 1)
    print(f"unknown appear once {once}")
    print("top unknown keys (instances, first page, top ucs)")
    shown = 0
    for key, n in inst.most_common():
        if key in seeded:
            continue
        u, un = ucs_of[key].most_common(1)[0]
        try:
            us = chr(u) if 0 <= u <= 0x10FFFF else "?"
        except Exception:
            us = "?"
        print(
            f"{n:5} p{first_page[key]:03d} {key:28} "
            f"U+{u:04X} {us!r} ({un}/{inst[key]})"
        )
        shown += 1
        if shown >= 40:
            break

    unk_path = ROOT / "data" / "decode" / "quran_gid_unknown.json"
    unk_path.write_text(
        json.dumps(
            {
                "pages": [start, end],
                "unknown": [
                    {
                        "key": k,
                        "n": inst[k],
                        "first_page": first_page[k],
                        "top_ucs": ucs_of[k].most_common(1)[0][0],
                    }
                    for k, _n in inst.most_common()
                    if k not in seeded
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"unknown list {unk_path.relative_to(ROOT).as_posix()}")

    if write:
        data = {
            "font_family": "UrduTypesetting+ArabicTypesetting",
            "scheme": "gid",
            "source_pdf": "pdfs/QURANIC_TRANSLATION_in_GOJRI_by_Dr_Rafiq.pdf",
            "notes": [
                "Key is FONT:GID from get_texttrace. Do not copy Batool/NOORIN maps.",
                "Seeded from ToUnicode values that are already real Arabic/ASCII.",
                "Zero-width Arabic letters are nuqta overlays. The decoder names the next host glyph from that ToUnicode value.",
                "Joining bodies that ToUnicode maps to FFFD stay unknown until filled.",
            ],
            "map": dict(sorted(seeded.items())),
            "evidence": dict(sorted(evidence.items())),
        }
        SEED.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {SEED.relative_to(ROOT).as_posix()} table {len(seeded)}")


if __name__ == "__main__":
    main()
