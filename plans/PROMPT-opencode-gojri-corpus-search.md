# Prompt for OpenCode: find existing Gojri text, book and audio sources

Date: 2026-11-24. Audience: an AI agent (OpenCode) that searches the web. Research only. Give the text below to the agent as it is.
No private data in it: it names no person of the project, no path, no account.

```
TASK
Find and list existing Gojri (Gujari) text, book and audio sources on the open internet. This is research only. Do not build anything.

CONTEXT
I run a non-commercial research project. We build OCR (reading printed pages), speech recognition and a language model for Gojri.
Gojri is also called Gujari, Gujjari, Gojari. ISO 639-3 code: gju. Do NOT confuse it with Gujarati (Gujarat state, code guj). They are different languages.
Gojri is an Indo-Aryan language of the Gujjar people in Jammu and Kashmir, Himachal Pradesh, Azad Kashmir, Gilgit-Baltistan, Hazara and Khyber Pakhtunkhwa, and eastern Afghanistan.
It is written in Perso-Arabic Nastaliq (Pakistan, Indian Kashmir), in Devanagari in parts of India, and sometimes in Roman letters.
Gojri shares many words with Urdu but it is a separate language. It has no standard spelling.
Gojri uses letters that Urdu does not use: ݨ (U+0768 or U+0769, noon with a small v) and ڵ (U+06B5, lam with a small v). They help to tell Gojri from Urdu.

WHY WE NEED TEXT
Our OCR makes errors in word spaces and letters. We need correctly spaced and correctly spelled Gojri text, typed by people (not OCR output).
We use it to train small text models, to check OCR output, and to build an evaluation set. We also need it later for speech and language-model work.
Parallel text (Gojri next to Urdu, Hindi or English) is very valuable.

WHAT WE ALREADY HAVE (do not list these as new; mention one only if you find a better copy or a newer version)
- The Forum for Language Initiatives (FLI) "Gojri Literature Corpus" on Mozilla Data Collective (11 text files, about 60,000 words).
- Common Voice 26.0 Gujari speech (about 10.7 hours, scripted).
- The online Gojri dictionary at webonary.org/gojri.
- About 64 PDF books, mostly by Dr. Javaid Rahi (dictionaries, folklore, poetry), the Concise Gojri-English Dictionary by Dr. M. R. Anjum Awan, a Gojri Quran translation by Dr. Rafiq, the Gojri-Hindi-English dictionary, J&K school primers, Kahawat-Kosh (proverbs), Banjara, Dil-Darya.
- Two Hugging Face datasets of ours (dictionary text, Devanagari to Nastaliq lexicon).

WHAT TO FIND, IN THIS ORDER
A. Born-digital Gojri text in Unicode: websites, blogs, news pages, magazines, public social media pages, Wikimedia Incubator, Wikisource, Wiktionary, Bible and other religious translations, constitution or human-rights texts translated into Gojri, NGO, UN or government material in Gojri, school textbooks as text, folk tales, poetry and song sites.
B. Datasets and corpora that include Gojri: Hugging Face, Kaggle, GitHub, Zenodo, OPUS, Tatoeba, Mozilla Data Collective, web-crawl sets (GlotCC, FineWeb2, MADLAD-400, OSCAR, CulturaX, Glot500; check if codes such as gju, gju_Arab or gju_Deva exist), language archives (ELAR, PARADISEC, SIL, LDC, ELRA, TDIL-DC, LDC-IL, CIIL Mysore, Bhashini).
C. Books and magazines as PDF or scan (list only): title, author, year, URL, page count. Say if the PDF has a text layer, and if the text is real Unicode or garbled.
D. Audio or video with transcripts or subtitles (radio, TV, YouTube channels, Bible audio, Global Recordings Network): list only.
E. Papers, theses and reports on Gojri language technology or spelling. They often name corpora.

HOW TO SEARCH
- Search in English (Gojri, Gujari, Gujjari, "Gojri corpus", "Gojri dataset", "Gojri Bible", "Gojri text"), in Urdu (گوجری، گوجری زبان، گوجری کتاب، گوجری ادب، گوجری شاعری، گوجری لوک کہانی), in Hindi (गोजरी, गुजरी भाषा) and in Roman letters.
- Check at least: webonary.org, bible.com, ebible.org, Scripture Earth, globalrecordings.net, Wikimedia Incubator, archive.org, HathiTrust, Google Books, Academia, Hugging Face datasets search ("gojri", "gujari", "gju"), GitHub, Kaggle, OPUS, JKAACL (J&K Academy of Art, Culture and Languages), university repositories in India and Pakistan.
- Follow the references of every paper you find.

RULES
- Research only. Do not download whole books, datasets or sites. For each source, take at most one small sample (50 lines or 1 page, under 5 MB) only to check the language, script and encoding.
- Obey robots.txt, site terms and rate limits. No logins. No account creation. No paywall or CAPTCHA bypass. No scraping at scale.
- Never send our files or any personal data to any site.
- Never invent anything. Every row needs a URL that you really opened. If you saw only a search snippet, write "snippet only".
- Check the language: is it Gojri, or Urdu, Punjabi, Hindko, Pahari or Gujarati? Evidence can be the marker letters ݨ ݩ ڵ, typical Gojri words in the sample, or a clear statement by the source. If you cannot tell, write "unsure". Do not guess.
- Write the license or terms exactly (quote the short phrase and give the URL). If none is stated, write "no license stated, assume all rights reserved". Our project is non-commercial, so CC BY-NC is acceptable. Say whether redistribution is allowed.
- For every priority 1 source, give the maintainer or contact page so we can ask for permission.
- If you find a clean source of more than 100,000 words, stop and report it at once.

OUTPUT
Make one folder named gojri-corpus-search with:
1. sources.tsv with these columns: id, title, type (A to E), url, script, language-evidence, size (number and unit: words, pages, lines or hours), format (HTML, PDF with Unicode text, PDF with garbled text, scanned image, audio, video), spacing quality of the sample (good, doubtful, none), license or terms, redistribution allowed (yes, no, unknown), already-have (yes, no, maybe), access (open, login, paywall), priority (1 to 3), notes.
   Priority 1 = real Unicode Gojri text of 10,000 words or more, with a usable license or a clear way to ask permission. Priority 2 = smaller, or license unclear. Priority 3 = needs OCR, or has no text.
2. report.md with: the top 10 sources (one short paragraph each), the dead ends, the gaps you could not fill, and the list of search queries you used.
3. samples/ with the small text samples, one file per source, named by id.
Use short, plain sentences. Do not use em dashes.
```

After the agent returns: check the language and the spacing of every sample, check every license, and download nothing large without the speaker's yes.
