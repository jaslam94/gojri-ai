# Random OCR rows, speaker check (2026-11-26)

`review_marks_20261126.json`: the speaker checked 120 random prose rows (Banjara 95, Dil-Darya 25) from `data/ocr/prose-words/random_ocr_review.html`.
Each key is `book|page|row`; fields `m` (ok or wrong), `ocr` (the OCR text on the card), `text` (the speaker's text box), `types` (unused; one row has a tick).
Tags of the rows: `data/reviews/prose-language/lang_tags_final_20261124.json` (Gojri 112, Urdu 6, same 2).

Truth is always the `text` field. Notes on the file:
- `Banjara|443|19` is marked ok but the text was fixed (`گُٹی` to `ٹُٹی`; the image shows `ٹُٹی`). Count it as wrong.
- `Banjara|214|5` and `Banjara|230|15` are marked wrong but the text is unchanged. The images match the OCR text. Count them as no difference.
- The speaker did not use the type ticks. The error types come from a character diff of `ocr` against `text`.

Result (OCR run `prose-aws-full2`, same-letter rules of `score_prose_review.py`):
- 42 of 120 rows have no difference; 78 differ.
- Letters: 31 edits on 5,142 letters = 0.60% (22 rows). Marks: 7 of 126 = 5.6% (7 rows).
- Spaces: 173 missing and 9 extra, on 1,314 true spaces; 64 rows have a space difference, 48 of them only that.
- Punctuation: 4 rows (quote marks the OCR read as another quote or missed). Digits: 2 rows (page and line numbers).
- 9 of the 31 letter edits are a `گ` that should be another letter (`ک` 7, `ٹ` 1, `ئ` 1); 8 of them sit next to a pesh.
- Gojri rows: letters 0.59%, marks 5.7%. Urdu rows (6 only): letters 0.63%.

Space model on these rows: `scripts/ocr_eval/score_space_rule_random.py` (98 rows with equal letters). The model adds 209 spaces, 122 right, and finds 80% of the missing ones.
With "token of 8 letters or more" it adds 67, 52 right (78%), and finds 34%.
