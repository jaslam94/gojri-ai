# Kahawat-Kosh spacing review (200 cards)

Book: *Kahawat-Kosh* (proverbs). 200 random idioms (`sample.json`, seed 20261116, no card from the earlier reviews),
read from the OCR run `kahawat-pdfmarks-v2` (local). Each card shows the printed rows and the OCR text; the speaker
wrote the text as **words** (spaces follow meaning, ruling 2026-11-16) and corrected any wrong letter.

| File | What it is |
|---|---|
| `spacing_marks_20261121.json` | The speaker's export of 2026-11-21. Key = card id (the position in `sample.json`, from 0; the page shows it plus 1). Each value has `m` (`fixed` 156, `ok` 44, `unsure` 0) and `text`. |
| `sample.json` | The 200 cards: PDF page, entry number, row ranges and the OCR text that the page showed. |

Truth of a card: the speaker's text. On an `ok` card the OCR text counts as the truth, so scores are a little
optimistic (see the parent `README.md`). Three `fixed` cards (ids 2, 9, 71) equal the OCR text.

What the 156 `fixed` cards changed: spaces on nearly all; letters or punctuation on 44 cards (10 times گ for ک,
7 times a missing ب in جیبھ, 6 missing colons, the rest single letters); marks on 3 cards.

Read by: `scripts/ocr_eval/score_spacing.py`. The review page itself (`index.html`, built by
`scripts/ocr_eval/build_spacing_review.py`) holds crops of the printed book and stays local.

## Scores (2026-11-21, `score_spacing.py`)

| Text | Letter error | Spaces, on the 162 cards whose letters match | Cards with exact spaces |
|---|---|---|---|
| OCR as read | 44 of 4,036 letters (1.1%) | 759 in the truth; text has 553; 527 right, 232 missing, 26 extra | 50 of 162 |
| + word splitter, margin 4 | same | text has 656; 613 right, 146 missing, 43 extra | 70 of 162 |
| + word splitter, margin 6 | same | text has 624; 595 right, 164 missing, 29 extra | 68 of 162 |

The OCR text has 901 words; the speaker's text has 1,165. 205 of the 232 missing spaces follow a non-joining letter
(ا د ڈ ذ ر ڑ ز ژ و ے), where the print shows no gap. The splitter (`space_fix.py`) added 103 spaces at margin 4, 86 of
them right, and 71 at margin 6, 68 of them right. Its word list comes from the FLI corpus and the Banjara and
Dil-Darya OCR, not from Kahawat-Kosh. Four margins (2, 4, 6, 8) were tried on these same cards, so treat the numbers
as a development result. Adding the speaker's own words from the other cards (5-fold test) gained 1 to 2 spaces.
