"""Shared helpers for Devanagari → Gojri Nastaliq dictionary transliteration."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DICT_DIR = ROOT / "data" / "extracted" / "clean-pdf" / "gojri-hindi-english-dictionary"
TRANSLIT_DIR = DICT_DIR / "translit"

DEV = r"[\u0900-\u097F\u097D\u093D\u0964\u0965]"
HEADWORD_RE = re.compile(
    rf"^(?P<dev>{DEV}+(?:\s+{DEV}+)*)\s*"
    rf"(?:\((?P<roman>[A-Za-z][^)]*)\))?"
    rf"(?P<rest>.*)$"
)
PAGE_TAG_RE = re.compile(r"^\[\d+\]\s*$")
SECTION_RE = re.compile(rf"^{DEV}\s*/\s*[A-Za-z/]", re.UNICODE)

TSV_FIELDS = [
    "entry_id",
    "page",
    "line",
    "devanagari",
    "roman",
    "raw_line",
    "nastaliq_pass1",
    "nastaliq_pass2",
]


def parse_page_file(path: Path) -> list[dict]:
    page = int(path.stem.rsplit("-", 1)[-1])
    rows: list[dict] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or PAGE_TAG_RE.match(line):
            continue
        if SECTION_RE.match(line):
            continue
        if line in {"ओ", "अ", "ए", "ऐ", "औ", "आ", "इ", "ई", "उ", "ऊ"}:
            continue
        m = HEADWORD_RE.match(line)
        if not m:
            continue
        dev = m.group("dev").strip()
        roman = (m.group("roman") or "").strip()
        rest = (m.group("rest") or "").strip()
        if not dev:
            continue
        if rest and rest[0].isdigit():
            continue
        rows.append(
            {
                "entry_id": f"p{page:04d}:L{line_no}",
                "page": page,
                "line": line_no,
                "devanagari": dev,
                "roman": roman,
                "raw_line": raw,
                "nastaliq_pass1": "",
                "nastaliq_pass2": "",
            }
        )
    return rows


def collect_entries(pages: list[int] | None = None) -> list[dict]:
    files = sorted(DICT_DIR.glob("page-*.txt"))
    if pages:
        wanted = {f"page-{p:04d}.txt" for p in pages}
        files = [f for f in files if f.name in wanted]
    entries: list[dict] = []
    for path in files:
        entries.extend(parse_page_file(path))
    return entries


def aksharamukha_to_urdu(devanagari: str) -> str:
    from aksharamukha import transliterate

    return transliterate.process(
        "Devanagari",
        "Urdu",
        devanagari,
        post_options=["UrduRemoveShortVowels"],
    )


def read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TSV_FIELDS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
