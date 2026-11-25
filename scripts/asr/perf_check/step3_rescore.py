"""Step 3: re-score the saved test_predictions.tsv of the SageMaker job without any audio.

Expected (results.json of the job): all 22.66, seen 23.38, unseen 21.57 word error; 8.3 character error overall.
Run: python step3_rescore.py PREDICTIONS_TSV
"""
import sys

from asrlib import group_scores, read_tsv

rows = read_tsv(sys.argv[1])
print(len(rows), "rows")
res = group_scores(rows)
for k, v in res.items():
    print(k, v)
for k, want in (("all", 22.66), ("seen", 23.38), ("unseen", 21.57)):
    print(k, "match" if abs(res[k]["wer"] - want) < 0.005 else f"MISMATCH (want {want})")
