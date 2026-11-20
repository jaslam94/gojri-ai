# Research: Shahmukhi and Nastaliq OCR, and what Gojri can reuse

Date: 2026-11-09. Scope: models, datasets and methods for Shahmukhi (Pakistani Punjabi) and for printed Urdu Nastaliq. Goal: find parts that a Gojri Nastaliq OCR project can reuse on top of UTRNet-Large.

## Short answer

- No public Shahmukhi OCR system exists in anything I found. A 2020s survey says the same. Punjabi University (Patiala) works on Gurmukhi OCR, not Shahmukhi OCR. Shahmukhi uses the same Nastaliq style as Urdu, so Urdu tools are the real source.
- For printed Urdu Nastaliq, the open tools are UTRNet, Kraken (Urdu base model), Tesseract (weak), TrOCR variants, and large vision-language models. In the LREC 2026 newspaper test, Gemini 2.5 Pro is far ahead of every open OCR engine.
- UTRNet does not travel well. On the UNB newspaper set it scores WER 0.602 and CER 0.306. Kraken scores WER 0.558 and CER 0.221 on the same set. Your 2 to 3 percent letter error on dictionary pages is therefore a domain effect, not a general result.
- For the space and diacritic gaps, no ready Urdu or Shahmukhi post-corrector exists as a download. The reusable parts are methods: a CRF space model (code and data are open), a small seq2seq corrector trained on synthetic noise, and CTC beam search with a KenLM word model.
- Synthetic data is cheap and well documented. Real lines are still needed. UTRNet's own paper shows synthetic-only training loses 13 accuracy points on real lines.

How to read the "Verified" column. Y means I read the page, README, model card, abstract or table myself during this session. Y(abs) means I read only the abstract page. N means I saw it only in a search summary or a secondary page.

Metric warning. Word error rate (WER) and character error rate (CER) are always labelled. UTRNet's own paper reports "character-wise accuracy" (higher is better), which is not an error rate.

---

## 1. Shahmukhi and Punjabi OCR

| Name | What it is | Script / type | Licence | Reported accuracy (metric, test set) | Link | Verified |
|---|---|---|---|---|---|---|
| Rafique and Javid, "An Insight for Cursive Context-Specific Printed Script Recognition" | Survey preprint on Shahmukhi and Perso-Arabic recognition. States that work on Shahmukhi script recognition is rare. Lists benchmark datasets and CNN/RNN options. | Shahmukhi, survey | engrXiv preprint, licence not checked | None (survey) | https://engrxiv.org/preprint/download/2075/4142 | Y (read 21 pages) |
| Punjabi University Gurmukhi OCR project (ACTDPL) | Consortium project for Gurmukhi OCR. Page says an earlier offline OCR reached about 97 percent on clean text. | Gurmukhi, not Shahmukhi | Not stated | "about 97%" (metric and test set not given) | https://www.learnpunjabi.org/ocr/project.html | Y (page only) |
| Gurmukhi to Shahmukhi and Shahmukhi to Gurmukhi transliteration (Lehal, Saini and others) | Rule and dictionary systems. They start from typed text, not images. | Text | Not stated | Not compared here | https://learnpunjabi.org/pdf/GurmukhiToShahmukhiTransliteration.pdf | N (search result only) |
| SLPG Punjabi Transliteration Corpus and two fairseq models | HF card claims 6.3 million Gurmukhi-Shahmukhi sentence pairs. Card says "The dataset is currently empty". | Text | None stated | BLEU 98.1 (Gur to Shah) and 87.7 (Shah to Gur), test set FLORES-101. Card also prints "CER 99.1%" with no explanation. | https://huggingface.co/datasets/SLPG/Punjabi_Transliteration_Corpus | Y (card) but claims not reproducible |
| PSMT-eval (WAT 2026) | English to Shahmukhi MT test set. Not OCR. | Text | Not checked | Not relevant | https://aclanthology.org/2026.wat-1.1.pdf | N |
| HF Hub search "shahmukhi" | 12 models and 1 dataset. All are MT, ASR (Whisper) or QA. No OCR model. | Mixed | Mixed | None | https://huggingface.co/models?search=shahmukhi | Y (search via HF tool) |

What engines do Shahmukhi people use? I found no paper that runs an OCR engine on Shahmukhi page images. The survey above lists only Urdu and Arabic recognisers as nearest work. Practical reading: Shahmukhi text work starts after the text exists.

---

## 2. Urdu Nastaliq OCR models and benchmarks

### 2a. Models and engines

| Name | What it is | Script / type | Licence | Reported accuracy (metric, test set) | Link | Verified |
|---|---|---|---|---|---|---|
| UTRNet (ICDAR 2023, arXiv 2306.15782) | HRNet + BiLSTM + CTC line reader. Large and Small weights. | Printed Urdu lines | CC BY-NC-SA 4.0 (README) | Character-wise accuracy, UTRNet-Large: 92.97 (UTRSet-Real), 88.01 (IIITH), 95.97 (UPTI). Small: 90.87, 86.35, 95.08. | https://github.com/abdur75648/UTRNet-High-Resolution-Urdu-Text-Recognition | Y (README + paper HTML tables) |
| UTRNet on other data (third party) | Same model run by Arif and Farid | Newspapers | as above | On UNB high-res: WER 0.602, CER 0.306. On OpenITI-Naskh: WER 0.989, CER 0.741. On OpenITI-Nastaliq: WER 0.862, CER 0.638. | https://arxiv.org/html/2505.13943v3 | Y (table read) |
| Kraken "Printed Urdu Base Model" (OpenITI) | Kraken recognition model, fine-tuned from the Arabic-script base model on about 11k Urdu lines. Meant as a base for fine-tuning. | Printed Urdu lines | Apache 2.0 | CER 4.13 percent (test set not named on the record) | https://zenodo.org/records/14585602 | Y |
| Kraken in the UNB test | Same engine, third-party test | Newspapers | Apache 2.0 | UNB high-res: WER 0.558, CER 0.221. OpenITI-Nastaliq: WER 0.626, CER 0.305. | https://arxiv.org/html/2505.13943v3 | Y |
| TrOCR in the UNB test | Row "TrOCR" in Table 3 (v3). Fine-tuning details not stated on the page I read. | Newspapers | n/a | UNB high-res: WER 0.422, CER 0.159. OpenITI-Nastaliq: WER 0.451, CER 0.177. Best of the five open OCR engines. | https://arxiv.org/html/2505.13943v3 | Y (table); training of the TrOCR row unverified |
| EasyOCR (Urdu) in the UNB test | Generic engine | Newspapers | Apache 2.0 (not re-checked) | UNB high-res: WER 0.802, CER 0.246 | https://arxiv.org/html/2505.13943v3 | Y (table) |
| Tesseract in the UNB test | Stock Urdu model | Newspapers | Apache 2.0 | UNB high-res: WER 2.401, CER 2.580 (above 1 means more edits than words) | https://arxiv.org/html/2505.13943v3 | Y (table) |
| Tesseract `urd_naw` (tessdata_contrib) | Community fine-tune of `urd` on 12,748 Urdu image-text pairs. README gives only training-set numbers: BCER 27.125 percent, BWER 63.071 percent (training set, Tesseract's own batch metrics). One sample image compared by eye. | Printed Urdu | Apache 2.0 | No held-out result | https://github.com/tesseract-ocr/tessdata_contrib/tree/main/urd_naw | Y (README) |
| Rapit Labs blog on `urd_naw` | Vendor blog about the same model. No numbers. | Printed Urdu | "permissive" | None | https://rapitlabs.com/blog/custom-ocr-hard-scripts-urdu-nastaliq/ | Y (page) |
| PaddleOCR PP-OCRv5 multilingual | Docs list Urdu code "ur" among 106 languages. Arabic mobile recogniser listed at accuracy 81.27 (metric and test set not clear to me). | General | Apache 2.0 (not re-checked) | Not tested on Nastaliq in any paper I found | https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html | N (search summary) |
| Google Cloud Vision, Azure Read, ABBYY | Cloud OCR | General | Commercial | I found no published Urdu Nastaliq test of these. | n/a | N (nothing found) |
| Large vision-language models in the UNB test | Zero-shot readers | Newspapers | Closed | WER and CER, UNB high-res: Gemini-2.5-Pro 0.133 / 0.032; Claude-3.7-Sonnet 0.249 / 0.100; GPT-4.1 0.254 / 0.096; Llama-4-Maverick 0.305 / 0.128. On low-res images Claude-3.7-Sonnet and Llama-4-Scout "Fail"; Gemini 0.177 / 0.046. | https://arxiv.org/html/2505.13943v3 | Y (table) |
| DeepSeek-OCR-2 LoRA for Urdu (kingabzpro) | LoRA adapter trained on only 800 synthetic Nastaliq lines for one epoch. Two example lines: CER 0.6290 to 0.0806 and 1.5385 to 0.3846. | Synthetic Nastaliq | Apache 2.0 | CER on 2 validation lines only. Card warns about real scans. | https://huggingface.co/kingabzpro/deepseek-ocr-2-urdu-ocr-1m-lora | Y (card) |
| Cross-lingual HTR within Arabic script (arXiv 2605.02089, ICDAR 2026 DALL workshop) | CRNN and HTR-VT trained on a union of Arabic, Urdu and Persian handwriting sets, tested with 100, 500 and 1,000 target lines. | Handwriting | Not stated | CER, UNHD (Urdu): 17.20 to 14.45 with joint training. CER, PHTD (Persian): 9.99. | https://arxiv.org/abs/2605.02089 | Y(abs) |

Already-ruled-out items (Qaari, three HF TrOCR Urdu models, Qwen3-VL, Haiku and Sonnet) are not repeated. The many `*-si26` Urdu TrOCR repos on the Hub are student projects with empty cards. I did not test them.

### 2b. Datasets and benchmarks

| Name | What it is | Script / type | Licence | Size | Link | Verified |
|---|---|---|---|---|---|---|
| UTRSet-Real | Real printed Urdu lines, annotated | Printed Nastaliq | CC BY-NC 4.0 per the repo LICENSE file; its README says CC BY-NC-SA 4.0 | over 11,000 lines | https://github.com/abdur75648/UTRNet-High-Resolution-Urdu-Text-Recognition | Y |
| UTRSet-Synth | Synthetic lines made with the Urdu-Synth tool. Paper says over 130 Urdu fonts. | Synthetic | CC BY-NC-SA 4.0 | 20,000 lines | same repo | Y |
| UrduDoc | Page-level line detection benchmark. Not a recognition set. Not downloadable. Needs a free licence agreement. | Scanned pages | Needs request | not stated | same repo | Y (README) |
| UPTI | Older synthetic printed Urdu set, linked from the UTRNet README | Synthetic | Not checked | not stated | same repo | Y (link only) |
| Urdu Newspaper Benchmark (UNB) | Manually annotated newspaper paragraphs | Newspaper Nastaliq | Not stated in the paper | 829 paragraph images, 9,982 sentences | https://github.com/sameearif/urdu-newspaper-benchmark (the LREC page gives https://github.com/paper-seven/UrduOCR) | Y (paper); repo not opened |
| OpenITI arabic_print_data | Training data for Kraken Arabic-script models, grouped by typeface. Source of the Kraken Urdu model (about 11k Urdu lines). | Printed, several typefaces | Not stated on the repo page | not stated | https://github.com/OpenITI/arabic_print_data | Y (README only) |
| PuristanLabs1/urdu-ocr-1M | Synthetic. 499,845 Nastaliq samples (Jameel Noori Nastaleeq, headless Chromium) and 1,000,160 Naskh samples. Four noise variants per line. Text source not documented. | Synthetic lines | MIT (tag) | 1.5 million rows | https://huggingface.co/datasets/PuristanLabs1/urdu-ocr-1M | Y (card) |
| Khurram123 Urdu poetry Nastaleeq OCR | 17,610 couplet images in Jameel Noori Nastaleeq | Synthetic | Apache 2.0 (tag) | 17,610 | https://huggingface.co/datasets/Khurram123/urdu-poetry-nastaleeq-ocr | N (listing only) |
| MMU-OCR-21 Urdu text lines (deepcopy) | Text-line set, 100k to 1M rows. Card is bare. | Urdu lines | None stated | 100k to 1M | https://huggingface.co/datasets/deepcopy/MMU-OCR-21-Urdu-TextLines | Y (listing only) |
| Urdu Nastaliq 1908 eval sample (vettedlance) | Three pages of a 1908 lithographed dictionary, word-by-word human truth. Card says training, fine-tuning and redistribution are not allowed. | Historical print | Evaluation only | 3 pages, 2,378 truth words | https://huggingface.co/datasets/vettedlance/urdu-nastaliq-1908-eval-sample | Y (card) |
| Urdu Katib Handwritten Dataset (arXiv 2606.19139) | Historical Nastalique handwriting lines. CNN-BGRU-CTC best of the CRNN baselines. Size, licence and CER not on the abstract page. | Handwriting | Not stated | not stated | https://arxiv.org/abs/2606.19139 | Y(abs) |
| PsOCR (Pashto, arXiv 2505.10055) | About 1 million synthetic images, 1,000 font families, 10K benchmark subset. Closest "second Nastaliq-family language" precedent. | Pashto synthetic | Paper CC BY 4.0, data licence not stated | 1M images | https://github.com/zirak-ai/PashtoOCR | Y(abs) |
| IDPL-PFOD2 (Farsi) | Printed Farsi OCR set. CRNN accuracy 78.49 percent, ViT 81.32 percent (metric is exact line accuracy as I read the abstract; not checked in the paper). | Printed Farsi, not Nastaliq | Not stated | 2,003,541 images | https://arxiv.org/abs/2312.01177 | Y(abs) |

New evidence on frontier models, flagged for you. The vettedlance card reports strict word accuracy of 89.95 percent for "Claude Opus 5.5" and 91.08 percent for "Claude Fable 5.1" on those three 1908 pages. That is word error of about 10 and 9 percent. This is a different page type and newer models than your Haiku and Sonnet tests. I did not reproduce it.

Other tool notes:
- Kraken model repository is a Zenodo community. Filter with `kraken show --recognition --language urd`. The listing I could read showed only the Printed Urdu Base Model for Urdu (https://kraken.re/6.0.0/advanced/repo.html). I did not find an eScriptorium or HTR-United Nastaliq model. The search found none.
- OCR4all and Calamari: not researched in depth. No Urdu model found. Treat as unknown.
- A digitalorientalist tutorial reports a learning rate of 1e-4 works better than the default when fine-tuning Kraken on Nastaliq. Secondary source: https://digitalorientalist.com/2023/09/26/train-your-own-ocr-htr-models-with-kraken-part-1/ (N, search snippet).

---

## 3. Post-correction: missing spaces, missing diacritics

Finding: I found no 2023 to 2026 paper on Urdu or Shahmukhi OCR post-correction for space insertion. What exists is older Urdu word segmentation work plus general post-OCR methods.

| Name | What it is | Script / type | Licence | Reported accuracy (metric, test set) | Link | Verified |
|---|---|---|---|---|---|---|
| Zia, Raza, Athar, "Urdu Word Segmentation using CRFs" (COLING 2018) | CRF that predicts word boundary (space) and sub-word boundary (ZWNJ) from orthographic, linguistic and morphological features | Urdu text | Code MIT, data CC-BY 4.0 (README) | Word boundary F1 0.97. Sub-word boundary F1 0.85. Manually annotated corpus of about 111,000 tokens. | https://github.com/harisbinzia/Urdu-Word-Segmentation | Y (abs + README) |
| Akram et al., Urdu ligature-to-word segmentation (2010) | Takes recognised ligatures and ranks word splits with min-word, unigram and bigram scores | Urdu OCR | Not stated | 95.8 percent overall accuracy (as summarised; metric unclear) | https://preview.aclanthology.org/moar-dois/W10-3212.pdf | N (search summary) |
| Lehal and Saini, Shahmukhi word segmentation (2011) | Transliteration-based. Uses Gurmukhi lexical resources, a Shahmukhi-Gurmukhi dictionary and n-grams. | Shahmukhi text | Springer, closed | Not found | https://www.springerprofessional.de/a-transliteration-based-word-segmentation-system-for-shahmukhi-s/3603488 | N |
| Lehal, two-stage Urdu space-insertion system | Fixes extra spaces inside words | Urdu text | Closed | 98.57 percent on a 1.84 million word corpus (second-hand) | https://typeset.io/pdf/a-two-stage-word-segmentation-system-for-handling-space-4035lgwsgh.pdf | N |
| CLE Urdu Word Segmentation System | Paid tool. Trained on a 37-million-word corpus. | Urdu typed text | Paid licence | 97.9 percent on typed text (metric not stated) | https://cle.org.pk/clestore/segmentation.htm | N |
| Rijhwani, Anastasopoulos, Neubig, "OCR Post Correction for Endangered Language Texts" (EMNLP 2020) | Character encoder-decoder with attention that corrects first-pass OCR. Built to train on very little data. Can use translations. | Ainu, Griko, Yakkha | Code and sample data each have a licence file (type not read) | 34 percent average reduction in recognition error rate across three languages (metric is error rate; page does not say CER or WER) | https://github.com/shrutirij/ocr-post-correction and https://arxiv.org/abs/2011.05402 | Y |
| Guan and Greene, "Advancing Post-OCR Correction: A Comparative Study of Synthetic Data" (ACL Findings 2024) | ByT5 trained on synthetic OCR errors. New glyph-similarity method for making the errors. | Several languages, names not on abstract page | Paper CC BY-SA 4.0 | CER reduction claimed, no number on the abstract page | https://arxiv.org/abs/2408.02253 | Y(abs) |
| RoundTripOCR (Kashid and Bhattacharyya, ICON 2024) | Makes noisy text by rendering, running OCR and pairing; treats errors as translation | Devanagari languages | Paper CC BY 4.0 | No numbers on abstract page | https://arxiv.org/abs/2412.15248 | Y(abs) |
| pyctcdecode | CTC beam search with KenLM n-gram shallow fusion and hotword boost. Word-level LM only. | Any CTC model | Apache 2.0 | n/a | https://github.com/kensho-technologies/pyctcdecode | Y (README) |
| UrduHack | Urdu text normalisation and tokenisation toolkit. Not a spell checker. | Urdu text | MIT (as summarised) | n/a | https://pypi.org/project/urduhack/ | N |
| SymSpell | Spelling correction from a frequency list. You must build the Gojri list yourself. | Any | MIT (as summarised) | n/a | https://github.com/wolfgarbe/SymSpell | N |
| NastaliqBERT | Character-level Urdu encoder trained on CC-100 Urdu. Card does not mention OCR correction. | Urdu text | MIT | Perplexity 1.67 on CC-100 Urdu (self-reported) | https://huggingface.co/mahwizzzz/NastaliqBERT | Y (card) |

Cautions from the sources:
- An Urdu CRF trained on Urdu will not know Gojri words. Its features (affixes, ZWNJ rules) may still transfer. This is my judgement, not a tested result.
- Small real fine-tuning sets can make post-correction worse than no fine-tuning (found in a search summary of a 2022 paper on OCR noise; not read by me). Always compare against "no correction".
- Dropped diacritics are a known weak point of readers. The vettedlance card counts 130 dropped diacritics for Opus 5.5 and 113 for Fable 5.1 on 3 pages. Diacritic restoration for Urdu has no open tool in my results.

---

## 4. Synthetic data and fine-tuning on a new language

| Name | What it is | Script / type | Licence | Reported result | Link | Verified |
|---|---|---|---|---|---|---|
| Urdu-Synth | Generator behind UTRSet-Synth, built on trdg. Options in the example command suggest skew, blur, noise, distortion, backgrounds. README does not name fonts. | Urdu synthetic lines | README says CC BY-NC-SA 4.0. GitHub sidebar says Apache-2.0. Conflict, see below. | n/a | https://github.com/abdur75648/urdu-synth | Y (README) |
| TextRecognitionDataGenerator (trdg) | General synthetic line tool. Custom .ttf only. README does not mention right-to-left or Arabic shaping. | Latin first | MIT | n/a | https://github.com/Belval/TextRecognitionDataGenerator | Y (README) |
| PuristanLabs urdu-ocr-1M recipe | Headless Chromium keeps Nastaliq ligatures. PIL breaks them, per the card. Four noise types: dusty scan, thin and compressed, heavy ink, snowy field. | Synthetic | MIT | n/a | https://huggingface.co/datasets/PuristanLabs1/urdu-ocr-1M | Y (card) |
| UTRNet training-data study (Table 4) | Trains on UPTI only, UTRSet-Synth only, or a mix of UPTI, UTRSet-Real and UTRSet-Synth | Urdu lines | n/a | Character-wise accuracy, UTRNet (Large) tested on UTRSet-Real: UPTI only 64.73, Synth only 80.26, Mix-All 93.39. | https://arxiv.org/html/2306.15782v2 | Y |
| UTRNet augmentation ablation (Table 2) | Augmentation and temporal dropout | Urdu lines | n/a | UTRNet-Large on UTRSet-Real: none 91.07, augmentation 92.35, plus temporal dropout 92.97 (accuracy). | same | Y |
| Super-resolution before reading (UNB paper) | SwinIR step before LLM readers | Newspapers | n/a | WER drops 24.9 percent (Gemini) to 70.6 percent (Maverick) relative to low-res; applies to LLM readers, not tested on UTRNet | https://arxiv.org/html/2505.13943v3 | Y |
| GPT-4o fine-tune in UNB paper | 500 images for training, 329 for test | Newspapers | closed | WER 0.330 to 0.269 | same | Y |
| Cross-script joint training (2605.02089) | See 2a. Shows joint training helps most when target data is tiny. | Handwriting | n/a | see 2a | https://arxiv.org/abs/2605.02089 | Y(abs) |

How others fine-tune UTRNet. I found no published recipe. The UTRNet README gives one training command (train.py, LMDB data, HRNet + DBiLSTM + CTC, 100 epochs, batch 8) and no fine-tune section. No paper fine-tunes UTRNet on Pashto, Sindhi or Kashmiri in my search results.

---

## 5. Shahmukhi word lists and corpora

| Name | What it is | Script | Licence | Size | Link | Verified |
|---|---|---|---|---|---|---|
| Punjabi Literature Corpus (Tamahi Suneha Magazine, Mozilla Data Collective) | Shahmukhi literary text, TXT | Shahmukhi | CC-BY-NC-4.0, with a "request different license" option | 1,039,430 tokens, 1.83 MB | https://mozilladatacollective.com/datasets/cmhp42gmu00aumk07w7k22tbp | Y |
| Mediamen Punjabi Literature Corpus | Western Punjabi literature | Shahmukhi | CC-BY-NC-4.0 (search summary) | about 1.82 MB | https://datacollective.mozillafoundation.org/datasets/cmhrlxa1100h3mn07l6tpvqwz | N |
| Chishti Sons Punjabi Literature Corpus | Western Punjabi | Shahmukhi | CC-BY-NC-4.0 plus a bar on organisations above one million USD revenue (search summary) | over 1 million tokens | https://datacollective.mozillafoundation.org/datasets/cmi39dqwq08jnmn0739vleijb | N |
| Western Punjabi Wikipedia (pnbwiki dump) | Wikipedia in Shahmukhi. Dump listing confirmed. Wikimedia text is normally CC BY-SA; I did not re-read the licence page. | Shahmukhi | CC BY-SA (not re-checked) | `pages-articles.xml.bz2` 116,583,395 bytes (compressed), dated 2026-11-01 | https://dumps.wikimedia.org/pnbwiki/latest/ | Y (listing); licence N |
| pnbTenTen (Sketch Engine) | Web corpus of Western Punjabi, about 2.8 million words | Shahmukhi | Paid or trial access, not an open download | 2.8 million words | https://www.sketchengine.eu/?p=31251 | N |
| Humayoun and Ranta (2010) Shahmukhi morphology and lexicon | Reported as open source in a paper. I did not check the download. | Shahmukhi | Not checked | not checked | https://preview.aclanthology.org/moar-dois/Y10-1020.pdf | N |
| HF `shoaibtahir72/Punjabi-Shahmukhi-Sentences` | Sentence set, MIT tag, no card read | Shahmukhi | MIT (tag only) | not stated | https://huggingface.co/datasets/shoaibtahir72/Punjabi-Shahmukhi-Sentences | N |
| OSCAR and CC-100 | Large web corpora. I could not confirm a Western Punjabi (`pnb`) portion. | Mixed | OSCAR-2301 tagged CC0 (card tag), gated | not confirmed | https://huggingface.co/datasets/oscar-corpus/OSCAR-2301 | N for pnb |

Why this prior is weak for Gojri. Shahmukhi spelling differs from the print you read. Punjabi and Gojri share many words, but the project's own sources (FLI corpus, dictionary text, lexicon) match the target orthography better. Use Punjabi as a secondary list only, and mark the source on every word.

---

## What Gojri can reuse (ranked by expected gain and cost)

1. Space-insertion post-corrector trained on Gojri text (gain: high, cost: low to medium). The main error class is missing spaces after non-joiners (ا ے و د). A character-tagging model (the CRF design from Zia et al., MIT code and CC-BY data) can learn this. Build training pairs from your own clean Gojri lines: delete spaces after non-joiners at the observed rate, then train the tagger to put them back. Test on the 200 reviewed lines. Pair it with a no-correction baseline. Risk: Gojri has only about 60k words of FLI text plus your dictionary lines, so keep the model small.
2. Synthetic-error ByT5 or small seq2seq corrector (gain: medium to high, cost: medium). Method from Guan and Greene (ACL Findings 2024) and Rijhwani et al. (EMNLP 2020, code open). Make errors with the actual UTRNet confusion pairs seen on your gold pages (space loss, zer loss, ں/ھ, ک/گ, ت/م). Train on your Gojri text with those errors. The Rijhwani code is built for very small data. Always check that it does not change correct letters.
3. Fine-tune UTRNet-Large on real Gojri lines plus synthetic lines (gain: high, cost: medium, needs GPU). UTRNet's own Table 4 shows mixing real and synthetic beats synthetic-only by 13 points (93.39 vs 80.26 accuracy). You have 11,126 clean real-print label rows and 20,932 synthetic rows. Hold the 200 reviewed lines and the 12 gold pages out. Licence: UTRNet weights and code are CC BY-NC-SA 4.0, so any derived Gojri model must stay non-commercial and share-alike. Your earlier CRNN failure was a different model trained from scratch, so it is weak evidence against this step.
4. CTC beam search with a KenLM word model (gain: medium, cost: low, but untested). Use pyctcdecode (Apache 2.0) if you can export UTRNet's CTC logits. Build the word list from the dictionary, the lexicon and the FLI texts. It can bias spaces and fix word forms. Limits: the README shows a word LM only, and only hotword boost beyond that. Test whether it hurts rare words. This is my proposal, not a published result for UTRNet.
5. Kraken Urdu base model as a second reader and a fine-tune candidate (gain: medium, cost: low). Apache 2.0 and CER 4.13 percent on its own record. It beat UTRNet on newspapers (WER 0.558 vs 0.602), so it may handle your degraded pages better. Fine-tune on a few hundred of your lines and score on the same 200 lines. If it wins on spaces, use it for word boundaries and UTRNet for letters.
6. Frontier vision models as a cheap spot-checker (gain: medium, cost: depends on quota). Gemini 2.5 Pro gave WER 0.133 on UNB high-res. The vettedlance card reports about 90 percent strict word accuracy for newer Claude models on a 1908 print. Use them only to flag disagreements between UTRNet and a second reader, not as the text source.
7. Better synthetic pipeline details (gain: small to medium, cost: low). Your Chrome-based rendering already matches the method PuristanLabs describes. Borrow their four noise types. Use Urdu-Synth's degradation flags as a checklist. Skip trdg for Nastaliq, because its README does not mention Arabic shaping.
8. Punjabi Shahmukhi corpora as a secondary word list (gain: low, cost: low). Use only to catch spelling forms that Gojri shares. Licence is CC-BY-NC, so it is fine for research only.
9. Tesseract `urd_naw` and PaddleOCR (gain: low). Their evidence is training-set numbers only or none. Skip unless you need a free baseline.

Cheap experiment order: 1, then 5, then 3, then 2, then 4.

---

## Unverified or conflicting claims

- UNB fine-tune gain. The abstract says "6.13% absolute". Section 4.4 calls the same number "relative". The table values 0.330 to 0.269 give 6.1 points absolute (about 18.5 percent relative). The 0.330 baseline does not appear in Table 4, where GPT-4o scores 0.327.
- UNB table versions. The v2 HTML I read listed four open OCR engines. The v3 HTML (4 Mar 2026) adds TrOCR. I quote v3. The paper's claim that Gemini is a "50% improvement" over TrOCR does not match the numbers (0.133 vs 0.422 is about 68.5 percent lower).
- UNB repository address. arXiv v3 gives github.com/sameearif/urdu-newspaper-benchmark. The ACL Anthology page gives github.com/paper-seven/UrduOCR. I opened neither repo. The dataset licence is not stated in the paper.
- Urdu-Synth licence. README says CC BY-NC-SA 4.0. GitHub's sidebar says Apache-2.0. Read the LICENSE file before reuse.
- UTRNet README gives no accuracy numbers. The numbers above come from the paper HTML. The paper calls the metric "character-wise accuracy"; I did not recompute CER from it.
- UTRNet in the UNB test looks very poor (WER 0.989 on OpenITI-Naskh). I do not know whether those authors used the Large weights, fine-tuned them or cropped lines as UTRNet expects. Treat that as a warning about domain shift, not a final ranking.
- SLPG transliteration corpus. Card claims BLEU 98.1 and 87.7, prints "CER 99.1%", and says the dataset is empty. Do not rely on it.
- Kraken Urdu CER 4.13 percent. The record gives no test split. It is likely the held-out part of the same OpenITI data (my guess).
- Tesseract `urd_naw`. Only training-set batch metrics are given (BCER 27.125 percent, BWER 63.071 percent). The model has no named authors in the README. The Rapit Labs blog gives no numbers.
- PaddleOCR Urdu. Docs list "ur" but I could not confirm which recogniser handles it. Third-party ONNX notes conflict.
- Vettedlance claim. Model names "Claude Opus 5.5" and "Claude Fable 5.1" and the accuracy figures are the card author's. I could not reproduce or audit them. The card forbids training on the data.
- Akram 95.8 percent, Lehal 98.57 percent, CLE 97.9 percent. All from search summaries. Metrics and test sets unconfirmed.
- Small-data warning for fine-tuned post-correctors (2022 paper) and the digitalorientalist learning-rate tip come from search summaries only.
- Western Punjabi Wikipedia licence and any OSCAR or CC-100 `pnb` portion: not confirmed.
- Not covered: OCR4all and Calamari Urdu models, HTR-United Nastaliq sets (none found), eScriptorium Persian Nastaliq models (none found), UPTI and IIITH details, UNHD and NUST-UHWR licences, Google Vision and Azure on Urdu (no published test found).

---

## Sources

- UTRNet repo: https://github.com/abdur75648/UTRNet-High-Resolution-Urdu-Text-Recognition
- UTRNet paper: https://arxiv.org/abs/2306.15782 (tables read at https://arxiv.org/html/2306.15782v2)
- Urdu-Synth: https://github.com/abdur75648/urdu-synth
- From Press to Pixels (UNB): https://arxiv.org/abs/2505.13943 , https://arxiv.org/html/2505.13943v3 , https://aclanthology.org/2026.lrec-1.235/
- Kraken Urdu base model: https://zenodo.org/records/14585602
- Kraken model repository docs: https://kraken.re/6.0.0/advanced/repo.html
- OpenITI arabic_print_data: https://github.com/OpenITI/arabic_print_data
- Tesseract urd_naw: https://github.com/tesseract-ocr/tessdata_contrib/tree/main/urd_naw
- Rapit Labs blog: https://rapitlabs.com/blog/custom-ocr-hard-scripts-urdu-nastaliq/
- PaddleOCR PP-OCRv5 languages: https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html
- Cross-lingual Arabic-script HTR: https://arxiv.org/abs/2605.02089
- Urdu Katib dataset: https://arxiv.org/abs/2606.19139
- PsOCR (Pashto): https://arxiv.org/abs/2505.10055
- IDPL-PFOD2 (Farsi): https://arxiv.org/abs/2312.01177
- GPT-4o OCR on low-resource scripts: https://arxiv.org/abs/2412.16119 (abstract only; no numbers; not used in tables)
- Shahmukhi survey (Rafique and Javid): https://engrxiv.org/preprint/download/2075/4142
- Punjabi University OCR project: https://www.learnpunjabi.org/ocr/project.html
- SLPG transliteration corpus: https://huggingface.co/datasets/SLPG/Punjabi_Transliteration_Corpus
- Urdu word segmentation CRF: https://arxiv.org/abs/1806.05432 , https://github.com/harisbinzia/Urdu-Word-Segmentation
- Akram et al. 2010: https://preview.aclanthology.org/moar-dois/W10-3212.pdf
- Lehal and Saini Shahmukhi segmentation: https://www.springerprofessional.de/a-transliteration-based-word-segmentation-system-for-shahmukhi-s/3603488
- CLE segmentation tool: https://cle.org.pk/clestore/segmentation.htm
- OCR post-correction for endangered languages: https://arxiv.org/abs/2011.05402 , https://github.com/shrutirij/ocr-post-correction
- Advancing Post-OCR Correction: https://arxiv.org/abs/2408.02253
- RoundTripOCR: https://arxiv.org/abs/2412.15248
- pyctcdecode: https://github.com/kensho-technologies/pyctcdecode
- NastaliqBERT: https://huggingface.co/mahwizzzz/NastaliqBERT
- PuristanLabs urdu-ocr-1M: https://huggingface.co/datasets/PuristanLabs1/urdu-ocr-1M
- DeepSeek-OCR-2 Urdu LoRA: https://huggingface.co/kingabzpro/deepseek-ocr-2-urdu-ocr-1m-lora
- vettedlance Urdu 1908 eval: https://huggingface.co/datasets/vettedlance/urdu-nastaliq-1908-eval-sample
- trdg: https://github.com/Belval/TextRecognitionDataGenerator
- Punjabi Literature Corpus: https://mozilladatacollective.com/datasets/cmhp42gmu00aumk07w7k22tbp
- Western Punjabi Wikipedia dumps: https://dumps.wikimedia.org/pnbwiki/latest/
- pnbTenTen: https://www.sketchengine.eu/?p=31251
- Digital Orientalist Kraken tutorial: https://digitalorientalist.com/2023/09/26/train-your-own-ocr-htr-models-with-kraken-part-1/
