# Final review analysis (200 lines, 94 tables)

Lines: 200. Marked ok: 18. Any mark: 182 of 200 = 91.0% (95% CI 86.2% to 94.2%)

## Lines by error type (a line can have several)

- paren-space: 172 of 200 = 86.0% (95% CI 80.5% to 90.1%)
- other-letter: 26 of 200 = 13.0% (95% CI 9.0% to 18.4%)
- heh: 21 of 200 = 10.5% (95% CI 7.0% to 15.5%)
- latin->arabic gap: 14 of 200 = 7.0% (95% CI 4.2% to 11.4%)
- kaf: 5 of 200 = 2.5% (95% CI 1.1% to 5.7%)
- diacritic: 4 of 200 = 2.0% (95% CI 0.8% to 5.0%)
- hamza: 4 of 200 = 2.0% (95% CI 0.8% to 5.0%)
- other-space: 4 of 200 = 2.0% (95% CI 0.8% to 5.0%)
- arabic-word-space: 2 of 200 = 1.0% (95% CI 0.3% to 3.6%)
- arabic->latin gap: 1 of 200 = 0.5% (95% CI 0.1% to 2.8%)
- arabic-comma-space: 1 of 200 = 0.5% (95% CI 0.1% to 2.8%)

Lines whose ONLY error is spaces around the (transliteration) group: 114 of 200 = 57.0% (95% CI 50.1% to 63.7%)
Lines whose ONLY errors are spacing (any kind): 126 of 200 = 63.0% (95% CI 56.1% to 69.4%)
Lines with at least one non-space (letter or mark) error: 56 of 200 = 28.0% (95% CI 22.2% to 34.6%)
Lines with a letter error that is not a heh or kaf spelling choice: 32 of 200 = 16.0% (95% CI 11.6% to 21.7%)
Lines correct if paren-space AND heh/kaf choices were fixed by rule: 155 of 200 = 77.5% (95% CI 71.2% to 82.7%)

## Space errors by place (label -> your fix)

- paren-space / delete: 305
- latin->arabic gap / insert: 15
- other-space / insert: 4
- arabic-word-space / delete: 2
- arabic-comma-space / delete: 2
- arabic->latin gap / delete: 1
- latin->arabic gap / delete: 1

## Letter changes (label -> your fix), grouped


### heh (27 edits)
- `ہ` -> `ھ`: 21
- `` -> `ھ`: 2
- `ہ ` -> `ه`: 1
- `ہ` -> `ه`: 1
- `ہ` -> ` ھ`: 1
- `ھ` -> ``: 1

### kaf (7 edits)
- `ک ` -> `ك`: 4
- `ک` -> `ك`: 3

### hamza (4 edits)
- `ا` -> `ئ`: 2
- `` -> `ئ`: 1
- `ء ` -> `ہ`: 1

### diacritic (4 edits)
- `ُ` -> ``: 3
- `ّ` -> ``: 1

### other-letter (29 edits)
- `` -> `ا`: 5
- `ا` -> ``: 4
- `ک` -> `ب`: 3
- `ہ` -> `ن`: 2
- `ں ` -> `ن`: 2
- `` -> `، `: 1
- ` ،` -> ``: 1
- `ں` -> `ن`: 1
- `و ` -> `ہ`: 1
- `(` -> ``: 1
- `ی` -> ``: 1
- `.` -> ``: 1
- `` -> `/Ta`: 1
- `` -> `ا    `: 1
- `ام` -> `ؔ`: 1
- `ل ` -> `ٹ`: 1
- ` ` -> `.`: 1
- `` -> `؛ `: 1

## Paren group spacing: what your fixes say the print looks like

- print (your fix): ('no-space-before', 'no-space-after'): 143
- print (your fix): ('space-before', 'no-space-after'): 26
- print (your fix): ('space-before', 'space-after'): 4
- print (your fix): ('no-space-before', 'space-after'): 4

What Pass 2 labels have:
- label: ('space-before', 'space-after'): 175
- label: ('no-space-before', 'no-space-after'): 2

On lines with a raw decode that has a paren group: 
- raw: ('no-space-before', 'no-space-after'): 61
- raw: ('no-space-before', 'space-after'): 5
- raw: ('space-before', 'no-space-after'): 3
- raw spacing equals print: 57 of 69
- Pass 2 label spacing equals print: 4 of 69

## Heh forms in your final text (all 200 lines, Arabic part only)

- ه arabic heh final: 2
- ه arabic heh initial: 8
- ه arabic heh medial: 2
- ھ do chashmi final: 14
- ھ do chashmi initial: 6
- ھ do chashmi medial: 90
- ہ gol he final: 9

Words with ه (U+0647) in lines you did not mark for wrong letters: 6
- ('page-0050:L2', ['ok'], 'هیٹھ')
- ('page-0050:L2', ['ok'], 'هوتو')
- ('page-0109:L12', ['spacing'], 'پرهیز')
- ('page-0168:L22', ['ok'], 'هار')
- ('page-0227:L3', ['spacing'], 'هینسرنو')
- ('page-0486:L19', ['spacing'], 'هاضمُو')

## Table uses

Total glyph uses over 160 codes: 80438
- right: 76170 uses = 94.7%
- wrong: 4267 uses = 5.3%
- unsure: 1 uses = 0.0%
Wrong codes that are convention choices (heh, kaf): 1799 uses
Wrong codes that are real shape errors: 2330 uses = 2.90% of all glyphs
  - F0F1 ا -> ئ  (440 uses, 217 pages)
  - F066 ک -> ب  (430 uses, 166 pages)
  - F0E0 ہ -> ن (386 uses, 221 pages)
  - F0E1 ں -> ن (376 uses, 216 pages)
  - F0E5 ئی -> ہ (220 uses, 138 pages)
  - F0DC ام -> م (183 uses, 112 pages)
  - F038 ل -> ٹ (140 uses, 88 pages)
  - F0F2 ی -> ئ (77 uses, 48 pages)
  - F044 ے -> ( (24 uses, 23 pages)
  - F045 ی -> ) (18 uses, 17 pages)
  - F0BC بط -> ط (14 uses, 12 pages)
  - F023  ->  ㅤU+3164 ㅤ (7 uses, 6 pages)
  - F0FA م -> ؔ (6 uses, 6 pages)
  - F0EB ح -> ؑ (5 uses, 5 pages)
  - F0FC ُ ->  ٗ  (2 uses, 2 pages)
  - F0F3 ۔ -> . (1 uses, 1 pages)
  - F057 : -> ؛ (1 uses, 1 pages)

## Whole label file (non-folio lines)

Lines: 11326
- has paren group: 9981 (88.1%)
- space-before: 9853 (87.0%)
- space-after: 9757 (86.1%)
- has ھ: 2878 (25.4%)
- has ک: 2694 (23.8%)
- has ہ: 1160 (10.2%)
- has ه (U+0647): 302 (2.7%)
- no-space-after: 224 (2.0%)
- no-space-before: 128 (1.1%)