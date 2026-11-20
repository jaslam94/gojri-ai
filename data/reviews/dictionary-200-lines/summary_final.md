# Dictionary review summary

## Line sample

Reviewed 200 lines. Bad crop (left out of the rate): 0.

- Any error: 182 of 200 = 91.0% (95% CI 86.2% to 94.2%)
- Wrong letters: 50 of 200 = 25.0% (95% CI 19.5% to 31.4%)
- Wrong spacing: 176 of 200 = 88.0% (95% CI 82.8% to 91.8%)
- Source of the errors: raw decode also wrong 8 (table or decode rule), raw decode right 44 (Pass 2 broke it), unknown 130.

Most common changes (label to your fix):

- ` ` to `(nothing)`: 311
- `ہ` to `ھ`: 21
- `(nothing)` to ` `: 16
- `(nothing)` to `ا`: 5
- `ک ` to `ك`: 4
- `ا` to `(nothing)`: 4
- `ک` to `ك`: 3
- `ُ` to `(nothing)`: 3
- `(nothing)` to `  `: 3
- `ک` to `ب`: 3
- `ہ` to `ن`: 2
- `ا` to `ئ`: 2
- `ں ` to `ن`: 2
- `(nothing)` to `ھ`: 2
- `(nothing)` to `، `: 1
- ` ،` to `(nothing)`: 1
- `ں` to `ن`: 1
- `ّ` to `(nothing)`: 1
- `و ` to `ہ`: 1
- `(` to `(nothing)`: 1
- `ی` to `(nothing)`: 1
- `(nothing)` to `ئ`: 1
- `.` to `(nothing)`: 1
- `(nothing)` to `/Ta`: 1
- `(nothing)` to `ا    `: 1

## Table check

Right 137, wrong 22, unsure 1, not checked 0.
- F061 wrong: table says `ه`, your letters `ھ`. Used 953 times on 246 pages. All images show Do Chashmi Hay ھ
- F060 wrong: table says `ہ`, your letters `ھ`. Used 496 times on 184 pages. All images show Do Chashmi Hay ھ
- F0F1 wrong: table says `ا`, your letters `ئ `. Used 440 times on 217 pages. Yeh with Hamza Above ئ 
- F066 wrong: table says `ک`, your letters `ب `. Used 430 times on 166 pages. The letter Bay (ب) 
- F0E0 wrong: table says `ہ`, your letters `ن`. Used 386 times on 221 pages. The letter noon (ن)
- F0E1 wrong: table says `ں`, your letters `ن`. Used 376 times on 216 pages. The letter noon (ن)
- F0E5 wrong: table says `ئی`, your letters `ہ`. Used 220 times on 138 pages. Gol he urdu (ہ)
- F0D4 wrong: table says `ک`, your letters ` ك`. Used 215 times on 130 pages. ك / ک both are same letter kaf just written differently.. ک one is urdu and ك is written in arabic/persion
- F0DC wrong: table says `ام`, your letters `م`. Used 183 times on 112 pages. Meem م
- F038 wrong: table says `ل`, your letters `ٹ`. Used 140 times on 88 pages. Ṭe (ٹ)
- 0020 wrong: table says ` `, your letters ` `. Used 138 times on 110 pages. The bounding box in red is showing letter, not space. Space comes after a letter. There is a space after چِٹا and کُٹ only. کُلis wrong کُل کُٹ is right کُٹ
- F0D5 wrong: table says `ک`, your letters `ك`. Used 135 times on 93 pages. 
- F0F2 wrong: table says `ی`, your letters `ئ`. Used 77 times on 48 pages. Yeh With Hamza Above
- F044 wrong: table says `ے`, your letters `(`. Used 24 times on 23 pages. It's a bracket, not a gojri letter.
- F045 wrong: table says `ی`, your letters `)`. Used 18 times on 17 pages. It's a bracket, not a Gojri letter
- F0BC wrong: table says `بط`, your letters `ط`. Used 14 times on 12 pages. 
- F023 wrong: table says ``, your letters ` ㅤU+3164 ㅤ`. Used 7 times on 6 pages. 
- F0FA wrong: table says `م`, your letters `ؔ`. Used 6 times on 6 pages. The Sign Takhallus (ؔ) is a special diacritic mark (U+0614) used in Arabic, Persian, and Urdu literary texts. It appears above letters. E.g. بؔ In above images, the Takhallus appears on meem م.
- F0EB wrong: table says `ح`, your letters `ؑ`. Used 5 times on 5 pages. The Unicode sign for "Alayhe Assallam" is U+0611 (ؑ).
- F0FC wrong: table says `ُ`, your letters ` ٗ `. Used 2 times on 2 pages. ٗ ARABIC INVERTED DAMMA. It appears above a letter. In above images, it appears above alif ا.
- F0F3 wrong: table says `۔`, your letters `.`. Used 1 times on 1 pages. Dot .
- F0FB unsure: table says `k`, your letters ``. Used 1 times on 1 pages. 
- F057 wrong: table says `:`, your letters `؛`. Used 1 times on 1 pages. In written Urdu, the inverted semicolon (؛) is a standard punctuation mark known as Waqfa (وقفہ). Unicode: U+061B
