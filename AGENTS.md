# Agent instructions (Gojri AI)

Follow this file in every Cursor session. The project brief, data inventory,
technical findings, and current status live in `CLAUDE.md`. Treat `CLAUDE.md`
as the source of truth for those facts. Do not copy it here. Update `CLAUDE.md`
when a finding or status changes. Update this file when agent behaviour or
writing rules change.

## Writing (always)

Write all English output in ASD-STE100 Simplified Technical English. Use one
meaning per word, active voice, simple tenses, and short sentences. Do not use
preambles, pleasantries, conversational filler, or vague jargon.

Use no em dashes. Write with natural structure. Use commas, periods, or
conjunctions instead. This is a compositional principle. Apply it during
composition, not as a later edit. Do not write sentences that rely on
interruption or a dramatic pause. Keep this rule unless the user cancels it.

## How to work with this user

- Explain AI/ML in plain terms. Teach as you go.
- The user is a native Gojri and Urdu speaker, fluent in English, and a Gujjar.
  Use that skill for labels, translation checks, and dialect judgement.
- Research and agree before writing pipeline code. The project is still in
  planning except for Stage 0 tools (manifest, gold set, extract scripts,
  Devanagari lexicon pipeline).
- Run Python as `py -3`.
- Do not commit unless the user asks.
- Journal experiments in `LOG.md`. Keep `CLAUDE.md` Status current.

## Lexicon deliverable

Public Devanagari ↔ Gojri Nastaliq lexicon lives in **`data/lexicon/`**
(tracked). Do not publish full PDF page dumps from `data/extracted/` (gitignored).
Upload steps: `data/lexicon/PUBLISH.md`.

## Decode-table work

**NOORIN decode is abandoned (Aug 2026).** Do not rebuild NOORIN tables or
scripts. See `data/archive/noorin-decode-spike/README.md`.

Batool and Quran GID decode scripts remain but are **paused** and not
validated at book scale. **Bulk vision OCR stays paused** until we replan
OCR (likely Gemini API, Tier 1 first).
