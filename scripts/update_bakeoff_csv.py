"""Rewrite data/gold/bakeoff_results.csv from the current gold text.

Runs scripts/score_gold.py, reads its per-run word error rates and the TOTAL
lines, and replaces the matching rows. A row keeps its setup, role and run
label; only word_error_rate_pct changes. Run it after any edit to a *_gold.txt.

Run: py -3 -X utf8 scripts/update_bakeoff_csv.py
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "gold" / "bakeoff_results.csv"

out = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts" / "score_gold.py")],
                     capture_output=True, text=True, encoding="utf-8", check=True,
                     env={"PYTHONIOENCODING": "utf-8", "SYSTEMROOT": "C:/Windows"}).stdout
runs = {}
for m in re.finditer(r"^(\S+)\s+(\S+_v\d)\s+\d+\s+\d+\s+([\d.]+)%", out, re.M):
    runs[(m.group(1), m.group(2))] = m.group(3)
totals = {m.group(1): m.group(2) for m in re.finditer(r"^\s+TOTAL (\S+?)\s+([\d.]+)%", out, re.M)}
TOTAL_KEY = {"gemini_3.6_flash": "gemini_3.6_flash", "sonnet_4.6": "sonnet_4.6", "composer_2.5": "composer_v1"}

rows = list(csv.DictReader(CSV.open(encoding="utf-8", newline="")))
changed = []
for r in rows:
    if r["page_id"] == "__pooled__":
        new = totals.get(TOTAL_KEY[r["model"]])
    else:
        run = "composer_v1" if r["model"] == "composer_2.5" else f"{r['model']}_{r['prompt']}"
        new = runs.get((r["page_id"], run))
    if new is None:
        raise SystemExit(f"no score for {r['page_id']} {r['model']} {r['prompt']}")
    if abs(float(new) - float(r["word_error_rate_pct"])) > 1e-9:
        changed.append((r["page_id"], r["model"], r["word_error_rate_pct"], new))
        r["word_error_rate_pct"] = new
with CSV.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\r\n")  # as published
    w.writeheader()
    w.writerows(rows)
for c in changed:
    print("changed:", *c)
print(f"{len(changed)} rows changed")
