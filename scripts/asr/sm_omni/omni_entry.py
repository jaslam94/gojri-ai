"""SageMaker entry: zero-shot test of Meta Omnilingual ASR on the Common Voice Gujari test set (no training).

Channel `data` = s3://$GOJRI_BUCKET/asr/cv-gju-26/ (train.tsv, test.tsv with path, sentence, speaker; clips/).
Each model spec is `card` or `card:lang`, for example `omniASR_LLM_7B_v2:gju_Arab`. The language tag goes only to LLM models.
Scoring is the same as sm_whisper_entry.py (one normalisation on both sides; word and character error; all, seen, unseen speakers),
so the numbers compare with Whisper-small (22.7%) and Whisper-medium (18.3%).

The AWS user cannot read CloudWatch logs, so this script never crashes: install output and every error go to results.json
(/opt/ml/model). Read `install_log` and `errors` there first if a run has no scores.
"""
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import unicodedata

ap = argparse.ArgumentParser()
ap.add_argument("--models", default="omniASR_LLM_300M:gju_Arab,omniASR_LLM_1B:gju_Arab,omniASR_LLM_3B:gju_Arab,omniASR_LLM_7B:gju_Arab,omniASR_LLM_7B:urd_Arab,omniASR_LLM_7B,omniASR_CTC_1B")
ap.add_argument("--batch", type=int, default=4)
ap.add_argument("--limit-eval", type=int, default=0)
ap.add_argument("--fairseq2-index", default="https://fair.pkg.atmeta.com/fairseq2/whl/pt2.8.0/cu128")
args = ap.parse_args()

DATA = os.environ.get("SM_CHANNEL_DATA", "data")
OUT = os.environ.get("SM_MODEL_DIR", "out")
os.makedirs(OUT, exist_ok=True)
results = {"args": vars(args), "install_log": "", "errors": [], "runs": []}


def save():
    with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    results["install_log"] += f"\n$ {cmd}\n(exit {r.returncode})\n" + (r.stdout + r.stderr)[-3000:]
    save()
    return r.returncode


py = sys.executable
sh("apt-get update -qq && apt-get install -y -qq libsndfile1 build-essential cmake")
sh(f"{py} -m pip install -q fairseq2==0.6.0 --extra-index-url {args.fairseq2_index}")
sh(f"{py} -m pip install -q omnilingual-asr jiwer soundfile")
# fairseq2 0.6 needs the CUDA 12.8 build of PyTorch 2.8.0; the SageMaker image ships the CUDA 12.9 build
sh(f"{py} -m pip install -q --force-reinstall torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128 --extra-index-url https://pypi.org/simple")
sh("ldconfig -p | grep -i sndfile")
sh(f"{py} -c \"import torch;print(torch.__version__, torch.version.cuda, torch.cuda.is_available())\"")

try:
    import jiwer
    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio
    from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline
except Exception:
    results["errors"].append("import: " + traceback.format_exc()[-3000:])
    save()
    sys.exit(0)

FOLD = str.maketrans({"ك": "ک", "ي": "ی", "ه": "ہ"})


def norm(s):
    s = unicodedata.normalize("NFC", s)
    s = "".join(c for c in s if not unicodedata.category(c).startswith(("M", "P")))
    return re.sub(r"\s+", " ", s.translate(FOLD)).strip()


def scores(refs, hyps):
    pairs = [(norm(r), norm(h)) for r, h in zip(refs, hyps) if norm(r)]
    rr, hh = [p[0] for p in pairs], [p[1] for p in pairs]
    return {"wer": round(100 * jiwer.wer(rr, hh), 2), "cer": round(100 * jiwer.cer(rr, hh), 2), "n": len(pairs)}


def read(name, limit=0):
    rows = list(csv.DictReader(open(os.path.join(DATA, name), encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    return rows[:limit] if limit else rows


def audio(path):
    x, sr = sf.read(os.path.join(DATA, "clips", path), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != 16000:
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy()
    return x


train, test = read("train.tsv"), read("test.tsv", args.limit_eval)
seen = {r["speaker"] for r in train}


def report(rows, hyps):
    refs = [r["sentence"] for r in rows]
    out = {"all": scores(refs, hyps)}
    for name, keep in (("seen_speakers", lambda r: r["speaker"] in seen), ("unseen_speakers", lambda r: r["speaker"] not in seen)):
        idx = [i for i, r in enumerate(rows) if keep(r)]
        if idx:
            out[name] = scores([refs[i] for i in idx], [hyps[i] for i in idx])
    return out


cache = os.path.expanduser("~/.cache/fairseq2")
specs = [s for s in args.models.split(",") if s]
for n, spec in enumerate(specs):
    card, _, lang = spec.partition(":")
    next_card = specs[n + 1].partition(":")[0] if n + 1 < len(specs) else None
    is_llm = "_LLM_" in card
    t0 = time.time()
    try:
        pipe = ASRInferencePipeline(model_card=card)
        hyps = []
        for i in range(0, len(test), args.batch):
            chunk = test[i:i + args.batch]
            data = [{"waveform": audio(r["path"]), "sample_rate": 16000} for r in chunk]
            kw = {"lang": [lang] * len(chunk)} if (is_llm and lang) else {}
            hyps += [str(h) for h in pipe.transcribe(data, batch_size=args.batch, **kw)]
        run = {"model": card, "lang": lang or None, "seconds": round(time.time() - t0), "test": report(test, hyps)}
        results["runs"].append(run)
        print(spec, run["test"], flush=True)
        tag = re.sub(r"\W+", "_", spec)
        with open(os.path.join(OUT, f"pred_{tag}.tsv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["path", "speaker", "seen", "reference", "hypothesis"])
            for r, h in zip(test, hyps):
                w.writerow([r["path"], r["speaker"], int(r["speaker"] in seen), r["sentence"], h])
        del pipe
    except Exception:
        results["errors"].append(f"{spec}: " + traceback.format_exc()[-3000:])
    try:
        torch.cuda.empty_cache()
        if next_card != card:  # free disk before the next big checkpoint; keep it when the next run uses the same one
            shutil.rmtree(cache, ignore_errors=True)
    except Exception:
        pass
    save()
print("done", flush=True)
