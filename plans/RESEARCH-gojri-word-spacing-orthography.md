# Research: how to divide words when we label printed Gojri (print spacing or language rules)

Date: 2026-11-16. Scope: whether a published Gojri rule for word division exists, what Urdu and other Perso-Arabic languages do, what NLP corpora do with unreliable spaces, and which labeling rule we should use for the Kahawat-Kosh lines. This note continues `plans/RESEARCH-nastaliq-word-spacing.md`.

## Summary

- No published Gojri rule for word division exists in the sources I could open. I found no guide from SIL, FLI, a J&K body, Gojri Adabi Sangam, Dr Javaid Rahi or Common Voice that says how to space Gojri words. [S1, S2, S4]
- The only deep orthography study is Losey 2002 (SIL). It sets rules for letters, tone and affixes. From the parts I could read, it also treats postpositions as separate words in its examples and argues against joining the dative /na/ to a pronoun. I could not read its full text, so this is partly unverified. [S2]
- Losey says that Gojri writers write "phonetically, and with wildly varying degrees of reference to the conventions of Urdu". So the best proxy for a Gojri word rule is the Urdu rule. [S2]
- Urdu has no single official word-division rule either. But Urdu NLP research gives a clear working rule: a space marks a word, and an invisible joiner stop (ZWNJ) marks a break inside one word. Postpositions (ka, ko, se, ne) and helping verbs are separate words. [S7, S8]
- Urdu, Shahmukhi and Sindhi sources agree on one fact. A space in Nastaliq text is often a typing tool for letter shape. It is not always a word mark. Hand-written Urdu has no word spaces. [S7, S8, S10, S11]
- NLP corpora in this script family do one of two things. They normalize to one linguistic spacing, or they only collapse repeated spaces. I found no corpus that stores both a print field and a linguistic field. [S8, S15, S16]
- Recommendation: option C. Store both fields. Use the print field to train the line reader. Use the linguistic field to train and test the space model. The user marks word boundaries with 8 simple rules (below).
- Gaps: I could not open the Losey PDF, the Persian Academy text, the NLPD Urdu spelling rules, or any Gojri dictionary page on Webonary. I found nothing on pnb Wikipedia style, Pakistan Punjabi Adabi Board, Saraiki or Pashto word division.

## How to read the verification tags

- Read: I opened the text and read the cited passage.
- Fetched: a fetch tool gave me a summary of the page. I did not see the raw text. Quotes marked this way are relayed by the tool.
- Snippet: I saw the claim only in a search result summary. Treat it as unverified.
- Not opened: the source blocked me (HTTP 403 or 404). I list it so you can look.

Every source has a number. The Sources list at the end gives the URL and the tag. Sources marked "own count" are results of my own simple scripts on files in this repo.

---

## Q1. Is there a published Gojri rule for word division?

### Short answer

No. I found no document that tells a Gojri writer where to put spaces. The most relevant work is the Losey thesis. It does not appear to give a general word-division rule.

### What exists

- **Losey 2002, "Writing Gojri: Linguistic and sociolinguistic constraints on a standardized orthography for the Gujars of South Asia"** (SIL Work Papers vol. 46; also a University of North Dakota MA thesis). The abstract says it evaluates the spelling conventions of prominent writers and institutions, proposes Urdu-based spellings, and treats tone at length. [S1, Fetched]
  - It says: "Writers and editors tend to write phonetically, and with wildly varying degrees of reference to the conventions of Urdu" (abstract, page xvi). [S2, Fetched]
  - It says Gujar writers "almost always use the original spellings" for Urdu loan words (section 2.6.1, page 70) and that Gojri consonants "may be readily represented as per the representation of the equivalent consonants in Urdu" (page 69). [S2, Fetched]
  - It sets two spelling principles: "consistent representation of morphological affixes" and fixed "word-images" based on the isolation form (sections 5.2.2 and 5.3.1, pages 207 to 210). It also says "maintenance of word shape is primary and tone marking is secondary" (section 5.3.8, page 223). [S2, Fetched]
  - On the dative /na/ with pronouns, it argues against joining: "joining complicates the literacy task without contributing any corresponding benefit" (section 5.3.7, pages 218 to 219). It also says that Western contracted dative and agentive forms "can be written as fused according to their pronunciations", and that "intervening words are not allowed" between the fused form and the postposition (section 5.3.7, page 237). [S2, Fetched]
  - On negation, it says the Gojri negatives /na2/ and /na/ "are both written with the Urdu spelling" (section 5.3.6, page 214). It gives no spacing statement for them in what I saw. [S2, Fetched]
  - In its grammar part, it shows a postposition as a separate word "wherever the shape of both morphemes remains unaltered by intervening words" (section 4.1.4, page 129). It lists auxiliaries as separate verb elements that stand to the right of the main verb (section 4.2.1.1, pages 158 to 160) and says Gojri conjunct verbs "are lexicalized" (section 4.2.1.6). [S2, Fetched]
  - Important limit: these are grammar and spelling statements. The summaries I saw do not show a section called "word division". A fuller read could still find one. I could not open the PDF (HTTP 403) and I did not read the whole 443,000 character text. [S3, Not opened]
- **FLI workshop report (Muzaffarabad, December 2025 to January 2026).** It says only that "further work is needed to standardize its orthography". It gives no spelling or spacing rule. [S4, Fetched]
- **FLI Gojri dictionary on Webonary.** I could not open it (HTTP 403). A search summary says the dictionary has no standardization consensus and follows general Urdu or English spelling for sorting. I could not check how it spaces headwords, compounds or postpositions. [S5, Not opened and Snippet]
- **Mozilla Data Collective "Gojri Literature Corpus" page (FLI text).** It says only that cleaning included "Unicode normalization" and "Whitespace and punctuation cleanup". It gives no rule for word spacing. [S23, Fetched]
- **BGSBU Rajouri writers' meeting.** A search summary says writers asked for a standard script and orthography. I could not confirm the date or the text, and the fetch showed no Gojri text. [S6, Snippet]
- **Gojri Linguistics overview (Academia).** A search summary says it cites Losey and mentions an October 2023 workshop on Gojri orthography. I did not open it. [S32, Snippet]
- **Grierson, Linguistic Survey of India vol. IX part IV (Pahari and Gujuri, 1916).** It contains Gujuri material. The review page is behind a paywall. I could not check what it says on postpositions or word division. Old surveys usually write words as the speakers say them, so they are not a spacing guide for modern print. [S24, Snippet]
- **Common Voice Gujari sentence rules, a Gojri Wikipedia project, a Gojri Unicode keyboard guide, J&K Academy of Art, Culture and Languages style notes, Gojri Adabi Sangam style notes, and Dr Javaid Rahi's writing on orthography.** I searched in English and Urdu. I found nothing for any of these. This is "not found", not "does not exist". The Common Voice rules I saw are general (no punctuation read aloud, normalize symbols). They have no Gojri spacing rule. [S22, Snippet]
- **Hindi or Devanagari sources.** My search found nothing on Gojri word division in Devanagari. I did not search in Devanagari script itself. This is a gap.

### Own count in the FLI text we hold

I counted spacing variants in `datasets/Gojri Language Corpus/` (60,814 tokens). The method is a simple string count, so it may count some unrelated matches. [S30, own count]

- Only 8 ZWNJ characters (U+200C) occur in 336,388 characters. They look accidental (five in a row after one word, two inside one word). The FLI text does not use ZWNJ as a method.
- The same unit appears joined and separate: `کر کے` 7 times against `کرکے` 3 times; `اس کو` 6 times against `اسکو` once. `اس نے` appears 10 times and `اسنے` never.
- So even inside one curated Gojri corpus, the spacing is mostly separate but not fixed.

---

## Q2. How do related languages decide word division in Perso-Arabic script?

### Urdu

- **There is no one official rule in the sources I could open.** Dawn (Rauf Parekh, 20 January 2025) says that standardisation of Urdu orthography "still remains elusive". It names Rasheed Hasan Khan's *Urdu Imla* (1974), the Urdu Dictionary Board, and NLPD seminars of 1985 and 2022. It does not discuss word division. [S21, Fetched]
- **I could not read the NLPD or Rasheed Hasan Khan text.** A search summary says Khan's book advises joining some prefix forms such as بلکہ and کیونکہ, and that کا، کی، کو، سے are written separate. I did not open the book. [S25, Snippet]
- **Hand-written Urdu has no word spaces.** Durrani (2007): "The notion of space between words is completely alien in Urdu hand-writing." Children "just tacitly use" join rules and "the human lexicon". The thesis shows a Nastaliq sample in which a non-Urdu reader cannot find the word boundaries. [S7, Read, section 2.6.3, page 21]
- **Why a space exists in print.** Space is "only inserted in printed texts to avoid joining between two words because there is no other way out". It also appears inside single words (affixes, compounds, proper nouns) "to achieve that visual impact". Users who do not want a visible gap use ZWNJ. [S7, Read, sections 3 and 3.2] The same facts appear in later papers. [S8, Read, section 4] [S10, Read] [S11, Read]
- **Space omission and space insertion.** After a non-joining letter (ا د ڈ ذ ر ز و ے and others) the next word looks right with no space, so writers omit it. After a joining letter, writers may add a space inside a word to keep its parts apart. [S8, Read, sections 4.1 and 4.2] [S7, Read, section 3.1.1]
- **The accepted working rule in Urdu NLP.** Zia, Raza and Athar (COLING 2018) annotated about 111,000 tokens. They put a space after each word and a ZWNJ at a break inside a word. The rules (from Rehman et al., 2011, as cited) place ZWNJ in X-Y compounds, X-e-Y compounds, X-o-Y compounds, reduplication, prefix plus root, root plus suffix, and multi-part transliterations. Two native annotators agreed at Cohen's kappa 0.98 on 100 sentences. [S8, Read, section 5.1] I did not find or open the Rehman et al. source itself.
- **Postpositions, helping verbs and similar items (Durrani 2007).** Both joined and separate forms occur in the corpus for oblique pronoun plus postposition, possessive pronouns, adverbial phrases, compound postpositions and helping verbs. Durrani decides each case with a replacement test. If a proper noun can replace only the pronoun (not the pronoun plus postposition), the postposition is a separate word. By that test he treats the following as two words: oblique pronoun plus ko/ka/se, possessive pronoun forms, adverbial phrases, and compound postpositions such as "ki taraf". He also separates a helping verb from the main verb, because "Separating these into two words is more helpful in syntactic and semantic analysis". [S7, Read, sections 3.1.2.1 to 3.1.2.5, pages 24 to 26]
- **Language rule or typography?** Durrani and Zia mix both. What counts as a word (postposition, helping verb) is a language decision, made by tests and agreed among annotators. Whether a visible gap shows up in print is a typography effect of letter joining. [S7, S8]

### Shahmukhi Punjabi

- **Same problem as Urdu.** Lehal and Saini (COLING 2012) state: "Like Urdu, Shahmukhi is written in Nastalique style. Due to Nastalique style and irregular use of space, Shahmukhi word segmentation has both space omission and space insertion problems." They add that the space inside a word is mostly a tool to control letter shape. [S10, Read]
- **Gurmukhi differs.** A search summary says Gurmukhi uses spaces between words. A Universal Dependencies note for Punjabi (Gurmukhi) says clitic postpositions that are written merged are split into separate tokens and tagged as adpositions. This is an annotation choice in Gurmukhi, not a Shahmukhi rule. [S26, Snippet]
- **No Shahmukhi orthography decision found.** I searched for the Pakistan Punjabi Adabi Board and for Punjabi Wikipedia (pnb) style rules. I found neither. This is "not found".

### Sindhi

- Ali et al. describe the same two problems for Sindhi: writers omit a hard space after non-joiner letters, and the word shape stays the same. [S11, Read] I found no Sindhi spelling-board rule on word division.

### Saraiki

- Richard Ishida's Saraiki page says only "Words are separated by spaces". It has nothing on postpositions or clitics. I found no Saraiki-specific rule. [S14, Fetched]

### Kashmiri

- Ishida's Kashmiri page says: "It is common for single lexical items to be split in Kashmiri." A palatalisation swash form can be made "by a space or 200C", with examples written both ways. The word-boundaries section is marked "tbd". So a space inside a Kashmiri word is a known typing method. [S13, Fetched]
- KS-LIT-3M and KS-PRET-5M are covered in Q3.

### Pashto

- A search summary lists two main standards (Academy of Sciences of Afghanistan and Pashto Academy Peshawar), plus variants. I found no statement on word spacing. I did not open the papers. [S27, Snippet]

### Persian

- Persian uses a space between words and ZWNJ (half-space) inside a word, for example after the verb prefix می and before the plural ها. Ebrahimkhani and Ansari (PerSpaCor, RANLP 2025) say modern Persian typography uses spaces to separate words and ZWNJ to prevent letters from joining, for example in a verb with a prefix. [S18, Read, introduction only] A search summary of the Ubuntu Persian team rules gives the same pattern (می‌خواهم). [S20, Snippet]
- **I could not read the Academy of Persian Language and Literature rule text** (دستور خط فارسی). A 2024 article in Nāme-ye Farhangestān (Shabani) says Persian writing sources explain half-space poorly and aims for a uniform style sheet. It reports half-space is used in all word classes, most in adjectives and nouns. This is research, not a rule. [S19, Fetched] So I cannot say which exact items the Academy requires.
- **Value for us.** Persian shows one clear design: the language has a rule for "one word", and a typing method (ZWNJ) that shows the break in shape without a word gap.

### Summary table

| Language | Rule found | Word mark | Break inside a word | Source quality |
|---|---|---|---|---|
| Urdu | Working rule in NLP (no official rule found) | space | ZWNJ | Read |
| Shahmukhi | Problem described, no rule | space (irregular) | space used as a shape tool | Read |
| Sindhi | Problem described, no rule | space (often omitted) | not stated | Read |
| Kashmiri | Typing note | space | space or ZWNJ | Fetched |
| Saraiki | None | space | none | Fetched |
| Pashto | None found | none found | none found | Snippet |
| Persian | Practice described, Academy text not read | space | ZWNJ | Read (intro) and Fetched |
| Gojri | None found | none found | none found | see Q1 |

---

## Q3. What do NLP corpora do when the source spacing is unreliable?

- **Urdu word segmentation (Zia et al. 2018).** They normalize the text to one linguistic standard: one space per word and ZWNJ for sub-word breaks, by documented rules and a measured agreement (kappa 0.98). The model then learns to restore both marks. They also removed diacritics and multiple spaces. [S8, Read, section 5.1]
- **Urdu OCR (Akram and Hussain 2010).** They note that scanned text has no visible space and that space use in Urdu is mainly a shape tool. They treat segmentation as a separate step after recognition. [S12, Read, introduction only]
- **Urdu tafseer text from InPage (Hassan, WNUT 2026).** The source text has fused words. The paper restores spaces with a confidence-gated step that only inserts spaces, and checks that no letter changed. An ungated splitter had 30.5 percent precision. The paper does not store a second print field, but it keeps the original text and edits only spaces. [S17, Read, abstract and method]
- **Kashmiri KS-LIT-3M (Malik).** The pipeline normalizes to NFC and sets "single spaces between words, standardized line termination, and uniform paragraph boundaries". It collapses extra spaces. It makes no linguistic word decision, and it does not store the original spacing. [S15, Read, preprocessing section]
- **Kashmiri KS-PRET-5M.** It collapses repeated spaces and tabs. [S16, Read, preprocessing lines]
- **FLI Gojri corpus.** Cleaning included "Whitespace and punctuation cleanup". The method is not described. [S23, Fetched]
- **Common Voice.** The general advice I saw is to normalize text and remove symbols that nobody speaks. I found no Gojri guide. [S22, Snippet]
- **Result.** For Perso-Arabic text, the research that deals with spacing chooses linguistic spacing, with a written rule and a measured annotator agreement. The corpus builders only collapse blanks. I found no source that says to copy visual gaps from print. I also found no source for "store both". Option C is my own design, based on the fact that the print gap and the word are different things (S7, S8).
- **Not verified:** whether UrduHack, UMC or CLE corpora store spacing in a special way. I did not open those sources.

---

## Q4. Gojri specific hazards

What published sources say, and what I could not check.

- **Postpositions and the dative /na/.** Losey separates postpositions in his examples and argues against joining dative /na/ to the pronoun for literacy reasons. He also allows a fused spelling for Western contracted forms when the sound changes and no word can stand between. So Gojri has both separate postpositions and some real fused pronoun forms. [S2, Fetched]
- **Same hazard in Urdu.** Oblique pronoun plus ko/ka/se is written joined and separate, and some linguists treat the joined form as one word. Durrani chooses separate. [S7, Read, section 3.1.2.1]
- **Helping verbs and compound verbs.** Gojri relies "heavily on various verbal auxiliaries"; the auxiliary is the right-most element. Conjunct verbs (noun plus verb) are fixed units that must be memorized. Losey does not say how to space them. Durrani separates helping verbs in Urdu. [S2, Fetched] [S7, Read]
- **Conjunctive /kE/ (کے or کر کے).** One Losey passage argues against analysing /kE/ as a suffix, which suggests it is a separate word. I saw only a fragment. Our FLI count shows both `کر کے` (7) and `کرکے` (3). [S2, Fetched] [S30, own count]
- **Request particle /da~/.** Losey treats it as a separate particle (section 4.2.1.2.1, page 152). [S2, Fetched]
- **Negation (نہ، نا، نہیں).** Losey says the spelling follows Urdu. No source I saw gives a spacing rule. I found no source on joined or separate negation, in Urdu or in Gojri.
- **Enclitic-like words (وی، ہی، بھی، ناں, تیں, تے).** I found no source that says whether these are separate words or clitics in Gojri print. Losey's grammar uses /te/ as an ablative postposition, so by his analysis تے is a separate postposition. The use of تے as a joined ending in a proverb (see Q5) is not covered by any source. In the FLI corpus `ناں` (77), `تیں` (364), `وی` (31) and `ہی` (125) all appear as separate tokens. I did not measure how often they appear joined. [S2, Fetched] [S30, own count]
- **Words written two ways.** Losey says writers vary widely. The only variants I measured are in the FLI corpus (Q1). [S2, Fetched] [S30, own count]
- **Spaces that come from InPage.** In our own tests the Noori PDF text has no space glyph, and printed letter gaps (3 to 4 px) overlap with word gaps (5 to 12 px). So print gaps cannot decide a word. [S29, Read, and `LOG.md` 2026-11-15, as quoted in the CLAUDE.md status text]
- **If a rule exists in Dr Javaid Rahi's books or in FLI dictionary notes, I did not find it.**

---

## Q5. Recommendation

### The three options

| Option | What it means | Good | Bad |
|---|---|---|---|
| A | Label with linguistic spacing only | Matches published NLP practice for Urdu (S7, S8). Gives a stable target for a language model and for ASR text. Needs a short rule list. | The label no longer matches the image. A line reader trained on A learns to guess spaces the print does not show. The Gojri rule list is our own design. |
| B | Copy the visual spacing from the print | Easy to audit against the image. Matches our rule "labels match the print" for letters. | Print gaps are unreliable in Nastaliq (S7, S10, S11). A and B would disagree on many words. Errors from print typing go into the corpus. |
| C | Store both fields; train the space model on the linguistic one | Keeps the print as evidence and gives a clean text for the space model and the LLM. Lets us measure how often print and language disagree. | More work per line. Two fields can drift apart if nobody checks them. |

My recommendation is C. It also fits your earlier ruling that letters follow the print. The rule: letters are always print-faithful in both fields. Only spaces differ.

- `print_text`: letters exactly as the print shows. A space only where a person sees a clear word gap. Do not add spaces the eye cannot see.
- `word_text`: the same letters, with one space at every word boundary by the 8 rules below. Never change a letter in this field (the same character-preservation check as S17).
- Train the line reader on `print_text`. Train and score the space model on `word_text`. Report word error twice, once on each field.
- Keep a `note` flag on lines where the user is unsure. Do not guess on those.

The cause of the problem is the script and typesetting, not the OCR model. This is the same finding as in `plans/RESEARCH-nastaliq-word-spacing.md`. [S29, Read]

### Labeling rules (for 200 lines, 30 to 40 minutes)

This is about 10 seconds per line. So the rule list stays short, and the tool should pre-fill `word_text` from the OCR line. The user only fixes boundaries.

Source tags: [Src] means a source supports the rule in Urdu or Gojri. [Mine] means it is my suggestion and the user must confirm.

1. **A word is a unit you can say alone and put another word inside only at its edges.** Test: if a different word can sit between two parts, they are two words. If no word can sit between them, and the sound changes when they join, they are one word. [Src: Durrani replacement test, S7; Losey "no intervening words", S2] [Mine: using it as the daily test]
2. **Postpositions and case words are separate words.** Examples to check in the print: کو، تے، تیں، نے، سے, کا/کے/کی, ناں (dative). [Src for Urdu: S7; Gojri support: Losey examples and dative argument, S2] [Mine: the full Gojri list]
3. **Exception: a real fused pronoun form is one word.** Use it only if the user knows it as one spoken word whose shape changed (Losey's Western contracted forms). Mark it with a note. [Src: Losey section 5.3.7, S2] [Mine: the note flag]
4. **Helping verbs and the verb being helped are separate words.** This covers ہے، تھو، تھی, ہو and a verb plus دینا/لینا/جانا. A noun plus verb conjunct verb is also two words. [Src: Durrani for Urdu, S7; Losey describes auxiliaries as separate right-most elements, S2] [Mine: applying it to Gojri conjunct verbs]
5. **The conjunctive کے or کر کے is separate from the verb.** Write `کر کے`, not `کرکے`. [Src: Losey argues /kE/ is not a suffix, S2 (fragment only)] [Mine: the exact choice]
6. **Negation words (نہ، نا، نہیں) are separate words.** [Mine; no Gojri source]
7. **Emphatic and linking small words (وی، ہی، بھی) are separate words, unless the user knows the speaker cannot pause before them.** If unsure, mark with the note flag. [Mine; no source covers this]
8. **Prefixes and suffixes that build one word are joined (for example بے-, نا-, -پن, -وار types).** If the print shows a gap inside such a word, `print_text` keeps the gap and `word_text` joins it. Do not use ZWNJ in `word_text`. [Src: Urdu uses ZWNJ for prefix and suffix breaks, S8; the Gojri affix list and the choice to join and not use ZWNJ are Mine]

Extra rules for both fields:

- Never change a letter when you fix a space. [Src: S17 invariant]
- One space only. No double spaces. No space before or after the Urdu full stop or a bracket unless the print shows one. [Mine]
- Do not use ZWNJ in labels. Our FLI text and the print have almost none. [S30, own count] [Mine]

### Idiom examples (Kahawat-Kosh style)

I am not a Gojri speaker. Check each of these yourself.

| Print form | Parts by rule | Rule | Check |
|---|---|---|---|
| آپ بھلاتے جگ بھلو | آپ / بھلا / تے / جگ / بھلو | 2 (if تے is the postposition or linking word "from, then") or 4 | Is `بھلاتے` one word in speech, or `بھلا` plus `تے`? This is the main test case. |
| یا آپ چنگاتے جگ چنگو | یا / آپ / چنگا / تے / جگ / چنگو | same | Same question for `چنگاتے`. |
| جگ بھلو | جگ / بھلو | 1 | A noun and its predicate adjective are two words. |

If the user decides `بھلاتے` is one word (for example, as a fixed adverbial form), rule 3 applies: keep it joined and add a note. Then the spelling of every `-تے` form in the book follows that decision. Ask this first, and decide the rest from it.

### Cost and safety notes

- Use the existing "no letter change" check in the tool. Reject any edit that changes a letter. [S17]
- Do not use an LLM to place spaces without that check. The WNUT paper shows an ungated function-word splitter at 30.5 percent precision. [S17]
- Inter-annotator check: Zia et al. measured kappa on 100 sentences. We have one annotator. Re-label 20 of the 200 lines a week later and count disagreements. [Mine, based on S8]

---

## Open questions

1. Does a Losey passage give a rule for how to space Gojri words? I could not read the full text. Someone should read sections 5.2 to 5.3 and chapter 3.2.2 in the PDF. [S3]
2. Is `بھلاتے` one word or two in Gojri? It decides how every `-تے` ending is labeled. Only the user can answer this.
3. Which of وی، ہی، ناں, تیں, تے are clitics (cannot stand alone) and which are free words? No source answers this.
4. How does the FLI Webonary dictionary space compounds, postpositions and multi-word headwords? I could not open it. It may be the best Gojri evidence.
5. Does Dr Javaid Rahi (or his co-editors) state a spacing policy in the introduction of any book? His books are in our PDF set. A search of the introduction pages is a short job.
6. What do the Academy of Persian Language and Literature and NLPD rules say about each affix? I read neither. Do not treat my Persian and Urdu summary as the rule text.
7. Do Gojri print books of different years use the same spacing? The Kahawat text shows run-together words. The dictionary, which has a different font family, may differ. Check on 20 lines each.
8. Is a single linguistic standard good enough for ASR text? Common Voice normalizes text for speech. The Gojri sentence guide, if one exists, may add spacing rules. I found none.

---

## Sources

| ID | Source | URL | Tag |
|---|---|---|---|
| S1 | Losey, "Writing Gojri: Linguistic and sociolinguistic constraints on a standardized orthography for the Gujars of South Asia", SIL Work Papers vol. 46 art. 3 (2002), abstract page | https://commons.und.edu/sil-work-papers/vol46/iss1/3 | Fetched |
| S2 | Losey 2002, full text via a Yumpu copy (title: "Writing Gojri - Forum for Language Initiatives"); I read tool summaries of the 443,000 character text, not the raw text | https://www.yumpu.com/en/document/view/18976161/writing-gojri-forum-for-language-initiatives | Fetched |
| S3 | Losey 2002 PDF at UND, CORE copy, SIL archive record 66625 | https://commons.und.edu/cgi/viewcontent.cgi?article=1376&context=sil-work-papers ; https://core.ac.uk/download/pdf/235075132.pdf ; https://www.sil.org/resources/archives/66625 | Not opened (HTTP 403 on all three) |
| S4 | FLI, capacity building workshop for Gojri curriculum developers in Muzaffarabad | https://fli-online.org/capacity-building-workshop-for-gojri-language-curriculum-developers-in-muzaffarabad/ | Fetched |
| S5 | Webonary Gojri dictionary, "Scheme of presentation" and alphabet overview | https://www.webonary.work/gojri/en/?p=146827 ; https://www.webonary.work/gojri/en/overview/alphabet/ | Not opened (HTTP 403); claim seen as Snippet |
| S6 | Daily Excelsior, "Gojri writers adopt 5-point resolution at BGSBU meet" | https://www.dailyexcelsior.com/?p=1624136 | Snippet (fetch showed no Gojri text) |
| S7 | Durrani, "Typology of Word and Automatic Word Segmentation in Urdu Text Corpus", MS thesis, FAST-NUCES Lahore, 2007 (sections 2.1.1, 2.6.3, 3, 3.1.2, 3.2) | https://www.cle.org.pk/Publication/theses/2007/typology_of_word.pdf | Read |
| S8 | Zia, Raza, Athar, "Urdu Word Segmentation using Conditional Random Fields (CRFs)", COLING 2018, arXiv 1806.05432 (sections 4, 5.1) | https://arxiv.org/pdf/1806.05432 | Read |
| S9 | Durrani and Hussain, "Urdu Word Segmentation", NAACL 2010 (cited in S8, S10) | https://aclanthology.org/N10-1077.pdf | Snippet |
| S10 | Lehal and Saini, "Conversion between Scripts of Punjabi: Beyond Simple Transliteration", COLING 2012 posters (word boundary passage) | https://aclanthology.org/C12-2062.pdf | Read (that passage only) |
| S11 | Ali et al., "Enhancing Sindhi Word Segmentation using Subword Representation Learning and Position-aware Self-attention", arXiv 2012.15079 | https://arxiv.org/pdf/2012.15079 | Read (abstract and sections 1 and 3) |
| S12 | Akram and Hussain, "Word Segmentation for Urdu OCR System", 2010 | https://aclanthology.org/W10-3212.pdf | Read (introduction only) |
| S13 | Ishida, Kashmiri script notes (r12a) | https://r12a.github.io/scripts/arab/ks | Fetched |
| S14 | Ishida, Saraiki and Urdu script notes (r12a) | https://r12a.github.io/scripts/arab/skr ; https://r12a.github.io/scripts/arab/ur | Fetched |
| S15 | Malik, "KS-LIT-3M", arXiv 2601.01091 (preprocessing) | https://arxiv.org/pdf/2601.01091 | Read (preprocessing section) |
| S16 | Malik and Nissar, "KS-PRET-5M", arXiv 2604.11066 | https://arxiv.org/pdf/2604.11066 | Read (preprocessing lines) |
| S17 | Hassan, "A Precision-First Whitespace Restoration Pipeline for Noisy Urdu Tafseer Text", WNUT 2026 | https://aclanthology.org/2026.wnut-1.1.pdf | Read (abstract, introduction, method) |
| S18 | Ebrahimkhani and Ansari, "PerSpaCor", RANLP 2025 | https://aclanthology.org/2025.ranlp-1.40.pdf | Read (introduction only) |
| S19 | Shabani, "نگاهی به نیم‌فاصله از دریچهٔ دستور زبان و نگارش", Nāme-ye Farhangestān (abstract page) | https://nf.apll.ir/article_196773.html | Fetched |
| S20 | Ubuntu Persian Translation Team rules | https://wiki.ubuntu.com/PersianTranslationTeam/TeamRules | Snippet |
| S21 | Parekh, "Orthographic issues in Urdu and solutions", Dawn, 20 January 2025 | https://www.dawn.com/news/1886473 | Fetched |
| S22 | Common Voice discourse threads and sentence tools on normalization | https://discourse.mozilla.org/t/spoken-text-normalisation/44433 | Snippet |
| S23 | Mozilla Data Collective, "Gojri Literature Corpus" (FLI) | https://mozilladatacollective.com/datasets/cmlgz1vdt001omg07rv25gwnu | Fetched |
| S24 | Grierson, Linguistic Survey of India vol. IX part IV, Pahari and Gujuri (review page) | https://www.cambridge.org/core/journals/journal-of-the-royal-asiatic-society/article/linguistic-sukvey-of-india-vol-ix-part-iv-pahari-and-gujuri-edited-by-sirgeorge-grierson-kcie/518179E3A4BE087F60BDD3224E2941F4 | Snippet |
| S25 | Rasheed Hasan Khan, *Urdu Imla* (1974), Rekhta e-book record | https://www.rekhta.org/ebooks/detail/urdu-imla-rasheed-hasan-khan-ebooks | Snippet (not opened) |
| S26 | Universal Dependencies, Punjabi guidelines | https://universaldependencies.org/pa/index.html | Snippet |
| S27 | Pashto orthography studies (Palatana journal; Pashto Standard Orthography and Bara Gali Decisions) | https://journals.uom.edu.pk/palatana/article/view/492 ; https://pashto.org.pk/index.php/path/article/view/424 | Snippet (not opened) |
| S28 | Cahill, effective orthographies (SIL; word breaks listed as an orthography part) | https://orthographyclearinghouse.org/papers/cahillEffectiveOrthographies.pdf | Snippet |
| S29 | Project note `plans/RESEARCH-nastaliq-word-spacing.md` and `LOG.md` entries for 2026-11-15 | D:\Code\VSCodeProjects\gojri-ai\plans\RESEARCH-nastaliq-word-spacing.md | Read (first 40 lines, source table and open questions); LOG.md only through the CLAUDE.md summary |
| S30 | Own count on the 11 FLI files in `datasets/Gojri Language Corpus/` (ZWNJ count; joined and separate pairs; token frequencies) | local files | Own count (simple string search, may include unrelated matches) |
| S32 | "Gojri Linguistics: An Overview" (Academia) | https://www.academia.edu/119107335/Gojri_Linguistics_An_Overview | Snippet (not opened) |

Not found, searched in English and Urdu: Gojri Wikipedia project style rules, Gojri Unicode keyboard guide, Common Voice Gujari sentence rules, J&K Academy of Art, Culture and Languages style notes, Gojri Adabi Sangam style notes, Dr Javaid Rahi writing on orthography, Pakistan Punjabi Adabi Board decisions, Punjabi Wikipedia (pnb) style rules, Academy of Persian Language and Literature rule text, NLPD Urdu spelling rules text.
