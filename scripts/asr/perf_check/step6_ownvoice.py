"""Step 6: own-voice test. Two stages around transcribe.py --audio-dir.

  sheet:  python step6_ownvoice.py sheet --pred OWN_PRED.tsv --out SHEET.tsv
          Writes file, model_output, corrected_text (empty). The speaker fills corrected_text by hand.
  score:  python step6_ownvoice.py score --sheet SHEET.tsv [--cv-sentences VALIDATED_TSV]
          Scores model_output against corrected_text (same normalisation as the job), prints each row side by side,
          and, with --cv-sentences, flags any corrected sentence that also appears in Common Voice.
All files stay local: they hold private recordings' text.
"""
import argparse

from asrlib import norm, read_tsv, scores, write_tsv

ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["sheet", "score"])
ap.add_argument("--pred")
ap.add_argument("--out")
ap.add_argument("--sheet")
ap.add_argument("--cv-sentences")
args = ap.parse_args()

if args.mode == "sheet":
    rows = [{"file": r["path"], "model_output": r["hypothesis"], "corrected_text": ""} for r in read_tsv(args.pred)]
    write_tsv(args.out, rows, ["file", "model_output", "corrected_text"])
    print("wrote", args.out, len(rows), "rows; fill the corrected_text column")
else:
    rows = [r for r in read_tsv(args.sheet) if r["corrected_text"].strip()]
    print(len(rows), "rows with a correction")
    cv = set()
    if args.cv_sentences:
        cv = {norm(r["sentence"]) for r in read_tsv(args.cv_sentences)}
    for r in rows:
        flag = "  [IN COMMON VOICE]" if norm(r["corrected_text"]) in cv else ""
        print(f"{r['file']}\n  model:     {r['model_output']}\n  corrected: {r['corrected_text']}{flag}")
    print("\nTOTAL", scores([r["corrected_text"] for r in rows], [r["model_output"] for r in rows]))
    print("Small set: treat as an anecdote, not an estimate.")
