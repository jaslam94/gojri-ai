# *گوجری* &mdash; Gujari (`gju`)

This datasheet is for cv-corpus-26.0-2026-06-12 of the Mozilla Common Voice *Scripted Speech* dataset for Gujari [گوجری - `gju`]. The dataset contains 11741 clips representing 10.67 hours of recorded speech (10.07 hours validated) from 7 speakers, recorded from a text corpus of 3,854 sentences.

## Language

Gojri is an Indo-Aryan language spoken by the Gujjar community in various parts of South Asia, particularly in: Regions 1. Jammu and Kashmir: Gojri is widely spoken in the Jammu region. 2. India: Many Gujjar communities in Himachal Pradesh, Rajasthan,  Gujarat  and in many other states speak Gojri. 3. Pakistan: Gojri is also spoken in all provinces of Pakistan including AJK, and GB 4. Afghanistan: Gojri is also spoken in Afghanistan, particularly in Kunar province.  Characteristics 1. Similarities with other languages: Gojri shares similarities with other Indo-Aryan languages, such as Punjabi, Urdu, and Hindi, Nepali,  Gojrati etc. 2. Unique vocabulary: Gojri has its own distinct vocabulary and expressions, reflecting the culture and traditions of the Gujjar community. Writing system  Gojri has its own writing system, and books have been written in various literary genres, including: Gojri Writing System and Literature 1. Perso-Arabic script: Gojri is often written in a modified Perso-Arabic script. 2. Literary works: Books, poetry, and other literary works have been written in Gojri, showcasing the language's rich cultural heritage. 3. Translation of the Holy Quran: The Quran has been translated into Gojri, making it accessible to the Gujjar community. 4. Cultural Expression: Gojri music, songs, films, dramas, radio programs and cultural events showcase the language's richness and the community's heritage. Gojri is a vital part of the Gujjar community's linguistic and cultural diversity.

## Demographic information

The dataset includes the following self-declared age and gender distributions. A coverage summary is shown below each table.

### Gender

Self-declared gender information. The table shows clip and speaker counts with percentages. Speakers who did not declare a gender are listed as Unspecified. A dash (-) indicates zero.

| Code | Gender | Clips | Speakers |
|---|---|---|---|
| male_masculine | Male, masculine | - | - |
| female_feminine | Female, feminine | - | - |
| transgender | Transgender | - | - |
| non-binary | Non-binary | - | - |
| do_not_wish_to_say | Prefer not to say | - | - |
| - | Unspecified | 11,741 (100.0%) | 7 (100.0%) |

*Gender declared: 0 of 11,741 clips (0.0%), 0 of 7 speakers (0.0%)*

### Age

Self-declared age information. The table shows clip and speaker counts with percentages. Speakers who did not declare an age are listed as Unspecified. A dash (-) indicates zero.

| Code | Age | Clips | Speakers |
|---|---|---|---|
| teens | Teens | - | - |
| twenties | Twenties | 1 (0.0%) | 1 (14.3%) |
| thirties | Thirties | 134 (1.1%) | 1 (14.3%) |
| fourties | Fourties | 9,050 (77.1%) | 3 (42.9%) |
| fifties | Fifties | - | - |
| sixties | Sixties | - | - |
| seventies | Seventies | - | - |
| eighties | Eighties | - | - |
| nineties | Nineties | - | - |
| - | Unspecified | 2,556 (21.8%) | 4 (57.1%) |

*Age declared: 9,185 of 11,741 clips (78.2%), 3 of 7 speakers (42.9%)*

## Data splits for modelling

**Clip buckets**

| Bucket | Clips |
|---|---|
| Validated | 11,081 (94.4%) |
| Invalidated | 154 (1.3%) |
| Other | 506 (4.3%) |

**Training splits**

| Split | Clips |
|---|---|
| Train | 3,207 (28.9%) |
| Dev | - |
| Test | 623 (5.6%) |

*Training split coverage: 3,830 of 11,081 validated clips (34.6%)*

The dataset contains 11081 validated, 154 invalidated, and 506 unresolved clips. The average clip duration is 3.274 seconds.

## Text corpus

The text have been taken from Gojri story books, folk tales, Islamic studies and from course books.

**Validated sentences:** 3,852

| Category | Count |
|---|---|
| Unvalidated sentences | 2 |
| Pending sentences | 2 |
| Rejected sentences | - |
| Reported sentences | - |

The corpus contains 3,854 sentences: 3,852 validated and 2 unvalidated (2 pending review, 0 rejected), with 0 reported for review.

### Writing system

Perso-Arabic script

#### Symbol table

```ا آ ب بھ پ پھ ت تھ ٹ ٹھ ث ج جھ چ چھ ح خ د دھ  ڈ  ڈھ ذ ر ڑ ز ژ س ش ص ض ط ظ ع غ ف ق ک کھ گ گھ ل ل°  م  ن ن°  و ہ ی ے```

### Sample

There follows a randomly selected sample of five sentences from the corpus.

1. *رِچھ کھائے*
2. *اُت بلادری کا لوک بے پوہچ آیا*
3. *گل زادا رِچھ نے مُچ زیادہ زخمی کر لیو تھو*
4. *بَر کا سیزن ما یہ لوک جھیل سیف الملوک پو ہوئے*
5. *باد شاہ نے اعلان کر کے لوک بٹلا کیا*

### Sources

Islamic studies Gojri stories

| Source | Sentences |
|---|---|
| Short stories | 2,528 (65.6%) |
| self | 1,218 (31.6%) |
| مہارو دین | 105 (2.7%) |
| Other | 1 (0.0%) |

### Text domains

General

| Code | Domain | Clips | Speakers |
|---|---|---|---|
| general | General | 3 (0.0%) | 3 (42.9%) |
| agriculture_food | Agriculture and Food | - | - |
| automotive_transport | Automotive and Transport | - | - |
| finance | Finance | - | - |
| service_retail | Service and Retail | - | - |
| healthcare | Healthcare | - | - |
| history_law_government | History, Law and Government | - | - |
| media_entertainment | Media and Entertainment | - | - |
| nature_environment | Nature and Environment | - | - |
| news_current_affairs | News and Current Affairs | - | - |
| technology_robotics | Technology and Robotics | - | - |
| language_fundamentals | Language Fundamentals | - | - |

### Processing

Book were collected to create corpus.

### Recommended post-processing

There are two special characters in Gojri that must be used to create difference from Urdu, Punjabi, Pahari and Mewati.

### Fields

#### Clips

Each row of a `tsv` file represents a single audio clip, and contains the following information:

- `client_id` - hashed UUID of a given user
- `path` - relative path of the audio file
- `sentence` - the sentence to be read aloud
- `sentence_id` - unique identifier for the sentence
- `sentence_domain` - domain classification(s) of the sentence
- `up_votes` - number of people who said audio matches the text
- `down_votes` - number of people who said audio does not match text
- `age` - age of the speaker[^1]
- `gender` - gender of the speaker[^1]
- `accents` - accents of the speaker[^1]
- `variant` - variant of the language[^1]
- `locale` - locale code of the language
- `segment` - if sentence belongs to a custom dataset segment, it will be listed here

[^1]: For a full list of age, gender, and accent options, see the [demographics spec](https://github.com/common-voice/common-voice/blob/main/web/src/stores/demographics.ts). These will only be reported if the speaker opted in to provide that information.

#### `validated_sentences.tsv`

The `validated_sentences.tsv` file contains one row per validated sentence in the text corpus:

- `sentence_id` - unique identifier for the sentence
- `sentence` - the sentence text
- `variant` - the variant of the language
- `sentence_domain` - the domain(s) the sentence belongs to
- `source` - the source the sentence was collected from
- `is_used` - whether the sentence is still in circulation for recording
- `clips_count` - number of clips recorded for this sentence

#### `unvalidated_sentences.tsv`

The `unvalidated_sentences.tsv` file contains one row per unvalidated sentence in the text corpus:

- `sentence_id` - unique identifier for the sentence
- `sentence` - the sentence text
- `variant` - the variant of the language
- `sentence_domain` - the domain(s) the sentence belongs to
- `source` - the source the sentence was collected from
- `up_votes` - number of upvotes the sentence received
- `down_votes` - number of downvotes the sentence received
- `status` - current status of the sentence (`pending` or `rejected`)

## Get involved

### Community links

- [Common Voice translators on Pontoon](https://pontoon.mozilla.org/gju/common-voice/contributors/)
- [Common Voice Communities](https://github.com/common-voice/common-voice/blob/main/docs/COMMUNITIES.md)

### Discussions

- [Common Voice on Matrix](https://chat.mozilla.org/#/room/#common-voice:mozilla.org)
- [Common Voice on Discourse](https://discourse.mozilla.org/t/about-common-voice-readme-first/17218)
- [Common Voice on Discord](https://discord.gg/9QTj9zwn)
- [Common Voice on Telegram](https://t.me/mozilla_common_voice)

### Contribute

- [Speak](https://commonvoice.mozilla.org/gju/speak)
- [Write](https://commonvoice.mozilla.org/gju/write)
- [Listen](https://commonvoice.mozilla.org/gju/listen)
- [Review](https://commonvoice.mozilla.org/gju/review)

## Acknowledgements

### Datasheet authors

Mumtaz Ahmed  Nizam Din Shahid-ur-Rehman

### Funding

This dataset was partially funded by the *Open Multilingual Speech Fund* managed by Mozilla Common Voice.

## Licence

This dataset is released under the [Creative Commons Zero (CC-0)](https://creativecommons.org/public-domain/cc0/) licence. By downloading this data you agree to not determine the identity of speakers in the dataset.
