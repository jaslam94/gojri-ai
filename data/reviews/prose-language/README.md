# Prose language tags (Gojri or Urdu), speaker, 2026-11-23

`lang_tags_20261123.json`: the speaker's tag for each of 262 prose rows (key = id in `lang_tag_sample.json`).
Tags: `gju` 226, `urd` 29, `mixed` 4, `unsure` 3. Page: `scripts/ocr_eval/build_lang_tag_review.py`.
`lang_tag_sample.json`: the rows (book, page, row index, text; 142 rows of the earlier prose review and 120 random new rows).

Read this before you use the tags:
- The 142 reviewed rows are not random: they come from a few pages (21 of the 29 Urdu rows are on Banjara p.12, the introduction essay).
  Only the 120 `origin: new` rows are a random sample: 110 gju, 5 urd, 4 mixed, 1 unsure.
- The speaker tags by the grammar and the words of the line. Gojri and Urdu write names and places the same way, so such rows are
  hard to tag from one line alone. The second pass (`build_lang_context_review.py`) shows two lines before and after, with a new
  tag `same` (the row reads the same in both languages).

## Second pass (2026-11-24)
`lang_tags_context_20261124.json` holds the speaker's re-tags of the 7 rows that were `mixed` or `unsure`, shown with two lines before and
after (`lang_context_sample.json`). Result: 2 `same`, 2 `urd`, 3 `gju`. The merged tags are in `lang_tags_final_20261124.json`
(key = `book|page|row`, with the old tag where the second pass changed it).
Final counts of the 262 rows: `gju` 229, `urd` 31, `same` 2. No `mixed`, `other` or `unsure` row is left.
Random rows only (120): 112 gju, 6 urd, 2 same (5% Urdu).
