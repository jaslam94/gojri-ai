# Gojri AI

Experimental work to help **Gojri** (گوجری, ISO 639-3: `gju`) show up properly
in AI, NLP, and related tech.

This project is run for the love of the language: OCR, speech, and language
models for a community language that is still barely present in mainstream AI.
Nothing here claims to be finished or production-ready. We learn in public,
document mistakes, and welcome help.

## Public datasets

| Dataset | Link |
|---------|------|
| Devanagari ↔ Nastaliq lexicon | https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon |
| Nastaliq OCR gold set (12 pages) + model bake-off | https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold |

## What lives in this repo

- Stage 0 research notes and experiment log (`CLAUDE.md`, `LOG.md`, `ROADMAP.md`)
- PDF catalog (`data/manifest.csv`)
- OCR gold images and transcriptions (`data/gold/`)
- Lexicon deliverable (`data/lexicon/`)
- Small scripts for extract, scoring, and transliteration (`scripts/`)

Large source PDFs and Common Voice audio stay local (see `.gitignore`). They are
not re-hosted here.

## Status (short)

- Lexicon: published on Hugging Face
- OCR gold + bake-off: published on Hugging Face
- Bulk vision OCR of the full PDF collection: **paused** (error rate still too high without human review)
- ASR / LLM fine-tuning: planned later

## Contributions

If you speak Gojri, work on OCR or speech, or want to help with data checks,
please open an issue or pull request. Native-speaker review, cleaner gold pages,
and better tooling all matter.

Please keep changes focused. Prefer discussion before large new pipelines.

## License notes

- Code and our packaging: see files in each folder
- Lexicon: derivative of Anjum & Sadiq’s dictionary; see `data/lexicon/LICENSE.md`
- OCR gold images: short book excerpts for research; see the HF dataset card

## Contact

GitHub: [jaslam94/gojri-ai](https://github.com/jaslam94/gojri-ai)  
Hugging Face: [junaidaslam](https://huggingface.co/junaidaslam)
