# Datasets in this folder

These files were collected for the gojri-ai project. They are **not** in this
GitHub repo and are not re-published anywhere by this project (audio and
third-party corpus terms). Download them from their sources into the paths below.
This README records where they came from, so anyone cloning the project knows the
source and the license. Until November 2026 the FLI text files and the Common Voice
TSV files were tracked here. They are now untracked and gitignored.

Long-term goal of the project: build Gojri ASR and a Gojri LLM in the same
spirit as community Pashto work such as **Katib** (ASR) and **Qehwa** (LLM).
The maintainer is a software engineer who learns by intuition and experiment;
learning speech and NLP is part of why this work exists. This folder is part
of that road: speech and text we can learn from locally.

## 1. Gojri Literature Corpus (text)

**Local path:** `datasets/Gojri Language Corpus/`

| Field | Detail |
|-------|--------|
| What it is | 11 UTF-8 Nastaliq text files (~60k words): stories, religious prose, Q&A, one poem, one Gojri-Urdu parallel file |
| Curated by | Forum for Language Initiatives (FLI) |
| Obtained from | [Mozilla Data Collective](https://datacollective.mozillafoundation.org/), dataset listed as Gojri Literature Corpus |
| License | **CC-BY-NC-4.0** (non-commercial; attribution required) |
| Notes | Not in this repo (gitignored). Download it into the local path above. Some files contain U+FFFF placeholders (see project `LOG.md`). Keep the FLI / Data Collective license if you reuse these texts. |

Please credit FLI and Mozilla Data Collective if you use these files.

## 2. Common Voice Gujari (speech)

**Local path:** `datasets/cv-corpus-26.0-2026-06-12/gju/`

| Field | Detail |
|-------|--------|
| What it is | Mozilla Common Voice **Scripted Speech** release for Gujari / Gojri (`gju`): clips + TSV splits |
| Obtained from | [Mozilla Common Voice](https://commonvoice.mozilla.org/) / Mozilla Data Collective releases |
| Release used here | Common Voice corpus **26.0** (folder name `cv-corpus-26.0-2026-06-12`) |
| License | **CC0** for contributed clips, with Common Voice terms (do not re-host in ways that break speaker privacy / terms) |
| Notes | Not in this repo (audio and TSV files are gitignored). Download the release from Mozilla into the local path above. |

Please follow Common Voice terms if you train or share models on this data.

## 3. Gojri blog text (typed Unicode Nastaliq)

**Local path:** `datasets/gojri-blogs/` (gitignored). Fetch with `scripts/corpus/fetch_blogger.py` (public Blogger feed, one request every 2 s).

| Folder | Source | Posts | Words | Notes |
|---|---|---|---|---|
| `gojrizubanoadab/` | [Gojri Zuban o Adab](https://gojrizubanoadab.blogspot.com/) (owner: Abrar Hussain Gujjar) | 199 | 67,177 | Gojri poetry, prose and translations; part is Urdu. About 78% of the letters tag as Gojri (`scripts/ocr_eval/langid.py`, a rough tag). |
| `rungewatan-hasan/` | [Rang-e-Watan](https://rungewatan.blogspot.com/), label of the poet Chaudhry Hasan-ud-Din | 10 | 607 | Gojri poetry. |

Fetched 2026-11-24 from public pages for non-commercial research. The pages state no license. Only the Gojri parts are kept for use (the blogs also carry Urdu).
Text from these blogs keeps its credit to the blog and to the poet or writer of each post. Owners who want a text removed can open an issue on GitHub. Typed text writes the small-v noon as ن or ں, not ݨ.

## What we do not claim

- We did not create the FLI literature corpus.
- We did not create Common Voice Gujari.
- We did not write the blog posts of section 3.
- We only keep local copies for research toward Gojri ASR and LLM work.

## Related public gojri-ai releases

- Lexicon: https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon  
- OCR gold set: https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold  
- Project: https://github.com/jaslam94/gojri-ai  

If you maintain FLI, Common Voice, or related Gojri data and want this note corrected, open an issue. Corrections are welcome.
