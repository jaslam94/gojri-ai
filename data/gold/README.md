# OCR Gold Set — Correction Instructions

This folder covers 14 page images (from 12 real pages, 2 of which are two-page
spreads split into halves). Layout:
- `images/` — the original page images (`.png`), rendered straight from the PDFs.
- `images_cropped/` — same images cropped to their content bounding box (+50px
  safety padding). **This is what OCR test calls actually use** — cuts image
  tokens substantially on pages with large blank margins (~60% on the densest
  pages). `images/` is kept only for comparison, not used for OCR calls.
- `transcriptions/<page_id>/` — one folder per page. Each *active* candidate model
  gets **two files**: `<page_id>_<model>_<prompt_version>_original.txt` (the raw,
  untouched model output — what the automated test scripts always save, never
  hand-edited) and `<page_id>_<model>_<prompt_version>_corrected.txt` (your hand
  correction against the source image, added separately once review is done — not
  every model has one yet). Keeping both, rather than correcting in place, is
  deliberate: it preserves a real before/after record of how much correction effort
  each model's output actually needed, and the raw output is never at risk of being
  overwritten. (Early on, corrections were made in place and the raw originals had
  to be recovered from git history — fixed going forward, see `LOG.md`.)
- `transcriptions_archived/<page_id>/` — same naming, for models that were tested
  and shelved (reasons + concrete examples in `LOG.md`). Kept for the record, not
  deleted, but not part of the active comparison.

Earlier this project had one `draft.txt` per page acting as the gold standard, but
it was produced without a real fixed, documented prompt, so it wasn't a fair
baseline for comparing models against. Dropped in favor of the model-per-file setup
above.

## Correction workflow (revised)
Correcting is per model, not per page, and is the user's own process — Claude
generates the raw `<model>_<version>_original.txt` files; the user adds a
`<model>_<version>_corrected.txt` copy by hand, comparing each model's raw output
against the source image. Naming convention is now fixed (see above), not open.
When two models' corrected outputs on the same page still disagree with each other,
that's a useful signal in itself — a real remaining ambiguity worth checking against
the image again, not just noise.

## What's in here (12 pages needing vision OCR, grouped by what they test)

| Files | Tests |
|---|---|
| `dict_alif` | Dictionary layout, PUA scheme, mixed Nastaliq+English on one page |
| `kahawat_kosh` | Two-column proverb layout, PUA scheme |
| `gojri_adbiyaat` | Dense literary prose, PUA scheme, multiple poem excerpts with author names |
| `gojri_ghazal` | Dense justified essay prose, PUA scheme |
| `mahatma_gandhi` | Mostly a full-page illustration + one caption line — tests that the method doesn't invent text that isn't there |
| `kulyate_spread_a_right` + `_b_left` | Two-page spread poetry, legacy_8bit scheme (the scheme found late in triage) |
| `nazir_spread_a_right` + `_b_left` | Second spread example; the left half has a lot of true blank space, another "don't invent content" test |
| `louk_warsti` | Real scanned page (visible show-through from the other side of the paper), image-only, folk story |
| `shingar_textbook` | Image-only, clean born-digital textbook page |
| `primer_pehli` | Children's primer: isolated captioned words + decorative graphics, not paragraphs — a very different layout from everything else |

Plus 2 `direct_extraction` pages (`hindi_dict`, `quran_translation`) — already
correct Unicode pulled straight from the PDF's text layer, not vision-OCR
candidates, not part of this model comparison.

## Why this matters (recap)
Every OCR approach tested gets run against these same 12 pages, so quality/cost
tradeoffs are based on real, comparable outputs instead of a handful of spot checks.
Current status (see `LOG.md` for the full, up-to-date picture): Gemini 3.6 Flash
and Sonnet 4.6 are the active candidates, both now fully hand-corrected on
`dict_alif` and `gojri_adbiyaat`, converging to the same reading on almost every
line — a real gold standard, not just two independent guesses. Haiku 4.5, Qwen3-VL,
Llama 4 Maverick, Pixtral Large, and now **Kimi K2.5** (checked against the
converged gold text — solid on dictionary layout, notably weak on poetry, see
`LOG.md`) were tested and shelved. Sonnet 5 is blocked on an AWS Sales-gated access
request (see `LOG.md`) — Sonnet 4.6 is standing in for it until that clears. The
decode-table idea and future prompt versions remain open follow-ups.
