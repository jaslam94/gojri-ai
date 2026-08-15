# OCR Gold Set

This folder covers 12 vision-OCR page images (from 10 PDF pages, 2 of which
are two-page spreads split into halves). Layout:

- `images/` — the original page images (`.png`), rendered straight from the PDFs.
- `images_cropped/` — same images cropped to their content bounding box (+50px
  safety padding). **This is what OCR test calls actually use.** `images/` is
  kept only for comparison.
- `transcriptions/<page_id>/` — one folder per page:
  - `<page_id>_gold.txt` — the single source of truth. You check this against
    the cropped image. There is one gold file per page, not one per model.
  - `<page_id>_<model>_<prompt_version>_original.txt` — raw model output.
    Scripts always save this suffix. Never edit these files.
- `transcriptions_archived/<page_id>/` — models that were tested and shelved
  (reasons in `LOG.md`). Not part of the active comparison.
- `ocr_runs_log.csv` — token/cost log for scripted API runs.

Direct-extraction pages (`hindi_dict`, `quran_translation`) are not in the
image folders. Those PDFs already have a correct text layer. Source PDFs stay
in `pdfs/`.

## How to score a model

You edit only `_gold.txt`, against the image. Then each `*_original.txt` is
compared to that gold file. Do not make a corrected copy per model.

Run `py -3 scripts/score_gold.py` from the repo root. It prints word error
and a coarse error mix (diacritic, honorific/takhallus, heh, missing, extra,
letter/word). Dictionary pages mix English and Nastaliq on one line, so word
error there is noisier than on poetry.

**Not real errors** (do not chase these in gold): spacing between Gojri text
and an adjacent English gloss (`آپ (aap)` vs `آپ(aap)`), and spacing around
punctuation (`:`, `،`, `۔`). Only spacing between two Gojri words matters.
Illustration notes (`[illustration: ...]`, `[photo: ...]`) need not match
word for word across models; score the printed text. If a model wraps a
**printed** header or footer in `[badge:]` / `[footer:]`, those words are
missing from the scored text. That is a real error.

Agreement between models is evidence, not proof. On `gojri_ghazal` and
`kahawat_kosh` the true reading matched neither model's first guess at least
once. Always check the image.

## Bake-off result (Aug 2026, after the first-six gold re-check)

Pooled word error on 12 pages (1790 scored gold words). **One-shot API** is
the bulk-pipeline comparison. Chat numbers are a ceiling, not a fair rank.

| Setup | Pooled WER | Role |
|---|---|---|
| Composer 2.5 chat, prompt v1 | 12.7% | Gold-draft helper only |
| Gemini 3.6 Flash API, latest prompt per page | **17.3%** | Best one-shot on this set |
| Sonnet 4.6 API, latest prompt per page | 21.9% | Worse, and more expensive on Bedrock |
| Sonnet 5 Claude Code chat (6 pages) | 30.1% | Incomplete; possible gold leak |

Gemini wins or ties Sonnet 4.6 on 11 of 12 pages. Sonnet wins only
`dict_alif`. Composer chat is lower error on most pages because it is not
one-shot. Full table and failure modes: `LOG.md` (2026-08-15 bake-off).
Shelved models stay under `transcriptions_archived/`.

**Use for bulk transcription (provisional):** none. Gemini 3.6 Flash is the
best one-shot API here, but bulk vision OCR is paused until a method can run
without a person on every page. Spot-check remains required for any vision
output you do keep. Do not use Haiku 4.5, Qwen3-VL, or the other archived
models.

**Next prompt trial (do not edit v2 until scored):** keep banner footers as
plain text, never `[badge:]`; keep takhallus `ؔ`; do not rewrite Gojri labels
as Urdu (`پچھان`, `تانجے`, `کنّی`); do not skip the first stanza of a poem.
Do not put gold-page answers into the prompt. Re-run the six v1-only API
pages under v2 (or v3) before treating prompt version as a controlled factor.

## Pages (what each tests)

| Files | Tests |
|---|---|
| `dict_alif` | Dictionary layout, PUA scheme, mixed Nastaliq+English |
| `kahawat_kosh` | Two-column proverb layout, PUA scheme |
| `gojri_adbiyaat` | Dense literary prose, PUA scheme |
| `gojri_ghazal` | Dense justified essay prose, PUA scheme |
| `mahatma_gandhi` | Full-page illustration + one caption; do not invent text |
| `kulyate_spread_a_right` + `_b_left` | Spread poetry, legacy_8bit scheme |
| `nazir_spread_a_right` + `_b_left` | Second spread; left half has true blank space |
| `louk_warsti` | Real scan with paper show-through, image-only |
| `shingar_textbook` | Image-only textbook page |
| `primer_pehli` | Children's primer: captioned words + graphics |

## Status

All 12 pages have a `_gold.txt` file (Aug 2026). You re-checked the first six
against the image. Active originals: Gemini 3.6 Flash, Sonnet 4.6 (API, v1
and/or v2 by page), Composer 2.5 (chat, v1). Some pages also have Sonnet 5
Claude Code chat originals (`sonnet_5_cc_v2`). Chat is not a one-shot API
run. **Bulk vision OCR is paused.** Gemini is the best one-shot API on this set
(pooled WER 17.3% vs Sonnet 4.6 at 21.9%) but 17% word error without a human
check is not acceptable for the corpus. Dual-model agreement still shares a
wrong word on about 5% of agreed tokens. Next OCR work is the decode-table
spike. Score with `py -3 scripts/score_gold.py`. Shelved models live under
`transcriptions_archived/`. See `LOG.md`.
