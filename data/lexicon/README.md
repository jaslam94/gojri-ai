---
pretty_name: Gojri Devanagari–Nastaliq Lexicon
language:
  - gju
license: other
license_name: derivative-of-copyrighted-dictionary
license_link: LICENSE.md
task_categories:
  - translation
  - other
tags:
  - gojri
  - gujari
  - gju
  - nastaliq
  - perso-arabic
  - devanagari
  - dictionary
  - lexicon
  - low-resource
  - indo-aryan
  - orthography
  - script-conversion
size_categories:
  - 1K<n<10K
dataset_info:
  features:
    - name: entry_id
      dtype: string
    - name: page
      dtype: int32
    - name: line
      dtype: int32
    - name: devanagari
      dtype: string
    - name: roman
      dtype: string
    - name: nastaliq
      dtype: string
    - name: english_gloss
      dtype: string
    - name: quality
      dtype: string
configs:
  - config_name: default
    data_files:
      - split: train
        path: gojri_lexicon_final.tsv
  - config_name: human_verified
    data_files:
      - split: train
        path: gojri_lexicon_human_verified.tsv
---

# Gojri Devanagari–Nastaliq Lexicon

Script-conversion lexicon for **Gojri** (also spelled Gujari; ISO 639-3: `gju`).

The language of this dataset is **Gojri**, not Urdu and not Hindi.

Each row maps a **Devanagari headword** from a published Gojri dictionary to a
**Gojri Nastaliq** (Perso-Arabic) form. Optional Roman transliteration and a short
English gloss come from the same source line.

This dataset supports Gojri NLP: orthography tools, OCR/ASR lexicon checks, and
future translation work. It is **not** a re-publication of the full dictionary text.

## Source attribution (required)

This lexicon is a **derived script-conversion resource** built from headwords in:

> Anjum, Rafique, and Ruksana Sadiq. *Concise Gojri–English–Hindi Dictionary*.
> Educational Publishing House / J K Anjuman Taraqi Gojri Adab, New Delhi.
> ISBN **978-81-19225-29-3**. Compilation: Prof. (Dr.) Rafique Anjum (D.Phil).
> Composition and vetting: Ms. Ruksana Sadiq (M.Phil). © All rights reserved
> by the original rights holders.

Local PDF file used for extraction:
`anjumshanasi/Gojri-Hindi-English-Dictionary.pdf` (458 pages; MD5
`dbcf6814f1b19a111f8bb3955e341b11` in the gojri-ai project manifest).

**Please cite both this dataset and the original dictionary** in any publication
or redistribution that uses these headwords. See [Citation](#citation) and
[License](#license).

## Dataset files

| File | Rows | Description |
|------|-----:|-------------|
| `gojri_lexicon_final.tsv` | 1,862 | Full lexicon (default split) |
| `gojri_lexicon_human_verified.tsv` | 50 | Native-speaker verified subset |
| `LICENSE.md` | — | Derivative / rights notice |
| `README.md` | — | This dataset card |

## Language

| Field | Value |
|-------|--------|
| Language | **Gojri** (Gujari) |
| ISO 639-3 | `gju` |
| Source script | Devanagari |
| Target script | Perso-Arabic Nastaliq |

Gojri is an Indo-Aryan language. It shares script and some vocabulary with Urdu,
but it is **not** a dialect of Urdu. Spellings in this lexicon follow **Gojri**
print practice.

## Columns

| Column | Description |
|--------|-------------|
| `entry_id` | Stable id, e.g. `p0019:L14` (source page + line) |
| `page` | Page number in the source PDF |
| `line` | Line number in the page extract |
| `devanagari` | Headword in Devanagari |
| `roman` | Optional Latin form from the dictionary |
| `nastaliq` | Gojri Nastaliq headword (**main field**) |
| `english_gloss` | Short English gloss snippet when present |
| `quality` | Trust tag (see below) |

### Quality tags

| `quality` | Count | Meaning |
|-----------|------:|---------|
| `human_verified` | 50 | Native Gojri speaker approved |
| `pass2_refined` | 299 | Pass 2 changed Pass 1 |
| `pass1_kept` | 1,513 | Pass 1 kept as correct Gojri Nastaliq |

Only **50** rows are human-verified so far. Treat other rows as useful drafts.
Spot-check before training-critical use.

## How it was built

1. Extract clean Unicode text from the Devanagari dictionary PDF (no OCR needed).
2. **Pass 1:** Aksharamukha `Devanagari → Urdu` (local), short vowels removed.
3. **Pass 2:** Gojri orthography refinement:
   - Keep Pass 1 when already correct.
   - Map न and ण to standard `ن` (U+0646). Never use `ݨ` (U+0768).
   - Prefer Gojri endings (e.g. final `و`) when needed.
   - Fix clear Perso-Arabic etymology for Arabic/Persian loans.
4. **Human verify:** 50 seed entries (pages 19, 31, 167) reviewed by a native
   Gojri speaker.

Known verified correction: Devanagari `अंगणू` → Nastaliq `انگنو` (not `انگݨو`).

Pipeline code lives in the [gojri-ai](https://github.com/jaslam94/gojri-ai) repository
(`scripts/dict_translit_*.py`, `prompts/devanagari_to_gojri_nastaliq_v1.txt`).

## Load

```python
from datasets import load_dataset

ds = load_dataset("junaidaslam/gojri-devanagari-nastaliq-lexicon")
print(ds["train"][0])

# Higher-trust subset only
gold = load_dataset(
    "junaidaslam/gojri-devanagari-nastaliq-lexicon",
    name="human_verified",
)
```

Or load the TSV directly:

```python
from datasets import load_dataset

ds = load_dataset(
    "csv",
    data_files="gojri_lexicon_final.tsv",
    delimiter="\t",
)
```

## Intended use

- Devanagari ↔ Nastaliq headword lookup for Gojri
- Seed data for orthography / transliteration tools
- Support checks for OCR and ASR (not a speech dataset)

## Limitations and non-goals

- Not a full bilingual dictionary of every sense and gloss.
- Includes some single-letter alphabet rows from early dictionary pages.
- Most rows are not yet human-verified.
- Does **not** redistribute full page text, examples, or the copyrighted book PDF.
- Separate from the FLI Gojri Literature Corpus (CC-BY-NC-4.0) and from Mozilla
  Common Voice Gujari audio.

## License

See [`LICENSE.md`](LICENSE.md).

Summary:

- The **original dictionary** remains © All rights reserved (Anjum / Sadiq /
  Educational Publishing House / J K Anjuman Taraqi Gojri Adab).
- This release is a **script-conversion derivative of headwords** for language
  preservation and research. It does not grant rights to the original book.
- Users must retain attribution to the original authors and to this dataset.
- For commercial reuse of dictionary content beyond this headword conversion,
  contact the original rights holders.

## Citation

### This dataset

```bibtex
@dataset{gojri_devanagari_nastaliq_lexicon_2026,
  title     = {Gojri Devanagari--Nastaliq Lexicon},
  author    = {Aslam, Junaid},
  year      = {2026},
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon},
  note      = {Script-conversion derivative of headwords from Anjum and Sadiq,
               Concise Gojri--English--Hindi Dictionary; 50 rows human-verified}
}
```

### Original source dictionary (required)

```bibtex
@book{anjum_sadiq_gojri_dictionary,
  title     = {Concise Gojri--English--Hindi Dictionary},
  author    = {Anjum, Rafique and Sadiq, Ruksana},
  publisher = {Educational Publishing House / J K Anjuman Taraqi Gojri Adab},
  address   = {New Delhi},
  isbn      = {978-81-19225-29-3},
  note      = {Compilation by Prof. (Dr.) Rafique Anjum; composition and vetting
               by Ms. Ruksana Sadiq}
}
```

## Contact

Dataset maintainer: [junaidaslam](https://huggingface.co/junaidaslam).
Project repository: [jaslam94/gojri-ai](https://github.com/jaslam94/gojri-ai).
