# Datasets in this folder

These files were collected for the gojri-ai project. They are **not** re-published
from this GitHub repo as separate Hugging Face uploads (audio and third-party
corpus terms). This README only records where they came from, so anyone cloning
the project knows the source and license.

Long-term goal of the project: build Gojri ASR and a Gojri LLM in the same
spirit as community Pashto work such as **Katib** (ASR) and **Qehwa** (LLM).
This folder is part of that road: speech and text we can learn from locally.

## 1. Gojri Literature Corpus (text)

**Local path:** `datasets/Gojri Language Corpus/`

| Field | Detail |
|-------|--------|
| What it is | 11 UTF-8 Nastaliq text files (~60k words): stories, religious prose, Q&A, one poem, one Gojri–Urdu parallel file |
| Curated by | Forum for Language Initiatives (FLI) |
| Obtained from | [Mozilla Data Collective](https://datacollective.mozillafoundation.org/) — dataset listed as **Gojri Literature Corpus** |
| License | **CC-BY-NC-4.0** (non-commercial; attribution required) |
| Notes | Some files contain U+FFFF placeholders (see project `LOG.md`). Keep the FLI / Data Collective license if you reuse these texts. |

Please credit FLI and Mozilla Data Collective if you use these files.

## 2. Common Voice Gujari (speech)

**Local path:** `datasets/cv-corpus-26.0-2026-06-12/gju/`

| Field | Detail |
|-------|--------|
| What it is | Mozilla Common Voice **Scripted Speech** release for Gujari / Gojri (`gju`): clips + TSV splits |
| Obtained from | [Mozilla Common Voice](https://commonvoice.mozilla.org/) / Mozilla Data Collective releases |
| Release used here | Common Voice corpus **26.0** (folder name `cv-corpus-26.0-2026-06-12`) |
| License | **CC0** for contributed clips, with Common Voice terms (do not re-host in ways that break speaker privacy / terms) |
| Notes | Audio under `clips/` is gitignored in this repo. Metadata TSVs may be tracked. Prefer linking to Mozilla rather than re-uploading the full audio dump. |

Please follow Common Voice terms if you train or share models on this data.

## What we do not claim

- We did not create the FLI literature corpus.
- We did not create Common Voice Gujari.
- We only keep local copies for research toward Gojri ASR and LLM work.

## Related public gojri-ai releases

- Lexicon: https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon  
- OCR gold set: https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold  
- Print PDF collection (with per-file credits): https://huggingface.co/datasets/junaidaslam/gojri-print-pdf-collection  
- Project: https://github.com/jaslam94/gojri-ai  

If you maintain FLI, Common Voice, or related Gojri data and want this note corrected, open an issue. Corrections are welcome.
