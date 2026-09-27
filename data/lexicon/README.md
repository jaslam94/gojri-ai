---
pretty_name: Gojri Devanagari–Nastaliq Lexicon
language:
  - gju
  - ur
  - hi
license: other
task_categories:
  - translation
  - text2text-generation
tags:
  - gojri
  - gujari
  - nastaliq
  - devanagari
  - dictionary
  - low-resource
  - indo-aryan
size_categories:
  - 1K<n<10K
---

# Gojri Devanagari–Nastaliq Lexicon

Script conversion lexicon for **Gojri** (ISO 639-3: `gju`).

Each row maps a dictionary **Devanagari headword** to a **Gojri Nastaliq** form.
Optional Roman and short English gloss fields come from the source dictionary line.

## Files in this folder

| File | Rows | Use |
|------|-----:|-----|
| `gojri_lexicon_final.tsv` | 1,862 | Full public lexicon (upload this) |
| `gojri_lexicon_human_verified.tsv` | 50 | Higher-trust subset only |
| `README.md` | — | This dataset card |
| `PUBLISH.md` | — | Hugging Face upload steps |

## Language

| Field | Value |
|-------|--------|
| Language | Gojri / Gujari |
| ISO 639-3 | `gju` |
| Scripts | Devanagari (source), Perso-Arabic Nastaliq (target) |

Gojri shares script and much vocabulary with Urdu, but it is its own language.
Spellings follow **Gojri** print practice where it differs from Urdu.

## Columns

| Column | Description |
|--------|-------------|
| `entry_id` | Stable id, e.g. `p0019:L14` (page + line) |
| `page` | Source PDF page number |
| `line` | Line number in the page extract |
| `devanagari` | Headword in Devanagari |
| `roman` | Optional Latin form from the dictionary |
| `nastaliq` | Gojri Nastaliq headword (main field) |
| `english_gloss` | Short English gloss snippet when present |
| `quality` | See table below |

### Quality tags

| `quality` | Count | Meaning |
|-----------|------:|---------|
| `human_verified` | 50 | Native Gojri speaker approved |
| `pass2_refined` | 299 | Pass 2 changed Pass 1 |
| `pass1_kept` | 1,513 | Pass 1 kept as correct Gojri Nastaliq |

Only **50** rows are human-verified. Treat other rows as useful drafts.
Spot-check before training-critical use.

## How it was built

1. Extract clean Unicode text from `Gojri-Hindi-English-Dictionary.pdf`
   (Devanagari; no OCR needed for this PDF).
2. **Pass 1:** Aksharamukha `Devanagari → Urdu` (local), short vowels removed
   (`scripts/dict_translit_pass1.py`).
3. **Pass 2:** Gojri orthography refinement using project rules in
   `prompts/devanagari_to_gojri_nastaliq_v1.txt`:
   - Keep Pass 1 when already correct.
   - Map न and ण to standard `ن` (U+0646). Never use `ݨ` (U+0768).
   - Prefer Gojri endings (e.g. final `و`) when needed.
   - Fix clear Perso-Arabic etymology for Arabic/Persian loans.
4. **Human verify:** 50 seed entries (pages 19, 31, 167) reviewed by a native
   Gojri speaker.

Known verified correction: Devanagari `अंगणू` → Nastaliq `انگنو` (not `انگݨو`).

## Load example

```python
from datasets import load_dataset

ds = load_dataset(
    "csv",
    data_files="gojri_lexicon_final.tsv",
    delimiter="\t",
)
print(ds["train"][0])
```

After you publish on Hugging Face, replace with:

```python
ds = load_dataset("YOUR_HF_USERNAME/gojri-devanagari-nastaliq-lexicon")
```

## Intended use

- Lexicon / dictionary lookup Devanagari ↔ Nastaliq for Gojri
- Seed data for orthography tools and translation experiments
- Support checks for OCR and ASR (not a speech dataset)

## Limitations

- Not a full bilingual dictionary of every sense and gloss.
- Includes some single-letter alphabet rows from early dictionary pages.
- Most rows are not yet human-verified.
- Original dictionary copyright still applies to the source book. This release is
  a **script-conversion derivative** of headwords. Check rights before commercial use.
- Separate from the FLI Gojri Literature Corpus (CC-BY-NC-4.0) and from Mozilla
  Common Voice Gujari audio.

## Source

Derived from headwords in the Devanagari **Gojri–Hindi–English Dictionary** in the
gojri-ai PDF collection (`Gojri-Hindi-English-Dictionary.pdf`, 458 pages).

Pipeline scripts (tracked in this repo): `scripts/dict_translit_*.py`,
`prompts/devanagari_to_gojri_nastaliq_v1.txt`.

## Citation

```bibtex
@misc{gojri_devanagari_nastaliq_lexicon,
  title        = {Gojri Devanagari--Nastaliq Lexicon},
  author       = {{Gojri AI Project}},
  year         = {2026},
  howpublished = {Hugging Face Datasets / project repository},
  note         = {Derived headword script conversion; 50 rows human-verified}
}
```

## License

Set the Hugging Face license field when you create the repo.

Suggested default if your rights review allows it:

- **CC-BY-4.0** (attribution required), with a note that the source dictionary
  remains under its own copyright.

Do not mark as public domain unless you confirm that is allowed.
