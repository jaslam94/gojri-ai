# Agent instructions (Gojri AI)

Follow this file in every Cursor session. The project brief, data inventory, technical findings, and current status live in `CLAUDE.md`. Treat `CLAUDE.md` as the source of truth for those facts. Do not copy it here. Update `CLAUDE.md` when a finding or status changes. Update this file when agent behaviour or writing rules change.

## Writing

Write all English output in ASD-STE100 Simplified Technical English. Use one meaning per word, active voice, simple tenses, and short sentences. Do not use preambles, pleasantries, conversational filler, or vague jargon.

Use no em dashes. Write with natural structure. Use commas, periods, or conjunctions instead. This is a compositional principle. Apply it during composition, not as a later edit. Do not write sentences that rely on interruption or a dramatic pause. Keep this rule unless the user cancels it.

## Working guidelines

- Explain AI and ML in plain terms. Teach concepts as you go.
- The user is a native Gojri and Urdu speaker, fluent in English, and a Gujjar. Use that skill for labels, translation checks, and dialect judgement.
- Research and agree before writing pipeline code.
- Run Python as `py -3`.
- Do not commit unless the user asks.
- Journal experiments in `LOG.md`. Keep `CLAUDE.md` status current.

## Public deliverables

- Gojri-English dictionary corpus: `junaidaslam/gojri-english-dictionary` on Hugging Face.
- Devanagari to Nastaliq lexicon: `data/lexicon/` (tracked) and `junaidaslam/gojri-devanagari-nastaliq-lexicon` on Hugging Face.
- OCR gold benchmark: `data/gold/` (tracked) and `junaidaslam/gojri-nastaliq-ocr-gold` on Hugging Face.
- PDF credits and rights notice: `data/pdf-corpus/` (tracked). The source PDFs are not a public deliverable. The Hugging Face repo `junaidaslam/gojri-print-pdf-collection` stays private (since 2026-11-23, no written permission to redistribute the books). Never make it public and never add PDFs to this repository.

Do not publish raw full PDF page text dumps from `data/extracted/` (gitignored).

## Decode and OCR status

NOORIN decode is abandoned. Do not rebuild NOORIN tables or scripts. See `data/archive/noorin-decode-spike/README.md`.

Batool font decode, multimodal Pass 2 with Gemini, and Image-vs-Text audit are complete for all 474 body pages of `Gojri-English-Dictionary.pdf`.

Quran GID decode remains paused. Bulk vision OCR for other books stays paused.

OCR model tests: report Arabic-letter error (Arabic-block letters only, no marks, ك=ک and ه=ہ equal, ھ separate), not whole-line character error, because English is 87% of the characters in dictionary lines. UTRNet-Large reads the Arabic runs of the 200 held-out lines at 2.1% with a 0 px crop margin (seed 0; 2.0% to 2.2% over seeds 0 to 4). UTRNet's dropout stays on at inference, so fix `--seed` when you report a UTRNet number. Details: `data/utrnet-test/README.md`.
