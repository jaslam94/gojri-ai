# Gojri text sources found by OpenCode (2026-11-24), with my checks

Source: an OpenCode agent searched the open web with `plans/PROMPT-opencode-gojri-corpus-search.md`. Its raw folder `gojri-corpus-search/` stays local and
gitignored: it holds third-party text samples and the private phone number and e-mail of individuals. It lists 32 sources, 3 at priority 1.
Everything below is the agent's report unless it says "checked". Nothing was downloaded by me.

## Result in one line
No clean Gojri source above 100,000 words was confirmed. Typed Unicode Gojri is rare. The big print collections (JKAACL, Javaid Rahi, JKBOSE, Bazm-e-Gojri, the
archive.org scans) are InPage or scan PDFs, so their text layer is garbage: they are OCR work, not text.

## Sources worth acting on
| Id | What | Size (agent) | Rights | My view |
|---|---|---|---|---|
| A01 | Blog `gojrizubanoadab.blogspot.com`: typed Gojri poetry, prose, translation, Unicode Nastaliq | 199 posts; the agent estimates 100,000 to 160,000 words from 6 posts | none stated: ask the owner | Best free lead. The estimate rests on 6 posts, and poetry posts have only 159 to 371 words, so the true count may be far lower. Count it only after permission. The sample (checked) is Gojri (مناں, ڈاہڈی, سجناں, گیو), not Urdu, but it has glued words (`جےکر`, `لگوجگ`): typed text has space errors too. Mostly poetry. |
| B01, B02 | LDC-IL parallel text, Gojri with English and 146 Indian languages | 29,139 and 33,476 words, 5,332 sentences, probably overlapping | paid, non-commercial undertaking | Good for translation tests. Sentence set made for grammar coverage, not running text. Price unknown. No purchase without the speaker's decision. |
| E01 | Losey, *Writing Gojri* (UND thesis, 2002) | 282 pages | thesis | Spelling rules (ݨ, ڵ, InPage habit of writing ن for both). Read it for the orthography decisions. |
| B03 | Common Voice Gujari 27.0 | 10.67 h, 3,854 sentences | CC0 but "forbidden to re-host" | We hold 26.0. Compare the sentence list with ours before any use. |
| A04 | Second blog (Rang-e-Watan, Gojri label) | about 8 posts, 2,500 words | none stated | Small. |

## Dead ends (agent, not re-checked)
No `gju` in OPUS, FineWeb2, GlotCC, Glot500, HPLT. MADLAD-400 has a `gju` config of 0.4 MB, mostly mislabeled Urdu, Pashto and spam. No Gojri Bible text online
(eBible, bible.com, Scripture Earth: audio and video only). Wikimedia Incubator Gujari Wikipedia has 3 pages. Tatoeba has no Gojri. Bhashini covers 22 languages.
Open Bible Stories gju is audio only. A paid Hugging Face "Gojri" set (B05) carries the language tag `gjk` (Kachi Koli): unverified, do not pay.

## Notes for our project
- Typed text spells the small-v noon with ن or ں, not ݨ. Our print-faithful OCR labels use ݨ and ڵ where the print shows them. A text model must fold ݨ ݩ ڵ to the plain letter (the tagger in `scripts/ocr_eval/langid.py` already folds them to one symbol). The marker rule cannot work on this text.
- C05 (archive.org `gojri-eng-dictionary`, 498 pages) is probably the dictionary we already hold (also 498 pages). The agent names "Altaf Aarsi"; our title page says M. R. Anjum Awan. The archive.org "public domain mark" is the uploader's claim, not proof.
- C03 (a 988-page Gojri Quran translation, CC0 claimed by the uploader, OCR garbled) is a different book from the 717-page one we hold.
- The largest Gojri text we can get is our own corrected OCR of about 70 books (14,060 pages needing OCR). Corrected text from our own pipeline is worth more than another small web source.
