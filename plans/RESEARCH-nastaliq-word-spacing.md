# Research: word spacing in Nastaliq OCR output, and how to fix it for Gojri

Date: 2026-11-15. Scope: how Perso-Arabic systems find word boundaries, how Urdu and Nastaliq OCR treat spaces, whether a Gojri language model can help, and what InPage does with spaces. Goal: pick a small, testable plan that lowers the word error rate of our UTRNet-Large line reader without changing letters.

## Summary

- Recommendation: do not use a plain word list. Build a Gojri character-level model from clean Gojri text and use it in two cheap ways, in this order. (1) Re-decode the UTRNet output with a character n-gram model and a tunable space bonus. (2) Train a small CRF space tagger on synthetic noise and use it as a second opinion. Change a space only when the image evidence and the text model agree, or when a human confirms.
- First, count where the space errors fall. Urdu sources say that omitted spaces appear after non-joining letters, and inserted spaces appear after joining letters. If our errors follow that pattern, a narrow rule set can fix most of them.
- Every Urdu or Persian paper I read treats spacing as a text problem. Clean-text CRF taggers reach about 0.97 F1 for word boundaries with 90K training tokens. None of these papers works on OCR output or on Gojri. Expect lower numbers for us.
- A model trained on only about 60K Gojri words is enough for a character n-gram or a CRF. It is probably too small for a neural transformer from scratch. I found no paper that gives a hard minimum.
- Do not train the model on our own OCR output without checks. Akram and Hussain (2010) blame unclean spaces in their training corpus for many of their errors.
- PDF glyph geometry (option c) is already tested in this project and does not work for Noori text. I found no primary source that says how InPage draws word gaps. See the InPage section.
- An LLM may insert or delete spaces only if a code check proves that no letter changed. A 2026 paper uses this rule and shows that an ungated splitter has 30.5 percent precision.
- Our 20-line test is too small. One word is about 1 percent. Label at least 200 gold lines before you compare methods.
- Big gaps in my search: no paper on Kashmiri or Shahmukhi space errors with numbers, no paper on OCR space errors for Nastaliq with numbers, and no source on how InPage encodes spaces.

## How to read the verification tags

- Read: I opened the paper or page text myself and read the cited passage.
- Fetched: I read the page through a fetch tool that returns a summary. I did not see the raw text.
- Snippet: I saw the claim only in a search result summary. Treat it as unverified.
- Not opened: I could not open the source. I list it only so you can look.

Every source has a number. The Sources list at the end gives the URL and the tag.

---

## Q1. How do Perso-Arabic systems solve word segmentation and space insertion?

### Why the problem exists (plain words)

- In Urdu print and typing, a space is not only a word divider. Typists use a space to get the right letter shape. [S1, Read] [S3, Read]
- Some Urdu letters do not join to the next letter (the "non-joiners", for example ا د ڈ ذ ر ز و ے). After such a letter the next word looks correct even with no space. So writers often leave out the space. This is "space omission". [S1, Read]
- If a word has two parts and the first part ends in a joining letter, the writer may type a space so that the parts do not join. This puts a space inside one word. This is "space insertion". [S1, Read]
- The correct fix in Unicode is the zero-width non-joiner (ZWNJ). It is an invisible mark that stops two letters from joining without adding a gap. Most writers do not know it and many keyboards lack it. [S1, Read]
- Papers say the same for Shahmukhi Punjabi and Sindhi. [S6, Read] [S11, Read] I found no paper with numbers for Shahmukhi or Kashmiri space errors. [S12, Not opened]
- This is the same trap as in our print. Our books show gaps inside words and no gaps between words. The cause is the script and the typesetting, not the OCR model. Lehal and Rana say that for Nastaliq "there is not much difference between inter-word and intra-word vertical gap", and they show a six-ligature, three-word example that a person cannot split from gaps alone. [S7, Read]

### Statistical and rule methods (Urdu)

- Durrani: take a run of letters without spaces, list all ways to cut it into dictionary words (maximum matching), then rank the cuts. Test corpus: 2,367 words with 404 segmentation errors. Training for the n-gram ranker: 70K manually segmented words. Result: 95.8 percent of words correct with a unigram ranker, 95.7 with a bigram ranker, 93.3 with max-match alone. The ranker found 85.8 percent of all omission and insertion errors (unigram). The test set is small. [S3, Read]
- Akram and Hussain (2010): made for Urdu OCR. The OCR gives ligatures (connected pieces) with no reliable spaces. They score cuts with ligature and word trigrams. Ligature corpus: half a million words, manually cleaned for spaces. Word counts: an 18 million word corpus. The paper reports 96.10 percent word identification on 150 test sentences (2,156 words). Unknown words are the weak point: the table I read shows 56 to 63 percent for unknown words against about 96 percent for known words. They also say that many errors come from unclean spaces in the larger training corpus. [S4, Read]
  - My note: the abstract says 96.10 percent at beam 50, but the beam table I read lists 94.62 percent at beam 50 for the setting shown. I did not resolve this. Quote the paper's own 96.10 figure with care.
- Lehal (2010): finds merged words, then splits them. It uses a bilingual Urdu-Hindi corpus, because the Hindi side has reliable spaces. It reports 99.15 percent correct segmentation on 1.61 million test words. The task is space omission only, and the text is typed text, not OCR. [S5, Read]
- Lehal (2009) handles space insertion with grammar rules plus statistics. I saw it only named in a search result and in other papers. I did not open it.

### CRF sequence tagging (Urdu)

- Zia, Raza and Athar (2018): a CRF (a model that labels each character in a sequence) predicts, for each character, "inside a word", "begin word" or "begin sub-word" (ZWNJ). Input is a string of letters with spaces removed. Data: 4,325 sentences, 3,500 for training (90K tokens), 825 for testing (21K tokens). Result: F1 0.97 for word boundaries and 0.85 for sub-word boundaries, without diacritics. [S1, Read]
- Feature ablation (Table 4 in S1): a window of only the current letter gives 0.59 F1. A window of three letters on each side gives 0.92. Adding "is this letter a joiner" and a Unicode class gives 0.97. So the joiner flag matters, and the whole model is small.
- Metric: precision, recall and F1 per boundary type. The authors say these are more informative than word or character error rates. [S1, Read]
- Code and corpus are public on GitHub, as the paper says. [S1, Read] I did not open the repository.
- Farhan, Islam and Sharma (2020) add morphological context features, use a 19,651 sentence corpus and report F1 0.98 (word) and 0.92 (sub-word). I read only the abstract page. [S2, Fetched]

### Neural tagging

- Sindhi (SGNWS): BiLSTM encoder, self-attention, CRF layer. Characters get tags B, I, E, S, X. Data: 91,753 sentences, 2.38 million tokens. F1 98.51 percent on the combined test set. Metric: word boundary precision, recall, F1. The paper also lists older Sindhi results as "segmentation error rate" (SER 9.54 percent on a 16,601 word lexicon). [S11, Read]
- Persian, PerSpaCor (RANLP 2025): a BERT model labels each character as no space, space or ZWNJ. Data: Bijankhan and Peykare, 12.7 million words. Best macro F1 97.26 percent. In the test tables I read, the space class scores about 0.985 to 0.989 F1 and the ZWNJ class about 0.92 to 0.93. [S8, Read] The authors build labels by removing all spaces and ZWNJ from correct text. This is the "synthetic removal" idea in our option (b).
- Persian joint BERT model (arXiv 2010.00287): 92.40 percent macro F1 on a 500-sentence hard test set. [S9, Fetched]
- ViraPart (arXiv 2110.09086) is a related Persian system. I saw only the search snippet. [S10, Snippet]
- A general character-level BiLSTM that restores spaces, punctuation and case works for Japanese and for Gujarati (low-resource). It uses character-level precision, recall and F1. It reports F 0.90 overall on English. I read the abstract and dataset part. [S26, Read]
- Zia et al. say that deep models "need much training data, which is a barrier for low-resource languages". This is their statement, not a measured test. [S1, Read]

### Pashto

- The Pashto work I found is CRF based, with one model for whitespace correction (character features) and one for word segmentation (token features). I could not open the paper. [S12, Not opened] The NLPashto Python package lists a tokenizer that "corrects space omission and insertion errors" and a segmenter, but its page names no model type. [S13, Fetched]

### Kashmiri

- I found no space-restoration paper for Kashmiri. The Kashmiri text corpora (KS-LIT-3M, KS-PRET-5M) were made from InPage files with a reverse-engineered converter. Their papers say that the conversion adds irregular spaces, and they normalize spaces to single spaces. They give no accuracy for word boundaries. [S15, Read] [S16, Read]

### Persian ZWNJ in one paragraph

- Persian writers must put a ZWNJ inside many words (for example before plural and verb suffixes). People forget it. Two sources treat "space or ZWNJ or nothing" as a three-class label per character. [S8, Read] [S9, Fetched] I do not know whether Gojri print or the FLI text uses ZWNJ. Check the FLI files for U+200C. If they have none, we need only the two-class form (space or no space).

### Insert-only and gated methods

- Hassan (WNUT 2026) studies Urdu text exported from InPage, where adjacent words fuse. The system may only insert spaces. It checks that removing all spaces from the input and the output gives the same string, so no letter changed. It accepts only high-confidence edits. On a 1,000-row silver-labeled sample, accepted edits reach 96.9 percent precision, against 30.5 percent for an ungated function-word splitter and 39.7 percent for a frequency-only baseline. The author says the labels are model-assisted and share evidence with the system, so the numbers are provisional. [S14, Read]
- This is the only paper I found that links InPage output, Urdu space loss and a letter-preservation check. It matches our option (d).

---

## Q2. How do OCR systems treat word boundaries?

- UTRNet (the model we use): a CNN plus BiLSTM that outputs characters with CTC. CTC is a way to train a line reader without marking where each letter sits. The paper reports character-wise accuracy only. It does not give a word error rate and does not discuss spaces. [S17, Read]
- The UTRNet code decodes by taking the best class at each step (greedy). It adds the space as one more ordinary character to the alphabet. No language model and no special space rule appear in the file I saw. [S18, Fetched] So a decoder with a language model or a space bonus is possible, because the model already outputs a space score at each step.
- Third-party test of UTRNet on Urdu newspapers: word error rate 0.602 and character error rate 0.306 on UNB. The same paper lists Kraken, TrOCR, EasyOCR, Tesseract and large vision-language models. For the language models it gives only insertion, deletion and substitution counts, and it says deletions dominate. It gives no count of space errors. [S19, Read]
- Older Urdu OCR research handles spaces as a separate step. Akram and Hussain say that "spacing cues are not available to the OCR for word separation" in typed and scanned text, so segmentation has to be done from ligature statistics. [S4, Read]
- A thesis on Urdu handwriting used a ligature trigram model with Kneser-Ney smoothing together with CTC and said it fixed some errors. I saw this only in a search snippet. [S36, Snippet]
- CTC beam search with a language model:
  - Garst et al. (Google, 2023) add a word-based language model and a modified CTC beam search to OCR and report a "substantial reduction" in word error rate, with no numbers on the page I read. [S21, Fetched] A search snippet said the baseline has a character-level language model. I could not confirm this.
  - pyctcdecode is a Python CTC beam search decoder that uses KenLM n-gram models. Its README does not say it supports character-level models. It treats the space label as the word divider in its example. [S22, Fetched]
  - KenLM builds n-gram models with `lmplz`. The README names Linux, OS X, Cygwin and MinGW and does not mention Windows. It does not mention character-level models or a minimum data size. [S23, Fetched]
- Kolak and Resnik (2005), a character n-gram approach for low-resource OCR. They treat merged and split words as plain insertions and deletions of the space character, handled inside the error model. They use character n-gram language models because these are simple, easy to train and usually good. Findings I read: a Cebuano dictionary test cut word error by 20 to 50 percent relative, and it gained "even using only 500 dictionary entries for training". Higher-order n-grams did worse when the model had to fix merges and splits, because it then needs "more training data". [S20, Read]
- Other engines, only as far as spacing:
  - Calamari and Kraken: the pages I opened say nothing about language models, beam search or spaces. They are line based. [S24, Fetched]
  - PaddleOCR: the docs I saw (old 2.x versions) say a flag called `use_space_char` lets the recognizer output the space class. I saw this only in a search summary. [S25, Snippet]
  - TrOCR and Qaari: I found no source that gives their space errors. Our project already ruled out Qaari and the Hugging Face Urdu TrOCR models, as `CLAUDE.md` records.
  - Vision-language models: only the UNB counts above. No space breakdown.
- Post-OCR correction in general: ByT5 models trained on synthetic noise lower the character error rate in several low-resource languages. The abstract gives no numbers. [S28, Fetched] An action-tagging model (insert, replace, insert-space, delete per character) trained on synthetic OCR noise exists for English. [S27, Read] Both are templates for option (b). Neither tests Nastaliq.

---

## Q3. Will a Gojri language model help? How much data?

### What the sources say about size

| Source | Method | Training text | Result |
|---|---|---|---|
| Durrani [S3] | unigram/bigram ranker over max-match cuts | 70K manually segmented words | 95.8 percent words correct on 2,367 test words |
| Zia et al. [S1] | CRF, 7-letter window plus joiner flags | 90K tokens (3,500 sentences) | F1 0.97 word boundary on 21K test tokens |
| Kolak and Resnik [S20] | character n-gram plus error model | as little as 500 dictionary entries | 20 to 50 percent relative WER cut in the Cebuano test |
| Akram and Hussain [S4] | ligature and word trigrams | 500K words (ligatures), 18M words (words) | about 96 percent known words, about 60 percent unknown words |
| SGNWS [S11] | BiLSTM-CRF | 2.38M tokens | F1 98.51 percent |
| PerSpaCor [S8] | BERT tagger | 12.7M words | macro F1 97.26 percent |

My reading: n-gram and CRF methods work from about 50K to 100K words of clean text. The neural methods in these papers use 2 to 13 million words. I found no paper that tests a small transformer on under 100K words for spacing. So "a small transformer from scratch on 60K words" is untested and I would not start there. A multilingual pretrained BERT fine-tuned for tagging might work. PerSpaCor says its multilingual model "may have" generalized without large task data, but they did not test this. [S8, Read]

### What data we have, and how clean it is

- FLI literature: about 60,814 words of typed Unicode text. Good size for a CRF or a character n-gram. Two cautions. The genres differ (religious biography, Q and A book, folk stories). And typed Urdu-script text carries typists' habits, with spaces used for shaping. [S1 says this for Urdu.] Check the FLI spacing against print on a sample before you trust it. Leave one file out when you test, so that the test genre differs from the training genre.
- Gojri-English dictionary, about 11,700 lines: our own review found that the old labels had errors in 91 percent of lines, mostly spaces around the romanisation group (`CLAUDE.md`). The v3.1 labels fix most of this but the lines are headwords and glosses, not running text. Use only the Arabic-script runs, and only the lines the user has reviewed.
- Gojri-Hindi-English dictionary headwords: Devanagari has reliable spaces. Lehal (2010) used a Hindi side to find Urdu word cuts. [S5, Read] An analogous use for Gojri is possible but unproven. Our Nastaliq column for these words is machine-made (`CLAUDE.md`), so it carries transliteration risk.
- The word list from the dictionary corpus (14,455 forms) holds Urdu words that split Gojri words. A word list is wrong for this job. The failure in `LOG.md` (join 0.175, variant 0.206, split 0.278) matches what Hassan found for frequency-only baselines (39.7 percent precision). [S14, Read]
- OCR output, a few hundred thousand words: useful only after checks. See the risk paragraph below.

### Why a character model fits better than a word model

- Gojri has many words that are not in any list. Akram and Hussain show a drop to about 60 percent on unknown words with a word-based method. [S4, Read]
- Character n-grams can still score an unknown word. Kolak and Resnik chose them for low-resource OCR for this reason (simple, easy to train). [S20, Read]
- A character model also learns letter patterns around word ends. In Urdu, the last letter of a word and the first letter of the next word follow strong patterns, and Zia et al. show that a window of three letters on each side lifts F1 from 0.59 to 0.92. [S1, Read]

### Risk: training on our own OCR errors

- If the language model trains on OCR output, it learns the OCR's wrong spacing. The decoder then keeps the wrong spacing. This loop is called confirmation bias in self-training. I found no paper on Nastaliq that measures it. My advice is my own reasoning.
- Akram and Hussain say unclean spaces in their larger corpus caused many of their remaining errors. [S4, Read]
- Safe use of OCR text: (1) train only on gold text, FLI text and reviewed dictionary lines first; (2) add OCR lines only if two independent readers agree and a person checked a random sample; (3) never use the same lines for training and for scoring; (4) keep the 200 reviewed dictionary lines out of training, as the project already does.
- Also watch the synthetic data in `data/synth/line_full`: it uses the old spaces around romanisation. Do not use its spacing as a label.

---

## Q4 detail: option (c), PDF geometry (project test, not a paper)

- This project tested it on 2026-11-15 (`LOG.md`, section "can the PDF text layer give word spaces? No."). Kahawat-Kosh page 50, 20 gold lines. The text layer has no space glyph. Cluster box holes and pen advance minus font advance both give 0.0 to 0.9 pt inside words and between words. A line with 5 gold spaces shows 9 tiny holes and no clear peak. The pixel test of 2026-10-24 gave the same answer. [S35, Read]
- The earlier Batool dictionary work found that a word space can be set where the right-to-left x-gap is above about 1 px (`LOG.md` line near 1684). So geometry works for Batool and fails for NOORIN. [S35, Read]
- Background from the PDF standard: "word spacing" (Tw) applies "to every occurrence of the single-byte character code 32 in a string when using a simple font or a composite font that defines code 32 as a single-byte code. It shall not apply to occurrences of the byte value 32 in multiple-byte codes." [S29, Read] Our Noori fonts are Identity-H (two-byte codes, `CLAUDE.md`), so Tw cannot widen their spaces. A producer that wants a space there must draw a glyph or move the pen. We saw neither. See the InPage section.

---

## Q5. How do papers score space errors?

| Metric | Used by | What it measures |
|---|---|---|
| Boundary precision, recall, F1 for each class (word boundary, sub-word boundary) from a confusion matrix | Zia et al. [S1, Read]; Sindhi SGNWS [S11, Read] | Per character position: is this a boundary? |
| Macro-average F1 over the classes no space, space, ZWNJ | PerSpaCor [S8, Read] | Same, averaged so that rare classes count equally |
| Character-level precision, recall, F1 for each restored feature | Dyer et al. [S26, Read] | Same, per feature |
| Error detection rate (share of known omission and insertion errors fixed) and word accuracy | Durrani [S3, Read] | How many of the 404 real errors were repaired |
| Word identification rate and sentence identification rate | Akram and Hussain [S4, Read] | A sentence is wrong if one word is wrong |
| Merged-word recall and precision, then segmentation accuracy | Lehal 2010 [S5, Read] | Two stages scored apart |
| Word error rate and character error rate | Kolak and Resnik [S20, Read]; UNB [S19, Read] | General OCR metrics |
| Precision on accepted edits, plus count of character-altering edits | Hassan [S14, Read] | Safety of an insert-only pass |

For our project I propose the following (my own definition, not from one paper):

1. Remove all spaces from the OCR line and from the gold line. If the letters differ, score the letter error apart and do not count those lines as space tests.
2. For the lines where letters match, align the space positions and count: gold spaces missed (merge errors), extra spaces (split errors), and spaces right.
3. Report space precision, recall and F1, and also "space errors per 100 gold spaces". Also report the plain word error rate, so you can compare with the 17.5 and 13.4 percent figures.
4. Report letter changes made by the repair step. The target is zero.
5. Report separately the errors after a non-joining letter and after a joining letter, because Urdu sources say the two kinds differ. [S1, Read]

---

## InPage: how it stores and exports text

### What is documented

- The .inp format is not publicly documented, as far as I could find. I found no specification and no byte layout. [Searched; nothing found]
- Published converters exist.
  - The Center for Language Engineering (UET Lahore) offers an "InPage to Unicode Converter" v1.0 (user guide dated July 24, 2012). Its page says InPage "uses its own encoding scheme for text manipulation which is different form Unicode" and that the tool was built by modifying "freely available source code at IT Duniya". The page and the guide do not say how spaces are handled or which InPage versions work. [S32, Fetched and Read]
  - Malik built a reverse-engineered InPage-to-Unicode converter for Kashmiri and related languages. The KS-LIT-3M paper says it reverse-engineered "InPage's character storage format" and that InPage "implements a proprietary rendering system where character codes, position information, and formatting data are interleaved". It points to a separate paper for the method. [S16, Read] [S15, Read] I could not open that paper (HTTP 403). [S34, Not opened] I did not find its code.
  - Search results mention a GitHub project and vendor tools that convert in both directions. I did not open them. [S37, Snippet]
- A vendor page (convert.guru) says newer .inp files need a reverse-mapping table from byte codes to Unicode, and one site says older versions use custom font sets and the latest is based on Unicode Urdu. I saw both only in snippets. [S37, Snippet] Wikipedia says version 3 is "Unicode based" with no reference. [S33, Fetched]

### How Noori Nastaleeq builds words

- Noori Nastaleeq is a ligature-based font. It has "over 20,000 pre-composed ligatures" and "can only be used with the proprietary software InPage", according to Gulzar and Rahman (a Nastaliq rendering paper). [S31, Read]
- Their paper also says the diagonal shape of Nastaliq "produces extra white space between two ligatures" and so needs kerning, and that the shape of the last letter in a ligature depends on the letters before it. [S31, Read]
- Claim that InPage "licensed" Noori Nastaliq from Monotype is on Wikipedia with no reference. [S33, Fetched] I found no Monotype or InPage technical paper about its internal glyph pieces. So the "component font" structure we found in the PDFs (the NOORIN01 to NOORIN86 sub-fonts) has no primary source behind it except our own inspection (`CLAUDE.md`).
- Separate old design for a ligature-based Nastaliq system: US patent 4680710 (Kizilbash, filed 1984, granted 1987). It says a space typed at the end of a word starts word forming, that a "space dictionary" sets gaps between ligatures inside a word, and that "the single space which is entered at the end of the word results in a standard interword distance". [S30, Fetched] I found no evidence that this patent is the design behind Noori Nastaleeq or InPage. I list it only as an example that, in one ligature-based design, the gap between ligatures and the gap between words come from two different tables.

### Is a space a real character in InPage, and how is it drawn in a PDF?

- I found no primary source that answers either part. The Hassan paper says that in InPage-to-text exports the fused-word defect appears and that "the exact stage at which the whitespace is lost cannot be isolated". The author makes "no claim about how InPage represents or emits spacing internally". [S14, Read]
- What we know from this project: the PDF text layer of Noori books has no space glyph, and the pen advance is not larger between words than inside words. [S35, Read]
- What the PDF standard allows: with two-byte fonts, word spacing (Tw) cannot act on a space. So a producer must use a glyph or an explicit pen move. We saw neither. [S29, Read]
- My hypothesis, not tested: InPage may build the word gap into the advance width of the last ligature piece of each word, or place each word as its own positioned run with no separate gap. If so, the information may sit in the identity of the last piece (which sub-font and code it is), not in the distance. A test is in step T6 below. No source supports or rejects this.

### Does any tool or paper recover word spaces from InPage PDFs?

- I found none. Two papers recover text from InPage files (not PDFs) and normalize spaces afterwards. [S15, Read] [S16, Read] One paper restores spaces after an InPage export, with an insert-only gate. [S14, Read] Search results on "InPage PDF text gibberish" returned only forum and vendor pages that advise OCR or the original .inp file. [S37, Snippet]
- Important consequence: if you have the original .inp file, a converter may give spaces that the PDF lacks. We do not have the .inp files for our books. I did not check whether the publishers can supply them. Ask Dr. Javaid Rahi, whose collection supplies many of the books.

---

## Ranked options

Cost is for one person on a CPU PC. "Needs" lists data and tools. Ranking uses my judgment from the sources above. No option here is tested on Gojri.

| Rank | Option | Cost | Risk | Needs | Evidence |
|---|---|---|---|---|---|
| 0 | Error census: count merges and splits by letter class (joiner or non-joiner), by line, by genre | 2 to 4 hours | None | Current UTRNet output and gold text for the 20 lines, plus more gold lines | Zia et al. omission and insertion rules [S1] |
| 1 | (a) Re-decode with a character n-gram language model plus a tunable space bonus, using the UTRNet scores | 1 to 3 days (the KenLM README does not name Windows, so write a small beam search or use WSL) | Medium. The model may favor common Urdu-like spacing. Tune on a held-out genre | Gojri text for the model; UTRNet logits saved per line; 200 or more gold lines for tuning | Kolak and Resnik [S20]; Akram and Hussain [S4]; UTRNet greedy code [S18] |
| 2 | (b) CRF space tagger (Zia-style features) trained on FLI text with random space removal and random insertion | 1 day (`sklearn-crfsuite` on CPU, minutes to train) | Medium. Synthetic noise may not match print gaps. FLI spacing may have shaping spaces | FLI text (60K words), a joiner table for Gojri letters | Zia et al. [S1]; PerSpaCor labels by removal [S8] |
| 3 | Combine (a) and (b): change a space only if both agree against the OCR, or if a person confirms | 1 day after 1 and 2 | Low | Outputs of 1 and 2 | Gating idea: Hassan [S14] |
| 4 | (d) LLM that may only insert or delete spaces, with the letter check, for lines that the combination flags | 1 day of prompt work plus API cost; no new model | Medium. An LLM trained mostly on Urdu may re-split Gojri words like the word list did. Old test: 13.4 percent WER and letter changes on 2 of 20 lines | Gemini or similar; a checker `ρ(x) = ρ(y)` that removes all spaces and compares | Hassan [S14] |
| 5 | (e) Human spot check tool: show the line image and the proposed spacing, mark only low-confidence spaces | 2 to 3 days to build; then user time | Low technical risk; the user's time is the cost | A small web or Tkinter page; confidence score from 1 to 4 | Hassan's defer path [S14] |
| 6 | (c) PDF glyph geometry | already tested | High. Tested and failed for NOORIN; works for Batool | PDF text layer | `LOG.md` 2026-11-15 [S35] |
| 7 | Small neural transformer or BiLSTM tagger | 2 to 5 days | High. Needs more text than we have | A pretrained multilingual model, more clean text | Sindhi [S11], Persian [S8] use 2 to 13M tokens |

Recommended order: 0, then 1, then 2, then 3, then 5 for the residual, and 4 only on the lines that remain disputed. Skip 6 and 7 for now. Add the optional T6 test only if steps 0 to 3 stall.

---

## Proposed test plan (all steps run on a CPU PC)

Gold data first. The 20 lines from page 50 are too few. One word is about 1 percent, so 17.5 versus 13.4 percent is about 4 words. Before step T1, label at least 200 gold lines from at least three different books or genres, and keep 100 of them as a locked test set that no tuning touches. The user, as a native speaker, can do this with the gold images that the project already has.

- T0. Census (about 2 hours). Align OCR and gold with spaces removed. List every merge and split. Tag each by the letter before the boundary (joiner or non-joiner, using Zia's table [S1]) and by whether the word is a Gojri word or an Urdu word. Win: you learn the main pattern. If at least 70 percent of errors sit at non-joiner boundaries (my threshold, not from a paper), later steps can focus there.
- T1. Space bonus on the CTC scores (about 1 day). Save the UTRNet output scores per line. Add a fixed bonus (positive or negative) to the space class and decode again. Pick the bonus on a dev split. Win: word error falls by at least 2 points on the dev split with no letter change. This step needs no language model and no new data. It is my suggestion from how CTC works, not from a paper.
- T2. Character n-gram model (about 2 days). Train orders 3, 4, 5 and 6 on the FLI text with leave-one-file-out splits. Write a small prefix beam search over the UTRNet scores that adds the n-gram score and the space bonus. Tune the model weight and the bonus on dev lines. Win on the locked test: word error at most 11 percent (from 17.5), space F1 above the T1 value, zero letter changes versus the greedy letters. Also report the result on lines whose genre was not in training. If order 6 beats order 4, note that Kolak and Resnik found that higher order needs more data. [S20]
- T3. CRF tagger (about 1 day). Train on FLI text. Input: letters with no spaces. Features: Zia's window of 3 letters each side, joiner flag, Unicode class. [S1] Add noise training lines: drop 30 to 70 percent of spaces, add random spaces after joiners with a small probability. Test first on clean FLI held-out files (reference: Zia got F1 0.97 with 90K tokens), then on OCR lines. Win: F1 at least 0.90 on held-out FLI text, and better than T2 alone when the two are combined.
- T4. Combine. Rule: apply a change only if T2 and T3 both vote for it, or if the T2 score margin is large. Win: word error at most 9 percent on the locked test, with space errors per 100 gold spaces cut by at least 40 percent against greedy UTRNet, and no worse than greedy on lines that were already exact. (My targets. They are guesses until T0 gives the baseline.)
- T5. Gated LLM and human check. Run the LLM only on lines where T2 and T3 disagree. Use the letter-invariant check and drop any edit that fails it. Send the rest to a person with a small page that shows the line image and the two or three candidate spacings. Win: the user can finish 200 lines in under two hours, and the final word error on the locked test is at most 6 percent.
- T6 (optional). Last-piece test for Noori PDFs. For each line in the 200 gold lines that has a PDF text layer, mark the last cluster before each gold space. Count how often those clusters come from a small set of (sub-font, code) pairs that rarely appear inside words. Win: if one set predicts word ends with at least 90 percent precision, a table of "word-final pieces" could give spaces for free for that book. Treat this as research. It could fail for the same reason the glyph decode failed (`CLAUDE.md`).

What a win means in one line: lower word error on lines the model never saw, with no change to letters, and no loss on lines that were already right.

---

## Open questions

1. How many of our space errors fall after non-joining letters? T0 answers this. The answer decides how narrow the fix can be.
2. Is FLI text spaced like the printed books? Typed Urdu-script text may use spaces for shaping. A sample check against print is needed.
3. Does Gojri print use ZWNJ or "half space" rules? I found nothing. Ask the user and check the FLI files for U+200C.
4. Can the .inp files for the books be found? A converter may give correct text with spaces. I could not verify that any converter keeps spaces, because I could not open the Malik paper.
5. Does InPage place word gaps in the advance width of the last piece of a word? No source answers this. T6 tests it for one book.
6. How large is the gain of a character n-gram over a plain space bonus (T1)? I found no paper that compares them on Nastaliq. The comparison may show that T1 is enough.
7. Do Gojri words differ from Urdu words in joiner and non-joiner statistics? The Zia rules were found on Urdu news text.
8. Does an LLM that knows little Gojri keep a word together? Only a test on gold lines can show it.
9. The beam table in Akram and Hussain does not match their headline figure (see Q1). I did not resolve this.
10. I could not open the Pashto CRF paper, the Malik converter paper, the ViraPart paper (only a snippet), and PaddleOCR current docs. They may add facts.

---

## Sources

Tags: Read, Fetched, Snippet, Not opened (see the key at the top).

| Id | Source | URL | Tag |
|---|---|---|---|
| S1 | Zia, Raza, Athar, "Urdu Word Segmentation using Conditional Random Fields (CRFs)", 2018, arXiv 1806.05432 | https://arxiv.org/pdf/1806.05432 | Read (whole text) |
| S2 | Farhan, Islam, Sharma, "Enhanced Urdu Word Segmentation using CRFs and Morphological Context Features", WiNLP 2020 | https://aclanthology.org/2020.winlp-1.41 | Fetched (abstract page) |
| S3 | Durrani, "A word segmentation system for handling space omission problem in Urdu script" (the PDF lists Nadir Durrani first; other papers cite "Durrani and Hussain 2010") | https://alt.qcri.org/~ndurrani/pubs/SpaceOmission.pdf | Read |
| S4 | Akram and Hussain, "Word Segmentation for Urdu OCR System", 2010 | https://aclanthology.org/W10-3212.pdf | Read (method and results parts) |
| S5 | Lehal, "A Word Segmentation System for Handling Space Omission Problem in Urdu Script", 2010 | https://aclanthology.org/W10-3606.pdf | Read (abstract and introduction) |
| S6 | Lehal and Saini, "Conversion between Scripts of Punjabi: Beyond Simple Transliteration", COLING 2012 posters (Shahmukhi space statement) | https://aclweb.org/anthology/C12-2062.pdf | Read (the cited passage) |
| S7 | Lehal and Rana, "Recognition of Nastalique Urdu Ligatures", MOCR 2013 | https://learnpunjabi.org/pdf/Lehal.11.pdf | Read |
| S8 | Ebrahimkhani and Ansari, "PerSpaCor", RANLP 2025 | https://aclanthology.org/2025.ranlp-1.40.pdf | Read (method and test tables) |
| S9 | "Joint Persian Word Segmentation Correction and ZWNJ Recognition Using BERT", arXiv 2010.00287 | https://arxiv.org/abs/2010.00287 | Fetched (abstract) |
| S10 | ViraPart, arXiv 2110.09086 | https://arxiv.org/pdf/2110.09086 | Snippet |
| S11 | Ali et al., "Enhancing Sindhi Word Segmentation using Subword Representation Learning and Position-aware Self-attention", arXiv 2012.15079 | https://arxiv.org/pdf/2012.15079 | Read (method, data, metric, result) |
| S12 | Haq et al., "Correction of Whitespace and Word Segmentation in Noisy Pashto Text using CRF", Speech Communication 2023 | https://doi.org/10.1016/j.specom.2023.102970 | Not opened (publisher redirect only; facts from a search summary) |
| S13 | NLPashto package page | https://pypi.org/project/nlpashto/ | Fetched |
| S14 | Hassan, "A Precision-First Whitespace Restoration Pipeline for Noisy Urdu Tafseer Text", WNUT 2026 | https://aclanthology.org/2026.wnut-1.1.pdf | Read (whole text up to evaluation setup; results from the abstract) |
| S15 | Malik and Nissar, "KS-PRET-5M", arXiv 2604.11066 | https://arxiv.org/pdf/2604.11066 | Read |
| S16 | Malik, "KS-LIT-3M", arXiv 2601.01091 | https://arxiv.org/pdf/2601.01091 | Read |
| S17 | "UTRNet: High-Resolution Urdu Text Recognition in Printed Documents", arXiv 2306.15782 | https://arxiv.org/pdf/2306.15782 | Read (related work, model, datasets) |
| S18 | UTRNet repository and `read.py` | https://github.com/abdur75648/UTRNet-High-Resolution-Urdu-Text-Recognition and https://raw.githubusercontent.com/abdur75648/UTRNet-High-Resolution-Urdu-Text-Recognition/main/read.py | Fetched |
| S19 | "From Press to Pixels: Evolving Urdu Text Recognition", arXiv 2505.13943 | https://arxiv.org/pdf/2505.13943 | Read (results and error analysis) |
| S20 | Kolak and Resnik, "OCR Post-Processing for Low Density Languages", HLT/EMNLP 2005 | https://aclanthology.org/H05-1109.pdf | Read |
| S21 | Garst, Ingle, Fujii, "OCR Language Models with Custom Vocabularies", arXiv 2308.09671 | https://arxiv.org/abs/2308.09671 | Fetched (abstract) |
| S22 | pyctcdecode README | https://github.com/kensho-technologies/pyctcdecode | Fetched |
| S23 | KenLM README | https://github.com/kpu/kenlm | Fetched |
| S24 | Calamari and Kraken project pages | https://github.com/Calamari-OCR/calamari and https://kraken.re/main/index.html | Fetched (nothing on spaces or language models) |
| S25 | PaddleOCR text recognition docs (2.x) | https://www.paddleocr.ai/main/en/version2.x/ppocr/model_train/recognition.html | Snippet |
| S26 | Dyer et al., "Comparison of Token- and Character-Level Approaches to Restoration of Spaces, Punctuation, and Capitalization", ICNLSP 2022 | https://aclanthology.org/2022.icnlsp-1.19.pdf | Read (abstract and dataset part) |
| S27 | Gupte et al., "Lights, Camera, Action! A Framework to Improve NLP Accuracy over OCR documents", arXiv 2108.02899 | https://arxiv.org/pdf/2108.02899 | Read (action labels part) |
| S28 | Guan and Greene, "Advancing Post-OCR Correction: A Comparative Study of Synthetic Data", ACL Findings 2024, arXiv 2408.02253 | https://arxiv.org/abs/2408.02253 | Fetched (abstract) |
| S29 | ISO 32000-1:2008 (PDF 1.7), section 9.3.3 word spacing | https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf | Read (page 253 of the file) |
| S30 | US patent 4680710, Kizilbash, "Computer composition of nastaliq script of the urdu group of languages" | https://patents.google.com/patent/US4680710 | Fetched |
| S31 | Gulzar and Rahman, "Nastaleeq: A challenge accepted by Omega", TUGboat 29(1) | https://tug.org/TUGboat/tb29-1/tb91gulzar.pdf | Read |
| S32 | CLE (UET Lahore) InPage to Unicode converter, page and user guide | https://cle.org.pk/software/langproc/inpagetounicode.htm and https://www.cle.org.pk/Downloads/langproc/inpageunicode/Inpage-to-Unicode-Converter.pdf | Fetched (page); Read (guide, 3 pages, no technical detail) |
| S33 | Wikipedia, "InPage" | https://en.wikipedia.org/wiki/InPage | Fetched (no format information) |
| S34 | Malik, "A Robust InPage-to-Unicode Encoding Converter for Kashmiri and Related Languages", ResearchGate 2024 | https://www.researchgate.net/publication/387522744 | Not opened (HTTP 403) |
| S35 | Project files: `LOG.md` (entries 2026-10-24, 2026-11-05 dictionary pass, 2026-11-15 PDF space test) and `CLAUDE.md` | D:\Code\VSCodeProjects\gojri-ai\LOG.md | Read |
| S36 | Malik thesis on Urdu handwriting with a ligature language model (named in a search result) | https://shehryar-malik.github.io/theses/sp | Snippet |
| S37 | Vendor and community pages on .inp conversion and InPage PDFs | https://convert.guru/inp-to-txt , https://www.fileinfo.com/extension/inp , https://redlib.hyperreal.coffee/r/Urdu/comments/1i0mm26/need_help_with_inpage_generated_pdf_back_in | Snippet |

Things I did not find after searching: a primary source for the .inp byte layout; a paper with numbers on space errors in Kashmiri or Shahmukhi; a paper that scores space errors of an Urdu or Nastaliq OCR system; a paper that tests a small transformer on under 100K words for spacing; any tool that recovers word spaces from an InPage PDF.
