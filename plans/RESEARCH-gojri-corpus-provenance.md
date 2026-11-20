# Research: how the FLI "Gojri Literature Corpus" was digitised, and what its text error rate is

Date: 2026-11-17. Scope: how the text of the Mozilla Data Collective "Gojri Literature Corpus" (steward FLI, dataset id `cmlgz1vdt001omg07rv25gwnu`) was produced, whether any error rate or quality check is published, whether FLI describes its digitisation workflow anywhere, and whether the source books are public.

## Summary

- **Method of digitisation: NOT FOUND.** The dataset page does not say how the text was produced (OCR, typing or copy from digital files). It lists only cleaning steps: UTF-8, Unicode normalization, whitespace and punctuation cleanup, removal of stray symbols and markup. [S1]
- **Error rate or validation: NOT PUBLISHED.** The page has no error rate, WER, CER, sample check or review of text accuracy. Its only quality sentence is about suitability for release ("All materials were reviewed to ensure they are suitable for open, non-commercial research use"). That is a rights and ethics check, not a text accuracy check. [S1]
- **Other FLI corpora: same picture.** The Khowar Literature Corpus page also has no OCR statement and no error rate. [S3] The Hussain Faizy Indus Kohistani Corpus page is the only FLI page that describes a workflow. It says native speakers reviewed the corpus and that PDF text "will be extracted directly" and normalised. It gives no error rate and no OCR tool. [S4] The Punjabi Literature Corpus you named is not an FLI dataset. Its steward is "Tamahi Suneha Magazine", and its page has no method text. [S2]
- **No FLI or SIL document describes an OCR workflow for Gojri.** I found none on fli-online.org, in the FLI annual reports, in SIL's "Writing Gojri", on arXiv or in the ACL Anthology. [S5, S6, S7, S8, S9]
- **Source books: not found online as scans.** The corpus files themselves name two sources. File 01 says the Gojri text is a translation by Mukhlis Wijdani of a Qazi Zain ul Abidin Merathi book (header dated March 19, 2018). File 09 says its story comes from the Bakarwal Mobile School (BMS) Pakistan. I found no scan or print link for any of the 11 titles. [L1, L2]
- **Best inference:** the 2018 date and the 82 U+FFFF characters in the BMS-type story files point to text that was typed or edited in a word processor, not OCR output. This is inference only. See Q1.

## How to read the tags

- CONFIRMED: a source says it. I give a short quote and the source number.
- NOT FOUND: I looked and found nothing. I say where.
- INFERENCE: my own reasoning. Treat it as a hypothesis.
- Fetched: a fetch tool gave me a summary of the page. I did not see the raw HTML. Quotes are relayed by the tool, and are short.
- Snippet: I saw the claim only in a search result summary. Unverified.
- Not loaded: the page shell loaded, but the dataset text did not.
- L = local fact from files in this repo (not searched).

## Sources

| # | Source | URL | Type | Tag |
|---|---|---|---|---|
| S1 | Mozilla Data Collective, "Gojri Literature Corpus" (steward FLI) | https://mozilladatacollective.com/datasets/cmlgz1vdt001omg07rv25gwnu | Primary (dataset page) | Fetched, two calls |
| S2 | Mozilla Data Collective, "Punjabi Literature Corpus" | https://mozilladatacollective.com/datasets/cmhp42gmu00aumk07w7k22tbp | Primary (dataset page, other steward) | Fetched |
| S3 | Mozilla Data Collective, "Khowar Literature Corpus by FLI" | https://mozilladatacollective.com/datasets/cmlgys7fj001knx077yktc0pd | Primary (dataset page) | Fetched |
| S4 | Mozilla Data Collective, "Hussain Faizy Indus Kohistani Corpus" (FLI) | https://mozilladatacollective.com/datasets/cmixehxof005dnr07yp80kluh | Primary (dataset page) | Fetched |
| S5 | FLI organization page on Mozilla Data Collective (5 datasets) | https://datacollective.mozillafoundation.org/organization/cmi67tk2i002lmj071kz09ogn | Primary, seen only through search results. The fetch of the new domain returned HTTP 404. | Snippet |
| S6 | FLI Annual Report 2023 (PDF, text extracted locally) | https://fli-online.org/wp-content/uploads/2024/05/FLI-Annual-Report.pdf | Primary | Read (text layer) |
| S7 | FLI Annual Report 2025 (PDF, text extracted locally) | https://fli-online.org/wp-content/uploads/2026/02/Annual-Report-2025.pdf | Primary | Read (text layer) |
| S8 | FLI page "Gojri" | https://fli-online.org/gojri/ | Primary | Fetched |
| S9 | FLI news: MoU with Mozilla Foundation (Sept 3, 2025) | https://fli-online.org/fli-and-mozilla-foundation-sign-mou-for-data-sharing/ | Primary | Fetched |
| S10 | FLI news: Gojri curriculum workshop, Muzaffarabad | https://fli-online.org/capacity-building-workshop-for-gojri-language-curriculum-developers-in-muzaffarabad/ | Primary | Fetched |
| S11 | FLI news: undocumented languages workshop (April 2025) | https://fli-online.org/exploring-the-undocumented-and-under-documented-languages-of-pakistan/ | Primary | Fetched |
| S12 | Losey 2002, "Writing Gojri", SIL Work Papers vol. 46 (repository page, DOI 10.31356/silwp.vol46.03) | https://commons.und.edu/sil-work-papers/vol46/iss1/3 | Primary (SIL, repository) | Fetched |
| S13 | Alam and Tyers, "Common Voice for Pakistan", LREC 2026 | https://aclanthology.org/2026.lrec-1.265/ | Primary (ACL Anthology) | Fetched |
| S14 | Mozilla Data Collective community FAQ | https://community.mozilladatacollective.com/tag/faq/ | Primary (platform docs) | Fetched |
| S15 | Common Voice Scripted Speech 24.0 and 25.0, Gujari (datasheets) | https://mozilladatacollective.com/datasets/cmj8u3p5m009pnxxbmrz4hqru and https://mozilladatacollective.com/datasets/cmn2aus9q01ddmm07rsn6o1jj | Primary, but the pages did not load text for me. Quotes come from search result summaries. | Snippet, Not loaded |
| S16 | Gojri language, Wikipedia (bibliography) | https://en.wikipedia.org/wiki/Gojri_language | Secondary | Fetched (first 100,000 of 165,421 characters) |
| S17 | Web search (several queries) for Mukhlis Wijdani, Qazi Zain ul Abidin Merathi, the BMS stories, "Maharo Deen" and the other titles | n/a | Search results only | NOT FOUND for the Gojri editions |
| S18 | Kashmir Life, JKBOSE Gojri textbooks; Selfstudys JKBOSE Gojri textbook pages | https://www.selfstudys.com/books/jammu-kashmir/state-books/class-5th/gojri/44282 | Secondary (resale site), different books | Snippet, not opened |
| L1 | Local corpus file headers: `datasets/Gojri Language Corpus/01-Seerat Nabi Arbi - ...txt` | local | Local fact | Read |
| L2 | Local corpus file `09-Rasheed Ko Ghoro - Story (Pictorial) - 368.txt` (intro paragraph) | local | Local fact | Read |

Note on S1: the old domain `datacollective.mozillafoundation.org` redirects (HTTP 301) to `mozilladatacollective.com`. The content is the same page.

---

## Q1. Which OCR model, tool or manual process did FLI use?

### Short answer

NOT FOUND. No source says. The dataset page does not name a method.

### CONFIRMED

- The Gojri page describes the corpus as "approximately 60,821 tokens of Gojri (Gujari) text" from "poetry, short stories, narrative prose, and question-answer literary books". [S1]
- It lists the cleaning steps: UTF-8 encoding, Unicode normalization, "Whitespace and punctuation cleanup", "Removal of stray symbols and markup". [S1]
- It says: "The corpus was curated from literary and educational Gojri texts under an internal ethical review process by FLI." [S1]
- The page has no "Methodology" or "Data quality" section. The nearest sections are "Processes" (with "Ethical Review") and "Cleaning and Preprocessing". The page does not mention OCR, scanning, typing or transcription. [S1]
- The file list marks file 09 as "Story, pictorial text" and file 10 as "Three Stories with Urdu Translations". Token counts are shown per file. [S1]
- Local fact: the headers of the files give some provenance. File 01 says (in Urdu): book "Seerat Nabi Arbi", author "Qazi Zain ul Abidin Merathi", "Gojri translation: Mukhlis Wijdani", date "March 19 2018". [L1]
- Local fact: file 09 has an introduction. It says Bakarwal Mobile School Pakistan is the first institution that teaches Bakarwal children in their mother tongue from nursery to class five. It adds that the BMS system prepares stories beside the curriculum, and that "Rasheed Ko Ghoro" is the first of this series. [L2]
- The Common Voice Gujari datasheets say their sentences "have been taken from Gojri story books, folk tales, Islamic studies and from course books". For version 25.0 they report 3,852 validated sentences: 2,528 from short stories, 1,218 written by the contributor, 105 from one religious text. [S15, Snippet]

### NOT FOUND

- Any statement of OCR, scanning, typing or transcription for this corpus. Searched: S1 (two fetches), the FLI organization listing [S5], the FLI pages and annual reports [S6 to S11], web search for FLI with "OCR", "digitization", "Nastaliq".
- Any FLI Gojri digitisation project. A search for "FLI Gojri corpus digitization OCR Nastaliq" returned only the dataset page, the FLI Gojri-workshop pages and the FLI Awami Nastaliq font news. The Awami Nastaliq news is about a font, not OCR. [S5, S8, S10]
- A named tool, model or vendor. None is named anywhere I could open.

### Closest FLI method statement (another corpus)

- The Hussain Faizy Indus Kohistani Corpus page says: "Reviewed by native speakers", texts "all transcribed with a consistent community orthography", "Text from PDFs will be extracted directly and standardized for Unicode, spacing, and orthography", and "The final output will include uniformly formatted UTF-8 text files". The tool relayed these quotes. The page uses the future tense, so it describes planned steps. It does not mention OCR. [S4]
- This tells us FLI's pipeline for at least one corpus starts from PDFs with a text layer ("extracted directly"). It does not tell us about the Gojri files.

### INFERENCE (mine, not from a source)

- The Gojri files probably did not come from OCR of print. Reasons:
  1. File 01 carries a header line with a date in 2018 and a translator credit. That looks like a word-processor document, not a scan. [L1]
  2. The text is clean Unicode Nastaliq, with the colloquial words spelled the same way within a file. The repo notes that OCR on Gojri Nastaliq is hard, and OCR output is usually less regular. This is weak evidence.
  3. The 82 U+FFFF characters sit only in files 08 to 11 (the BMS-type stories and poems). A U+FFFF in a word like `بن￿نو` (file 08), `ہال￿و` and `نال￿` (file 09) sits where Gojri needs a letter or mark that Urdu does not have. One reading: the author typed a special mark in InPage or Word with a font mapping, and the conversion to Unicode lost it. That would point to typing plus font conversion. I cannot prove it.
  4. The Common Voice Gujari datasheet says its sentences come from "story books" and "short stories". The same BMS-style stories may have supplied both datasets. This is a guess. [S15]
- The practical meaning: if the text came from typed or converted files, the error type is likely conversion loss (lost marks, wrong spaces) and typos. It would not be OCR-type letter swaps. We cannot confirm without the source files.

---

## Q2. Is any error rate, WER, CER or validation published for this corpus or other FLI corpora?

### Short answer

NOT PUBLISHED for the Gojri corpus. NOT PUBLISHED for any FLI corpus that I could open.

### CONFIRMED

- Gojri page: no error rate and no text-accuracy check. The only review step named is the "internal ethical review process by FLI". The quality sentence is: "All materials were reviewed to ensure they are suitable for open, non-commercial research use." The tool also says the page states materials were checked against copyright and cultural norms. [S1]
- Khowar Literature Corpus by FLI: same cleaning list (UTF-8, Unicode normalization, whitespace and punctuation cleanup, removal of stray symbols and markup). It says "Permissions were obtained from original authors or translators where applicable". "The page gives no error rate, accuracy figure, or quality assessment." It does not say if texts were scanned, typed or validated. [S3]
- Hussain Faizy Indus Kohistani Corpus: native-speaker review is stated. No error rate and no formal validation procedure. [S4]
- Punjabi Literature Corpus: the steward is "Tamahi Suneha Magazine", not FLI. The page gives "10,39,430 tokens of Punjabi Shahmukhi script", TXT 1.83 MB, CC-BY-NC-4.0, and no method, cleaning or quality text. So it cannot show how FLI works. [S2]
- FLI organization page on Mozilla Data Collective: five datasets. Seen in search results: Gojri Literature Corpus, Hussain Faizy Indus Kohistani Corpus, Khowar Literature Corpus by FLI. The Khowar Word List and the Kohistani Shina Word List also appeared in searches as related FLI-type datasets. I did not confirm the steward of those two, and I did not open the organization page itself (HTTP 404 on the new domain). [S5, Snippet]
- Mozilla Data Collective FAQ: "We aim to review all dataset submissions within 7 days." The FAQ topics I saw do not cover data quality checks by the platform. Problems are reported through the uploader or the "report dataset" link. [S14]
- MoU with Mozilla Foundation: the page speaks of "protection, sharing, and celebration of indigenous language data" and "community-driven" tools. It does not describe collection, digitisation, cleaning or validation. It does not mention Gojri, OCR or corpora. [S9]

### NOT FOUND

- Any WER, CER, sample-based accuracy figure, inter-annotator check or proofreading statement for the Gojri corpus. Looked at: S1, S5, S9, S14, web search.
- Any datasheet, paper or blog post by FLI about quality of its Mozilla Data Collective corpora. Looked at: arXiv and ACL Anthology searches through the web search tool. The searches found no FLI paper. The one related ACL paper (Common Voice for Pakistan, LREC 2026) does not mention Gojri or FLI, and it is about speech sentences, not text corpora. [S13]
- I did not search the Mozilla Data Collective site by its own search box. The site renders by script, so my fetch tool cannot use it. I used web search for the steward name instead. A person with a browser should check the steward list.

### INFERENCE

- Because no quality check is published, treat the stated 60,821 tokens as a size, not a quality claim. Our local count is 60,814 words, so the size claim holds. The page also says "117.97 KB". Our local files total 554,595 bytes (about 541.6 KiB, 339,969 characters), so the page size is not the size of the text. The page figure is probably a mistake or the size of an archive. This matches the existing note in `CLAUDE.md` and does not change the finding.
- For our work the error rate of this corpus is unknown until we measure it. The 82 U+FFFF characters in files 08 to 11 are the one known defect, and it is a local finding, not an FLI one.

---

## Q3. Any paper, blog, SIL or FLI document, repo or Mozilla documentation on FLI's digitisation workflow, including OCR of Gojri or other Nastaliq text?

### Short answer

NOT FOUND for a workflow description of the Gojri corpus. A few FLI and SIL documents give background only.

### CONFIRMED

- FLI Annual Report 2023 and 2025: I extracted the text from both PDFs and searched for Gojri, corpus, digitisation, OCR, dataset, Mozilla and typing. The 2023 report lists Gojri among the 11 communities FLI supported and says FLI published "18 books under its Academic and 22 books under its Vernacular series". The 2025 report mentions the Gojri curriculum workshop and the MoU with Mozilla. Neither describes digitisation or OCR. [S6, S7]
- FLI Gojri page: it links a thesis, "Gojri Writing; A thesis" (https://fli-online.org/site/wp-content/uploads/2015/02/losey_thesis.pdf), and describes the Bakarwal Mobile School System ("40 mobile schools for nomad children in northern Pakistan"; basic education in Gojri, then Urdu and English). It lists no corpus, dictionary or digitised text. [S8]
- FLI workshop page (Muzaffarabad, Dec 29, 2025 to Jan 2, 2026): "Gojri ... has long been in written use", and "further work is needed to standardize its orthography". No digitisation text. [S7, S10]
- FLI undocumented-languages workshop page (April 2025): Gojri is one of the languages represented. No corpus or OCR content. [S11]
- Losey 2002 (SIL): the repository page gives the abstract and the PDF link. It does not name the Gojri books or publishers the study used. It is a 2002 orthography study and cannot describe a 2026 corpus. [S12]
- Common Voice for Pakistan (LREC 2026): no mention of Gojri, FLI or OCR. [S13]
- FLI and Mozilla MoU (Sept 2025) is the only link between FLI and Mozilla Data Collective that I found. It has no workflow. [S9]

### NOT FOUND

- Gojri dictionary at webonary.org/gojri: HTTP 403 for my fetch tool. I could not read it. I do not know how it was digitised. The repo's earlier note [plans/RESEARCH-gojri-word-spacing-orthography.md] also could not open it. Someone should look in a browser.
- A GitHub repo from FLI for corpus building. The web search showed none. I did not search GitHub directly.
- Any paper on OCR of Gojri. The search for Nastaliq OCR returned general Urdu OCR work (for example arXiv 2412.16119, a benchmark of LLM OCR on low-resource scripts) with no FLI link. I did not open it, because it does not concern FLI. [Snippet only]
- Any Mozilla Data Collective guideline that requires stewards to state their digitisation method. The FAQ topics I saw do not include one. I did not open the "Guides" tag page. [S14]

### INFERENCE

- FLI is a publisher of print books (22 Vernacular series books and 18 Academic series books in 2023 [S6]). It may hold the typed source files of its own books. If the corpus came from FLI-held files, the best way to learn the method is to ask FLI by email. I did not contact them.

---

## Q4. Are the source books public? Print or scan links.

### Short answer

I found no online print or scan for any of the 11 titles. The corpus files give two provenance clues that help to find the print.

### What the corpus files say (local facts)

| File | Title (as on the page) | Provenance clue |
|---|---|---|
| 01 | Seerat Nabi Arbi (Book, 28,256 tokens) | Header: author Qazi Zain ul Abidin Merathi, Gojri translation by Mukhlis Wijdani, dated March 19, 2018 [L1] |
| 02 to 06 | Aqalmand Dhiyani, Dukh Ki Chaan, Sacha Qissa Haji Sb, Sacha Qissa Mumtaz, Teachers Story | No header. File 06 has the same poem as file 11. File 04 and 05 are about Bakarwal nomad life (a bear attack, a Kaghan stream). |
| 07 | Maharo Deen (Q&A book, 11,635 tokens) | Opens with "سوال / جواب" pairs. No author line. |
| 08, 09, 11 | Shaal Kaka Ko Poot, Rasheed Ko Ghoro, Saeen Kaka Ki Bakri | File 09 says these come from the BMS Pakistan story series [L2]. Files 08, 09 and 11 hold U+FFFF. |
| 10 | Three Stories with Urdu Translations | Gojri stories with Urdu translation. Holds U+FFFF. |

### CONFIRMED (external)

- Gojri Wikipedia lists a Gojri Seerat title: "Gujari: Gwjry Syrt Alnby ... (lškār Mḥmd) Mṣnf Mfty Mḥmd Adrys Wly Hswāl Gwjr" (Mufti Muhammad Idris Wali Hasawal Gojar). It is a bare line with no publisher or date, and the author differs from the file 01 header. So it is probably a different book. [S16, Fetched]
- No Wikipedia entry has a scan link for a Gojri book in the part I read (first 100,000 of 165,421 characters). [S16]
- Catalogue hit: a Chughtai Library record "Nabi 'Arabi, tarikh-i millat" by Qazi Zain al-'Abidin (Urdu, Nadvat al-Musannifin, Delhi, 157 pages, volume 1). The tool could not confirm that this author is the same Meerathi, or that this is the Urdu original of the Gojri translation. https://www.chughtailibrary.com/digital_library/repository_detail.php?id=87156 [Snippet, secondary]
- Rekhta lists other books by Qazi Zain ul Aabideen Merathi (for example "kalam e arabi" parts 1 and 2, Maktaba-e-Ilmiya Meerut), so the author name is real. I did not find a Rekhta page for the Urdu "Seerat Nabi Arbi". https://rekhta.org/ebooks/detail/kalam-e-arabi-part-1-qazi-zain-ul-aabideen-merathi-ebooks [Snippet, secondary]

### NOT FOUND

- A print or scan of the Gojri translation by Mukhlis Wijdani. Searched in English and in Urdu script (queries with the translator and author names). Zero results for the Gojri edition.
- Any page for "Maharo Deen", "Dukh Ki Chaan", "Aqalmand Dhiyani", "Sacha Qissa" or "Teachers Story". Zero results.
- Any online copy of the BMS story series ("Rasheed Ko Ghoro" and the other stories). A search on BMS found news and academic articles about the mobile schools (for example a 2018 UMT Education Review paper, "Nomadic Education in Northern Pakistan: The Bakarwal Case", https://journals.umt.edu.pk/index.php/uer/article/view/124). They say that Gojri primers and short stories were written. They do not link the books. [Snippet]
- Selfstudys and other sites list JKBOSE Gojri school textbooks (classes 1 to 8). These are different books from India. They are not the corpus sources. [S18, Snippet]

### INFERENCE

- Files 02 to 11, apart from 01 and 07, probably come from the BMS Pakistan story series for Bakarwal children. File 09 says so directly for one story. The other story files share the same themes (Bakarwal herders, a school, a goat). This is a guess for 02 to 06, 08 and 10 to 11.
- The best next step to get a print is a request to FLI (they steward the dataset and publish Gojri-adjacent material) or to Bakarwal Mobile School Pakistan. The Common Voice Gujari sentences may overlap with the same stories. A local text overlap check between the CV `validated.tsv` sentences and the corpus files would test this cheaply. I did not run it.

---

## What we can and cannot say about the text error rate

| Claim | Status |
|---|---|
| FLI used OCR to make the Gojri text | NOT FOUND, no source says so |
| FLI typed the text by hand | NOT FOUND, no source says so |
| A published WER or CER for the corpus | NOT PUBLISHED |
| Any proofreading or validation of text accuracy | NOT PUBLISHED. Only an ethics and rights review is stated. |
| The corpus has 82 U+FFFF characters in files 08 to 11 | Local fact |
| The text probably came from typed or converted files, not OCR | INFERENCE, weak to medium |
| The error rate is unknown | True. We must measure it ourselves. |

## Suggested next steps (not done)

1. Write to FLI (info address is on its site) and ask three things: how the Gojri files were produced, whether the source files or print are available, and what the U+FFFF mark stood for.
2. Compare the CV Gujari sentences with the corpus files to see if they share sources. If they do, the CV audio gives a second reference for spelling.
3. Look at the Webonary Gojri dictionary and the Mozilla Data Collective steward list in a normal browser. My tools could not open them.
4. Do not quote an error rate for this corpus in any paper or dataset card. Say "no error rate published by the steward".
