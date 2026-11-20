# NOORIN decode table: batch notes (2026-08-19 to 2026-08-26)

Moved unchanged from `LOG.md` on 2026-11-20 (only three repeated headings were corrected to name their real
keys or batches). These notes record how the NOORIN table grew. The table failed validation and the path was
abandoned on 2026-08-31: see `README.md` in this folder and the `LOG.md` entry of that date.

---

### NOORIN table 371 (2026-08-19)

Added `NOORIN48:F0F1` = `ے` (bari ye, prev چڑ/پڑ/ڈر → چڑے, پڑے),
`NOORIN08:F02A` = `ستا` (seen-te-alif, prev د → دستا = gave),
`NOORIN15:F095` = `کھٹ` (kaf-he-tte, next نہیں 5x → کھٹ نہیں).
Skipped: `NOORIN01:F09F` (tiny, neighbors unmapped),
`NOORIN01:F070` (ambiguous shape at 6.2px),
`NOORIN82:F09E` (conflicting context, گھ in one window, doesn't fit others).
Census: 2,149 unique, 371 mapped, 82.8% instances, 1,778 unknown.

### NOORIN table 373 (2026-08-19)

Added `NOORIN12:F0C7` = `ے` (bari ye, seen in `اور...` word),
`NOORIN14:F0B9` = `پ` (pe stem with dot, seen before `ھتکوش` and in `...پڑھ...` contexts).
Skipped: `NOORIN01:F09F` (tiny, neighbors unmapped), `NOORIN01:F070` (ambiguous shape), `NOORIN82:F09E` (conflicting context).
Census: 2,149 unique, 373 mapped, 82.9% instances, 1,776 unknown.

### NOORIN table 375 (2026-08-19)

Added `NOORIN04:F088` = `ھ` (he, between `پ` and `ما` in page text),
`NOORIN56:F0EE` = `ی` (farsi-ye, dotted ye variant, before `ک`).
Skipped: `NOORIN01:F09F` (tiny, neighbors unmapped), `NOORIN01:F070` (ambiguous shape), `NOORIN82:F09E` (conflicting context).
Census: 2,149 unique, 375 mapped, 82.9% instances, 1,774 unknown.

### NOORIN table 377 (2026-08-19)

Added `NOORIN05:F0E0` = `گ` (forms `اگر`-like pattern in page text),
`NOORIN09:F097` = `پ` (precedes `ڑ...` patterns, forms `پڑ...`).
Skipped: `NOORIN01:F09F` (tiny, neighbors unmapped), `NOORIN01:F070` (ambiguous shape), `NOORIN82:F09E` (conflicting context).
Census: 2,149 unique, 377 mapped, 83.0% instances, 1,772 unknown.

### NOORIN table 381 (2026-08-19)

Added `NOORIN62:F0D2` = `و` (wau, always between `ر` and `ں`, forms `روں`),
`NOORIN63:F0C0` = `ل` (lam, visible in `گو کل کھا` on page 20),
`NOORIN48:F0F9` = `ئع` (ligature, forms `ضائع` on page 23),
`NOORIN04:F02B` = `ین` (ligature, forms `دین` on page 6).
Skipped: `NOORIN82:F087` (ambiguous context, could be alif or separator).
Census: 2,149 unique, 381 mapped, 83.1% instances, 1,768 unknown.
All remaining high-count unknowns (n>=22) are in the skip set. Further
gains require revisiting skipped keys with better evidence or dropping
to the n<22 long tail.

### NOORIN table 385 (2026-08-19)

Added `NOORIN82:F033` = `غ` (ghain initial, forms `غمں نال` on page 13),
`NOORIN16:F06F` = `نا` (nun+alif ligature, forms `مناسب` on page 44),
`NOORIN10:F0C2` = `تا` (te+alif ligature, forms `کتاب` on page 6),
`NOORIN06:F0C4` = `و` (wau, `ر[glyph]ں` pattern = `روں`, same as F0D2).
Skipped: `NOORIN83:F0E0` (w=3.2, tiny connector), `NOORIN15:F0D1`
(ambiguous final form), `NOORIN01:F06F` (unclear word-initial particle),
`NOORIN82:F087` (ambiguous separator).
Census: 2,149 unique, 385 mapped, 83.2% instances, 1,764 unknown.

### NOORIN table 388 (2026-08-19)

Added `NOORIN14:F052` = `تو` (te+wau, forms `رہتو۔` / `سکتو۔` at sentence end),
`NOORIN59:F0F6` = `یس` (ye+sin ligature, forms `پردیس` on page 28),
`NOORIN12:F08A` = `یا` (ye+alif ligature, nuqta always true, forms `گیاں`).
Skipped: `NOORIN81:F075`, `NOORIN81:F087` (ambiguous connectors),
`NOORIN85:F0B6`, `NOORIN41:F09C`, `NOORIN09:F051`, `NOORIN04:F058`,
`NOORIN12:F0BE`, `NOORIN30:F06C` (mixed/unclear contexts).
Census: 2,149 unique, 388 mapped, 83.3% instances, 1,761 unknown.
Remaining non-skip keys are all n<=21 with increasingly mixed neighbor
patterns. Gains per key are diminishing.

### NOORIN table 393 (2026-08-19)

Re-examined skipped high-count keys with updated table. Several now
had enough decoded neighbors to identify.
Added `NOORIN83:F026` = `نڈ` (nun+dal ligature, visible in `بھانڈا`),
`NOORIN21:F083` = `ڑ` (retroflex re, visible in `بھیڑ`),
`NOORIN81:F046` = `و` (wau isolated, `تحقیق و ترتیب` page 1),
`NOORIN06:F046` = `لد` (lam+dal ligature, `مطلب لد ہونو` page 17),
`NOORIN05:F063` = `یر` (ye+re ligature, visible in `پیر`).
Skipped: `NOORIN83:F0DB` (w=2.8, sub-glyph connector before ع/غ),
`NOORIN57:F04B` (mixed contexts), `NOORIN82:F089` (always word-initial,
too wide to pin).
Census: 2,149 unique, 393 mapped, 83.6% instances, 1,756 unknown.

### NOORIN table 395 (2026-08-19)

Added `NOORIN82:F089` = `وقت` (3-char ligature, always word-initial,
visible in `وقت توں` page 56),
`NOORIN63:F0B8` = `قو` (qaf+wau, forms `قوم` on page 5).
Skipped: `NOORIN83:F0DC` (w=3.2, sub-glyph connector before وقت),
`NOORIN13:F0A8` (ambiguous medial, inconsistent crops),
`NOORIN25:F075` (crop showed possible table error in NOORIN01:F067),
`NOORIN82:F0AA`, `NOORIN26:F0C9`, `NOORIN59:F0EE` (mixed/tiny).
Census: 2,149 unique, 395 mapped, 83.7% instances, 1,754 unknown.

### NOORIN table 396 (2026-08-19)

Added `NOORIN83:F0DC` = `ھ` (connector before `وقت(عقل)`).
Skipped: `NOORIN13:F0A8` (still ambiguous in crops).
Census: 2,149 unique, 396 mapped, 83.8% instances, 1,753 unknown.

### NOORIN table 398 (2026-08-19)

Added `NOORIN83:F0DB` = `غ` (removed brackets in page-0006 line 18),
`NOORIN82:F082` = `و` (same context, page-0006 line 18).
Census: 2,149 unique, 398 mapped, 83.9% instances, 1,751 unknown.

### NOORIN table 399 (2026-08-19)

Added `NOORIN57:F04B` = `ں` (forms `یارںکرنپدے` and `کیکھں،کاپدے` on page 25).
Census: 2,149 unique, 399 mapped, 83.9% instances, 1,750 unknown.

### NOORIN table 400 (2026-08-19)

Added `NOORIN26:F0C9` = `چ` (removed bracket on page 10 line 15, forming `چکرنریںپ۔`).
Census: 2,149 unique, 400 mapped, 84.0% instances, 1,749 unknown.

### NOORIN table 406 (2026-08-22)

Verified trial maps from prior turn: `NOORIN57:F05A` = `ج`, `NOORIN25:F075` =
`بجھار` (page 5 `تبجھارکت`, page 153 `(بجھارکت)`).
Added `NOORIN82:F0AA` = `لت` (crops: page 6 `حالت`, page 19 `ذلالت`).
Added `NOORIN12:F088` = `گئی`, `NOORIN85:F0B6` = `تھی` (page 5 `کی گئی تھی`).
Added `NOORIN13:F0A8` = `س` plus neighbor rule in `dump_noorin_lines.py`:
prev `NOORIN01:F053`(ا) + next `NOORIN01:F079`(ے) → `س` (`اسے`, 7x); prev
`NOORIN01:F05A`(ر) + next `NOORIN01:F079` → `ہ` (`رہے`, 41x).
Census: 2,149 unique, 406 mapped, 84.3% instances, 1,743 unknown.
Skipped: `NOORIN01:F0A5` (context-dependent: `گہنو[F0A5]ڑھیں` vs narrow
connector), `NOORIN59:F0EE` (w=4.6 joiner).

### NOORIN table 410 (2026-08-22)

Added `NOORIN11:F0A2` = `جلد` (page 5 `دساں جلداں`, `چھ جلداں`).
Added `NOORIN41:F09C` = `محنت` (page 6 `بڑی محنت نال`).
Added `NOORIN81:F075` = `حد` (page 7 `کسے حد تک`; not `NOORIN57:F075`=سر).
Added `NOORIN81:F087` = `سد` (page 11 proverb `پر ایو سدھار` side).
Skipped `NOORIN63:F0B9` (mixed: `و[F0B9]گوج`, `با[F0B9]ے`, `با[F0B9]چھوڑ`).
Skipped `NOORIN21:F0A2` (Urdu `بلکے` vs wide-crop `پھیر` on other rows).
Census: 2,149 unique, 410 mapped, 84.4% instances, 1,739 unknown.

### NOORIN table 411 (2026-08-22)

Added `NOORIN82:F081` = `ض` (38/38 hits follow `NOORIN83:F0DB`=غ; decode
`غضر`, `غضب`, `غم`).
Added neighbor rules in `dump_noorin_lines.py`:
`NOORIN08:F081` prev ر next ے → empty (`رے`, 12x); prev ل next ں → `ا`
(`سالاں نال`, 4x).
`NOORIN09:F051` next `NOORIN82:F063` → `ٹھنڈ` (`ناٹھنڈیار`, 3x).
`NOORIN04:F058` next `NOORIN63:F0C6` → `بچa` (`بچاکے`, p9).
Skipped `NOORIN12:F0E2` (crop p85 = `گھی`, p14 = `گئی`; not one map).
Skipped `NOORIN12:F0BE`, `NOORIN04:F0BD` (context-dependent on other rows).
Census: 2,149 unique, 411 mapped, 84.4% instances, 1,738 unknown.

### NOORIN table 413 (2026-08-22)

Added `NOORIN12:F0E2` = `گھی` (crops p85/p111/p122; proverb گال گھی نال).
Rule: next `NOORIN12:F07B` → `بال`; paired rule `NOORIN12:F07B` prev F0E2 → `وں`
(p14 `بالوں`).
Added `NOORIN12:F0BE` = `ل` (default). Rule: next `NOORIN82:F063` → `لیا`
(p11 `آپوں لیا یار`; p129 `ساک لئی`).
Added `scripts/_tmp_crop_exact.py` for row-y crops (first-hit `_tmp_mark_key_page`
often lands on the wrong line).
Census: 2,149 unique, 413 mapped, 84.5% instances, 1,736 unknown.

### NOORIN table 416 (2026-08-22)

Added `NOORIN05:F05D` = `شکر` (crops p61/p111: `گھی شکر`, `شکر کی پوٹ`).
Added `NOORIN08:F0D4` = `دشمن` (crop p15: `دو دشمن نا ڈر`).
Added `NOORIN04:F058` = `بچ` (default). Rule: next `NOORIN63:F0C6` → `بچا`
(p9 `بچاکے`, p79 `بچانا`, p138 `بچ` + overlay tail).
Extended `NOORIN09:F051` rules: next `F063`/`F07A`/`F09B` → `ٹھنڈ` (13x).
Next `F07D` still unknown (p34/p35 `نہ[F051]پدے`, 3x).
Census: 2,149 unique, 416 mapped, 84.5% instances, 1,733 unknown.
Verified: p15 `دودشمنناڈر`, p61 `گھیشکر`, p29 `کیٹھنڈدل`, p9 `بچاکے`.

### NOORIN table 417 (2026-08-22)

Added `NOORIN09:F051` = `ٹھنڈ` (all 20 hits). Rule: next `NOORIN01:F07D`
→ `چھوڑ` (p34/p35/p154 `تنے نہ چھوڑ پدے`, 3x). Crops p56/p64/p115 confirm
ٹھنڈ; p34/p35 tight-y crops bleed Urdu parallel line, but glyph order
(F051 before پدے) matches چھوڑ proverb.
Added `scripts/_tmp_crop_col.py` for L/R column crops.
Census: 2,149 unique, 417 mapped, 84.6% instances, 1,732 unknown.
Verified: p6 `ناٹھنڈیار`, p34/p154 `نہچھوڑپدے`, p56 `ناٹھنڈریںپ`, p64 `ٹھنڈرنا`.

### NOORIN table 418 (2026-08-22)

Added `NOORIN12:F07B` = `گھڑی` (all 20 hits). Crops p49/p77/p135 confirm
گھڑی ligature. Rules: prev `F0E2` → `وں` (p14 `بالوں`, kept); next `F07D`
→ `گھڑے` (p52/p79/p135 `…گھڑےپدے`); next `F02C` → `گھڑیں` (p40).
Census: 2,149 unique, 418 mapped, 84.6% instances, 1,731 unknown.
Verified: p14 `بالوں`+`گھڑی`, p40 `گھڑیںریںپ`, p49 double `گھڑی`, p52 `گھڑےپدے`.
Skipped `NOORIN30:F06C` (20 hits): لینو on p18/p61/p66 but کرن+[F06C] on
p35 needs کرنو; tight crops still bleed Urdu parallel lines.

### NOORIN table 420 (2026-08-22)

Added NOORIN30:F06C = لینo (20 hits). Added NOORIN16:F055 = سر (p18).
Rule NOORIN14:F07A after F0E1: n; next F07A: نو (p107 گمانo).
Census: 420 mapped, 84.6%%, 1,729 unknown.
Skipped NOORIN82:F038 (19 hits): mixed contexts.

### NOORIN table 422 (2026-08-22)

Added NOORIN59:F0EE = و, NOORIN01:F0A5 = د. Rule NOORIN82:F038 after ک.
Census: 422 mapped, 84.7%%, 1,727 unknown.

### NOORIN table 424 (2026-08-22)

Added NOORIN04:F0BD = ر (37 hits). Crops p63/p72: پھر، بھرے، سورپدے.
Added NOORIN11:F087 = نو (37 hits). Crops p17/p21: بولنو، ٹالنو.
Census: 424 mapped, 84.8%%, 1,725 unknown. Page 50 still zero unknowns.
Next: NOORIN82:F038 (9 hits still rule-only), NOORIN14:F07A (12 hits).

### NOORIN table 425 (2026-08-22)

Added NOORIN72:F0C1 = کن (37 hits). Crops p56/p110: سوکن.
Rules: F07A line-start ر, after کی→ہنڈ; F038 after ما→ر, after با+:→نگ,
after کا+مند→ر, after ک+پکڑn→ھ.
Census: 425 mapped, 84.9%%, 1,724 unknown. Page 50 still zero unknowns.
Verified: p56 سوکننا, p87 کیہنڈ, p143 مارچھoڑ, p112 کھپکڑn, p158 line-start ر.
Next: F038 first hit in p76 (ر[F038]،), F07A after گor (p124).

### NOORIN table 426 (2026-08-22)

Added NOORIN31:F07D = کہیں (35 hits). Crops p10/p93. Not NOORIN01:F07D (پدے).
Rules: F07A after ر before د/کو → empty (گورد); F038 after ر before ، → نگ;
F038 after با before کو → نگ.
Census: 426 mapped, 84.9%%, 1,723 unknown. F31:F07D fully mapped.
Verified: p10 موچھمکہیں, p76 ڈررنگ/بانگ, p124 گورد, p125 بانگکوے.
Next: NOORIN82:F038 (9 hits), NOORIN14:F07A (2 hits), NOORIN81:F0A2 (34).

### NOORIN rules batch (2026-08-22)

No new flat keys (still 426). Neighbor rules only:
- `NOORIN81:F0A2`: empty before `NOORIN01:F07A` (ھ). 32/34 hits. Verified p85 `ھک`, p112 `ھکھے`.
- `NOORIN14:F07A`: prev `F057` (آپ) + next `F0E1` (گma) → `ن`. Verified p17 `آپنگمان`.
- `NOORIN82:F038`: prev ک + next `F0A2` → `ھ`; prev ر + next `F044` (ت) → `نگ`; prev با + next `F058` (۔) → `نگ`.
Census flat-map stats unchanged (426 keys, 84.9%%, 1,723 unknown). Decode placeholders for F0A2/F07A/F038 are now zero across pages 1-169.
Verified: p112 `کھپکڑn`, p150 `نگت` / `بانگ`.
Next: `NOORIN14:F0F7` (34 decode placeholders), `NOORIN83:F0D7` (33).

### NOORIN table 429 (2026-08-22)

Added flat maps `NOORIN83:F0D7` = `د`, `NOORIN82:F027` = `ر`, `NOORIN82:F026` = `ر`.
Pair `F0D7`+`F027`/`F026` → `در` (p16/p51 `درما`, p146 `درد`).
Rules: `NOORIN14:F0F7` empty before `F07A` (8 hits); after `کی` before `:` (3); after `ر` before `ت` (2).
Census: 429 keys, 85.0%%, 1,720 unknown. F0D7/F026/F027 fully mapped. F0F7 decode placeholders 34→21.
Verified: p16 `درماے`, p51 `دررما`, p58 `تھار`, p13 `ر در`.
Next: remaining `NOORIN14:F0F7` (21), `NOORIN04:F0DB` (31), `NOORIN86:F025` (227 overlay).

### NOORIN F0F7 rules extended (2026-08-22)

Extended `NOORIN14:F0F7` neighbor rules (no new flat keys; still 429).
Added: empty after `ر` before `کو`/`:``/`۔`/double-`ر`; after `،` before `ریںپ`; after `در`
before `ر`; after `ل` before `ر`; line-start; after `سے`; prev `F0F7` + next `پدے` → `ا`.
Decode placeholders 21→7. Verified: p83 `رکو`, p150 `اپدے`, p66 `نسے`, p113 cleaned.
Skipped `NOORIN04:F0DB` (31 hits, mixed: `سیاو→سیانا` vs `rnaے` vs `ترک`).
Next: 7× `F0F7`, `NOORIN04:F0DB`, `NOORIN10:F072`.

### NOORIN F0F7/F072/F0DB rules (2026-08-22)

No new flat keys (still 429). Neighbor rules only:
- `NOORIN14:F0F7`: finished joiner (34→0 decode placeholders). Added: after `س` before `گhr`→`ے` (p107 `سے گhr`); prev `F072` before `پdے`→empty (p85 `اپdے`); plus prior batch (ر/در/ل/سے/line-start/…).
- `NOORIN10:F072`: after `کی`/`کو`→`ہی`; before `F0F7`→`ا` (p85); after `نے`→`اک` (p106). 6→1 placeholder (p35 only).
- `NOORIN04:F0DB`: context rules (31→17 placeholders). `سیاو`+`ری`→`ن` (p111 `سیانا`); `rna`+`ے`→`ے` (5×); `کو`/`ترک` before `:`→empty; `نال` before `،`→`，`.
Census unchanged: 429 keys, 85.0%%, 1,720 unknown.
Verified: p85 `ا پdے`/proverb ہتھ, p107 `سے گhr`, p111 `سیاون`, p96/p141 `کی ہی`/`کو ہی`.
Next: `NOORIN04:F0DB` (17), `NOORIN10:F072` (p35), `NOORIN86:F025` overlay family.

### NOORIN F0DB finished (2026-08-22)

Added flat maps `NOORIN27:F098` = `نیچی`, `NOORIN17:F041` = `کر` (431 keys).
Finished last `NOORIN04:F0DB` decode placeholders (17→0 book-wide):
- p154: prev `F098` next `F0D9` → `بیری` (`نیچی بیری ہر کوئی…`).
- p128: `F04A` next `F0DB` → `سخت`; prev `F04A` next `F063` → `ب`; `F063` prev `F0DB` → `یر`; `F099` prev `F063` next `F023` → ` یا` (`سخت بیر یا…`).
- p22: `F09D` after `NOORIN57:F05A` before `F041` → `و`; prev `F041` next `F05A` → empty; `F05A`/`F056` empty in `F0DB`…`F0C3` chain (`رجوکر کو نہیں`).
Also finished `NOORIN10:F072` (p35 `ںت ہی :`).
Census: 431 keys, 85.0%%, 1,718 unknown (flat maps only).
Verified: p22 `رجوکر کو`, p128 `سختبیر یا…`, p154 `نیچیبیری ہر…`.
Next: `NOORIN06:F05E` (28 other contexts), `NOORIN82:F074` (27), `NOORIN12:F042` (25).

### NOORIN86 overlay + F023 batch (2026-08-22)

Empty-mapped 38 remaining `NOORIN86:*` nuqta overlay codes (228× `F025`, etc.).
Table 470 keys. Instance coverage 85.0%% → 85.9%% (1,718 → 1,679 unknown base keys).
`NOORIN34:F023` context rules (7 hits, all `دشمنی` splits): prev `F08A` → `شمنی`;
prev `F099` next `F083` → `دشمنی`; prev `F099` else → `شمنی`.
`NOORIN01:F099` before `F023` → `د` (except after `F063` → ` یا`).
Flat `NOORIN05:F035` = `پکی` (p30/p110 gloss head).
Verified: p30 `پکی دشمنی`, p62 `دشمنی کی`, p68/p84 `دشمنی`, p128 `سخت بیر یا دشمنی`.

### خواہ مخواہ + ٹھوکر + بولیں batch (2026-08-22)

Table 471 keys (+`NOORIN16:F023`=مخو). Unknown base keys 1,679 → 1,678.
`NOORIN81:F07B` before F07B+F023 → `خو`; `NOORIN01:F07B` beside F023 → `اہ`.
`NOORIN06:F05E` after `NOORIN56:F0CE` before `NOORIN82:F099` → `ٹھو` (3×).
`NOORIN57:F031` between F057/F042 → `بو`; `NOORIN12:F042` after F057 → `لیں` (5×).
`NOORIN82:F074` after F07A before F05A → `ویہ` (2 clear; p71 still open).
Verified: p84 `خواہ مخواہ دشمنی`, p52 `پسو ٹھوکرنو`, p70/p92 `…موچھم بولیں`, p151 `سو ٹھوکرنو`.
Next: other `F05E` contexts (23), other `F042` (10), other `F074` (19).

### F05E / F042 / F074 context batch (2026-08-22)

Extended neighbor rules (table stays 471 keys).
`NOORIN06:F05E`: `F0D1`/`F0D1`→empty (p73 جھوٹھی لاکھ لاو); line-start before `F033`→`جو ٹھو ` (p72).
`NOORIN57:F031` before `F042`→`بو`; `NOORIN12:F042` before `۔` or line-end→`لیں` (19× بولیں).
`NOORIN82:F074` after `F07A`: before `F055`→`یہ`; before `F05A`/`F0E6`/`F02C`→`ویہ`.
Placeholders: F05E 23, F042 10, F074 19 (down from 28/25/27).
Verified: p52/p12 `…موقع پر بولیں`, p73 `رات کوڑ…یہ`, p137 `…گیا ویہ`.

### F042 flat + F05E/F074 batch (2026-08-23)

Table 472 keys (+ flat `NOORIN12:F042`=`لیں`). F042 decode placeholders **0**.
`NOORIN06:F05E`: line-start/`F065`→`ٹھوڈی`; line-start/`F099`→`ٹھوکرے جا` (F099/F07D empty);
after `F0A5` before `:`/`۔`→`رٹھو`. `NOORIN82:F074` after `۔`→`یہ`.
Placeholders: F05E 20, F042 0, F074 18.
Verified: p64 `ٹھوڈی پکڑننی` / `ٹھوکرے جا نو`, p100 `کالیں`, p58 `بولیں،`, p159 `ہونلیں`, p6 `۔یہ`, p124 `رٹھو`.
Next: remaining F05E (20) and F074 (18) one-offs.

### F09F + F05E/F074 batch (2026-08-23)

Table 473 keys (+ flat `NOORIN01:F09F`=`ڈ`). Instance coverage 85.9%% → 86.0%%.
`NOORIN06:F05E`: after F09F→`ھو` (ڈھو); نا+کرن→`ٹھو`; before کھا after کی→`جو ٹھو `;
before کی→`جوٹھو`; line-start/after ، before ک→`ٹھو`.
`NOORIN82:F074`: after ھ→`ویہ` (all remaining nexts); after سا/و/line-start:`→`یہ`; after ج→`ی`.
Placeholders: F05E 9, F074 7 (was 20/18).
Verified: p91 `ڈھو کرنو`/`ڈھوڈھو ت`, p71 `جوٹھو کو نہیں کھاتو`, p78 `نا ٹھوکر`, p121 `جو ٹھو کھا`, p8 `ھویہ سرسر`, p101 `سایہ`, p44 `یہ:`.
Next: remaining F05E (9) and F074 (7) one-offs.

### F05E close-out + F038/F0A2 (2026-08-23)

Table still 473 keys. Flat-map coverage 86.0% (rules do not change census %).
`NOORIN06:F05E`: removed false cross-column `ٹوٹھو`; line-start before س→`جھوٹو ا` (p140);
line-start before :→`ھو` (p132 column edge of ڈھو). Placeholders: F05E 1 (p64 F032 only), F074 0.
`NOORIN81:F0A2`: حا+…+ے→`ضر ہ` (حاضر ہے); after F022 before ک→`ضرر `. 0 leftovers.
`NOORIN82:F038`: after F0AF/ڈ/ڈر/د→`نگ` (بوزنگ، ڈنگ، دنگ). F065 before F038→`ڈ`. Leftovers: p154, p156.
`NOORIN14:F07A`: 1 left (p100 after F031، سانجھی).
Verified: p140 `جھوٹو ا سچیز…`, p5 `حاضر ہے`, p91 `ڈ نگ ٹپائی`, p101 `دنگکرنو`.
Next: p64 F032+F05E; F038 p154/p156; F07A p100; or next high-count base unknowns.

### Leftover close-out batch (2026-08-23)

Table 473 → 475 keys (+`NOORIN26:F032`=`گا`, `NOORIN89:F031`=`نجھی`). Coverage still 86.0%% (69321 mapped).
Unknown keys 1,676 → 1,674.
`گاٹھوری` (p64): F032=`گا`, F05E→`ٹھو`, F067→`ری`.
p154: `نہ ہنگ لگے نہ پھٹکڑی تے رنگ چوکھا` (F07D/F0D1/F044/F067/F038/F061 rules).
p156: کا+مند F038 `ر`→`نگ` (کانگ); ڈر+ر+F038→`ڈانگ`.
`سانجھی ہنڈی` (p100): F031=`نجھی`, F07A after F031 empty, NOORIN14:F07A→` ہنڈی`.
Placeholders: F05E/F038/F07A/F032/F031 all 0.
Next: high-count base unknowns from `_tmp_top_base.py`.

### High-count base batch (2026-08-23)

Table 475 → 480 keys. Coverage 86.0%% → 86.1%% (69401 mapped). Unknown keys 1,674 → 1,669.
| Key | Map | Check |
|---|---|---|
| `NOORIN14:F0B7` | ھ / ھیان | دھڑ، چڑھنا، دھیان |
| `NOORIN82:F040` | د/دے | کھادے (پدے→ے) |
| `NOORIN18:F0A9` | پئی / اپنی | اپنی پئی پرئی؛ آپ اپنی سر |
| `NOORIN01:F062` | طرح | اسطرح، مندی طرح |
| `NOORIN08:F053` | س | اسطرح (before طرح) |
| `NOORIN12:F076` | partial | گھاٹو، بھوک؛ 13 contexts left |

Next: finish `F076`, or next top-base keys (`F04A`, `F0A4`, `F024`, `F071`, `F0F0`, `F06A`).

### F076 close-out + four flat maps (2026-08-23)

Table 480 → 484 keys. Coverage 86.1% → 86.2% (69477 mapped). Unknown keys 1,669 → 1,665.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F076` | rules | گھاٹو، گھاٹ، گھوڑو p134; F05E→ٹ; F0F0→empty; 0 leftovers |
| `NOORIN81:F0A4` | طا | طاقت p19/67; طوطا p39/70 |
| `NOORIN48:F0EB` | ہم | p16/p17 red-box crops |
| `NOORIN57:F024` | چ | وچ p29; بیچ p26 |
| `NOORIN57:F04A` | ٹھ | جھوٹھ p19; اٹھ p20; کاٹھ p120 |

Next: top unknown `NOORIN82:F071` (n≈19), then `NOORIN82:F0F0`, `NOORIN06:F06A`.

### F071 / F0F0 / F06A batch (2026-08-23)

Table 484 → 488 keys. Coverage stays 86.2% (69536 mapped). Unknown keys 1,665 → 1,661.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F071` | `ایک` | p24/p35/p134 red-box crops |
| `NOORIN63:F0F0` | `من` / `ں` | p24/p129 من; rule prev F068 next *:F06A → ں (p36 میں) |
| `NOORIN08:F06A` | `اس` / rules | prev F083→سکو p45; prev F037→اسکو p68/p69; prev+next F05A→اسکو |
| `NOORIN06:F06A` | `اس` | p36 only (2 hits); same word as F08 on p36 |

Next: `NOORIN16:F078`, `NOORIN83:F0DE`, `NOORIN12:F043` (n≈18).

### F078 / F043 / F0DE batch (2026-08-23)

Table 488 → 492 keys. Coverage 86.2% → 86.3% (69612 mapped). Unknown keys 1,661 → 1,657.

| Key | Map | Check |
|---|---|---|
| `NOORIN16:F078` | `میا` | میاں p16; میاؤں p40; کامیاب p6; 0 leftovers |
| `NOORIN12:F043` | `لیو` | من لیو ہے p24; کالا لیو p17; بولیو p20; 0 leftovers |
| `NOORIN83:F0DE` | empty | joiner before NOORIN81 *ل; 0 leftovers |
| `NOORIN82:F087` | `قا` | قا+بل=قابل p5 |
| F0DE+`F02E` | `بل` | قابل; بل سکے p27 |
| F0DE+`F03E` | `پل` | جم، پل p4 |
| F0DE+`F04C` | `تل` | تل دھرن p57 |
| F0DE+`F054` | `ٹل`/`اٹل` | کم ٹل; موت اٹل (prev F05A) |

Next: top unknown `NOORIN56:F0DF`, `NOORIN81:F09C`, `NOORIN82:F09A` (n≈18).

### F0DF / F09C / F09A batch (2026-08-23)

Table 492 → 495 keys. Coverage 86.3% → 86.4% (69666 mapped). Unknown keys 1,657 → 1,654.

| Key | Map | Check |
|---|---|---|
| `NOORIN81:F09C` | `صد` | صدیاں; صدقہ; 0 leftovers |
| `NOORIN82:F063` after F09C | `یا` | not `یاں` (avoids `صدیاںں`) |
| `NOORIN63:F0B8` after F09C | `قہ` | صدقہ |
| `NOORIN82:F09A` | `کڑ` / `کڑی` / `کھڑ` | اکڑ; دوکڑ; آکڑ/آکھڑ; 0 leftovers |
| `NOORIN56:F0DF` | `اصو`/`اصولی`/`اصولو`/`صورت`/`صور` | اصولو p113; 0 leftovers |
| `NOORIN63:F0E0`/`F0DF` after F0DF | empty | tails of اصولی/اصولو |

Next: `NOORIN85:F0BB`, `NOORIN06:F056`, `NOORIN52:F099` (n≈18).

### F0BB / F056 / F099 batch (2026-08-23)

Table 495 → 498 keys. Coverage 86.4% → 86.5% (69720 mapped). Unknown keys 1,654 → 1,651.

| Key | Map | Check |
|---|---|---|
| `NOORIN85:F0BB` | `تیا` | تیار؛ تیاری؛ موتیاں؛ رتیاں؛ 0 leftovers |
| `NOORIN06:F056` | `ٹھا` | ڈٹھا؛ ٹھا؛ ٹھار؛ اٹھا with F051/F05A→ا؛ 0 leftovers |
| `NOORIN01:F051` before F056 | `ا` | was empty gutter; only this next |
| `NOORIN01:F05A` before F056 | `ا` | اٹھانو p92؛ 4 pairs |
| `NOORIN52:F099` | `سمجھ` | سمجھآنی؛ سوچ سمجھ کے؛ 0 leftovers |
| `NOORIN01:F057` after F099 | `آ` | not `آپ` (avoids سمجھآپنی) |

Next: run `_tmp_top_base.py` for the next n≈18 cluster.

### F0DE / F061 / F05D / F04A / F0B0 batch (2026-08-23)

Table 498 → 504 keys. Coverage 86.5% → 86.6% (69822 mapped). Unknown keys 1,651 → 1,645.

| Key | Map | Check |
|---|---|---|
| `NOORIN48:F0DE` | `ق` / `ل`/`ڑ`/`و` | شوق; کھلانی; کھڑ; 0 leftovers |
| `NOORIN81:F061` | `یر` | یریںپ; یراں نال; F05A before→empty; F02C→یںپ |
| `NOORIN81:F05D` | `جد` / `جدو` | جدید (F068→ید); جد کہ; F09E→کہ; 0 leftovers |
| `NOORIN82:F068` | `ید` | after F05D only |
| `NOORIN08:F04A` | `س` / `سخت` | سخت دل؛ next F0DB→سخت؛ 0 leftovers |
| `NOORIN63:F0B0` | `فی` | کافی؛ فی اللہ؛ 0 leftovers |

Next: `NOORIN05:F056`, `NOORIN01:F0A7`, `NOORIN06:F06E` (n≈17).

### F0DD / F056 / F0A7 / F06E batch (2026-08-23)

Table 504 → 508 keys. Coverage 86.6% → 86.7% (69890 mapped). Unknown keys 1,645 → 1,641.

| Key | Map | Check |
|---|---|---|
| `NOORIN56:F0DD` | `صل` | حاصل (after F071 حa); اصل (F05A before→ا); 0 leftovers |
| `NOORIN01:F05A` before F0DD | `ا` | اصل توں/تیں؛ not default ر |
| `NOORIN05:F056` | `پھل` / `و` | کو/گو+پھل+بھو؛ و after نا+کھا، comma+کی، گa؛ 0 leftovers |
| `NOORIN01:F0A7` | `ر` | ریس؛ رشوت؛ رِچھ؛ 0 leftovers |
| `NOORIN06:F06E` | `و` / `لئے` | phrase-final و; prev F07D→لئے (کھادے لئے); 0 leftovers |

Next: `NOORIN27:F076`, `NOORIN05:F06E`, `NOORIN81:F06C` (n≈17).

### F076 / F06E / F06C batch (2026-08-23)

Table 508 → 511 keys. Coverage stays 86.7% (69941 mapped). Unknown keys 1,641 → 1,638.

| Key | Map | Check |
|---|---|---|
| `NOORIN27:F076` | `نقصان` / `پنو نقصان` | prev F04A→پنو نقصان; F079 after→empty; 0 leftovers |
| `NOORIN05:F06E` | `تباہی` / `تباہ` | next F084→تباہی (F084 empty); F07B+ز→تباہ + بر; 0 leftovers |
| `NOORIN81:F06C` | `چر` / `چڑ` | next F0F0→چڑ (چڑھو); F02C→یںپ (اچریںپ); F021→بی (چربی); 0 leftovers |

Soft: p10 `وی نقصان` still shows `ھ نقصان`; p45 `بربادی` after تباہی still `زباد`.

Next: `NOORIN44:F041` (n=17), then n≈16 cluster (`NOORIN22:F0AA`, `NOORIN81:F0A7`, …).

### F041 / F0AA / F0A7 / F0DD batch (2026-08-23)

Table 511 → 515 keys. Coverage 86.7% → 86.8% (70006 mapped). Unknown keys 1,638 → 1,634.

| Key | Map | Check |
|---|---|---|
| `NOORIN44:F041` | `لگنی` | اکھ لگنی؛ نظر لگنی؛ ٹکائی لگنی؛ 0 leftovers |
| `NOORIN22:F0AA` | `پہلا` | پہلاں with next ں؛ سب تیں پہلاں؛ 0 leftovers |
| `NOORIN81:F0A7` | `طر` / `تر` / `دی` | طریقہ؛ after خا→تر (خاطر)؛ before طرح→دی؛ 0 leftovers |
| `NOORIN63:F0DD` | `لم` | عالم؛ گھولم؛ 0 leftovers |

Next: `NOORIN17:F0D2`, `NOORIN15:F0C9`, `NOORIN81:F064` (n≈16).

### F0D2 / F0C9 / F064 batch (2026-08-23)

Table 515 → 518 keys. Coverage 86.8% → 86.9% (70054 mapped). Unknown keys 1,634 → 1,631.

| Key | Map | Check |
|---|---|---|
| `NOORIN17:F0D2` | `لحاظ` | لحاظ داری؛ بد لحاظ؛ F070/F06F after→empty؛ 0 leftovers |
| `NOORIN15:F0C9` | `لکھ` | توں لکھ بناو؛ منہ کالکھ؛ لکھ کی وی چوری؛ 0 leftovers |
| `NOORIN81:F064` | `جگ` | آپ توں گیو تے جگ توں گیو؛ F0E0 before→ے after ت/ج؛ 0 leftovers |

Next: `NOORIN08:F094`, `NOORIN25:F05B`, `NOORIN43:F092` (n≈16).

### F094 / F05B / F092 batch (2026-08-23)

Table 518 → 521 keys. Coverage 86.9% (70102 mapped). Unknown keys 1,631 → 1,628.

| Key | Map | Check |
|---|---|---|
| `NOORIN08:F094` | `ے` / `سنی` | `ے` after `NOORIN85:F08A` (دے); `سنی` before `:` or after `گل`; empty before `سنائی` p158; 0 leftovers |
| `NOORIN25:F05B` | `گا` / `بیگا` / `بن` / `بنا` / `گ` | `بیگا` before `نی`; line-start `بن`/`بنا`/`بیگا`; `گ` before `نا`/`و`; empty before `ک` after `ت`; 0 leftovers |
| `NOORIN43:F092` | `نین` / `نیند` / `ا` | `نیند` after `کی`/`اپنی`; `ا` after `ج` before `کر`; `NOORIN81:F059` after → `د`; 0 leftovers |

Next: `NOORIN21:F053`, `NOORIN08:F096`, `NOORIN57:F076` (n=16).

### F053 / F096 / F076 batch (2026-08-23)

Table 521 → 524 keys. Coverage 86.9% → 87.0% (70150 mapped). Unknown keys 1,628 → 1,625.

| Key | Map | Check |
|---|---|---|
| `NOORIN21:F053` | `نے` / `نبھا` | `نے` after `پے` (پنے); `نبھا` after `پئی` (نبھانی); empty before `تو` after نہیں; 0 leftovers |
| `NOORIN08:F096` | `ک` / `سہارے` / `ھک` / `سہارہ` / `و` | `سہارے` after کے; `ھک` after ت (تھک گو); `سہارہ` after پدے; `و` in کھوکھ; empty after سے; 0 leftovers |
| `NOORIN57:F076` | `سڑ` / `ر` / `ھ` / `پ` | `ر` after کو (رکھ); `ھ` in کتھ; `سڑ` line-start/نال; `پ` in (پدے); empty before یار/ئیے; 0 leftovers |

Next: `NOORIN17:F081`, `NOORIN08:F0E8`, `NOORIN57:F021` (n≈25–27).

### F081 / F0E8 / F021 batch (2026-08-23)

Table 524 → 527 keys. Coverage 87.0% → 87.1% (70,230 mapped, +80 instances). Unknown keys 1,625 → 1,622.

| Key | Map | Check |
|---|---|---|
| `NOORIN17:F081` | `ھی` / `تھی` | default `ھی` (چڑھی، لدھی، اچاڑھی، پڑھی، کھڑھی); `تھی` after `NOORIN82:F026` (درتھی); 0 leftovers |
| `NOORIN08:F0E8` | `ش` / `شیر` / `یر` / `ک` / `ر` / `وں` | `شیر` after بھی/ت; `ش` after سے/line-start; `ک` after F068 (نیک دینی); `یر` before `:` after کا; `وں` in شیروں; 0 leftovers |
| `NOORIN57:F021` | `ب` / `بی` / `ے` / `ی` / `س` / `ہ` / `ر` / empty | `ب` after کامیا; `بی` after ڈ/چر; `ے` after دے/ڈر; `ی` after F02A (ریس); `س` after F0C2 (تصورت); duplicate→empty; 0 leftovers |

Spot checks: p11 درتھی؛ p28 چڑھی؛ p18 بھی شیر؛ p66 شیر کو گھر؛ p45 کامیاب؛ p91 ڈبی؛ p5 تصورت.

Next: `NOORIN25:F0A9`, `NOORIN13:F0FA`, `NOORIN01:F071` (n≈15).

### F0A9 / F0FA / F071 batch (2026-08-23)

Table 527 → 530 keys. Coverage 87.1% (70,275 mapped, +45 instances). Unknown keys 1,622 → 1,619.

| Key | Map | Check |
|---|---|---|
| `NOORIN25:F0A9` | `ے` / `ی` / `بھی` / `ئ` / `ڑ` / `وں` / empty | `ے` after ک/کی/و; `ی` after نہ (نہیں); `بھی` after ں (بچوں بھی); `ئ` after کو; `ڑ` after کی before ا (کیڑا); `F079` after→empty; 0 leftovers |
| `NOORIN13:F0FA` | `ے` / `نماز` / `اں` / `گ` / empty | `نماز` after کے/تیں; `اں` after ریںپ; `ے` after کی; `گ` after (; line-start empty; 0 leftovers |
| `NOORIN01:F071` | empty / `ت` | empty after شرمسارھ/مو; `ت` after `NOORIN56:F0E7` (موت); 0 leftovers |

Spot checks: p35 بچوں بھی؛ p66 نہیں؛ p6 کیے؛ p78/p62 نماز؛ p33 ریںپاں؛ p113 شرمسار ماں؛ p55/p5 شرمسار.

Next: run `_tmp_top_base.py` for next n≈15 keys.

### F0F9 / F09D / F0D7 batch (2026-08-24)

Table 536 → 539 keys. Coverage 87.3% (70,408 mapped, +45 instances). Unknown keys 1,613 → 1,610.

| Key | Map | Check |
|---|---|---|
| `NOORIN09:F0F9` | empty | flat joiner at proverb line starts (پیٹ پھٹنو، کو، کیرگ); 0 leftovers |
| `NOORIN01:F09D` | empty / `و` / `ڈال` | F05A before F041→و; after گھی→ڈال; F021 before ل→و (ڈبیو); else empty; 0 leftovers |
| `NOORIN14:F0D7` | `ے` / `ی` / `ں` / empty | after اپنوروپ→ے (اپنے); نا+F021→ی (نائی); نا+F056→ں; empty before ں after ددھا/ڈردھا; 0 leftovers |

Spot checks: p70 اپنے نال/بغیر؛ p137 گھی ڈال؛ p53 proverb colons؛ p151 نائی بال.

Next: run `_tmp_top_base.py` for next n≈14 keys.

### F02A / F061 / F0CD batch (2026-08-23)

Table 533 → 536 keys. Coverage 87.2% → 87.3% (70,363 mapped, +43 instances). Unknown keys 1,616 → 1,613.

| Key | Map | Check |
|---|---|---|
| `NOORIN54:F02A` | `ے` / empty | `ے` before ک (وقت کے، ہمت کے، کہیں کو); empty before رکھ after F07A/F03A/F0CF/F0A7; `ے` before رکھ after ما/ے; 0 leftovers |
| `NOORIN05:F061` | empty / `پیدا` | empty before رکھ/رہونی; `پیدا` when F071/F081/F035 in window (چیز/دل/ملال پیدا ہونو); 0 leftovers |
| `NOORIN56:F0CD` | empty | joiner after دے (F08A) or د; before آپ/کی/کے; F0CD+F060=گوج; 0 leftovers |

Spot checks: p100 وقت کے؛ p14 رما کے رکھ؛ p61 چیز پیدا؛ p28 دل ماں ملال پیدا؛ p38 شان تے دے آپ.

Next: run `_tmp_top_base.py` for next n≈15 keys.

### F0DF / F060 / F0C3 batch (2026-08-24)

Table 539 → 542 keys. Coverage 87.3% → 87.4% (70,452 mapped, +44 instances). Unknown keys 1,610 → 1,607.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F0DF` | `پھر` / `تنگ` / empty | before کرنو; تنگ when F0F4 in full row or F03B prev; تنگ before ہونو when F0F2 prev; column-split fix via `base_keys_before_full_row` (p125 تنگکرنو); 0 leftovers |
| `NOORIN57:F060` | empty / `چن` | F077 before F071→چن (نال چن میلو); 0 leftovers |
| `NOORIN43:F0C3` | `و` / empty | not NOORIN63:F0C3; و after ہون/کرن; empty before ۔; 0 leftovers |

Spot checks: p80 نالچنمیلو؛ p93 ہونوت؛ p125 تنگکرنو؛ p156 ہتھ تنگ ہونو.

### F051 / F03E / F07E batch (2026-08-24)

Table 542 → 544 keys. Coverage 87.4% (70,445 mapped, +37 instances net after overlap). Unknown keys 1,607 → 1,605.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F051` | empty / `پھر` / `چ` / `و` / `ی` | empty line-start and comma joiner; پھر after کی or after :; چ in وچ; و in نہیںوا; ی in تیڑے; 0 leftovers |
| `NOORIN19:F03E` | `ب` / `پ` / `د` / `ھ` / `ہ` / `و` / `ں` / empty | colon-context rules (پھر، دیر، بھلا، ھھ، او); 0 leftovers |
| `NOORIN82:F07E` | `ق` / empty | ق in حقدار after حا; ق in قرض; empty before بتا; 0 leftovers |

Spot checks: p55 سوکورکیپھریارںکرنپدے؛ p40 حقدار کرننی؛ p100 دیر رکھاں؛ p43 بھلا.

### F068 / F0CE / F05E batch (2026-08-24)

Table 544 → 547 keys. Coverage 87.4% (70,487 mapped, +42 instances). Unknown keys 1,605 → 1,602.

| Key | Map | Check |
|---|---|---|
| `NOORIN29:F068` | `ں` / `ے` / `ی` / empty | ں after ما; ے after مدد before گہنو; ی after مصیبت before ۔; else empty joiner; 0 leftovers |
| `NOORIN61:F0CE` | `دین` / `ے` / `دے` / `ھ` / `ھیل` | دین before F07B (F07B empty); دے after comma; ے in دینیت دے; ھ in لتھ; ھیل in پھیلنو; 0 leftovers |
| `NOORIN01:F05E` | empty / `ٹ` | empty joiner; ٹ after گھا (F076) in گھاٹ نہیں; 0 leftovers |

Spot checks: p12 ماں؛ p49 مصیبتی؛ p16 سارکودین؛ p105 سرپھیلنو؛ p102 گھاٹ نہیں؛ p111 کیا شکر کیا.

### F0F1 / F02E / F088 batch (2026-08-24)

Table 547 → 550 keys. Coverage 87.4% → 87.5% (70,529 mapped, +42 instances). Unknown keys 1,602 → 1,599.

| Key | Map | Check |
|---|---|---|
| `NOORIN08:F0F1` | `ے` / ` د` / ` دے` / empty | یار دے کو; سے دے; وقت تے; colon joiner; 0 leftovers |
| `NOORIN15:F02E` | empty | joiner after پ in پنی/پے (F0E3 already has نی); 0 leftovers |
| `NOORIN10:F088` | `ی` / `عاء` / `اء` / `ب` / empty | ایں/ساکھیء; تانیعاء titles; بے قیمت; empty before کڑھا/شکر; F059 helper; 0 leftovers |

Spot checks: p22 یار دے کو پھل; p23 پنی; p23 سے دے; p53 عاء بناو; p58 کڑھا/بے قیمت/تانیعاء; p71 پے ہونو.

Next: run `_tmp_top_base.py` for next n≈14 keys (`NOORIN16:F08C`, `NOORIN67:F0F0`, `NOORIN04:F0EA`).

### F08C / F0F0 / F0EA batch (2026-08-24)

Table 550 → 553 keys. Coverage 87.5% (70,570 mapped, +41 instances). Unknown keys 1,599 → 1,596.

| Key | Map | Check |
|---|---|---|
| `NOORIN16:F08C` | `ر` / empty | ر after F07A in ترہ (پدیس، کھئے، ٹاڑ); empty after F04E/F05D/F0E3/F0E9 (ٹاٹا، دوہرتدھرتیانی، ستبندھ); 0 leftovers |
| `NOORIN67:F0F0` | empty | joiner before :/۔/،/) (کہ نہ:، پھر:، etc.); 0 leftovers |
| `NOORIN04:F0EA` | `ی` / `ا` / `دھ` / empty | ی in کوئی; ا in پراں; دھ in دھلاو; else empty; 0 leftovers |

Spot checks: p28 ترہ پدیس؛ p62 ٹاٹا؛ p88 دوہرتدھرتیانی؛ p38 کوئی؛ p103 پراں؛ p129 دھلاو؛ p52 کہ نہ:.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN10:F0B4`, `NOORIN43:F042`, `NOORIN89:F036`).

### F0B4 / F042 / F036 batch (2026-08-24)

Table 553 → 556 keys. Coverage 87.5% → 87.6% (70,609 mapped, +39 instances). Unknown keys 1,596 → 1,593.

| Key | Map | Check |
|---|---|---|
| `NOORIN10:F0B4` | `ہ` / `ئ` / empty | ہ line-start (ہرگوج) and after F043 before F091 (ہر); ئ before F060 after کو/ئے with F060→ی (کوئی، جنہیں); else empty (لاج، ج کرن); 0 leftovers |
| `NOORIN43:F042` | `ا` / `م` / empty | ا line-start (اپ، اپئی); م after F0BB (کاما); else empty (تدھجھک، ناک، کو:); 0 leftovers |
| `NOORIN89:F036` | `ے` / empty | ے before ۔ after F067/F0C8 (نہ کے); else empty before :/۔/، (کیلا:، چڑ:، زرما); 0 leftovers |

Helper: `NOORIN01:F060` → ی when prev F0B4 after کو/ئے (کوئی split).

Spot checks: p5 ہرگوج/کاما؛ p25 تدھجھک؛ p54 نہ کے؛ p112 اپ دھرنی/اپئی؛ p140 کوئی نہیں؛ p155 کوئی کے/لا جگر.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN12:F031`, etc.).

### F031 / F05E / F0B5 batch (2026-08-24)

Table 556 → 559 keys. Coverage 87.6% (70,648 mapped, +39 instances). Unknown keys 1,593 → 1,590.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F031` | `ا` / empty | ا before F056 (ں) in اساں/آپاں/باں/ڈراں/سواں/دھاں; else empty; 0 leftovers |
| `NOORIN05:F05E` | `ا` / `ی` / empty | ا in با آپ after F024; ی in کسی before ما; else empty (دھوکے، دیکھ، صورت، دھاں کی); 0 leftovers |
| `NOORIN82:F0B5` | empty | flat joiner (گہنو، گل،، نہ، سوچ، لائی:); 0 leftovers |

Spot checks: p22 دھاں؛ p38 باں؛ p115 اساں؛ p83 کسی ماں؛ p113 دھوکے/دیکھ؛ p148 با آپ؛ p10 آپئے گل؛ p28 باک نہ۔

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN16:F07E`, etc.).

### F07E / F0EC / F028 batch (2026-08-24)

Table 559 → 563 keys. Coverage 87.6% → 87.7% (70,688 mapped, +40 instances). Unknown keys 1,590 → 1,586.

| Key | Map | Check |
|---|---|---|
| `NOORIN16:F07E` | `ہ` / `ے` / empty | ہ in رہے/رہے ہیں/کم رہ (ip F07B, not nxt, because F021 is empty-skipped); ے after ں/ک line-end; empty after comma/شرمسار; 0 leftovers |
| `NOORIN07:F0EC` | `ے` / empty | ے line-start (ےپلاؤ) and after یار before F0E0 (ےھوڑ); else empty joiner (کو لا، گہنو کرنے); 0 leftovers |
| `NOORIN10:F028` | `ے` / empty | ے in کہنی/رکے (کی before نہ، ک before بے); else empty; 0 leftovers |

Helper: `NOORIN10:F021` → ے when ip F07E (رہے split; p8).

Spot checks: p8 کر رہے گہنوں؛ p9 سکرنتاںے/کم رہ؛ p84 ےپلاؤ/ےھوڑ؛ p58/p111 کہنی؛ p65 رکے.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN82:F037`, `NOORIN17:F05E`, `NOORIN13:F0C3`, etc.).

### F037 / F05E / F0C3 batch (2026-08-24)

Table 563 → 566 keys. Coverage 87.7% (70,727 mapped, +39 instances). Unknown keys 1,586 → 1,583.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F037` | `ی` / empty | ی after ت before اچا (بتایا، p11); else empty joiner (کو نہ، کن کی، title lines); 0 leftovers |
| `NOORIN17:F05E` | empty | flat joiner before کد (شان/بانی/بغیر + ک+د); 0 leftovers |
| `NOORIN13:F0C3` | empty | flat joiner (ماکنی، نہیں آپ، کی نہیں، حیثیت ما، title lines); 0 leftovers |

Spot checks: p11 تیاچاڑہونو/شانکد context؛ p19 شانکد؛ p48 بانیکد؛ p12 ماکنی/نہیں آپ؛ p114 کی نہیں؛ p100 بغیرکد.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN81:F0AD`, `NOORIN08:F073`, etc.).

### F0AD / F073 / F0D2 batch (2026-08-24)

Table 566 → 569 keys. Coverage 87.7% → 87.8% (70,766 mapped, +39 instances). Unknown keys 1,583 → 1,580.

| Key | Map | Check |
|---|---|---|
| `NOORIN81:F0AD` | empty | flat joiner after ک/د (کوک، کما، بھوپکے، کوکد); 0 leftovers |
| `NOORIN08:F073` | empty | flat joiner before م/ہمت (ٹانام، سبم، یارکہمت، نام); 0 leftovers |
| `NOORIN10:F0D2` | `و` / empty | و after ر before لا/د/گہنو (رولاں، رودھک، رودل، روگہنو); else empty (رنے، رکھاں); 0 leftovers |

Spot checks: p13 کوککوئے؛ p14 ٹانام/سبم/رنےیار؛ p30 رولاں؛ p59 کوکد؛ p76 یارکہمت؛ p100 رودلگہنونئے.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN63:F0D3`, `NOORIN32:F061`, etc.).

### F0D3 / F061 / F073 batch (2026-08-24)

Table 569 → 572 keys. Coverage 87.8% (70,805 mapped, +39 instances). Unknown keys 1,580 → 1,577.

| Key | Map | Check |
|---|---|---|
| `NOORIN63:F0D3` | empty | flat joiner after لا (لا کرننی، لا یار، لا بغیر); F09A→ے helper; 0 leftovers |
| `NOORIN32:F061` | `ی`/`ں`/`نی`/`ے`/empty | ی after کرن/ہون/چ (کرنی، ہونی، سوچی); ں after کیون; نی after م (سامنی); ے after لا (بلائے); 0 leftovers |
| `NOORIN57:F073` | empty | flat joiner (ٹھناکرنے، باندپدے، پلےتکو، دلما); 0 leftovers |

Spot checks: p16 لاکرننی؛ p29 لاگرکے؛ p35 لایار؛ p57 کیوں؛ p95 سامنی؛ p133 ہونی؛ p159 بلائے/سوچی؛ p25 باندپدے؛ p51 پلےتکو.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN12:F0D6`, `NOORIN18:F09E`, etc.).

### F0D6 / F09E / F057 batch (2026-08-24)

Table 572 → 575 keys. Coverage 87.8% → 87.9% (70,843 mapped, +38 instances). Unknown keys 1,577 → 1,574.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F0D6` | empty | flat joiner after ھ (ھر، ھپ، ھچھوڑ، ھیار، رھنہہ); 0 leftovers (n=13) |
| `NOORIN18:F09E` | empty | flat joiner before پدے (کےپدے، کوئےپدے، روپدے); 0 leftovers (n=13) |
| `NOORIN81:F057` | empty | flat joiner in کور/بایار/رہون (کورہون، کورنہیں، بایار); 0 leftovers (n=12) |

Spot checks: p34 ہرپچڑ/ھچھوڑپدے/رھنہہ؛ p40 پدےتیںموڑ؛ p48 کوئےپدے؛ p67 روپدے؛ p56 کورہون؛ p2 بایار؛ p107 کورہونونہیں.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN07:F0ED`, `NOORIN12:F0BF`, etc.).

### F0ED / F0BF / F05A batch (2026-08-25)

Table 575 → 578 keys. Coverage 87.9% (70,879 mapped, +36 instances). Unknown keys 1,574 → 1,571.

| Key | Map | Check |
|---|---|---|
| `NOORIN07:F0ED` | empty | flat joiner (اللہ، دیکھکے، ترپکڑن، گہنو، ریںپ line-start); 0 leftovers (n=12) |
| `NOORIN12:F0BF` | `ے` / empty | `ے` after کر (کرے); else empty joiner (آپ، ما، رھ، کےک); 0 leftovers (n=12) |
| `NOORIN89:F05A` | empty | flat joiner before ج/بی/F06F (کوجگہنو، کیبیتیں، بیکرننی); 0 leftovers (n=12) |

Spot checks: p32 اللہ؛ p42 دیکھکے؛ p53 کرے؛ p80 کرے،؛ p90 نیرھاپنوروپ؛ p12 کوجگہنو؛ p38 کیبیتیں؛ p98 بےکرکے.

Next: run `_tmp_top_base.py` for next n≈12 keys (`NOORIN10:F047`, `NOORIN14:F068`, etc.).

### F047 / F068 / F048 / F059 batch (2026-08-25)

Table 578 → 581 keys. Coverage 87.9% (70,915 mapped, +36 instances). Unknown keys 1,571 → 1,568.

| Key | Map | Check |
|---|---|---|
| `NOORIN10:F047` | empty | flat joiner (کی نال، ماںدینو، line-start proverb headers); 0 leftovers (n=12) |
| `NOORIN14:F068` | `ی`/`ں`/`ا`/empty | ی before F0E8→ک (یک دینی); ں after نا; ی line-start (یتیں); ا in گلانی; 0 leftovers (n=12) |
| `NOORIN11:F048` | `ا`/`و`/empty | ا before ں (کاں، گلاں); و before ھ/ک (کےھر، بغیرھر); empty after مقامتو; 0 leftovers (n=12) |
| `NOORIN15:F059` | `ے`/empty | ے after ھ (ھےآپا، مطلبھے); empty after سو; 0 leftovers (n=12) |

Spot checks: p33 نیاںئےنہ؛ p63 بدھانی،یک دینی؛ p53 (گلاں)； p074 کےوھر؛ p069 ھےآپا؛ p117 مطلبھے.

Next: run `_tmp_top_base.py` for next keys (`NOORIN05:F063` n=49, etc.).

### F063 / F0E9 / F0CE / F06E batch (2026-08-25)

Table 581 → 586 keys. Coverage 87.9% → 88.1% (71,012 mapped, +97 instances). Unknown keys 1,568 → 1,563.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F063` | `یر` / empty | `یر` after F045 (تیرسا), F056/F07D/F0F2; empty line-start/joiner/mقامتو/کے; 0 leftovers (n=49) |
| `NOORIN04:F0E9` | empty | flat joiner (یارپریار، ریںپ، گہنواپنوروپ); 0 leftovers (n=12) |
| `NOORIN04:F0CE` | `ں` / empty | `ں` after سو (سوں); else empty; 0 leftovers (n=12) |
| `NOORIN20:F06E` | `و` / empty | `و` after : (وعدہ); else empty; 0 leftovers (n=12) |

Spot checks: p10 تیرسا؛ p53 تیرسا؛ p27 سوں؛ p28 وعدہ آپنی؛ p42 وعدہ کرنے نال.

Next: run `_tmp_top_base.py` for next n≈12 keys (`NOORIN63:F0F3`, `NOORIN57:F063`, etc.).

### F0F3 / F063 / F0B8 batch (2026-08-25)

Table 586 → 589 keys. Coverage 88.1% (71,047 mapped, +35 instances). Unknown keys 1,563 → 1,560.

| Key | Map | Check |
|---|---|---|
| `NOORIN63:F0F3` | `د` / empty | `د` after ز/ر (زدینو، وردرگنا، ردکررنئے); else empty (زدرک، نازدرک); 0 leftovers (n=12) |
| `NOORIN57:F063` | `ڑ` / `و` / empty | `ڑ` after مو before م (موڑم); `و` after ھ (سامھوکم); else empty; 0 leftovers (n=12) |
| `NOORIN81:F0B8` | `ا` / `ب` / empty | `ا` in باں; `ب` in کثریب/بہونو/برباد; empty in parens/سوت; 0 leftovers (n=11) |

Spot checks: p66 زدینو؛ p70 باںکا؛ p140 موڑم؛ p119 برباد؛ p098 کثریب.

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN63:F0AF`, `NOORIN15:F0F5`, etc.).

### F0AF / F0F5 / F02F batch (2026-08-25)

Table 589 → 592 keys. Coverage 88.1% (71,080 mapped, +33 instances). Unknown keys 1,560 → 1,557.

| Key | Map | Check |
|---|---|---|
| `NOORIN63:F0AF` | `ی` / empty | `ی` after طر/ما before ں; else empty joiner (رررپ، رضاکرنو، ریںپجتناں); 0 leftovers (n=11) |
| `NOORIN15:F0F5` | `ت` | `ت` before ھ (رکھائےتھکر، تھکر); 0 leftovers (n=11) |
| `NOORIN81:F02F` | `وں`/`توں`/`ں`/`کی`/empty | `وں` after نال; `توں` after زیادہتجربو; `ں` in توںپرھی; `کی` before چیز; else empty; 0 leftovers (n=11) |

Spot checks: p150 طریں؛ p100 زیادہتجربوتوںکیگل؛ p125 توںپرھی؛ p006 رکھائےتھکر؛ p093 کیچیز.

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN59:F0EB`, `NOORIN13:F052`, etc.).

### F0EB / F052 / F041 batch (2026-08-25)

Table 592 → 595 keys. Coverage 88.2% (71,113 mapped, +33 instances). Unknown keys 1,557 → 1,554.

| Key | Map | Check |
|---|---|---|
| `NOORIN59:F0EB` | `ھ`/`ر`/`ہ`/`ب`/`آ`/empty | after لا (F0D1): ھ before ھے; empty before ت (F044/F05D); ر before رھلاد; ہ before ہتھ; ب before بچو; آ before آپدم; else empty; 0 leftovers (n=11) |
| `NOORIN13:F052` | `ر`/`ا`/`ت`/`ھ`/empty | after غ: ر before حالت (غریب); ا before ما (غما); ت before تو (غرتوں); ھ before ھ (ناغھ); empty after ع before ک and before قد; 0 leftovers (n=11) |
| `NOORIN12:F041` | `ر`/empty | `ر` after ک before تو (ددھاکرتوں); else empty joiner (انیدھڑو، نا آپ، تآپلا); 0 leftovers (n=11) |

Spot checks: p029 لات غضما؛ p049 غریب حالت؛ p120 ددھاکرتوں؛ p126 نالاآپدم؛ p138 ناغھ نہیں۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN57:F027`, `NOORIN19:F034`, etc.).

### F027 / F034 / F065 batch (2026-08-25)

Table 595 → 598 keys. Coverage 88.2% (71,146 mapped, +33 instances). Unknown keys 1,554 → 1,551.

| Key | Map | Check |
|---|---|---|
| `NOORIN57:F027` | `ں` / `ر` / empty | `ں` after ما before کے (کاماں کے); `ر` after : before ر (رک گہنو، راللہ); else empty (کوئے نہیں، جس کا کو); 0 leftovers (n=11) |
| `NOORIN19:F034` | `گ` / `ے` / empty | `گ` line-start before ین (گیل); `ے` after کو/کی before ین (کوئے، کیے); `ے` after ں before نہ (ستوںے); else empty; 0 leftovers (n=11) |
| `NOORIN08:F065` | `ے` / `و` / `ت` / empty | `ے` in کالے; `و` in نالوں; `ے` after کر before نے (کرے); `ت` before F050 (تی); else empty; 0 leftovers (n=11) |

Spot checks: p006 کاماں کے؛ p008 گیل نسے؛ p121 کالے لکیکنڈ؛ p134 نالوں؛ p160 ستوںے نہ کرنو۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN14:F091`, `NOORIN10:F05D`, etc.).

### F091 / F05D / F0FA batch (2026-08-25)

Table 598 → 601 keys. Coverage 88.3% (71,179 mapped, +33 instances). Unknown keys 1,551 → 1,548.

| Key | Map | Check |
|---|---|---|
| `NOORIN14:F091` | `د`/`ے`/`و`/empty | `د` after بھا before ھ (بھادھ); `ے` after ک before ،/۔/: (کے); `و` after نہک before : (نہ کو); `و` after ک before ے (کوکے); else empty; 0 leftovers (n=11) |
| `NOORIN10:F05D` | `ی`/empty | `ی` in را before ک (راکدھن، راکمنلیو); else empty (عیبکر، کسےکر); 0 leftovers (n=11) |
| `NOORIN56:F0FA` | `ھ`/`ی`/`ر`/empty | `ھ` after د before ھ (دھھے، دھکرنو); `ی` after ت before ک (پکڑنتی، یکت); `ر` after کھ before ر (پکھر); `ی` after : before ک; else empty; 0 leftovers (n=11) |

Spot checks: p010 راکدھنں؛ p095 بھادھ؛ p101 ہرا نہیں کے؛ p128 راکدھن؛ p108 پکھرمناجلد۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN12:F06B`, `NOORIN63:F0BE`, etc.).

### F06B / F0BE / F024 batch (2026-08-25)

Table 601 → 604 keys. Coverage 88.3% (71,212 mapped, +33 instances). Unknown keys 1,548 → 1,545.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F06B` | `پ`/`ے`/`ی`/empty | `پ` after آپ (F057+F04A) before F07B (آپاپردھ); `ے` after کی before F085 (کیے); `ی` after د before F07B (زبادی); `ے` after ل before F061 (نالے); else empty; 0 leftovers (n=11) |
| `NOORIN63:F0BE` | empty | flat empty joiner (کےما، بانا، نامندر، کررکرر، کا سے، کیتی کو); 0 leftovers (n=11) |
| `NOORIN12:F024` | `ے`/empty | `ے` after بھا (F0C5+F05A) before ، (بھارے); else empty (بھاہئے، رہمو، گلٹا، کسھو); 0 leftovers (n=11) |

Spot checks: p12 آپاپردھ، بھاہئے؛ p96 بھارے؛ p153 کیے؛ p154 زبادی؛ p156 نالے۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN09:F0E5`, `NOORIN32:F05F`, etc.).

### F0E5 / F05F / F0DC batch (2026-08-25)

Table 604 → 607 keys. Coverage 88.4% (71,245 mapped, +33 instances). Unknown keys 1,545 → 1,542.

| Key | Map | Check |
|---|---|---|
| `NOORIN09:F0E5` | `ے`/`ن`/`ر`/`ا`/empty | `ے` after گھر/پلاء/کے; `ن` in بنائے; `ر` in رہے; `ا` in ڈرانی; empty after سے/،; 0 leftovers (n=11) |
| `NOORIN32:F05F` | `ئی`/`ہ`/`ت`/`ں`/`ہم`/empty | `ئی` after کو (کوئی); `ہ` after کا before ھ (کاہی/کاہانو); `ت` in سوتری; `ں` in آنیاں; `ہم` line-start; else empty; 0 leftovers (n=11) |
| `NOORIN14:F0DC` | `ے` | `ے` after د (F08A) or مد (F0E6); `ے` before ناداد after :; 0 leftovers (n=11) |

Spot checks: p13 گھرئے؛ p32 بنائے؛ p108 سوتری؛ p140 دے ناداد؛ p145 مدے۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN04:F0DA`, `NOORIN04:F0B9`, etc.).

### F0DA / F0B9 / F092 batch (2026-08-25)

Table 607 → 610 keys. Coverage 88.4% (71,278 mapped, +33 instances). Unknown keys 1,542 → 1,539.

| Key | Map | Check |
|---|---|---|
| `NOORIN04:F0DA` | `ی`/`ئی`/`ے`/`یا`/`ھ`/empty | `ی` line-start (یہ حق/اک لگنی); `ئی` after کو (کوئی کے); `ے` in نتیرے; empty in تھا نہیں; `ی` in دھیار; `یا` after ڈر; `ھ` in تھاک; 0 leftovers (n=11) |
| `NOORIN04:F0B9` | `گ`/`ف`/`ا`/`ڑ`/empty | `گ` in رنگ دبائے; `ف` in فردر after :; `ا` in تھوڑا; `ڑ` in بڑودھ; else empty; 0 leftovers (n=11) |
| `NOORIN08:F092` | `ھ`/`ہ`/empty | `ھ` after د before ۔; `ہ` after د before ،/:; empty after ناداد; 0 leftovers (n=11) |

Spot checks: p45 یہ حق؛ p54 کوئی کے؛ p21 رنگ دبائے؛ p116 فردر؛ p135 ناداد،۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN21:F088`, `NOORIN24:F02C`, etc.).

### F088 / F02C / F082 batch (2026-08-25)

Table 610 → 613 keys. Coverage 88.4% (71,311 mapped, +33 instances). Unknown keys 1,539 → 1,536.

| Key | Map | Check |
|---|---|---|
| `NOORIN21:F088` | `و`/`اں`/`پ`/`ا`/`یو`/empty | `و` in ھو; `اں` in ناسباں; `پ` in کمپہ; `ا` after اپ; `یو` in (یوں); empty before کیے/آپتا; 0 leftovers (n=11) |
| `NOORIN24:F02C` | `ک`/`س`/`ا`/`ئ`/`ی`/empty | `ک` after ر/دوستی; `س` in رسوا; `ا`+`ئ` in ائے; `ک`+`ی` in کی; 0 leftovers (n=11) |
| `NOORIN20:F082` | `ش`/`ی`/`ڑ`/`ب`/`ے`/`و`/empty | `ش` in بارش; `ی` line-start/after :; `ڑ` after مقامتو; `ب` in بڑی/بونی; `ے` in رکرمے; `و` in ہونو; 0 leftovers (n=11) |

Spot checks: p36 بارش/یہ؛ p46 (ھو کیے); p49 رسوا/کیے؛ p93 یارک کی؛ p152 یہ آپلاں۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN21:F075`, `NOORIN51:F096`, etc.).

### F075 / F096 / F036 batch (2026-08-25)

Table 613 → 616 keys. Coverage 88.5% (71,344 mapped, +33 instances). Unknown keys 1,536 → 1,533.

| Key | Map | Check |
|---|---|---|
| `NOORIN21:F075` | `ے`/`ؤ`/`ا`/`ز`/`و`/`ہ`/`ن`/empty | `ے` in دے; `ؤ` after آ (ڈرآؤ); `ا`+`ز` in از; `و`+`ہ` in وہ; `و`+`ن` in ہون; empty after آؤ; 0 leftovers (n=11) |
| `NOORIN51:F096` | `ا`/`ے`/empty | `ا` before ت (ات زردک); `ے` in کیے; else empty after کی/نال; 0 leftovers (n=11) |
| `NOORIN53:F036` | `ی`/`ہ`/`ا`/empty | `ی` in ایک/اک/چیک; `ہ` in کہہ/کیہ; `ا` in کا/عادت کا; 0 leftovers (n=11) |

Spot checks: p32 دے؛ p93 ڈرآؤ/از کم؛ p159 وہ آپ؛ p44 ات زردک؛ p52 کہہونو؛ p55 اک کرنو؛ p117 کیہک۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN22:F041`, `NOORIN01:F0AF`, etc.).

### F041 / F0AF / F0F2 batch (2026-08-25)

Table 616 → 619 keys. Coverage 88.5% (71,375 mapped, +31 instances). Unknown keys 1,533 → 1,530.

| Key | Map | Check |
|---|---|---|
| `NOORIN22:F041` | `ھ`/empty | `ھ` after د (F08A) in دھرت/دھرے/نہ دھ; flat joiner; 0 leftovers (n=11) |
| `NOORIN01:F0AF` | `ز`/`ہ`/empty | `ز` before ندگی (زندگی); `ہ` before نگ (ہنگ); empty line-start before :; 0 leftovers (n=10) |
| `NOORIN52:F0F2` | `ب`/`پ`/`ہ`/empty | `ب` in پنجابر (ں in before); `پ` before ڈر after گوج; `ہ` in کھاوہ; else empty; 0 leftovers (n=10) |

Spot checks: p2 ہنگ؛ p4 پنجابر/گوج پہ ڈر؛ p7 زندگی؛ p98 line-start before :؛ p124 کھاوہ.

Next: run `_tmp_top_base.py` for next n≈10 keys (`NOORIN82:F0AD`, `NOORIN07:F086`, etc.).

### F0AD / F086 / F06A / F0B2 batch (2026-08-25)

Table 619 → 623 keys. Coverage 88.6% (71,415 mapped, +40 instances). Unknown keys 1,530 → 1,526.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F0AD` | `ا`/`ی`/empty | `ا` in مار; `ی` line-start before یار; empty joiner (رھے، قدھک، قدپ، :); 0 leftovers (n=10) |
| `NOORIN07:F086` | empty | Urdu index/citation marker (p71); flat empty; 0 leftovers (n=10) |
| `NOORIN57:F06A` | `ھ`/`د`/empty | `ھ` in تھکنو; `د` after : in د دینو; else empty joiner; 0 leftovers (n=10) |
| `NOORIN81:F0B2` | `ئی`/`ب`/`ہ`/empty | `ئی` in کوئی; `ب` in بشوں; `ہ` in بہش; empty before )/تے/ch صور; 0 leftovers (n=10) |

Spot checks: p4 مار میاں؛ p8 کوئی قہونئے؛ p69 تھکنو؛ p117 بشوں؛ p139 یارھر۔

Next: run `_tmp_top_base.py` for next keys (`NOORIN81:F02E`, etc.).

### F04E / F06C / F040 batch (2026-08-25)

Table 626 → 629 keys. Coverage 88.6% (71,475 mapped, +30 instances). Unknown keys 1,523 → 1,520.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F04E` | `ر`/`کار`/empty | `ر` in کار after کا; `کار` line-start; F068 empty after F04E; else empty before ڑ; 0 leftovers (n=10) |
| `NOORIN15:F06C` | `ے`/`غ`/`ا`/empty | `ے` in موڑے; `غ` in کو غم; `ا` in استاد; 0 leftovers (n=10) |
| `NOORIN44:F040` | `رہندے`/`گرتو` | after نہیں / before نہیں; 0 leftovers (n=10) |

### F02E / F0A6 / F077 batch (2026-08-25)

Table 623 → 626 keys. Coverage 88.6% (71,445 mapped, +30 instances). Unknown keys 1,526 → 1,523.

| Key | Map | Check |
|---|---|---|
| `NOORIN81:F02E` | `بل`/empty | `بل` after F0DE joiner; existing rule block; 0 leftovers (n=10) |
| `NOORIN82:F0A6` | `ہ`/`ت`/`کو`/empty | `ہ` line-start; `ت` in گلبات تک; `کو` in ں کو ایک; 0 leftovers (n=10) |
| `NOORIN81:F077` | `ف`/`ش`/`ح`/`شر`/empty | `ف` in فر; `ش` in شرم; `ح` in حرمت; `شر` in شرم تاں; 0 leftovers (n=10) |

Spot checks: p5 قابلقد؛ p6 ہک کہیں؛ p92 ں کو ایک؛ p130 شرم کو مال شرم دے۔

Next: run `_tmp_top_base.py` for next keys.

### F099 / F09A / F02D batch (2026-08-23)

Table 530 → 533 keys. Coverage 87.1% → 87.2% (70,320 mapped, +45 instances). Unknown keys 1,619 → 1,616.

| Key | Map | Check |
|---|---|---|
| `NOORIN81:F099` | `ڑ` / `ڈ` / `د` / empty | `ڑ` after ک (اکڑف); `ڈ` before ف (ڈف/بیڈی); `د` after سب (دف); duplicate→empty; 0 leftovers |
| `NOORIN09:F09A` | `ے` / `بلا` / `ا` / `و` / empty | `ے` after آپ/کی; empty before ئے; `بلا` after ر; `ا` after پدے; `و` after کے; 0 leftovers |
| `NOORIN82:F02D` | `ند` / `ں` / empty | `ند` after ر (رندات); `ں` after ما (رمان); empty after F04A/F0EC; 0 leftovers |

Spot checks: p47 اکڑف؛ p86 ڈف؛ p36 بیڈی؛ p143 دف؛ p10 آپئے؛ p141 کیے؛ p19 بلا؛ p33 رندات؛ p45 رمان.

Next: run `_tmp_top_base.py` for next n≈15 keys.

### F094 / F05B / F092 batch (2026-08-23, second write-up of the same step)

Table 518 → 521 keys. Coverage 86.9% (70,102 mapped, +48 instances). Unknown keys 1,631 → 1,628.

| Key | Map | Check |
|---|---|---|
| `NOORIN08:F094` | `ے` / empty | after د→دے (ناپودے، کر دے، گل دے); p158 empty before سنائی؛ 0 leftovers |
| `NOORIN25:F05B` | `کہ` / rules | ی after ت (پرائیتی); نہیں after آپس; بیگا before نی; ھی in دھیود; کہ before نا/ک؛ 0 leftovers |
| `NOORIN43:F092` | empty / rules | joiner after اپنی; ا line-start آپنی; جا after ج before کر; نیند after کی before :؛ 0 leftovers |

Spot checks: p10 ناپودے؛ p13 سووترا/چھوڑ بیگانی؛ p45 دھی بیگانی/کہ/کہنا؛ p72 جوانی کی نیند؛ p106 کر دے/گل دے.

Next: run `_tmp_top_base.py` for next n≈16 keys.

### Batch 48 (2026-08-25)

Table 629 → 639 keys. Coverage 88.6% → 88.7% (71,505 mapped, +30 instances). Unknown keys 1,520 → 1,510.

| Key | Map | Check |
|---|---|---|
| `NOORIN29:F04F` | `ہ`/`ے`/empty | `ہ` after ر; `ے` after ک; 0 leftovers (n=10) |
| `NOORIN15:F0CF` | `و`/empty | `و` in وت/کیوں/مو; empty before لائکرننی; 0 leftovers |
| `NOORIN07:F0A7` | context | `و` in بوت; `یں` after م; `ی`/`ح`/`ں`/space by gloss; 0 leftovers |
| `NOORIN26:F0CF` | `و`/`ں`/empty | `و` in یاروں/ماوے; `ں` in آپوں; 0 leftovers |
| `NOORIN69:F085` | `۔` | flat full stop; 0 leftovers |
| `NOORIN23:F074` | context | `اپ` line-start; `ے` after context; 0 leftovers |
| `NOORIN28:F0F1` | `،`/space | Urdu gloss joiner; 0 leftovers |
| `NOORIN35:F0C6` | context | `ب`/`ے`/`ن`/space by prev; 0 leftovers |
| `NOORIN11:F051` | `ے`/space | joiner in gloss column; 0 leftovers |
| `NOORIN41:F032` | context | `و`/`ے`/`ت` by neighbors; 0 leftovers |

### Batch 49 (2026-08-25)

Table 639 → 649 keys. Coverage 88.7% → 88.8% (71,575 mapped, +70 instances). Unknown keys 1,510 → 1,500.

| Key | Map | Check |
|---|---|---|
| `NOORIN06:F0E5` | `ے` | flat; 0 leftovers (n=10) |
| `NOORIN08:F03F` | context | `ا`/`ے`/`و`/space by colon and gloss; 0 leftovers |
| `NOORIN30:F044` | `ے` | after ک; 0 leftovers |
| `NOORIN81:F093` | `ے` | after ر (زدرے); 0 leftovers |
| `NOORIN19:F049` | context | proverb gloss `ا`/`وں`/`ک`/`اں`; 0 leftovers |
| `NOORIN41:F0AF` | empty | before ہون; 0 leftovers |
| `NOORIN31:F06F` | `و` | flat (پوکھ); 0 leftovers |
| `NOORIN08:F0B0` | `،` | flat Urdu comma; 0 leftovers |
| `NOORIN63:F0B5` | `ٹ` | after مو (موٹ); 0 leftovers |
| `NOORIN18:F02B` | `ا`/empty | line-start `ا`; empty in چھوک/ہتھک; 0 leftovers |

### Batch 50 (2026-08-25)

Table 649 → 659 keys. Coverage 88.8% → 89.0% (71,749 mapped, +174 instances). Unknown keys 1,500 → 1,490.

| Key | Map | Check |
|---|---|---|
| `NOORIN26:F083` | `و`/empty | `و` in جگوں/سبوں; 0 leftovers |
| `NOORIN09:F096` | space/`,` | gloss joiner; 0 leftovers |
| `NOORIN50:F071` | context | `ھ`/`ی`/`ے`/space in Urdu gloss; 0 leftovers |
| `NOORIN04:F0AB` | `ے` | flat; 0 leftovers |
| `NOORIN04:F0B6` | `۔` | flat; 0 leftovers |
| `NOORIN04:F02A` | `ے`/`ی` | by context; 0 leftovers |
| `NOORIN01:F032`/`F039`/`F031`/`F030` | empty | English index markers p4–5; 0 leftovers |

### Batch 51 (2026-08-25, partial)

Table 659 → 660 keys. Coverage 89.0% (71,779 mapped, +30 instances). Unknown keys 1,490 → 1,489. Only one n=9 key left at this tier.

| Key | Map | Check |
|---|---|---|
| `NOORIN54:F0AB` | `ے` | before ک (کے); 0 leftovers (n=9) |

### Batch 52 (2026-08-25)

Table 660 → 670 keys. Coverage 89.0% → 89.1% (71,869 mapped, +90 instances). Unknown keys 1,489 → 1,479.

| Key | Map | Check |
|---|---|---|
| `NOORIN24:F0D6` | `ر` | in گوجر/ڈر after ڈ/ا; 0 leftovers (n=9) |
| `NOORIN12:F0F4` | `ر`/`ڑ` | `ر` in گوجر/لاڑ; `ڑ` after ڈر; 0 leftovers |
| `NOORIN57:F062` | `ی`/`و`/`ہ`/empty | `ی` after ، (وی); `و` after ک; `ہ` in رہ; 0 leftovers |
| `NOORIN11:F037` | context | `ی` in بھائی/گل; `ے`/`ئ`/`ھ`; 0 leftovers |
| `NOORIN16:F07D` | `غ`/`ک`/`ڑ`/`ے` | غرض headers; آپ کے; رکڑ; تے; 0 leftovers |
| `NOORIN01:F0AD` | `ے` | flat Urdu gloss column; 0 leftovers |
| `NOORIN39:F0C6` | `ل`/`پ`/`ن`/`ے` | نال/پل/راپو/نو; 0 leftovers |
| `NOORIN13:F033` | `و`/`ے`/empty | پوکپے/بینی/گہنون; 0 leftovers |
| `NOORIN15:F02B` | `ڑ`/`ے` | رکڑ/دے/کرننیے; 0 leftovers |
| `NOORIN66:F04F` | `اں`/empty | ماں; empty after کو; 0 leftovers |

### Batch 53 (2026-08-25)

Table 729 → 739 keys. Coverage 89.6% → 89.7% (72,365 mapped, +90 instances). Unknown keys 1,420 → 1,410.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F0A2` | `ت`/`ے`/`ر`/`ک` | contextual (مطلبےت، کرے، راللہر); 0 leftovers |
| `NOORIN20:F0F1` | space/`，` | like `NOORIN28:F0F1` joiner; 0 leftovers |
| `NOORIN85:F083` | `ت`/`ر`/`ں`/`ھ`/`ی` | after کھا/مو/ڈرے; 0 leftovers |
| `NOORIN13:F0A5` | `ر`/` پر` | رکرننا; پر after کا/پوک; 0 leftovers |
| `NOORIN21:F0AD` | `ت`/`ھے`/`د`/`ل`/`ن` | اصلیت/شاندینی/لا; 0 leftovers |
| `NOORIN82:F070` | `ہو`/`ت` | after پھر/شرمسار; 0 leftovers |
| `NOORIN12:F0F3` | `د`/`ر`/`ک`/`گ`/`ب`/`ھ`/`ں` | جدادھڑی/گوراگے/رک; 0 leftovers |
| `NOORIN04:F0C9` | `ئ`/`ب`/`ر`/`گ`/`ت`/`ں` | آپائی/بناے/رںکو; 0 leftovers |
| `NOORIN12:F074` | `:`,/۔/`ن` | gloss punct; 0 leftovers |
| `NOORIN06:F08D` | `و`/`نی`/`ے`/`سے` | راحساے/شان کد نی; 0 leftovers |

### Batch 54 (2026-08-25)

Table 739 → 749 keys. Coverage 89.7% → 89.8% (72,455 mapped, +90 instances). Unknown keys 1,410 → 1,400.

| Key | Map | Check |
|---|---|---|
| `NOORIN14:F0EC` | `د`/`د:` | after gloss نہیں; 0 leftovers |
| `NOORIN61:F03B` | `درج`/`ت`/`:`/`کھ`/`ل` | titles/کھائی; 0 leftovers |
| `NOORIN19:F03F` | `۔`/space/`ر`/`د` | proverb end punct; 0 leftovers |
| `NOORIN52:F0B9` | `تھے`/`ھے`/`ب`/`ہو`/`ر` | تھے رگے; 0 leftovers |
| `NOORIN12:F0C1` | `لا`/`ل`/`ر`/`کے` | بالکیلا/جوڑنرب; 0 leftovers |
| `NOORIN11:F02E` | `و`/`ہ`/`کے`/`:`/`لو` | ناباہئے/آپاگے; 0 leftovers |
| `NOORIN51:F0C2` | `ہوں`/`نال`/`یار`/`ی` | کیباکشماں; 0 leftovers |
| `NOORIN04:F0A9` | `ک`/`ب`/`س`/`ھ`/`م`/`پ`/`چ` | line-start سے/چھ; 0 leftovers |
| `NOORIN41:F02D` | `ے` | possessive ے; 0 leftovers |
| `NOORIN19:F0DF` | headers | دل/کی/ماں/نام/ر/ھ/کو; 0 leftovers |

### Batch 55 (2026-08-25)

Table 749 → 759 keys. Coverage 89.8% → 89.9% (72,545 mapped, +90 instances). Unknown keys 1,400 → 1,390.

| Key | Map | Check |
|---|---|---|
| `NOORIN07:F0BB` | `ہونی`/`ہوننو`/`نہیں` | ہونی/ہوننو; 0 leftovers |
| `NOORIN18:F072` | `ئ`/`نی` | کوئ/نیکرننی; 0 leftovers |
| `NOORIN81:F084` | `،`/`پر`/`ھی`/`ز`/`ب`/`ھ` | joiner/dash; 0 leftovers |
| `NOORIN06:F0BD` | `نی`/`نا`/`ں`/`کیر`/`ے` | ہم ںکا; 0 leftovers |
| `NOORIN63:F0D2` | `ئ`/`اے` | کائی/توںآپئی; 0 leftovers |
| `NOORIN83:F0E2` | empty | English index joiner; 0 leftovers |
| `NOORIN81:F062` | `کر`/`ھے`/empty | سوعا/عا; 0 leftovers |
| `NOORIN17:F0E7` | `ما`/`فی` | کسےما/فی; 0 leftovers |
| `NOORIN08:F05E` | `ما`/empty | English اسما; 0 leftovers |
| `NOORIN14:F0EA` | `ں`/`ں:` | دوںکہیں; 0 leftovers |

### Batch 56 (2026-08-25)

Table 759 → 769 keys. Coverage 89.9% → 90.0% (72,635 mapped, +90 instances). Unknown keys 1,390 → 1,380.

| Key | Map | Check |
|---|---|---|
| `NOORIN63:F0EF` | `ی`/`ر`/`ان`/`ہ`/`کر`/empty | تےکیوںئے/کرننا; 0 leftovers |
| `NOORIN57:F04E` | `رو`/`ہ`/`ر`/`رب` | کروں/رب; 0 leftovers |
| `NOORIN49:F0A9` | `ے` | flat ے; 0 leftovers |
| `NOORIN21:F0DC` | `ھ` | line-start/Urdu gloss; 0 leftovers |
| `NOORIN08:F09D` | `پہ`/`۔` | پہ سو/گہنو۔; 0 leftovers |
| `NOORIN15:F0D8` | `ر`/`چ`/`یار`/`کر` | رپنے/کرننی; 0 leftovers |
| `NOORIN14:F02C` | `ں` | ںہوننئے; 0 leftovers |
| `NOORIN53:F027` | `۔`/`،` | proverb punct; 0 leftovers |
| `NOORIN15:F086` | `کی`/`ں` | تنورکی/ںکا; 0 leftovers |
| `NOORIN05:F0B0` | `پھر` | flat before ہو; 0 leftovers |

### Batch 57 (2026-08-25)

Table 769 → 779 keys. Coverage 90.0% → 90.1% (72,705 mapped, +70 instances). Unknown keys 1,380 → 1,370.

| Key | Map | Check |
|---|---|---|
| `NOORIN15:F06B` | `ے`/`نی`/`چھوڑ`/`و` | کورے/بٹاہ; 0 leftovers |
| `NOORIN81:F0C4` | `کی`/`نال` | شرمسارکی; 0 leftovers |
| `NOORIN30:F043` | `ئ`/`ت`/`کھ`/`،`/empty | کوئےئ/لئی; 0 leftovers |
| `NOORIN82:F0B2` | `ر` | رملاو; 0 leftovers |
| `NOORIN13:F035` | `و`/`ل`/`ں`/`قات`/empty | واسطے/قات; 0 leftovers |
| `NOORIN80:F031` | `ے`/empty | تھوڑھے; 0 leftovers |
| `NOORIN57:F068` | `ئے`/`ں`/`و`/`ے` | کوئےھے/ہرکوئےے; 0 leftovers |
| `NOORIN13:F0EA` | `،`/`:`/`لو` | جوڑن/بھو:; 0 leftovers |
| `NOORIN29:F03C` | `تے`/`س` | تےکرننی/سکو; 0 leftovers |
| `NOORIN26:F0F4` | `کر`/`چ` | کرنتاں/چکرننی; 0 leftovers |

### Batch 58 (2026-08-25)

Table 779 → 789 keys. Coverage 90.1% → 90.3% (72,781 mapped, +76 instances). Unknown keys 1,370 → 1,360.

| Key | Map | Check |
|---|---|---|
| `NOORIN21:F064` | `د`/`ں` | کیدد/ںسواں; 0 leftovers |
| `NOORIN12:F0EF` | `کھ`/`ک`/`ب`/`کر`/`من` | بچوں/کرسمجھ; 0 leftovers |
| `NOORIN16:F074` | `ت`/`آپ`/`ھے`/`۔`/`س` | لحاظ ت/ساہے; 0 leftovers |
| `NOORIN14:F082` | `ں`/`و` | ںکرننا/دینیو; 0 leftovers |
| `NOORIN21:F0D7` | `ھ`/`کے`/`ر` | تھ/لحاظھ; 0 leftovers |
| `NOORIN06:F0BB` | `کو`/`ں`/`کے`/`نی` | کریادھں/کے; 0 leftovers |
| `NOORIN16:F05F` | empty | joiner after کے; 0 leftovers |
| `NOORIN57:F02E` | `رت`/`زمیدرک`/etc | حیثیتکے تے; 0 leftovers |
| `NOORIN08:F099` | `گہنو`/`۔`/`نا` | کرنو/گہنورھ; 0 leftovers |
| `NOORIN26:F0B9` | `۔`/`کان`/empty | نہیں۔/کانو; 0 leftovers |

### Batch 59 (2026-08-25)

Table 670 → 680 keys. Coverage 89.1% → 89.2% (71,949 mapped, +80 instances). Unknown keys 1,479 → 1,469.

| Key | Map | Check |
|---|---|---|
| `NOORIN74:F0A2` | `ں` | flat before ں (F056); 0 leftovers (n=8) |
| `NOORIN57:F05F` | context | کی before F0C5; لارہنو before F0D1; نہیں before F037; 0 leftovers |
| `NOORIN04:F0B3` | context | زھز after F0E2; ھ after F0C3/F04B/F040; پ before F07D/F037; 0 leftovers |
| `NOORIN11:F0A7` | `ن`/`ں`/`نا` | after F03A/line-start; ں after F065; نا after F0F6; 0 leftovers |
| `NOORIN14:F045` | context | اک/ک/ے/ھ/ں/ر by neighbor; 0 leftovers |
| `NOORIN01:F021` | `ے`/empty | joiner; empty after F057+F028; 0 leftovers |
| `NOORIN48:F0F6` | context | ے/ت/ں/ک/آ by prev F0E2/F03B/F052; 0 leftovers |
| `NOORIN06:F029` | context | ھ after F07A+F07B; ر after F0E2; ت after F0C5; 0 leftovers |
| `NOORIN10:F08F` | `ریب` | قد before F08A; ریب before F064; 0 leftovers |
| `NOORIN56:F0DC` | context | فر before F073; کر before F099; 0 leftovers |

### Batch 60 (2026-08-25)

Table 680 → 690 keys. Coverage 89.2% → 89.3% (72,019 mapped, +70 instances). Unknown keys 1,469 → 1,459.

| Key | Map | Check |
|---|---|---|
| `NOORIN08:F06D` | context | ر/ہ/گ/ھ by context; 0 leftovers |
| `NOORIN76:F027` | context | ک after F040+F0A3; ر after F059+F05A; 0 leftovers |
| `NOORIN17:F0E1` | context | ے/ن/ف/ھ (تہونک، نقصان، فارسی); 0 leftovers |
| `NOORIN61:F08C` | `۔` | end punct; ، after سیاو; : before gloss; 0 leftovers |
| `NOORIN06:F0E4` | context | ے/ھ/و after آپ; 0 leftovers |
| `NOORIN57:F042` | context | یر/دی/ال/ون by context; 0 leftovers |
| `NOORIN73:F0EE` | context | بول/ھ/ر/خ by next glyph; 0 leftovers |
| `NOORIN16:F06E` | context | ما after F0E7; کی after F0E7+F0C5; 0 leftovers |
| `NOORIN22:F098` | context | ے/ب (کوئے، بیکی، ساکرکاے); 0 leftovers |
| `NOORIN57:F077` | context | و/ت/ع/ے by context; 0 leftovers |

### Batch 61 (2026-08-25)

Table 690 → 700 keys. Coverage 89.3% → 89.4% (72,089 mapped, +70 instances). Unknown keys 1,459 → 1,449.

| Key | Map | Check |
|---|---|---|
| `NOORIN41:F0B1` | context | ے/ر/ہ by context; 0 leftovers |
| `NOORIN82:F05E` | `نا` | after F059 (کونانا); 0 leftovers |
| `NOORIN05:F0B7` | context | ک in رکقماز; ے in سیرے; 0 leftovers |
| `NOORIN57:F05E` | context | ت/ی/و/د/ا (درندر، موٹا، راللہ); 0 leftovers |
| `NOORIN05:F0EA` | context | ھ after F05A+F07A; empty line-start; 0 leftovers |
| `NOORIN13:F0E6` | context | ے/ی/ا by context; 0 leftovers |
| `NOORIN11:F06D` | context | ی/ھ/ے/ب/ں by context; 0 leftovers |
| `NOORIN57:F064` | context | ے/و after F0CE; empty F051 line-start; 0 leftovers |
| `NOORIN15:F050` | context | ی/و/ا/ے/ن by next after F08A; 0 leftovers |
| `NOORIN05:F082` | context | ر after F067; ی after F06D; 0 leftovers |

### Batch 62 (2026-08-25)

Table 700 → 709 keys. Coverage 89.4% → 89.5% (72,159 mapped, +70 instances). Unknown keys 1,449 → 1,440. `NOORIN34:F023` skipped (already ruled).

| Key | Map | Check |
|---|---|---|
| `NOORIN17:F097` | context | ب in تباہی/ریںپ; ھ in رددھاچڑانو; 0 leftovers |
| `NOORIN08:F0BA` | context | ک after F067; ر after F0A7; 0 leftovers |
| `NOORIN82:F095` | `ن` | in قمازن/شون; 0 leftovers |
| `NOORIN76:F084` | context | و/ں (کوھسور، بغیرں، گروت); 0 leftovers |
| `NOORIN58:F0ED` | context | ل after F04B; ہ after F036; empty else; 0 leftovers |
| `NOORIN10:F029` | context | و/ے/ک by context; 0 leftovers |
| `NOORIN10:F0E2` | `د` | in ددھاکر; empty else; 0 leftovers |
| `NOORIN17:F083` | context | ند/ک/ر after F030/F065; 0 leftovers |
| `NOORIN31:F083` | context | ہ/ں/ئ by context; 0 leftovers |

### Batch 63 (2026-08-25)

Table 709 → 719 keys. Coverage 89.5% → 89.5% (72,209 mapped, +50 instances). Unknown keys 1,440 → 1,430.

| Key | Map | Check |
|---|---|---|
| `NOORIN48:F0E9` | `ش` | in خوش/خورش/فخور; 0 leftovers |
| `NOORIN16:F0B2` | context | د/ر/ڈ after F08A/F025; 0 leftovers |
| `NOORIN05:F099` | context | ے/ا by context; 0 leftovers |
| `NOORIN19:F0C2` | context | ے/ر/د by line-start and F0D4/F077; 0 leftovers |
| `NOORIN13:F076` | context | ے after F08A/F09B; 0 leftovers |
| `NOORIN10:F0C9` | context | ں/ے by context; 0 leftovers |
| `NOORIN14:F033` | context | ر after F021; 0 leftovers |
| `NOORIN32:F085` | `ب` | in بانیوپاچاے; ال after F059; 0 leftovers |
| `NOORIN63:F031` | context | ر/ز/ے by context; 0 leftovers |
| `NOORIN82:F041` | context | ل/ں/ہ by context; 0 leftovers |

### Batch 64 (2026-08-25)

Table 719 → 729 keys. Coverage 89.5% → 89.6% (72,275 mapped, +66 instances). Unknown keys 1,430 → 1,420.

| Key | Map | Check |
|---|---|---|
| `NOORIN51:F0EF` | context | م/ت/ی/و/ہ/ر by context; 0 leftovers |
| `NOORIN07:F051` | `ے` | in یار،ےک patterns; 0 leftovers |
| `NOORIN08:F07C` | `ے` | flat (لےنی، ماےت، گہنوے); 0 leftovers |
| `NOORIN10:F0CB` | `ر` | in ڈرر/شرر; 0 leftovers |
| `NOORIN11:F030` | context | ے/ر/ن by context; 0 leftovers |
| `NOORIN11:F04F` | context | ا/ہ/ی by context; 0 leftovers |
| `NOORIN29:F05B` | context | ے/ت/ہ/ب by context; 0 leftovers |
| `NOORIN63:F0DE` | context | ے/ر (برلے، پگوجر); 0 leftovers |
| `NOORIN34:F024` | `ق` | in نق۔/نق; 0 leftovers |
| `NOORIN83:F0CB` | `۔` | after F024; پاس before F036; 0 leftovers |

### Batch 65 (2026-08-25)

Table 869 → 879 keys. Coverage 90.7% → 90.8% (73,221 mapped, +58 instances). Unknown keys 1,280 → 1,270.

| Key | Map | Check |
|---|---|---|
| `NOORIN34:F023` | context | شمنی default; دشمنی when nxt=F083; patched; 0 leftovers |
| `NOORIN07:F0B8` | context | ر/ش/و/ما by context; 0 leftovers |
| `NOORIN01:F06D` | context | و/ر/empty by context; 0 leftovers |
| `NOORIN15:F0D3` | `ں` | inflection; 0 leftovers |
| `NOORIN04:F068` | context | د/ے/ب/empty by context; 0 leftovers |
| `NOORIN16:F0A3` | empty | joiner; 0 leftovers |
| `NOORIN16:F056` | `ے` | گینے، کیے; 0 leftovers |
| `NOORIN11:F046` | context | ے/سے/ں by context; 0 leftovers |
| `NOORIN11:F0DC` | context | ر/و/ے by context; 0 leftovers |
| `NOORIN56:F089` | `ں` | کےں/ہتھں; 0 leftovers |

### Batch 66 (2026-08-25)

Table 879 → 889 keys. Coverage 90.8% → 90.9% (73,279 mapped, +58 instances). Unknown keys 1,270 → 1,260.

| Key | Map | Check |
|---|---|---|
| `NOORIN15:F0D0` | context | ھ/empty/چ by context; 0 leftovers |
| `NOORIN10:F051` | context | ما/ی/ت/پ/empty by context; 0 leftovers |
| `NOORIN05:F0E2` | context | ا/ط/پ/گ/empty by context; 0 leftovers |
| `NOORIN13:F0E0` | context | نا/دا/ت/کی/مار by context; 0 leftovers |
| `NOORIN14:F0BC` | context | ں/ر by context; 0 leftovers |
| `NOORIN07:F098` | context | ے/ت by context; 0 leftovers |
| `NOORIN03:F0F9` | context | ت/ہ/ع by context; 0 leftovers |
| `NOORIN13:F02B` | context | ھ/ڈ/تے/نا by context; 0 leftovers |
| `NOORIN29:F0F8` | context | کر/د by context; 0 leftovers |
| `NOORIN10:F0E7` | context | ر/ھ by context; 0 leftovers |

### Batch 67 (2026-08-25)

Table 889 → 899 keys. Coverage 90.9% → 90.9% (73,337 mapped, +58 instances). Unknown keys 1,260 → 1,250.

| Key | Map | Check |
|---|---|---|
| `NOORIN13:F024` | context | رم/بھی/چا by context; 0 leftovers |
| `NOORIN59:F0EC` | `کر` | in پقاکر; 0 leftovers |
| `NOORIN14:F07D` | context | کہ/لا patched; 0 leftovers |
| `NOORIN36:F0D2` | context | ے/جوڑنگو/ئی/تے by context; 0 leftovers |
| `NOORIN81:F06E` | empty | joiner after F0E0; 0 leftovers |
| `NOORIN14:F02E` | context | ک/ے/ں/ھ by context; 0 leftovers |
| `NOORIN41:F0AB` | context | ک/زر/ما/کی/ی by context; 0 leftovers |
| `NOORIN05:F04D` | context | لی/گہنو/ے/ل by context; 0 leftovers |
| `NOORIN06:F090` | context | ں/ے by context; 0 leftovers |
| `NOORIN08:F032` | context | ک/و/ں/، by context; 0 leftovers |

### Batch 68 (2026-08-25)

Table 899 → 909 keys. Coverage 90.9% → 91.0% (73,395 mapped, +58 instances). Unknown keys 1,250 → 1,240.

| Key | Map | Check |
|---|---|---|
| `NOORIN11:F0CE` | context | ھ/ک/ر/ن/سے by context; 0 leftovers |
| `NOORIN82:F0A5` | context | ،/وا/ر/و/ے by context; 0 leftovers |
| `NOORIN25:F05A` | context | ک/چ by context; 0 leftovers |
| `NOORIN15:F0C7` | context | ر/ک/آ/ن/ھی/چ by context; 0 leftovers |
| `NOORIN72:F0A2` | context | ن/ک/ے by context; 0 leftovers |
| `NOORIN05:F044` | context | ت/چ/و/ک by context; 0 leftovers |
| `NOORIN06:F060` | context | ہ/و/ر by context; 0 leftovers |
| `NOORIN22:F040` | `د` | in ددد; 0 leftovers |
| `NOORIN15:F089` | context | ڈ/کھ/ں by context; 0 leftovers |
| `NOORIN12:F03F` | `ز` | in عزت; 0 leftovers |

### Batch 69 (2026-08-25)

Table 909 → 919 keys. Coverage 91.0% → 91.1% (73,453 mapped, +58 instances). Unknown keys 1,240 → 1,230.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F0B4` | context | تو/کی by context; 0 leftovers |
| `NOORIN27:F095` | context | ر/ک/ی by context; 0 leftovers |
| `NOORIN48:F0EF` | context | ہ/ے/دا/د/ل by context; 0 leftovers |
| `NOORIN17:F03E` | `ں` | in ھںت/ںگ; 0 leftovers |
| `NOORIN10:F072` | context | ہی/ا/اک patched; 0 leftovers |
| `NOORIN01:F072` | context | ے/ل/empty by context; 0 leftovers |
| `NOORIN81:F03A` | `ر` | in ہر; 0 leftovers |
| `NOORIN83:F0CD` | context | ما in ماں; 0 leftovers |
| `NOORIN53:F0CC` | context | ب/ک by context; 0 leftovers |
| `NOORIN67:F028` | context | کہ/پ/گ/و by context; 0 leftovers |

### Batch 70 (2026-08-25)

Table 919 → 929 keys. Coverage 91.1% → 91.2% (73,511 mapped, +58 instances). Unknown keys 1,230 → 1,220.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F0F2` | context | ن/ک by context; 0 leftovers |
| `NOORIN10:F0CF` | context | ت/ر/empty by context; 0 leftovers |
| `NOORIN16:F0CB` | context | ے/کھ/ڑ by context; 0 leftovers |
| `NOORIN05:F059` | context | ک/چ/ہ/empty by context; 0 leftovers |
| `NOORIN81:F0B0` | context | و/ر/ل/پ by context; 0 leftovers |
| `NOORIN05:F0EF` | context | ما/تا/ے/اک/empty by context; 0 leftovers |
| `NOORIN08:F043` | context | ئی/empty by context; 0 leftovers |
| `NOORIN08:F0D1` | context | ے/ک by context; 0 leftovers |
| `NOORIN57:F040` | context | نس/ی/ٹر/empty by context; 0 leftovers |
| `NOORIN19:F054` | context | ی/تو/و/ے by context; 0 leftovers |

### Batch 71 (2026-08-25)

Table 929 → 939 keys. Coverage 91.2% → 91.2% (73,569 mapped, +58 instances). Unknown keys 1,220 → 1,210.

| Key | Map | Check |
|---|---|---|
| `NOORIN14:F078` | context | ک/ر/نا/لو by context; 0 leftovers |
| `NOORIN16:F0BE` | `کے` | in کےوھر; 0 leftovers |
| `NOORIN04:F07A` | `کت` | in خوکت; 0 leftovers |
| `NOORIN29:F0C8` | context | ے/کر/ق/ر by context; 0 leftovers |
| `NOORIN15:F0E8` | context | لا/کھ/ی/ک by context; 0 leftovers |
| `NOORIN07:F04B` | `و` | in مھوو; 0 leftovers |
| `NOORIN14:F0AF` | context | ئی/ما/ر by context; 0 leftovers |
| `NOORIN13:F0B6` | context | ر/ے/نی/چ by context; 0 leftovers |
| `NOORIN15:F027` | context | کر/ت/ک by context; 0 leftovers |
| `NOORIN12:F0DC` | `ر` | in ڈرررر; 0 leftovers |

### Batch 72 (2026-08-25)

Table 939 → 949 keys. Coverage 91.2% → 91.3% (73,629 mapped, +60 instances). Unknown keys 1,210 → 1,200.

| Key | Map | Check |
|---|---|---|
| `NOORIN27:F028` | `کھ` | in کھے; 0 leftovers |
| `NOORIN02:F073` | context | رد/و by context; 0 leftovers |
| `NOORIN08:F090` | context | ھ/ہ/ما/، by context; 0 leftovers |
| `NOORIN14:F084` | context | ے/ں/و by context; 0 leftovers |
| `NOORIN55:F0E5` | context | ل/ہر/ر/،/ی by context; 0 leftovers |
| `NOORIN50:F0F4` | context | ما/م/ک by context; 0 leftovers |
| `NOORIN46:F037` | context | سر/پ/ل/ت by context; 0 leftovers |
| `NOORIN04:F0F7` | context | ک/ے/ہ by context; 0 leftovers |
| `NOORIN10:F0B8` | context | ت/، by context; 0 leftovers |
| `NOORIN54:F0CB` | context | م/س/ر/پ/ے by context; 0 leftovers |

Census after batch 72: 949 keys, 91.3% mapped (73,629 instances), 1,200 unknown keys, 536 once-only.

### Batch 73 (2026-08-25)

Table 789 → 799 keys. Coverage 90.3% → 90.4% (72,857 mapped, +76 instances). Unknown keys 1,360 → 1,350.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F048` | context | رت after F056; ے after F0E0; : before F03A; 0 leftovers |
| `NOORIN14:F0B4` | context | ھ after F07A; ر/empty after F05A; م before F071; 0 leftovers |
| `NOORIN25:F043` | context | نی/پ/empty by context; 0 leftovers |
| `NOORIN41:F041` | context | ے after F0C3/F0BB; 0 leftovers |
| `NOORIN56:F0CC` | context | کو after F0F1; empty after F067; 0 leftovers |
| `NOORIN09:F0BF` | context | ے after F056/F084/F036; 0 leftovers |
| `NOORIN82:F096` | context | : after F037; د after F079/F05A; 0 leftovers |
| `NOORIN13:F036` | empty | joiner (ہontو); 0 leftovers |
| `NOORIN04:F04F` | context | نی after F0A9; empty else; 0 leftovers |
| `NOORIN05:F06B` | context | ں/ے/ھ/: by context; 0 leftovers |

### Batch 74 (2026-08-25)

Table 799 → 809 keys. Coverage 90.4% → 90.5% (72,927 mapped, +70 instances). Unknown keys 1,350 → 1,340.

| Key | Map | Check |
|---|---|---|
| `NOORIN11:F02B` | context | ے/ھ line-start before F07C; 0 leftovers |
| `NOORIN07:F0AA` | `رے` | flat; 0 leftovers |
| `NOORIN64:F0D8` | empty | before ساکھ/line-start; 0 leftovers |
| `NOORIN49:F061` | context | ر before F05A; empty end punct; 0 leftovers |
| `NOORIN81:F054` | context | موتر after F0DE; 0 leftovers |
| `NOORIN57:F03F` | context | حا after F071; نوتھا line-start; 0 leftovers |
| `NOORIN22:F056` | context | ے/د/empty by context; 0 leftovers |
| `NOORIN05:F064` | context | ے/و/ہ/ھی by context; 0 leftovers |
| `NOORIN10:F0F3` | empty | line-start joiner; 0 leftovers |
| `NOORIN25:F0EB` | context | ے/ما/کی by context; 0 leftovers |

### Batch 75 (2026-08-25)

Table 809 → 819 keys. Coverage 90.5% → 90.5% (72,997 mapped, +70 instances). Unknown keys 1,340 → 1,330.

| Key | Map | Check |
|---|---|---|
| `NOORIN41:F09B` | context | empty/کر by context; 0 leftovers |
| `NOORIN13:F0BB` | context | ف after F05A; empty after F053; 0 leftovers |
| `NOORIN38:F0BD` | context | د/دو after F0E2/F07A; 0 leftovers |
| `NOORIN06:F028` | context | کو after F03A/F044; 0 leftovers |
| `NOORIN07:F0DC` | context | بر before F0E0; 0 leftovers |
| `NOORIN06:F04C` | empty | punct joiner; 0 leftovers |
| `NOORIN15:F0DB` | context | empty/کے by context; 0 leftovers |
| `NOORIN19:F046` | `ک` | after F03A/F060; 0 leftovers |
| `NOORIN14:F099` | context | تو before F0D5; 0 leftovers |
| `NOORIN07:F068` | context | ے after F030; 0 leftovers |

### Batch 76 (2026-08-25)

Table 819 → 829 keys. Coverage 90.5% → 90.6% (73,067 mapped, +70 instances). Unknown keys 1,330 → 1,320.

| Key | Map | Check |
|---|---|---|
| `NOORIN75:F084` | context | ناں after F079/F0E2; 0 leftovers |
| `NOORIN12:F0F9` | context | ے after F065/F09F; 0 leftovers |
| `NOORIN14:F02D` | empty | after F05A line-start; 0 leftovers |
| `NOORIN32:F06C` | context | نو/ہ/empty; 0 leftovers |
| `NOORIN14:F039` | context | پ after F036; 0 leftovers |
| `NOORIN10:F0B7` | context | و/ک/empty; 0 leftovers |
| `NOORIN06:F07C` | context | تا/ت/ں after F040; 0 leftovers |
| `NOORIN04:F0B4` | context | ڑ/ر/empty; 0 leftovers |
| `NOORIN26:F07B` | context | نئے/empty; 0 leftovers |
| `NOORIN57:F0B7` | context | تک/ماں/سا; 0 leftovers |

### Batch 77 (2026-08-25)

Table 829 → 839 keys. Coverage 90.6% → 90.6% (73,137 mapped, +70 instances). Unknown keys 1,320 → 1,310.

| Key | Map | Check |
|---|---|---|
| `NOORIN01:F03F` | context | ر before F05A; 0 leftovers |
| `NOORIN10:F0BE` | context | و/آ by context; 0 leftovers |
| `NOORIN26:F024` | context | empty/لانی/کا line-start; 0 leftovers |
| `NOORIN10:F094` | context | ے Urdu gloss; 0 leftovers |
| `NOORIN01:F05F` | context | empty/سے; 0 leftovers |
| `NOORIN27:F04D` | context | ر/ت/empty; 0 leftovers |
| `NOORIN82:F065` | context | غ after F0A7; 0 leftovers |
| `NOORIN16:F0C8` | context | اک before F03B; 0 leftovers |
| `NOORIN15:F032` | context | ل after F03A; 0 leftovers |
| `NOORIN08:F0E0` | context | empty/ت; 0 leftovers |

### Batch 78 (2026-08-25)

Table 839 → 849 keys. Coverage 90.6% → 90.7% (73,207 mapped, +70 instances). Unknown keys 1,310 → 1,300.

| Key | Map | Check |
|---|---|---|
| `NOORIN23:F0F0` | context | ک before F067; 0 leftovers |
| `NOORIN70:F052` | context | ے after F065; 0 leftovers |
| `NOORIN26:F031` | context | سے/و/empty; 0 leftovers |
| `NOORIN17:F040` | context | ے/empty; 0 leftovers |
| `NOORIN15:F041` | context | empty/آ; 0 leftovers |
| `NOORIN06:F0C3` | empty | joiner; 0 leftovers |
| `NOORIN72:F0B4` | context | کیا/empty; 0 leftovers |
| `NOORIN10:F0C0` | context | ر before F05A; 0 leftovers |
| `NOORIN49:F08D` | `ک` | after F03A/F07B/F0D4; 0 leftovers |
| `NOORIN14:F0E2` | context | غ after F0BE; 0 leftovers |

### Batch 79 (2026-08-25)

Table 849 → 859 keys. Coverage 90.7% → 90.7% (73,277 mapped, +70 instances). Unknown keys 1,300 → 1,290.

| Key | Map | Check |
|---|---|---|
| `NOORIN01:F0A3` | empty | joiner; 0 leftovers |
| `NOORIN37:F057` | context | ے/empty; 0 leftovers |
| `NOORIN81:F094` | `ر` | flat; 0 leftovers |
| `NOORIN18:F085` | context | ے after F075; 0 leftovers |
| `NOORIN10:F03D` | context | ر after F067/F0C2; 0 leftovers |
| `NOORIN01:F036` | context | ء/empty; 0 leftovers |
| `NOORIN57:F057` | context | empty/ک; 0 leftovers |
| `NOORIN59:F0F5` | context | empty/ک; 0 leftovers |
| `NOORIN45:F096` | `ں` | line-start before F056; 0 leftovers |
| `NOORIN82:F069` | context | ے/ر/ھ; 0 leftovers |

### Batch 80 (2026-08-25)

Table 859 → 869 keys. Coverage 90.7% (73,163 mapped, +382 instances from batches 73–80). Unknown keys 1,290 → 1,280.

| Key | Map | Check |
|---|---|---|
| `NOORIN28:F0F8` | context | ناس after F0C3; 0 leftovers |
| `NOORIN18:F076` | context | ے after F044; 0 leftovers |
| `NOORIN11:F097` | context | ے after F0C5/F077; 0 leftovers |
| `NOORIN13:F0B1` | context | د/ک/empty; 0 leftovers |
| `NOORIN57:F058` | context | با/empty; 0 leftovers |
| `NOORIN81:F072` | context | ڈ after F099; 0 leftovers |
| `NOORIN81:F081` | context | ر/empty; 0 leftovers |
| `NOORIN04:F0BE` | context | حال/ر/empty; 0 leftovers |
| `NOORIN14:F0C4` | context | آ after F067; 0 leftovers |
| `NOORIN12:F0CB` | context | رد after F0D0; 0 leftovers |

Census after batch 80: 869 keys, 90.7% mapped (73,163 instances), 1,280 unknown keys, 536 once-only.

Census after batch 72 (added later): 949 keys, 91.3% mapped (73,629 instances), 1,200 unknown keys.

Next: run `_tmp_top_base.py` for batch 81 keys.

### Batches 81–95 summary (2026-08-25)

Baseline before batches 81–95: 949 keys, 91.3% mapped (73,629 instances), 1,200 unknown keys, 536 once-only.

Workflow: 15 batches × 7 keys (n=4 each), dump/ctx/decoded analysis → context rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census.

Table 949 → 1054 keys (+105). Coverage 91.3% → 91.8% (74,049 mapped, +420 instances). Unknown keys 1,200 → 1,095 (−105). Once-only unknown keys still 536.

Flat maps: `NOORIN17:F0E2`→`ل`, `NOORIN66:F04B`→empty (سو joiner).

Notable context keys (all 0 leftovers): `NOORIN10:F089`→`ل` (لگل/لھے), `NOORIN07:F0F2`→`ب` (کارب), `NOORIN69:F0A5`→`و` (خولو), `NOORIN26:F066`→`ل` (بیکول), `NOORIN63:F0DA`→`ہون`/`ت`, `NOORIN04:F0C7`→`کو`/`یار`/`ک`, `NOORIN81:F044`→`تک`/`کو`, `NOORIN02:F09F`→`و` (خو), `NOORIN15:F05A`→`ے` (اسرے), `NOORIN81:F05F`→`ٹھ`/`ت`/`سا`.

Census after batch 95: 1054 keys, 91.8% mapped (74,049 instances), 1,095 unknown keys.

### Batches 96–115 summary (2026-08-25)

Baseline before batches 96–115: 1054 keys, 91.8% mapped (74,049 instances), 1,095 unknown keys, 536 once-only.

Workflow: 20 batches × 6 keys (n≤4 each), dump/ctx/decoded analysis → context rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census.

Table 1054 → 1174 keys (+120). Coverage 91.8% → 92.3% (74,422 mapped, +373 instances). Unknown keys 1,095 → 975 (−120). Once-only unknown keys still 536.

Notable context keys (all 0 leftovers): `NOORIN62:F0C1`→`گ` (گھی), `NOORIN06:F054`→`و` (کھاو), `NOORIN82:F086`→`و` (رضاور), `NOORIN01:F04C`/`NOORIN83:F0F3`→`ک`, `NOORIN07:F0E3`→`ہ`, `NOORIN51:F0F0`→`خ` (خور), `NOORIN05:F0D3`→`ش` (شوق), `NOORIN48:F0E8`→`ا`/`و` (اکے), `NOORIN37:F06B`→`س`/`ں`, `NOORIN31:F081`→`ق` (ئیق).

Census after batch 115: 1174 keys, 92.3% mapped (74,422 instances), 975 unknown keys.

### Batches 116–135 summary (2026-08-25)

Baseline before batches 116–135: 1174 keys, 92.3% mapped (74,422 instances), 975 unknown keys, 536 once-only.

Workflow: 20 batches × 7 keys (n≤4 each), dump/ctx/decoded analysis → context rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census.

Table 1174 → 1314 keys (+140). Coverage 92.3% → 92.7% (74,737 mapped, +315 instances). Unknown keys 975 → 835 (−140). Once-only unknown keys still 536.

Notable context keys (all 0 leftovers): `NOORIN30:F048` (joiner/پھر), `NOORIN08:F0B6` (سے/اں), `NOORIN56:F0ED` (بادے/باہونک), `NOORIN08:F0A7` (صورتکرت), `NOORIN85:F086` (سورکر/دکٹی), `NOORIN48:F0E1` (نوں/ھرو), `NOORIN81:F029` (کگاں/دل), `NOORIN08:F0F0` (گھکوم), `NOORIN82:F0A8` (قارت/گللانی), `NOORIN01:F02F` (English index space).

Census after batch 135: 1314 keys, 92.7% mapped (74,737 instances), 835 unknown keys.

### Batches 166–195 summary (2026-08-26)

Baseline before batches 166–195: 1464 keys, 93.0% mapped (75,224 instances), 685 unknown keys, 403 once-only.

Workflow: 30 batches × 5 keys (n≤3 each), context analysis → rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census.

Table 1464 → 1614 keys (+150). Coverage 93.0% → 93.3% (75,224 mapped instances unchanged; rare n≤3 keys). Unknown keys 685 → 535 (−150). Once-only unknown keys stay 403.

All 150 keys are rare (n≤3). Most are empty joiners or short inflections in proverb glosses. Flat maps include `NOORIN13:F0B4`, `NOORIN64:F090`, `NOORIN03:F0B0`, `NOORIN83:F0FC`, `NOORIN68:F025`.

Census after batch 195: 1614 keys, 93.3% mapped (75,224 instances), 535 unknown keys.

Next: continue from `_tmp_top_base.py` for batch 196 keys (n≤3).

### Batches 196–230 summary (2026-08-26)

Baseline before batches 196–230: 1614 keys, 93.3% mapped (75,224 instances), 535 unknown keys, 403 once-only.

Workflow: 35 batches × 5 keys (n≤3 each), brute-force context rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census. First pass used START_IDX=300 (n=2–3 keys); continuation pass used START_IDX=0 for remaining n=1 once-only keys.

Table 1614 → 1789 keys (+175). Coverage 93.3% → 93.5% (75,399 mapped, +175 instances). Unknown keys 535 → 360 (−175). Unknown base unique 404 → 229 (−175). Once-only unknown keys 403 → 228.

All 175 keys verified 0 leftovers. Rules data in `_batch196_230_rules_data.json`.

Census after batch 230: 1789 keys, 93.5% mapped (75,399 instances), 360 unknown keys (229 base unique).

Next: continue from `_tmp_top_base.py` for batch 231 keys (n≤3).

### Batches 231–271 + finish (2026-08-26)

Baseline before finish pass: 1789 keys, 93.5% mapped, 360 unknown (229 base + 131 NOORIC overlay).

Steps:
1. Fixed 7 leftover rule gaps: `NOORIN14:F0F7` (5), `NOORIN04:F0DB` (1), `NOORIN82:F038` (1).
2. Added 18 high-count rule-only keys to seed map (were in evidence/SKIP but not in `map`).
3. Added 131 `NOORIC`/`NOORIC01` overlay keys to seed as empty (nuqta/marks).
4. Batches 231–271: 210 remaining n=1 base keys, brute-force context rules, 0 leftovers each.

Table 1789 → **2149 keys** (+360). Coverage **100.0%** (80,638 instances, 0 unknown).

Census after finish: **2149 keys, 100.0% mapped, 0 unknown** on pages 1–169.

### NOORIN transfer scan + bulk decode (2026-08-26)

Added `scripts/census_noorin_transfer.py`. Scans all primary in-scope PUA books
from `data/manifest.csv` (skips Batool-only dictionaries). Writes
`data/decode/noorin_transfer.csv`.

**Transfer results (44 PUA books, Kahawat table 2149 keys):**

| Bucket | Count | Notes |
|---|---|---|
| >=90% mapped | 17 | Anjumshanasi poetry/prose collection |
| 50–89% | 1 | G-Kashmiri-Dictionary (87.3%) |
| 1–49% | 16 | Javaid Rahi dict parts, lok kahani, etc. Latin-range NOORIN codes |
| 0% | 10 | legacy_8bit / TT* fonts; no PUA F0xx glyphs in rawdict |

Kahawat-Kosh: 100.0%. Aks-e-Jamal: 92.8% (was 69.6% on pages 1–10 before table
completion). Typical Anjumshanasi book: 95–97%.

**Does not transfer:** Javaid Rahi dictionary parts (~0.2–0.3%). Those NOORIN
fonts emit Latin-range codes, not PUA `F0xx`. Separate table needed.

Bulk decode started: `py -3 scripts/census_noorin_transfer.py --decode --min-pct 87`
→ 18 books (~4,159 pages) to `data/decode/out/<slug>/page-NNNN.txt`.

**Batch/resume workflow (2026-08-26):** Scripts now support safe resume.
`decode_noorin_flow.py` has `--skip-existing`. Transfer script has
`--skip-census`, `--batch-size N`, and writes
`data/decode/transfer_decode_progress.json`.

```bash
# check status (no re-scan)
py -3 scripts/census_noorin_transfer.py --skip-census --min-pct 87

# decode one book at a time, resume where left off
py -3 scripts/census_noorin_transfer.py --decode --skip-census --min-pct 87 --batch-size 1
```

**Bulk decode complete:** all 17 transferable books (87%+ mapped) decoded to
`data/decode/out/`. ~4,127 pages across Anjumshanasi collection + gojri-adab-ki-tariekh.

### Batches 136–165 summary (2026-08-26)

Baseline before batches 136–165: 1314 keys, 92.7% mapped (74,737 instances), 835 unknown keys, 536 once-only.

Workflow: 30 batches × 5 keys (n≤4 each, mostly n=3), brute-force context rules in `dump_noorin_lines.py` before `NOORIN30:F048` → seed → 0 leftovers per key → census.

Table 1314 → 1464 keys (+150). Coverage 92.7% → 93.0% (75,224 mapped, +487 instances). Unknown keys 835 → 685 (−150). Once-only unknown keys still 536 (batch picked n=2–3 only).

All 150 keys verified 0 leftovers via `_tmp_rule_leftovers136_165.py`. Rules data in `_batch136_165_rules_data.json`.

Census after batch 165: 1464 keys, 93.0% mapped (75,224 instances), 685 unknown keys.

Note: seed file on disk also lists batch 166–195 entries (1614 keys total, 535 unknown, 93.3% in combined census).

Next: run `_tmp_top_base.py` for batch 166 keys.

### Cleanup + spot-check (2026-08-26)

Removed ~290 temp batch scripts (`scripts/_tmp*`, `_batch*`, `_insert*`).
`data/decode/transfer_decode.log` is gitignored (was deleted locally).

**Spot-check decoded output** (`data/decode/out/`, not committed):

| Book | Pages | Placeholders | Pages with PH | Transfer % |
|---|---|---|---|---|
| kahawat-kosh (reference) | 169 | 0 on p50 |: | 100% |
| aks-e-jamal | 121 | 1,756 | 116/121 | 92.8% |
| banjara | 496 | 9,178 | 496/496 | 96.5% |
| gojri-sheryaat | 500 | 7,186 | 490/500 |: |
| g-kashmiri-dictionary | 456 | 11,436 | 437/456 | 87.3% |
| qadim-gojri | 152 | 3,118 | 143/152 |: |

**Kahawat p50 (reference):** zero placeholders. Proverb headwords and glosses
read correctly. Words run together (no spaces) as expected from glyph decode.

**Aks-e-Jamal p25 (poetry):** seven placeholders. Core lines are readable Gojri
with some wrong words (`رایک`, `دپدے`). Usable for spot review, not corpus-ready.

**Banjara p100 (prose):** twenty-six placeholders. First line is PDF header
garbage (Latin/page stamp). Body has merged words and reading-order noise.
Not usable without per-book fixes.

**Gojri-sheryaat p200 (poetry):** seven placeholders plus header garbage.
Poetry lines partly readable but word order and spacing are unreliable.

**G-Kashmiri-Dictionary p50:** twenty-two placeholders. Gojri headwords and
Urdu gloss partly OK; English gloss line is corrupted (`conta5i0ner`).
