# Gojri AI

Experimental work to help **Gojri** (گوجری, ISO 639-3: `gju`) show up properly
in AI and NLP.

The long-term aim is a **Gojri ASR** system and a **Gojri LLM**, in the same
spirit as community Pashto projects such as **Katib** (speech recognition) and
**Qehwa** (language model). This is early work. It is done for the love of the
language and for fairer representation in tech.

I am a software engineer. I learn best by intuition and by trying things. One
purpose of this project is to learn the speech and NLP domain while building
something useful for Gojri. Nothing here claims to be finished. Contributions
are welcome.

## Public datasets (Hugging Face)

These live on Hugging Face under [junaidaslam](https://huggingface.co/junaidaslam):

| Dataset | Hugging Face |
|---------|--------------|
| Devanagari ↔ Nastaliq lexicon | [gojri-devanagari-nastaliq-lexicon](https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon) |
| Nastaliq OCR gold set + bake-off | [gojri-nastaliq-ocr-gold](https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold) |
| Gojri print PDF collection (research mirror) | [gojri-print-pdf-collection](https://huggingface.co/datasets/junaidaslam/gojri-print-pdf-collection) |

Repo code, notes, and local third-party source notes stay on GitHub. The packaged
datasets above are on Hugging Face.

## Local data you may already have

Under `datasets/` we keep third-party material for training experiments. See
`datasets/README.md` for where it came from:

- **Gojri Literature Corpus** (FLI via Mozilla Data Collective, CC-BY-NC-4.0)
- **Common Voice Gujari** speech (Mozilla Common Voice 26.0)

Those are not re-uploaded as our own corpora from this GitHub repo. Please keep
their original licenses and terms.

## What lives in this repo

- Research notes and experiment log (`CLAUDE.md`, `LOG.md`, `ROADMAP.md`)
- PDF catalog (`data/manifest.csv`) and per-file credits (`data/pdf-corpus/`)
- OCR gold set (`data/gold/`)
- Lexicon deliverable (`data/lexicon/`)
- Scripts for extract, scoring, and transliteration (`scripts/`)

Large PDFs stay local under `pdfs/` (gitignored) and are mirrored on Hugging Face
with credits. Common Voice audio clips stay gitignored.

## Status (short)

- Lexicon, OCR gold, and PDF research mirror: on Hugging Face
- Bulk vision OCR of every page: paused until quality is safer
- ASR / LLM fine-tuning: the goal ahead

## Contributions

If you speak Gojri, work on OCR or speech, or want to help with data checks,
please open an issue or pull request. Native-speaker review, cleaner gold pages,
better credits, and rights-cleared books all help.

Please keep changes focused. Prefer a short discussion before large new pipelines.

## License notes

- Code and our packaging: see files in each folder
- Lexicon: derivative of Anjum & Sadiq’s dictionary; see `data/lexicon/LICENSE.md`
- OCR gold / PDF collection: third-party content remains with original rights holders

## Contact

GitHub: [jaslam94/gojri-ai](https://github.com/jaslam94/gojri-ai)  
Hugging Face: [junaidaslam](https://huggingface.co/junaidaslam)
