# Model space check, prose (55 of 170 cards)

Books: *Banjara* and *Dil-Darya*. The character n-gram space inserter (`scripts/ocr_eval/spacing_lm.py`, config of 2026-11-23) added spaces to
170 glued OCR tokens (`cards.json`: `id`, `row`, `token`, `proposal`, `context`). The speaker checked the first 55 on 2026-11-23 and wrote the right
spaces in `text` (`model_space_20261123.json`, key = card id). The `text` is the truth; some Accept marks are wrong clicks (`پونچھ`, `بدلیوں`).

Result: of 67 spaces that the model added in these tokens, 32 are right and 35 wrong; 9 truth spaces are missing. Most wrong cuts are inside single Urdu or
place-name words (`قدامت`, `مقبوضہ`, `قلانچیں`, `ڈوڈہ`, `جغرافیہ`). The text of these books is largely Urdu; the model was built for Gojri idioms. See `LOG.md`, 2026-11-23.

## Gojri-row check (2026-11-24)
`model_space_gju_20261124.json` (speaker marks and text) and `cards_gju.json` (106 cards: glued OCR tokens on rows tagged Gojri where the
space model adds a space; cards the speaker had not seen). 52 accepted, 54 rejected. Scored per space (101 cards with equal letters; 5 cards
hold letter fixes by the speaker and are left out): 79 right, 49 wrong, 10 missing.
By token length (letters): under 6: 16 right, 29 wrong; 6 to 7: 21 right, 14 wrong; 8 to 10: 18 right, 4 wrong; 11 or more: 24 right, 2 wrong.
30 of the 54 rejects are tokens under 6 letters (`مانہ` cut to `ما نہ` seven times, `عارف`, `انجم`, `جانے`). Rule "token of 8 or more letters":
42 right, 6 wrong. The threshold was picked on this same sample, so the numbers are optimistic. Needs a fresh test before use.
