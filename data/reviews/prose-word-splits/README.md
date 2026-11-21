# Word-split review (66 cards)

Books: *Banjara* and *Dil-Darya* (OCR text, `prose-aws-full2`, local). The word splitter (`scripts/ocr_eval/space_fix.py`,
margin 4, before the one-letter rule of 2026-11-21) proposed a split for 66 glued tokens. The speaker saw the token, the
proposal and the OCR row, marked Accept or Reject, and wrote the right split in a box (spaces follow meaning, ruling
2026-11-16). Reviewed 2026-11-21.

| File | What it is |
|---|---|
| `splits_20261121.json` | One entry per card: `id` (row and token), `token` (as OCR read it), `proposal`, `context` (the OCR row), `m` (accept or reject) and `text` (the speaker's split). |

The `text` is the truth. Letters never differ from the token. One card was marked Reject although its added space is
right and only incomplete (`کےنورمحمد`, truth `کے نور محمد`), while three similar cards were marked Accept; the scorer
uses `text`, not `m`.

Read by: `scripts/ocr_eval/score_splits.py`.

## Result (2026-11-21)

| | Cards | Spaces |
|---|---|---|
| Proposed by the splitter | 66 | 72 |
| Right | | 66 (91.7%) |
| Wrong cut | 6 | 6 |
| Truth spaces still missing in these tokens | 4 cards | 4 |

56 cards equal the proposal. 3 more are right but incomplete (the speaker added a space: `ہر ہر گل`, `آ کے جے`,
`کیو سر کھلا`), and 1 more (`کے نور محمد`, marked Reject). 6 proposals cut a word and the speaker kept it whole:
`پہاڑیوں`, `ہزارے`, `گویوں`, `گیارہ`, `ہولو`, `کیاری`. In all six the second piece (`یوں` twice, `ے`, `رہ`, `لو`, `ری`) is an
ending or has no meaning of its own there; the proposals that were right have a real word as the second piece.

Limits: these cards are the splitter's own proposals, so the result is a precision figure, not a recall figure. The
word list holds the OCR of these same two books, so the tokens were seen when it was built. The one-letter rule
(`MIN_PIECE = 2` in `space_fix.py`) was written after this review and removes the cut of `ہزارے` only. Run
`py -3 -X utf8 scripts/ocr_eval/score_splits.py` to compare `--min-piece 1` and `2`: 72 added, 66 right, 6 wrong, and
71 added, 66 right, 5 wrong.
