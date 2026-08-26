# Stage 0: Data Hygiene — Implementation Plan

**Goal**: end up knowing exactly what data we have, which files are worth processing,
in what order, and with a way to measure OCR quality. Nothing here trains a model.
This stage exists so that every later decision is made on facts instead of guesses.

**Guiding rule for this stage: nothing gets deleted.** Every step is additive or
reversible. Duplicates get *marked*, not removed, because a wrong delete is
unrecoverable and disk space is not our constraint.

---

## Step 0.1 — Build the manifest (the single source of truth)

Produce `data/manifest.csv`: one row per PDF, with every fact we've established,
so no future step has to re-derive them (and so we stop getting different numbers
each time we look).

Columns:
| Column | Meaning |
|---|---|
| `path` | relative path from `pdfs/` |
| `size_mb`, `pages` | basic stats |
| `md5` | file hash, for exact-duplicate detection |
| `dup_group` | id shared by byte-identical files, blank if unique |
| `is_primary` | 1 for the copy we keep, 0 for redundant copies |
| `category` | `good_text` / `bad_text` / `image_only` / `unclear` |
| `encoding_scheme` | `clean_unicode` / `pua` / `legacy_8bit` / `broken_tounicode` / `none` |
| `script_evidence` | `nastaliq_fonts` / `latin_only` |
| `likely_english` | 1 if real readable English detected |
| `in_scope` | 1 if it belongs in the Gojri corpus |
| `tier` | 1 dictionaries, 2 literature, 3 large volumes, 9 out of scope |
| `fonts` | sample of embedded font names (the evidence for the above) |

**Why a manifest and not just deleting duplicates**: it is re-runnable, reviewable,
auditable, and diffable. If a classification turns out wrong (which already happened
once with the poetry collections), we fix one column instead of recovering files.

**Success check**: numbers in the manifest reconcile with the figures already in
`CLAUDE.md` (92 files, 7 duplicate groups, 2,244 duplicate pages, 14,550 pages
needing OCR). Any mismatch means one of the two is wrong and must be resolved.

---

## Step 0.2 — Fix the triage errors the strategy review found

Two known problems to correct, both driven by the manifest:

1. **The 11 "unclear" files must be judged per file, by embedded font, not by
   character statistics.** Character-range counting is what caused two Gojri poetry
   collections (`gojri-kalam-israel-asar`, `gojri-kalam-_gulam_sarwar_rana`) to be
   mislabeled as English books. Rule to apply instead:
   - Nastaliq fonts present (NOORIN*, Batool, Aseer, Sadaf, Unwan, Zakharif...)
     → Gojri content, in scope, regardless of what the extracted characters look like.
   - Only Latin fonts (Calibri, Times, Arial...) *and* recognizable English words
     → genuinely an English book, out of scope for the Gojri text corpus.
2. **Separate the two legacy encoding schemes** (`pua` vs `ascii_legacy`) as an
   explicit column, since they need different decode tables if we go that route.

**Success check**: the two `gojri-kalam-*` files come out `in_scope=1`, and the
`the-gujjars-vol-*` files come out `likely_english=1, in_scope=0`.

---

## Step 0.3 — Build the OCR gold set (the yardstick)

The highest-value human work in the project. Without it we cannot measure OCR
quality at all, only form opinions about it.

- Script selects ~24 candidate pages, deliberately spread across the hard cases:
  PUA-scheme pages, ASCII-scheme pages, image-only pages, dense dictionary layout,
  poetry layout (unusual line breaks), and at least one page with mixed
  Nastaliq + English.
- Pages are rendered to PNG at zoom 2 into `data/gold/images/`.
- A starter transcription is produced for each so the user is **correcting, not
  typing from scratch**, which is far faster and less error-prone.
- User reviews each one against the image and writes one
  `data/gold/transcriptions/<page_id>/<page_id>_gold.txt` until it is exactly
  right. Raw model outputs stay in `*_original.txt` and are never edited.
- Result: one gold text per page, used to score every OCR method.

This set is then never used for training, only for measuring. Every OCR approach we
try (Haiku, Sonnet, Tesseract, decode table) gets scored against these same pages,
using character error rate, so comparisons are apples to apples.

**Success check**: 20+ pages the user has personally confirmed are letter-perfect.

**Progress (Aug 2026)**: `scripts/build_gold_candidates.py` selected 12 vision-OCR
images (2 are two-page-spread halves) spanning every hard case found in triage.
Direct-extraction pages (`hindi_dict`, `quran_translation`) were dropped from the
gold image folders. Each vision page has one `_gold.txt` (user-checked; first six
re-checked 2026-08-15). Score with `scripts/score_gold.py`. Working set is 12
images rather than the ~20-30 originally proposed. Can extend later if the eval
set is too small. One-shot bake-off: Gemini 3.6 Flash 17.3% pooled WER, Sonnet
4.6 21.9%. **Bulk vision OCR is paused** (no capacity for page-by-page review;
error rate is too high to accept unreviewed). Next: decode-table spike, scored
on this gold set. Details in `data/gold/README.md` and `LOG.md`.

---

## Step 0.4 — Decide the corpus layout and conventions

Small but worth settling before data starts flowing:
- Folder layout for extracted text, one `.txt` per source book, plus a JSONL with
  per-page records and provenance (source file, page number, method used, model).
  Provenance matters: if we later discover a method was flawed, we need to know
  exactly which text came from it.
- Note the orthography/normalization question (currently unowned, in the parking
  lot): check what spelling conventions the Common Voice sentences use, since those
  are already human-curated, and prefer matching them over inventing our own.
- Confirm backup plan for the derived data.

---

## What Stage 0 does *not* do
- No model training, no OCR at scale, no AWS spend on bulk vision pages.
- No file deletion of source PDFs.
- Gold-set bake-off (Aug 2026) ranked one-shot models and paused bulk vision
  OCR. The remaining OCR experiment is the decode-table spike, still scored
  on the same gold pages.

## Definition of done
1. `data/manifest.csv` exists, reconciles with known figures, and correctly
   classifies the previously-misjudged files.
2. A deduped, tiered, in-scope processing list is derivable from it.
3. A verified gold set of 20+ pages exists.
4. Corpus layout and provenance conventions agreed.
