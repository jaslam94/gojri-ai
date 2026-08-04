# OCR Gold Set — Correction Instructions

This folder covers 14 page images (from 12 real pages, 2 of which are two-page
spreads split into halves). Layout:
- `images/` — the page images only (`.png`), nothing else.
- `transcriptions/<page_id>/` — one folder per page, holding every text file for
  that page: `draft.txt` (your hand-corrected gold standard, the one to edit), plus
  whatever model outputs have been tested for that page so far, named
  `<model>_<prompt_version>.txt` (e.g. `gemini_3.6_flash_v1.txt`,
  `haiku_4.5_v1.txt`). A few pages also have `sonnet_5_original.txt`, the
  uncorrected first-pass draft kept for before/after comparison.

**`draft.txt` is a starting point, not a finished product** — it was produced by
Claude reading each image once, and is expected to contain real errors, especially:
- Diacritics and small marks (dots, nasalization strokes) — the hardest part of
  Nastaliq to get right and where most mistakes will be.
- Anywhere marked `[...]` in brackets — these are notes about images or uncertain
  content, not transcribed text, and need your judgment.

## How to correct each one
1. Open `images/<page_id>.png` and `transcriptions/<page_id>/draft.txt` side by side.
2. Read the image yourself and fix the text file until it exactly matches what's on
   the page, character for character.
3. Leave `[bracketed notes]` as-is if they're accurately describing a non-text
   element (like an illustration); delete them if they're wrong.
4. Don't worry about the two `direct_extraction` pages (`hindi_dict`,
   `quran_translation`) needing the same scrutiny as the others — those came from
   the PDF's real text layer, not a guess, but a quick check that nothing looks
   wrong is still worth doing.

## What's in here (12 pages, grouped by what they test)

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
| `hindi_dict` | Devanagari, direct extraction check (not vision OCR) |
| `quran_translation` | Perso-Arabic, direct extraction check (not vision OCR) |

## Why this matters (recap)
Once these are correct, they become the permanent yardstick. Every OCR approach we
test afterward (Haiku vs Sonnet, the decode-table idea, prompt tweaks) gets scored
against these exact pages, automatically, so we can tell what's actually better
instead of guessing from a handful of spot checks.

## Next step once corrected
Tell me when you've corrected as many as you have time for (doesn't have to be all
14 at once). I'll assemble the corrected ones into `gold.jsonl` and we move to
Stage 0's remaining item (corpus/provenance conventions) or into Stage 1.
