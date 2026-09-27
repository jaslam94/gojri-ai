# Publish this lexicon on Hugging Face

## Upload these files

| File | Required |
|------|----------|
| `gojri_lexicon_final.tsv` | Yes |
| `README.md` | Yes (dataset card) |
| `gojri_lexicon_human_verified.tsv` | Optional (gold subset) |

## Do not upload from this project

| Path | Why |
|------|-----|
| `pdfs/` | Copyrighted books |
| `data/extracted/**` page dumps | Full book text |
| FLI corpus under `data/extracted/fli-corpus/` | Separate CC-BY-NC-4.0 corpus |
| Common Voice `clips/` | Already public; do not re-host |
| `data/gold/` OCR images | Research eval set, different product |
| Internal Pass 1/2 work TSVs under `data/extracted/.../translit/` | Pipeline scratch |

## Steps

1. Create a Hugging Face account.
2. Choose a license (suggested: **CC-BY-4.0** if rights allow).
3. Replace `YOUR_HF_USERNAME` in `README.md`.
4. Install and log in:

```bash
pip install huggingface_hub
huggingface-cli login
```

5. From this folder (`data/lexicon/`):

```bash
huggingface-cli upload YOUR_USERNAME/gojri-devanagari-nastaliq-lexicon . --repo-type=dataset
```

Or create the dataset on the website and upload the TSV + README by hand.

6. Optional: mirror the same files on Zenodo for a DOI.
