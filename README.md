# Gojri AI

Development of OCR, ASR, and language model resources for Gojri (ISO 639-3: `gju`).

The primary objectives are building a Gojri speech recognition model (ASR) and a fine-tuned Gojri language model (LLM).

## Public datasets (Hugging Face)

Datasets hosted on Hugging Face under [junaidaslam](https://huggingface.co/junaidaslam):

| Dataset | Format | Link |
|---------|--------|------|
| Gojri-English dictionary text corpus | CSV, JSONL, TXT | [gojri-english-dictionary](https://huggingface.co/datasets/junaidaslam/gojri-english-dictionary) |
| Devanagari to Nastaliq lexicon | TSV | [gojri-devanagari-nastaliq-lexicon](https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon) |
| Nastaliq OCR gold set | Images, TXT, CSV | [gojri-nastaliq-ocr-gold](https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold) |
| Gojri print PDF collection | PDF, TSV | [gojri-print-pdf-collection](https://huggingface.co/datasets/junaidaslam/gojri-print-pdf-collection) |

Source code, processing scripts, and evaluation tooling remain in this repository.

## Third-party datasets

Local training data stored under `datasets/`:

- Gojri Literature Corpus (FLI via Mozilla Data Collective, CC BY-NC 4.0)
- Common Voice Gujari speech dataset (Mozilla Common Voice 26.0, CC0)

Detailed origins and licensing terms are recorded in `datasets/README.md`.

## Repository structure

- `CLAUDE.md`: Research findings, project status, and pipeline architecture
- `AGENTS.md`: Agent execution instructions and guidelines
- `LOG.md`: Chronological experiment and development log
- `ROADMAP.md`: Project strategy and implementation phases
- `data/manifest.csv`: Catalog of all collected PDFs and classification metadata
- `data/lexicon/`: Devanagari to Nastaliq lexicon files and build scripts
- `data/gold/`: 12-page OCR ground-truth benchmark and evaluation scripts
- `data/utrnet-test/`: UTRNet-Large zero-shot test on 200 dictionary lines (method, results, example crops)
- `scripts/`: Data extraction, scoring, and font decoding scripts

## Current status

- Digitized Gojri-English dictionary (474 pages, 11,767 entries) published on Hugging Face.
- Devanagari to Nastaliq lexicon (1,862 entries) published on Hugging Face.
- OCR gold benchmark (12 pages) published on Hugging Face.
- Pretrained UTRNet-Large reads the Arabic parts of dictionary lines at 2.1% letter error (2.0% to 2.2% over five seeds), with no training (`data/utrnet-test/`). Reading new scanned books still needs a line and script detector.
- Bulk vision OCR paused pending automated verification methods.

## Contributions

Contributions for native-speaker verification, additional OCR ground truth pages, or rights-cleared Gojri texts are welcome via issues or pull requests.

## Contact

- GitHub: [jaslam94/gojri-ai](https://github.com/jaslam94/gojri-ai)
- Hugging Face: [junaidaslam](https://huggingface.co/junaidaslam)
