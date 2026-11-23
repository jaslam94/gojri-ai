# Model space check, prose (55 of 170 cards)

Books: *Banjara* and *Dil-Darya*. The character n-gram space inserter (`scripts/ocr_eval/spacing_lm.py`, config of 2026-11-23) added spaces to
170 glued OCR tokens (`cards.json`: `id`, `row`, `token`, `proposal`, `context`). The speaker checked the first 55 on 2026-11-23 and wrote the right
spaces in `text` (`model_space_20261123.json`, key = card id). The `text` is the truth; some Accept marks are wrong clicks (`پونچھ`, `بدلیوں`).

Result: of 67 spaces that the model added in these tokens, 32 are right and 35 wrong; 9 truth spaces are missing. Most wrong cuts are inside single Urdu or
place-name words (`قدامت`, `مقبوضہ`, `قلانچیں`, `ڈوڈہ`, `جغرافیہ`). The text of these books is largely Urdu; the model was built for Gojri idioms. See `LOG.md`, 2026-11-23.
