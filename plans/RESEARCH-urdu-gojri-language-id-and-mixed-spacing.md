# Research: telling Gojri lines from Urdu lines, and spacing each language its own way

Date: 2026-11-23. Scope: language identification (LID) for two very close languages in one script with a tiny labelled set, how digitisation projects tag mixed-language text, Urdu word spacing tools, public Urdu text for the Urdu side, and a recommended pipeline. This note continues `plans/RESEARCH-nastaliq-word-spacing.md` and `plans/RESEARCH-gojri-word-spacing-orthography.md`.

**Outcome (2026-11-24).** A character n-gram tagger on free labels reached 78.4% on cross-validation but 76.1% on the
speaker's tags of 255 prose rows, below "always Gojri" (88.6%). Urdu is about 5% of random rows. See `LOG.md`.

## Summary

- No public LID model has a Gojri label. GlotLID v4 (2,060 labels), GlotLID v3, OpenLID (201 languages), OpenLID-v2 and NLLB LID have no `gju`. fastText lid.176 and CLD3 have none either. Hindko, Pahari and Potwari have no label in GlotLID. [S3, S5, S8, S9, S10, Read or Fetched]
- Because Gojri is missing, any off-the-shelf LID will push Gojri text into a cousin label. GlotLID names this risk ("out-of-model cousin" errors). Its `urd_Arab` label already shows weak precision (0.943) against its 0.998 recall. [S1, S3, Read]
- The best fit for our data is a small model that we train: character n-grams with naive Bayes or logistic regression, plus a short list of Gojri-only markers. On close language groups, simple character n-gram methods are near the top. [S12, S13, S14, S16, S17, Read or Fetched]
- Our own count on the FLI corpus: 15.8 percent of the lines (without file 10) hold ݩ, ݨ or ڵ. Urdu Common Voice sentences hold none of them (0 of 16,321 lines). So these letters are a high precision marker with low recall. Own count, see Q2.
- Closest precedent: PALI (Perso-Arabic LID). A multinomial naive Bayes model on character 2-4-grams beat fastText lid.176 on 7 of 8 noise settings. Urdu, Kashmiri, Punjabi, Sindhi and Saraiki form one confusion cluster. [S16, Read]
- Closest precedent for OCR text: the VarDial 2018 Indo-Aryan task used OCR text that native speakers corrected. Eight teams scored 0.819 to 0.958 macro F1 on five close languages with about 9,000 to 15,000 training lines each. [S12, S13, Read]
- Tagging format exists. ALTO and PAGE XML both allow a language tag on a line, and PAGE also on a word. [S20, S21, Read]
- Urdu spacing: a CRF with MIT code and CC BY 4.0 data (about 111,000 tokens) exists and runs on a CPU. Published word F1 is 0.97 to 0.98 on clean typed Urdu. None of these papers tests OCR output. [S27, S28, S33, Fetched or carried]
- Public Urdu text is plentiful. Permissive: Common Voice Urdu sentences (CC0), FineWeb2 `urd_Arab` (ODC-By), Wikipedia (CC BY-SA), FLORES+ (CC BY-SA), IndicCorp v2 (CC0 per its card). Non-commercial only: UrMonoCorp (CC BY-NC-SA). [Q5]
- Recommendation: option (a) plus the marker list of option (c), with GlotLID only as a side check. Split by book or story when you test. Details in Q6.
- Gaps: no paper on Gojri LID, none on word-level Urdu/Punjabi/Hindi tagging in Perso-Arabic script, none on how OCR projects tag two close languages in one script. See "Gaps".

## How to read the verification tags

- Read: I opened the text or file and read the cited passage.
- Fetched: a fetch tool gave me a summary of the page. I did not see the raw text.
- Snippet: I saw the claim only in a search result summary. Treat it as unverified.
- Not opened: the source did not open. I list it so you can look.
- Own count: a result of a small script that I ran on files in this repo or on a public file. No heavy job, no install.

Every source has a number. The Sources list at the end gives the URL and the tag.

---

## Q1. How do people identify very close and low-resource languages?

### Tools in wide use

| Tool | What it is | Languages | License | Note |
|---|---|---|---|---|
| fastText lid.176 | fastText linear classifier, trained on Wikipedia, Tatoeba, SETimes | 176 | CC BY-SA 3.0 | [S9, Fetched] |
| CLD3 | small neural net on hashed character n-gram embeddings | 107 output codes (my count of the README table) | Apache-2.0 | no mention of short text or close languages in the README [S10, Fetched] |
| langid.py | byte n-gram features, naive Bayes, you can retrain | 97 | BSD-style (LICENSE header) | the GlotLID authors left it out because it covers under 100 languages [S11, S1, Fetched, Read] |
| OpenLID | fastText, trained on 201 languages, FLORES-200 labels | 201 (v1), 189 (v2), 194 plus a "not a language" class (v3) | GPL-3.0 | [S5, S6, S7] |
| NLLB LID (lid218e) | fastText | 217 per the card | CC BY-NC 4.0 | label set follows FLORES-200 [S8, Fetched] |
| GlotLID | fastText, character n-grams 2 to 5 | 2,060 labels in v4 | Apache-2.0 plus notices | [S1, S2, S3] |

Limits I could confirm:

- fastText and CLD3 are closed-set. Every input gets a language, even an unknown one. GlotLID says this directly and added "und" and "zxx" labels to reject noise. [S1, S24, Read]
- GlotLID reports that a wrong label on a close language is the main failure. In its table of "conflated" pairs, 15 pairs are closely related (Arabic varieties, Persian and Dari, Hindi and Awadhi, Bihari and Bhojpuri, and others). [S1, Read]
- On the PALI test set, CLD3, langid.py and Franc each scored at most 0.15 F1 over 19 Perso-Arabic languages. The pre-trained lid.176 model was also beaten by simple naive Bayes and MLP baselines on 7 of 8 noise settings. In PALI's example table, lid.176 labelled Punjabi text as Urdu and Saraiki text as Punjabi. [S16, Read and Fetched]
- GlotLID v4 trains with random 5 to 40 character cuts so that short lines work better. [S3, Read]

### Close-language shared tasks

- **VarDial 2018, Indo-Aryan Language Identification (ILI).** Five languages: Hindi, Braj, Awadhi, Bhojpuri, Magahi. About 15,000 sentences per language, mainly literature. The team collected printed books, scanned them, ran OCR (Google OCR for Hindi) and asked native speakers to correct the output. Eight teams took part. [S12, Read]
  - Macro F1: SUKI 0.958, Tuebingen-Oslo 0.902, XAC 0.898, ILIdentification 0.889, safina 0.863, dkosmajac 0.847, we are indian 0.836, LaMa 0.819. [S12, Read]
  - Methods: SUKI used HeLI, a character n-gram model with word-level back-off (n-grams 1 to 6, lowercased), plus iterative model adaptation on the test text. Tuebingen-Oslo used a linear SVM. XAC's best was a ridge classifier. LaMa used multinomial naive Bayes on word 1-8 and character 1-6 grams and scored lowest. The CNN and RNN teams (safina, we are indian) also scored below the SVM and ridge systems. [S12, Read]
  - Training size: Bhojpuri 14,897, Hindi 15,642, Awadhi 9,307, Magahi 15,306, Braj 15,111 lines. SUKI says HeLI is robust to the smaller Awadhi set. [S13, Read]
  - An earlier paper on an earlier version of this data reached 96.48 percent accuracy and 0.96 macro F1. [S13, Read, citing Kumar et al. 2018]
- **DSL (Discriminating between Similar Languages), 2015.** Best closed-track accuracy 95.54 percent. A plain character 6-gram system was within 0.7 points of the best. Group prediction reached near perfect with about 1,000 examples per language, while language-level accuracy was still rising at 20,000 examples per language. Almost all errors lay inside a group of 2 to 3 close varieties. [S14, Read]
- **Survey (Jauhiainen et al.).** Accuracy rises with more data in most studies. There is no universal "enough". With under 100 KB per language, some languages are near perfect and others are very poor. Longer samples are easier. [S15, Read]
- **ILID (2025, 22 Indian languages plus English, 10,000 sentences per class).** The authors report that ensembles of classical classifiers on TF-IDF word and character features beat fastText and a fine-tuned MuRIL transformer. Shared-script groups (Devanagari, and Arabic: Kashmiri, Urdu, Sindhi) cause most errors. I did not read the score table. [S17, Fetched]
- **IndicLID (2023).** Its abstract says similar languages and small data are the main problems for romanized text. I did not read the paper body. [S18, Fetched]

### What works with a few thousand sentences

- Character n-gram models. Every close-language result above that I could read had character n-grams in the best or near-best system. [S12, S13, S14, S16, S17]
- Word features add little alone, but a word back-off (HeLI) or word 1-grams helps on close pairs. [S12, S13, Read]
- Plain naive Bayes with character n-grams of size 2 to 4 trained from scratch beat large pre-trained LIDs on noisy Perso-Arabic data. [S16, Read]
- Neural nets did not win on these small close-language tasks. In ILI the CNN and RNN teams ranked below the SVM and ridge teams. In code-switch word tagging, a CRF beat neural models by 3 to 5 points on Hindi-English. In ILID, MuRIL lost to classical ensembles. [S12, S19, S17]
- A confusion matrix guides the next step. PALI built small expert classifiers only for the confused cluster (Urdu, Kashmiri, Punjabi, Sindhi, Saraiki) and the hierarchy was statistically better at every realistic noise level. [S16, Read]
- Calibrate with a threshold. GlotLID says a higher threshold lowers false positives and F1 (recall). [S1, Read]
- Test on real, noisy text. Caswell et al. (quoted in S7) found that a model with 98 percent median F1 on benchmark data gave 5 percent median precision on real web crawls. [S7, Read, secondary]

### Word-level tagging for Urdu, Hindi, Punjabi

- I found no paper on word-level language tags for Urdu, Hindi and Punjabi in Perso-Arabic script. [Not found]
- The closest are Hindi-English word-level tagging sets: a CRF beat neural models by 3 to 5 points. [S19, Fetched]
- The survey lists the usual word-level features: neighbour word labels, character n-grams of the word, and a label transition model (HMM or CRF). Language labels of the previous words help. [S15, Read]
- Words that exist in both languages cannot be tagged by shape. Context (the previous word's tag) is the only help. [My reasoning, from S15]

---

## Q2. Does a public LID model already label Gojri?

### Short answer

No. I found no label for Gojri (`gju`), Hindko (`hno`, `hnd`), Pahari or Potwari (`phr`) in any of the lists below. I also found nothing on Hugging Face under "gju Gujari Gojri". [S3, S5, S8, S9, Read or Fetched; HF search 2026-11-23]

### Labels that exist (exact)

| Model | Urdu | Punjabi | Related labels | Gojri, Hindko, Pahari |
|---|---|---|---|---|
| GlotLID v4 | `urd_Arab`, `urd_Latn` | `pan_Guru`, `pan_Latn`, `pnb_Arab` (Western Punjabi) | `skr_Arab`, `skr_Mult` (Saraiki), `kas_Arab`, `kas_Deva`, `kas_Latn`, `doi_Deva`, `doi_Dogr`, `hin_Deva`, `hin_Latn`, `dty_Deva`, `kfy_Deva`, `mtr_Deva`, `mup_Deva`, `snd_Arab` | none [S3, Read, own grep of `languages-v4.md`] |
| GlotLID v3 | `urd_Arab`, `urd_Latn` | `pan_Guru`, `pan_Latn`, `pnb_Arab` | `skr_Arab`, `kas_*`, `doi_Deva`, `hin_*` | none [S3, Read, own grep of `languages-v3.md`] |
| OpenLID (v1 list) | `urd_Arab` | `pan_Guru` only | `kas_Arab`, `kas_Deva`, `awa_Deva`, `bho_Deva`, `hne_Deva`, `mag_Deva`, `mai_Deva`, `hin_Deva`, `snd_Arab` | none; no `pnb`, no `skr` [S5, Read, own grep of `languages.md`] |
| OpenLID-v2 and v3 | `urd_Arab` | `pan_Guru` | the v3 paper shows the same Perso-Arabic coverage as v1 in the list I saw | not listed [S7, Read, partial] |
| NLLB LID (lid218e) | `urd_Arab` | `pan_Guru` | `kas_Arab`, `kas_Deva`, `snd_Arab`, `hin_Deva`, `awa_Deva`, `bho_Deva` | none. I inferred this from the FLORES-200 list. I did not read the binary label file. [S8, Read for FLORES list; label file unverified] |
| fastText lid.176 | `ur` | `pa`, `pnb` | `hi`, `sd`, `ps`, `fa`, `ar`; no `ks` | no Gojri label. I did not read the label file. [S9, Fetched] |
| CLD3 | `ur` | `pa` | `hi`, `sd`; no `ks` | none [S10, Fetched] |
| langid.py | `ur` | `pa` | `hi`; no `ks`, no `sd` | none [S11, Fetched] |

GlotLID v4 held-out scores for the nearest labels (from the model's own test split, so higher than on independent data): [S3, Read]

| Label | F1 | Precision | Recall | False positive rate |
|---|---|---|---|---|
| `urd_Arab` | 0.970 | 0.943 | 0.998 | 3.4e-05 |
| `pnb_Arab` | 0.975 | 0.986 | 0.964 | 7.9e-06 |
| `skr_Arab` | 0.980 | 0.988 | 0.973 | 2.8e-06 |
| `hin_Deva` | 0.886 | 0.801 | 0.992 | 1.4e-04 |

Reading: `urd_Arab` and `hin_Deva` catch almost everything (recall about 0.99) and take in text from other languages (lower precision). The GlotLID paper calls this the "out-of-model cousin" effect. Gojri text will likely go to `urd_Arab` or `pnb_Arab`. This is my inference, not a tested result.

### Gojri data seen elsewhere

- Mozilla Data Collective lists the "Gojri Literature Corpus" (about 60,821 tokens) and Common Voice Gujari (11 hours, 6 speakers). Both are in our project already. [S36, Snippet; project `CLAUDE.md`]
- The Common Voice dataset sheet is said to state that Gojri has two special letters that set it apart from Urdu, Punjabi, Pahari and Mewati. I saw this only in a search summary. [S36, Snippet, unverified]
- PahariLI (Digital India BHASHINI) has 44,014 training and 11,004 test sentences for Dogri, Garhwali, Kumaoni and Nepali. License Apache 2.0 per the portal. It has no Gojri, Hindko or Potwari. It uses Devanagari, so it does not help the Perso-Arabic side. [S37, Fetched]

### Own count: do Gojri-only letters mark Gojri text?

I counted lines in the FLI corpus (files 01 to 09 and 11; file 10 holds Urdu translations, so I left it out) against the Urdu sentence list of Common Voice (`server/data/ur/sentence-collector.txt`). Script: a few lines of Python in the scratchpad, no install.

| Feature | FLI Gojri lines (2,996) | Urdu CV lines (16,321) |
|---|---|---|
| contains ݩ (U+0769, noon with small v) | 13.7 percent | 0.0 percent |
| contains ݨ (U+0768) | 0.0 percent | 0.0 percent |
| contains ڵ (U+06B5) | 10.7 percent | 0.0 percent |
| contains any of the three | 15.8 percent | 0.0 percent |
| contains Arabic marks (harakat) | 52.2 percent | 6.1 percent |

Findings:

- The FLI text writes the small-v noon as ݩ (U+0769). The project notes and scorers name ݨ (U+0768) for print. Both code points must be in any marker list. Also normalise them if you compare text.
- Precision is near 1.0 and recall is about 16 percent. So the letters can confirm Gojri on some lines. They cannot find Gojri on the others.
- The U+FFFF marks in 4 FLI files (see `CLAUDE.md`) may hide more of these letters. The true recall may be higher.
- Harakat are a weak marker, but a strong one for the FLI genre. Check whether the OCR keeps them.
- Word list check (own count). Of the 300 most common FLI word types (no file 10), 118 do not occur in the Urdu CV list at all. Examples: تَے, کَے, تیں, تھو, اُنھاں, یوہ, ناڵ, نال, گیو, نِیہہ, کُجھ, لوکاں, کرݩ, کری, فِر, رہیا, ہووے, جِہڑو. [Own count]
- 41.9 percent of FLI tokens are types that do not occur in the Urdu CV list. 35.7 percent of Urdu CV tokens are types absent from the FLI list. The two lists come from different genres, so this number overstates the true gap. [Own count]

---

## Q3. How do digitisation projects handle books with two close languages in one script?

### What I found

- I found no paper that describes tagging Gojri, Urdu, Punjabi, or Sanskrit and Hindi at line or word level during OCR work. A search for Sanskrit and Hindi in one Devanagari book gave only line-level Sanskrit OCR work and script-identification papers. [Snippet, not found]
- **VarDial ILI dataset (precedent).** The team scanned books, ran OCR, had native speakers correct it, then labelled each text by language. The labels come from the source (the book's language), not from a line-by-line tagger. [S12, Read]
- **IndicLLMSuite / Sangraha.** For PDFs, they ran OCR with Google Vision, then document cleaning, then LID with an ensemble (IndicLID preferred, CLD3 and NLLB used when both agree on another language with high confidence). They report that OCR text needs cleaning stages. [S25, Read]
- **Web corpora.**
  - OSCAR 22.01 keeps a document label and probability (`metadata.identification`) and a list of per-line labels (`metadata.sentence_identifications`), with null for lines where LID failed. [S22, Fetched]
  - MADLAD-400 takes the document label as the majority of the sentence labels. A sentence is "questionable" if its label differs from the document label. Documents with more than 20 percent questionable sentences are dropped. [S23, Read]
  - GlotCC (Ungoliant pipeline) applies LID at document and line level. It marks a document "LID-inconsistent" if 60 percent or more of the lines do not match the document label. It also marks "script-inconsistent". [S24, Read]
  - FineWeb2 stores `language`, `language_script`, `language_score` and `top_langs` for each document, made with GlotLID. Its card warns that GlotLID mixes close languages, and that stopword lists were curated to help. [S26, Read]
- **XML formats for tagging.**
  - ALTO 4.4 allows `LANG` on the page, text block, text line and string (word). `OTHERLANGS` on a page lists the other languages. The schema says to record the language "at the highest level possible". [S21, Read]
  - PAGE-XML (2024-07-15 schema) allows `primaryLanguage` and `secondaryLanguage` on page, region and line, `language` on a word, and a free text `customLanguages` on each. Its fixed list has "Urdu", "Punjabi", "Panjabi", "Persian", "Kashmiri" and "Hindi". It has no Gojri entry. `customLanguages` can hold `gju`. [S20, Read]
  - TEI P5 has `xml:lang` for text segments. I could not open the page to quote it. [Not opened]

### What this means for us

- Per-line tags are common in corpus pipelines (OSCAR, MADLAD, GlotCC). Per-word tags are available in PAGE and ALTO if needed.
- The tag should state who gave it (speaker, model, or rule) and a score. OSCAR, GlotCC and FineWeb2 store the score, and GlotCC and MADLAD use label disagreement as a quality flag. [S22, S23, S24, S26]
- Use the ISO 639-3 code (`gju`, `urd`) in the tag. PAGE's fixed list cannot hold Gojri, so use `customLanguages`. [S20]

---

## Q4. Word spacing in Urdu: methods, numbers, and usable tools

The earlier note holds the full reading. This section keeps what matters for the Urdu side. Sources marked "carried" were read in that note (2026-11-15) and not opened again.

### Methods and numbers

| Method | Task | Data | Result | Source |
|---|---|---|---|---|
| Durrani, max-match plus unigram or bigram ranker | space omission | 70K segmented words for the ranker | 95.8 percent words correct on 2,367 test words | S30, carried |
| Akram and Hussain 2010, ligature and word trigrams | Urdu OCR word cuts | 500K-word ligature corpus, 18M-word corpus | 96.10 percent (abstract); about 96 percent known words, 56 to 63 percent unknown words | S31, carried |
| Lehal 2010, bilingual Urdu-Hindi | space omission, typed text | Hindi side for reliable spaces | 99.15 percent on 1.61M test words | S32, carried |
| Zia, Raza, Athar 2018, CRF per character | word and sub-word (ZWNJ) boundaries | 3,500 train sentences (90K tokens), 825 test | F1 0.97 (word), 0.85 (sub-word) | S28, carried |
| Farhan, Islam, Sharma 2020, CRF with morphological features | same | 19,651 sentences | F1 0.98 (word), 0.92 (sub-word) | S33, Fetched |
| Hassan, WNUT 2026, insert-only with a letter check | InPage text with fused words | 1,000-row silver sample | 96.9 percent precision on accepted edits; 30.5 percent for an ungated function-word splitter | S34, carried |

All numbers are on clean, typed Urdu except Akram and Hussain (built for OCR output) and Hassan (InPage export). None tests Gojri. None scores a modern OCR line reader on Nastaliq print. [Carried]

### Which could be the Urdu side of our pipeline

1. **Zia et al. CRF** (code: `harisbinzia/Urdu-Word-Segmentation`). Code is MIT. Data is CC BY 4.0, about 111,000 tokens. It needs scikit-learn and python-crfsuite and runs on a CPU. The README shows no run steps, and a notebook is in the repo. The training data already comes with the repo, so the Urdu side needs no new Urdu data. [S27, Fetched]
2. **Farhan et al. CRF.** Same family, better numbers, no code or data link on the page. [S33, Fetched]
3. **Character n-gram language model plus a space bonus** (our option (a) in the earlier note). It needs only Urdu text, so the Urdu text in Q5 is enough. [Earlier note, Q3 and test T2]
4. **Hassan-style gate.** Accept an edit only when no letter changes and confidence is high. Its code is not known to me. [S34, carried]
5. **UrduHack** (MIT) lists tokenization and normalization. Its README does not mention space insertion or word segmentation, so it is not a spacing tool. [S38, Fetched]
6. **UTRNet-Large** is our line reader, not a spacing tool. The project notes record CC BY-NC 4.0 in its LICENSE file and CC BY-NC-SA 4.0 in its README. I did not re-check this. [`CLAUDE.md`]

### What text data they need

- The CRF needs text with correct spaces and ZWNJ marks. It ships with its own. [S27]
- A character n-gram model needs any clean Urdu text. A few million characters are enough for orders 3 to 5. Kolak and Resnik found gains from as few as 500 dictionary entries for a related task. [Earlier note, S20 there]
- For the Urdu lines in Gojri books, the spacing habits of the typesetter may differ from news text. Use Urdu text from the same genre where you can (religious, folk story). That is my advice, not a measured result.

### Licenses in one line each

Zia CRF: MIT code, CC BY 4.0 data. UrduHack: MIT. UTRNet: CC BY-NC (see above). KenLM and pyctcdecode licenses: not checked here.

---

## Q5. Public Urdu text for the Urdu class and the Urdu space model

Our project is non-commercial, so CC BY-NC is allowed but must be reported. Prefer permissive sources.

| Corpus | Size | License | Notes | Source |
|---|---|---|---|---|
| Common Voice Urdu sentence list (`server/data/ur/sentence-collector.txt`) | 16,320 lines, 1.15 MB (own count) | CC0 (the Common Voice rule: sentences must be CC0) | short read-aloud sentences, same style as our Common Voice Gojri set. I do not know whether this file is the full Urdu pool. | S39, S40 |
| FineWeb2 `urd_Arab` | 2,733,266,493 words, 4,809,542 documents, 19.93 GB UTF-8 | ODC-By 1.0, plus Common Crawl terms of use | web text. Labels came from GlotLID, so Gojri or Punjabi text may sit inside it. Has `language_score` per document. | S26, Read |
| FineWeb2 `pnb_Arab`, `kas_Arab` | not read | ODC-By | useful as negative classes (config names exist) | S26, Read |
| Wikipedia, Urdu (`20231101.ur`) | 200K rows | CC BY-SA 3.0 and GFDL | encyclopedic, formal register | S41, Fetched |
| FLORES+ `urd_Arab` | 997 dev and 1,012 devtest sentences | CC BY-SA 4.0 | clean, human translated. Small, but good for testing. It has no `pnb`, `skr`, `hno` or `gju`. | S42, Fetched |
| Tatoeba (Urdu sentences) | not counted | CC BY 2.0 FR (some CC0) | short sentences with ISO 639-3 tags | S43, Fetched |
| IndicCorp v2 `urd_Arab` | about 11.4M rows (as shown on the card; the card is not clear) | CC0 for the datasets (per card) | news and web. The card does not name the Urdu sources. | S44, Fetched |
| CC-100 `ur` | 884M (units not stated on the card) | "unknown"; Common Crawl terms apply | paragraph units | S45, Fetched |
| OSCAR 22.01 `ur` | 3.4 GB, 336,994 documents, 332,816,354 words | CC0 for metadata only; text under Common Crawl terms; access was suspended when I read the card | has per-line labels | S22, Fetched |
| UrMonoCorp (LINDAT, Jawaid, Kamran, Bojar 2014) | about 95.4M tokens, 5.46M sentences | CC BY-NC-SA 3.0 | news, religion, blogs, literature. Non-commercial. ShareAlike applies to derived data. | S46, Snippet |
| CLE Urdu Digest corpora (100K, 500K, 1M words) | as named | paid or licensed by CLE; terms not confirmed | not a free source | S47, Snippet |
| Urdu side of the project's own data | file 10 (Urdu translations), Kahawat-Kosh meanings | our own, FLI data is CC-BY-NC-4.0 | same genre as the Gojri text, so a fair negative class | `CLAUDE.md` |

Choice for the classifier: use Common Voice Urdu, FLORES+, Tatoeba and the Urdu parts of our books for training and checks. They are clean and permissive. Add FineWeb2 `urd_Arab` only after filtering with a marker list, because GlotLID may have put Gojri-like text in it. Use UrMonoCorp only if non-commercial terms are fine for the output (they are for this project, but state them).

A domain warning (my reasoning): our Gojri text is mostly religious prose and folk stories. Common Voice Urdu is short everyday sentences. A classifier can learn "religious versus everyday" and not "Gojri versus Urdu". Use Urdu text of the same genres in training and in tests.

---

## Q6. Recommended pipeline for close languages, tiny labelled data and OCR noise

### Four options

| Option | Pros | Cons | Evidence |
|---|---|---|---|
| (a) Character n-gram naive Bayes or logistic regression, trained on our own tagged data | Works with a few thousand lines. Needs only a CPU. Can score unknown words. Easy to read and to debug. Can add noise to training text. | Learns genre unless the Urdu text matches the Gojri genre. Gojri and Urdu share many words, so short lines give weak evidence. | PALI: MNB on char 2-4-grams beat lid.176 on 7 of 8 noise settings [S16]. ILI: character n-gram systems took the top spots with 9K to 15K lines per class [S12, S13]. DSL: char 6-gram within 0.7 points of the best [S14]. ILID: classical TF-IDF char and word models beat fastText and fine-tuned MuRIL [S17]. |
| (b) Existing LID (GlotLID) as a feature or baseline | No training. Supports Urdu, Western Punjabi, Saraiki and Kashmiri labels, so it can warn about "this is neither". | No Gojri label. Close-language errors are known. Gojri goes to a cousin label. Needs the 1.7 GB-class model files (size not checked). Its output is a prior from other data, not from our books. | GlotLID paper "out-of-model cousin" [S1]; `urd_Arab` precision 0.943 [S3]; PALI shows pre-trained LIDs near 0.15 F1 or less on noisy Perso-Arabic text [S16]. |
| (c) Word lists: Gojri word list, Urdu word list, plus a Gojri-only marker list | Simple, explainable. Gives a high precision signal on lines that hold a marker. Our own count shows letters such as ݩ and ڵ never occur in Urdu CV text. | Low recall (about 16 percent of FLI lines hold one of the three letters). Word lists break on OCR errors. The project's own test of a word list for spacing failed (join 0.175, split 0.278 in `LOG.md`, per the earlier note). Gojri text is full of Urdu words. | Own count, Q2. HeLI uses words only with a char back-off [S13]. |
| (d) Small fine-tuned multilingual transformer | Can use context. Strong on large data. | Needs more labelled data than we have. Slow to iterate on CPU. Hard to explain errors. | ILID: MuRIL below classical ensembles [S17]. ILI: CNN and RNN teams below SVM and ridge [S12]. Mave et al.: CRF above neural models [S19]. I found no paper that fine-tunes a transformer on a few thousand lines of two close languages and wins. |

### Recommendation

Use option (a) as the core, add the markers of option (c) as hard features and as a "Gojri confirmed" override, and use GlotLID (b) only as a side check on a sample. Skip (d) for now.

Why:

- It matches what won on close-language tasks with small data (S12, S13, S14, S16, S17).
- The markers cover the only known sure signs of Gojri (ݩ, ڵ, ݨ) with no Urdu counter-example in 16,321 Urdu lines.
- It runs on the PC and keeps each decision traceable. That matters because the speaker must check results.

Concrete design (my proposal built from the sources):

1. Labels: three classes per line, `gju`, `urd`, and `unsure` (mixed, too short, or the speaker cannot tell). Keep `unsure` out of accuracy scores but report its share. PALI removed mixed-script and code-switched sentences from training for the same reason. [S16, Read]
2. Features: character n-grams of size 1 to 5 (HeLI used 1 to 6 with word back-off) over text with spaces kept. Add flags for the marker letters, harakat share, and line length. Test both with and without word 1-grams. [S13]
3. Model: multinomial naive Bayes (like PALI's MNB, like HeLI's scoring) and a logistic regression on the same features. Pick on cross-validation. Both train in seconds on a CPU.
4. Output: a probability. Below a threshold, send the line to the speaker or tag it `unsure`. [S1 on thresholds]
5. Noise: add OCR-like noise to training lines (swap, drop, add characters, random space errors), as PALI did with clean to 100 percent noise. Check on real OCR rows. [S16]
6. Then spacing: Urdu lines use the Urdu CRF or Urdu n-gram model. Gojri lines use the Gojri model. Lines tagged `unsure` get no new spaces. This is the safe default and matches the "change a space only when the evidence is strong" rule in the earlier note.
7. If the first model confuses a third class (for example Punjabi in Shahmukhi, Hindko or Saraiki words), build a small expert model for that pair, as PALI did. [S16]

### How to evaluate with about 183 tagged rows

The set is small. One row is about 0.5 percent. Report intervals, not single numbers.

1. Tag all 183 rows plus more if the speaker can. Add the FLI lines and the Urdu parts of the books as extra labelled text, with their source file as the group id.
2. Split by source, never by row. Use group k-fold where the group is the book, story or dictionary entry. Hold out one genre at a time when you can (leave-one-file-out). This tests genre shift, the main risk.
3. Lock a final test set of about 60 speaker-tagged OCR rows that nobody tunes on. Use it once.
4. Report: confusion matrix, per-class precision, recall and F1, macro F1, and the share of `unsure`. Report precision for `gju` at the threshold you plan to use, because a wrong "Gojri" tag sends an Urdu line to the Gojri spacer (the 35 wrong spaces we already saw).
5. Add a 95 percent bootstrap interval over groups.
6. Compare with two baselines on the same rows: (i) GlotLID `urd_Arab` versus rest, (ii) the marker rule alone. A model that cannot beat the marker rule plus a majority class is not worth shipping.
7. Check the Urdu-spacing effect, not only the tags. The final test is the space score from the earlier note (precision and recall of spaces) on lines routed by the tagger, against the single Gojri model (32 right, 35 wrong on the 55 cards).

### How to avoid leaking text between train and test

- Keep the Gojri story and its Urdu translation in file 10 in the same fold. They share names, numbers and facts. [My reasoning from `CLAUDE.md`]
- Keep a Kahawat-Kosh idiom and its Urdu meaning in the same fold.
- Keep all lines of one dictionary entry, and the same headword in different print editions, in one fold. The project already keeps the 200 reviewed dictionary lines out of training. [`CLAUDE.md`]
- Remove exact and near duplicate lines (the FLI files hold repeated text; three primer pairs in `pdfs/` are two editions of one book). Check by hashing normalised text, then by n-gram overlap.
- Do not train on OCR text that the same model tagged, without a speaker check. This is the self-training bias that the earlier note flags.
- Fit any word list, marker list or n-gram vocabulary inside each training fold, not on all data. A marker found in the test lines then used as a rule is a leak.
- Do not tune the threshold on the locked set.

---

## Open questions and gaps

1. No source covers Gojri LID. All numbers here are from other languages. The Gojri-versus-Urdu confusion rate is unknown until we measure it.
2. I did not read the lid.176 and lid218e label files, only their pages and the FLORES-200 list. A direct read of the files can confirm "no gju" and the `pnb` and `skr` labels.
3. I could not read the TEI Guidelines page, the full ILID score table, the full IndicLID paper, the HeLI n-gram sweep table, or the UrMonoCorp and CLE licence pages (Snippet only).
4. The Common Voice Urdu sentence file may be only part of the Common Voice Urdu set. Its CC0 status comes from the Common Voice playbook rule, not from the file.
5. The FLI files hold U+FFFF marks in four files, which may hide marker letters. The recall figure of 15.8 percent is a lower bound.
6. I found no paper that ranks a small transformer against character n-grams on two very close languages with under 10,000 lines. ILID is the nearest and I read only a summary.
7. Word-level tagging of Urdu and Gojri inside one line has no published method. The survey's HMM and CRF features are the only template. [S15]
8. Whether Zia's Urdu CRF keeps Gojri words together is untested. The earlier note warned that Urdu-trained tools can split Gojri words.

---

## What Gojri can reuse

Ranked. Each step runs on a CPU PC and installs nothing beyond what the project uses today (scikit-learn is the one library to check).

1. **Tag the 183 prose rows** as `gju`, `urd` or `unsure`, with the source book and page as the group id. This is the one input that no source can supply. Add more rows from Kahawat-Kosh (idiom is Gojri, meaning is mostly Urdu) to reach a few hundred per class.
2. **Build the marker baseline** (about 1 hour): a rule that says `gju` when a line holds ݩ, ݨ or ڵ. Score it on the 183 rows. It sets the floor. Our own count says precision is near 1.0 and recall about 16 percent on FLI text.
3. **Train the character n-gram model** (naive Bayes and logistic regression) on FLI lines (Gojri), file 10 Urdu parts and Kahawat-Kosh meanings (Urdu), plus Common Voice Urdu and FLORES+ Urdu. Use group k-fold by file. Add noise copies of the training lines.
4. **Run GlotLID v4 on the same rows as a side check** (the model file is outside the repo, Apache 2.0 plus notices). Count how many Gojri rows go to `urd_Arab`, `pnb_Arab`, `skr_Arab` or `kas_Arab`. This measures the cousin effect in our own data.
5. **Route the spacers by tag.** Gojri lines to the Gojri n-gram spacer. Urdu lines to an Urdu spacer built from the Zia CRF (MIT code, CC BY 4.0 data) or an Urdu n-gram model trained on Common Voice Urdu and FineWeb2 text. `unsure` lines get no new spaces. Score with the space precision and recall of the earlier note on the 55 checked cards.
6. **Store the tag in the OCR output** as `primaryLanguage` or `customLanguages` (PAGE) or `LANG` (ALTO), with the model name and score. Keep the Gojri code `gju` and the Urdu code `urd`.
7. **Only if step 3 stalls on genre shift:** build a small expert model for the confused pair, as PALI did for its Urdu, Kashmiri, Punjabi, Sindhi, Saraiki cluster. A word-level tagger (CRF with previous-tag features) is the next step after that, and only if the speaker marks word-level tags on a sample.
8. **Do not start with a transformer.** No source shows a gain from one at this data size.
9. **Later, and optional:** ask FLI or the Common Voice team whether a Gojri entry can be added to GlotLID or to the Common Voice dataset sheet. Publishing the tagged rows (with the credits already used for derived text) would also give the first public Gojri versus Urdu LID set. This follows the project rule that only derived text, with a source credit, is shared.

---

## Sources

Tags: Read, Fetched, Snippet, Not opened, Own count (see the key at the top).

| Id | Source | URL | Tag |
|---|---|---|---|
| S1 | Kargaran et al., "GlotLID: Language Identification for Low-Resource Languages", arXiv 2310.16248 (v3, 2024) | https://arxiv.org/abs/2310.16248 (PDF: https://arxiv.org/pdf/2310.16248) | Read (intro, requirements, results, conflated pairs) |
| S2 | GlotLID model card | https://huggingface.co/cis-lmu/glotlid | Fetched |
| S3 | GlotLID language lists v4 and v3 (own grep for gju, hno, hnd, phr, pnb, skr, urd, pan, kas, doi) | https://raw.githubusercontent.com/cisnlp/GlotLID/main/languages-v4.md and https://raw.githubusercontent.com/cisnlp/GlotLID/main/languages-v3.md | Read, Own count |
| S4 | GlotLID corpus card (`cis-lmu/glotlid-corpus`), license "multiple", metadata CC0 | https://huggingface.co/datasets/cis-lmu/glotlid-corpus | Fetched |
| S5 | OpenLID repository: README and `languages.md` | https://github.com/laurieburchell/open-lid-dataset (raw: https://raw.githubusercontent.com/laurieburchell/open-lid-dataset/main/languages.md) | Read, Own count |
| S6 | OpenLID model card (`laurievb/OpenLID`, GPL-3.0, 201 languages) and OpenLID-v2 card (189 per card) | https://huggingface.co/laurievb/OpenLID and https://huggingface.co/laurievb/OpenLID-v2 | Fetched (v1), Snippet (v2) |
| S7 | Fedorova et al., "OpenLID-v3: Improving the Precision of Closely Related Language Identification", arXiv 2602.13139 | https://arxiv.org/abs/2602.13139 (HTML: https://arxiv.org/html/2602.13139v2) | Read (parts) |
| S8 | NLLB LID card (`facebook/fasttext-language-identification`, CC BY-NC 4.0, 217 languages); FLORES-200 language list | https://huggingface.co/facebook/fasttext-language-identification and https://github.com/facebookresearch/flores/blob/main/flores200/README.md | Fetched (card), Read (list) |
| S9 | fastText language identification page (lid.176: 176 languages, Wikipedia, Tatoeba, SETimes, CC BY-SA 3.0) | https://fasttext.cc/docs/en/language-identification.html | Fetched |
| S10 | CLD3 README | https://github.com/google/cld3 | Fetched |
| S11 | langid.py README and LICENSE | https://github.com/saffsd/langid.py | Fetched, Read (LICENSE header) |
| S12 | Zampieri et al., "Language Identification and Morphosyntactic Tagging: The Second VarDial Evaluation Campaign" (ILI section, Table 9) | https://aclanthology.org/W18-3901.pdf | Read |
| S13 | Jauhiainen, Jauhiainen, Linden, "Iterative Language Model Adaptation for Indo-Aryan Language Identification" (HeLI), VarDial 2018 | https://aclanthology.org/W18-3907.pdf | Read |
| S14 | Goutte, Leger, Malmasi, Zampieri, "Discriminating Similar Languages: Evaluations and Explorations", LREC 2016, arXiv 1610.00031 | https://arxiv.org/abs/1610.00031 | Read (results, learning curves) |
| S15 | Jauhiainen, Lui, Zampieri, Baldwin, Linden, "Automatic Language Identification in Texts: A Survey", arXiv 1804.08186 | https://arxiv.org/abs/1804.08186 | Read (parts) |
| S16 | Ahmadi, Agarwal, Anastasopoulos, "PALI: A Language Identification Benchmark for Perso-Arabic Scripts", VarDial 2023, arXiv 2304.01322; code and data (MIT code, data license not stated) | https://arxiv.org/abs/2304.01322 and https://github.com/sinaahmadi/PersoArabicLID | Read (parts), Fetched (repo) |
| S17 | "ILID: Native Script Language Identification for Indian Languages", arXiv 2507.11832 | https://arxiv.org/abs/2507.11832 | Fetched (summary; table not read) |
| S18 | Madhani et al., "Bhasha-Abhijnaanam / IndicLID", arXiv 2305.15814 | https://arxiv.org/abs/2305.15814 | Fetched (abstract) |
| S19 | Mave, Maharjan, Solorio, "Language Identification and Analysis of Code-Switched Social Media Text", CALCS 2018 | https://aclanthology.org/W18-3206/ | Fetched |
| S20 | PAGE-XML schema (2024-07-15) | https://raw.githubusercontent.com/PRImA-Research-Lab/PAGE-XML/master/pagecontent/schema/pagecontent.xsd | Read |
| S21 | ALTO 4.4 schema | https://raw.githubusercontent.com/altoxml/schema/master/v4/alto-4-4.xsd | Read |
| S22 | OSCAR 22.01 dataset card | https://huggingface.co/datasets/oscar-corpus/OSCAR-2201 | Fetched |
| S23 | Kudugunta et al., "MADLAD-400", arXiv 2309.04662 (ODC-BY data) | https://arxiv.org/abs/2309.04662 | Read (parts) |
| S24 | "GlotCC: An Open Broad-Coverage CommonCrawl Corpus and Pipeline for Minority Language Modeling", arXiv 2410.23825 | https://arxiv.org/abs/2410.23825 | Read (parts) |
| S25 | Khan et al., "IndicLLMSuite", arXiv 2403.06350 | https://arxiv.org/abs/2403.06350 | Read (parts) |
| S26 | FineWeb2 dataset card (ODC-By 1.0, GlotLID labels, `urd_Arab`, `pnb_Arab`, `kas_Arab`) | https://huggingface.co/datasets/HuggingFaceFW/fineweb-2 | Read (raw README) |
| S27 | Zia et al. Urdu word segmentation repository (MIT code, CC BY 4.0 data, about 111,000 tokens) | https://github.com/harisbinzia/Urdu-Word-Segmentation | Fetched |
| S28 | Zia, Raza, Athar, "Urdu Word Segmentation using Conditional Random Fields (CRFs)", COLING 2018, arXiv 1806.05432 | https://arxiv.org/pdf/1806.05432 | Carried (read in the earlier note) |
| S30 | Durrani, "A word segmentation system for handling space omission problem in Urdu script" | https://alt.qcri.org/~ndurrani/pubs/SpaceOmission.pdf | Carried |
| S31 | Akram and Hussain, "Word Segmentation for Urdu OCR System", 2010 | https://aclanthology.org/W10-3212.pdf | Carried |
| S32 | Lehal, "A Word Segmentation System for Handling Space Omission Problem in Urdu Script", 2010 | https://aclanthology.org/W10-3606.pdf | Carried |
| S33 | Farhan, Islam, Sharma, "Enhanced Urdu Word Segmentation using CRFs and Morphological Context Features", WiNLP 2020 | https://aclanthology.org/2020.winlp-1.41 | Fetched |
| S34 | Hassan, "A Precision-First Whitespace Restoration Pipeline for Noisy Urdu Tafseer Text", WNUT 2026 | https://aclanthology.org/2026.wnut-1.1.pdf | Carried |
| S36 | Mozilla Data Collective: Gojri Literature Corpus; Common Voice Scripted Speech 23.0 Gujari | https://datacollective.mozillafoundation.org/datasets/cmlgz1vdt001omg07rv25gwnu and https://datacollective.mozillafoundation.org/datasets/cmflnuzw5wyic798bz9dzcqt3 | Snippet |
| S37 | PahariLI (Digital India BHASHINI), AIKosh page | https://aikosh.indiaai.gov.in/home/datasets/details/paharili_pahari_language_identification_corpus.html | Fetched |
| S38 | UrduHack repository (MIT) | https://github.com/urduhack/urduhack | Fetched |
| S39 | Common Voice Urdu sentence list | https://github.com/common-voice/common-voice/blob/main/server/data/ur/sentence-collector.txt (raw: https://raw.githubusercontent.com/common-voice/common-voice/main/server/data/ur/sentence-collector.txt) | Own count |
| S40 | Common Voice community playbook, text and CC0 rule | https://common-voice.github.io/community-playbook/sub_pages/text.html | Fetched |
| S41 | Wikimedia Wikipedia dataset card (`20231101.ur`) | https://huggingface.co/datasets/wikimedia/wikipedia | Fetched |
| S42 | FLORES+ dataset card | https://huggingface.co/datasets/openlanguagedata/flores_plus | Fetched |
| S43 | Tatoeba downloads page | https://tatoeba.org/en/downloads | Fetched |
| S44 | IndicCorp v2 dataset card | https://huggingface.co/datasets/ai4bharat/IndicCorpV2 | Fetched |
| S45 | CC-100 dataset card | https://huggingface.co/datasets/statmt/cc100 | Fetched |
| S46 | UrMonoCorp (LINDAT, Jawaid, Kamran, Bojar) | https://lindat.mff.cuni.cz/repository/xmlui/handle/11858/00-097C-0000-0023-65A9-5 and https://ufal.mff.cuni.cz/node/998 | Snippet (the LINDAT page itself did not open) |
| S47 | CLE Urdu Digest corpus store pages | https://www.cle.org.pk/clestore/urdudigestcorpus1M.htm | Snippet |
| S48 | Own counts: FLI corpus (`datasets/Gojri Language Corpus/`, files 01 to 09 and 11 for the marker counts) against `server/data/ur/sentence-collector.txt` | local files, scratchpad scripts `cnt.py`, `wl.py`, `m2.py` | Own count |

Things I did not find after searching: any LID model with a Gojri, Hindko, Pahari or Potwari label; any paper on Gojri LID; any paper on word-level language tags for Urdu, Hindi and Punjabi in Perso-Arabic script; any OCR project note that tags per line for two close languages in one script; any paper that scores a space inserter on OCR text for Nastaliq.
