"""SageMaker entry: fine-tune Meta Omnilingual ASR (LLM family) on Common Voice Gujari, pick the best checkpoint on dev, score it on test.

Plan and sources: plans/PLAN-omnilingual-finetune-20261126.md.
Channel `data` = s3://$GOJRI_BUCKET/asr/omni-ft/ made by scripts/asr/omni_ft/make_parquet.py:
  version=0/corpus=cv/split={train,dev,test}/language=gju_Arab/part-00000.parquet, language_distribution_0.tsv, gojri_cv_gju26.yaml,
  splits/{train,dev,test}.tsv (path, sentence, speaker; same row order as the parquet files).
Steps: install the stack (as scripts/asr/sm_omni/omni_entry.py) and clone the training recipe at a pinned tag; register the dataset card
(FAIRSEQ2_USER_ASSET_DIR); run `torchrun -m workflows.recipes.wav2vec2.asr` on all GPUs with model-only checkpoints and NO validation inside
training (smoke tests 2026-11-26: the recipe's validation gathers the full 1B model on every 22 GB GPU and runs out of memory, also once at
the end of training unless `dataset.valid_split` is null, which makes the recipe build no validator); then score every
saved checkpoint on the dev clips ourselves, take the best dev word error, and score that one on the test clips. Checkpoints are registered as
cards (`base:` the original model card, `checkpoint:` the saved shards; fairseq2 reshards on load). Scorer: same as the Whisper and zero-shot
runs (NFC, marks and punctuation removed, ك=ک ي=ی ه=ہ).

The AWS user cannot read CloudWatch logs, so this script never crashes: every stage writes into results.json (/opt/ml/model), and the tail of the
training log is kept there. Read `errors`, `train_log_tail` and `install_log` first when a run has no scores.
"""
import argparse
import csv
import glob
import io
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
ap.add_argument("--model-card", default="omniASR_LLM_1B")
ap.add_argument("--tokenizer", default="omniASR_tokenizer_v1")
ap.add_argument("--num-steps", type=int, default=400)
ap.add_argument("--checkpoint-every", type=int, default=80)
ap.add_argument("--lr", type=float, default=5e-5)
ap.add_argument("--accum", type=int, default=4)
ap.add_argument("--max-num-elements", type=int, default=320000, help="samples per GPU micro-batch (20 s of audio at 16 kHz)")
ap.add_argument("--min-audio-len", type=int, default=8000)
ap.add_argument("--max-audio-len", type=int, default=320000, help="longer clips are skipped (the longest training clip is 15.1 s)")
ap.add_argument("--limit-eval", type=int, default=0, help="cap on dev and test clips (smoke test only)")
ap.add_argument("--upload-ckpt", type=int, default=0, help="1 = copy the best checkpoint to s3://BUCKET/asr/omni-ft/out/<job>/")
ap.add_argument("--bucket", default="gojri-ai-sagemaker-data")
ap.add_argument("--repo-ref", default="0.2.0", help="tag of facebookresearch/omnilingual-asr that holds the recipe")
ap.add_argument("--fairseq2-index", default="https://fair.pkg.atmeta.com/fairseq2/whl/pt2.8.0/cu128")
args = ap.parse_args()

DATA = os.environ.get("SM_CHANNEL_DATA", "data")
OUT = os.environ.get("SM_MODEL_DIR", "out")
JOB = os.environ.get("TRAINING_JOB_NAME", "local")
REPO = "/opt/ml/code/omnilingual-asr-repo"
RUN = "/opt/ml/run"
ASSETS = "/opt/ml/user_assets"
os.makedirs(OUT, exist_ok=True)
results = {"args": vars(args), "install_log": "", "errors": [], "stages": {}}


def save():
    with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)


def sh(cmd, tail=2500, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    results["install_log"] += f"\n$ {cmd}\n(exit {r.returncode})\n" + (r.stdout + r.stderr)[-tail:]
    save()
    return r.returncode


def stage(name):
    results["stages"][name] = round(time.time() - T0)
    save()


T0 = time.time()
py = sys.executable
try:
    # 1. stack
    sh(f"{py} -m pip install -q fairseq2==0.6.0 --extra-index-url {args.fairseq2_index}")
    sh(f"git clone -q --depth 1 --branch {args.repo_ref} https://github.com/facebookresearch/omnilingual-asr {REPO}")
    sh(f"{py} -m pip install -q -e {REPO} jiwer soundfile boto3")
    # fairseq2 0.6 needs the CUDA 12.8 build of PyTorch 2.8.0; the SageMaker image ships the CUDA 12.9 build
    sh(f"{py} -m pip install -q --force-reinstall torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128 --extra-index-url https://pypi.org/simple")
    # fairseq2n decodes flac with the system libsndfile; apt does not work in this container, so expose the copy bundled with `soundfile`
    sh(f"{py} - <<'E'\nimport soundfile, os, glob\nlib = getattr(soundfile, '_libname', None)\nprint('soundfile lib:', lib)\nif not lib or not os.path.exists(lib):\n    c = glob.glob(os.path.join(os.path.dirname(soundfile.__file__), '_soundfile_data', '*.so*'))\n    lib = c[0] if c else None\nos.makedirs('/opt/ml/libs', exist_ok=True)\nif lib:\n    t = '/opt/ml/libs/libsndfile.so.1'\n    if os.path.lexists(t): os.remove(t)\n    os.symlink(lib, t)\n    open('/etc/ld.so.conf.d/sndfile.conf', 'w').write('/opt/ml/libs\\n')\nE")
    sh("ldconfig && ldconfig -p | grep -i sndfile")
    sh(f"{py} -c \"import torch;print('torch', torch.__version__, torch.version.cuda, torch.cuda.device_count())\"")
    sh(f"{py} -m pip show omnilingual-asr fairseq2 | grep -E '^(Name|Version)'")
    stage("install")

    # 2. dataset card, config
    os.makedirs(ASSETS, exist_ok=True)
    card = open(os.path.join(DATA, "gojri_cv_gju26.yaml"), encoding="utf-8").read().replace("DATA_PATH", DATA.rstrip("/"))
    open(os.path.join(ASSETS, "gojri_cv_gju26.yaml"), "w", encoding="utf-8").write(card)
    os.environ["FAIRSEQ2_USER_ASSET_DIR"] = ASSETS
    publish = 10
    cfg = f"""model:
  name: "{args.model_card}"
dataset:
  name: "gojri_cv_gju26"
  train_split: "train"
  valid_split: null
  storage_mode: "MIXTURE_PARQUET"
  task_mode: "ASR"
  mixture_parquet_storage_config:
    dataset_summary_path: "{DATA.rstrip('/')}/language_distribution_0.tsv"
    beta_corpus: 0.5
    beta_language: 0.5
  asr_task_config:
    min_audio_len: {args.min_audio_len}
    max_audio_len: {args.max_audio_len}
    max_num_elements: {args.max_num_elements}
    batch_shuffle_window: 1
    normalize_audio: true
    example_shuffle_window: 1
tokenizer:
  name: "{args.tokenizer}"
optimizer:
  config:
    lr: {args.lr}
trainer:
  data_parallelism: "fsdp"
  fsdp:
    granularity: "stack"
    version: "v1"
    fp32_reduce: false
  freeze_encoder_for_n_steps: 0
  mixed_precision:
    dtype: "torch.bfloat16"
  grad_accumulation:
    num_batches: {args.accum}
regime:
  num_steps: {args.num_steps}
  score_metric: null
  checkpoint_every_n_steps: {args.checkpoint_every}
  publish_metrics_every_n_steps: {publish}
  save_model_only: true
"""
    os.makedirs(RUN, exist_ok=True)
    cfg_path = os.path.join(RUN, "config.yaml")
    open(cfg_path, "w", encoding="utf-8").write(cfg)
    results["config_yaml"] = cfg
    save()

    # 3. training
    ngpu = int(subprocess.run([py, "-c", "import torch;print(torch.cuda.device_count())"], capture_output=True, text=True).stdout.strip() or 1)
    results["gpus"] = ngpu
    train_dir = os.path.join(RUN, "train")
    log_path = os.path.join(RUN, "train.log")
    t1 = time.time()
    with open(log_path, "w", encoding="utf-8") as lf:
        rc = subprocess.run(f"PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True torchrun --standalone --nproc_per_node={ngpu} -m workflows.recipes.wav2vec2.asr {train_dir} --config-file {cfg_path}",
                            shell=True, cwd=REPO, stdout=lf, stderr=subprocess.STDOUT).returncode
    results["train_rc"] = rc
    results["train_seconds"] = round(time.time() - t1)
    txt = open(log_path, encoding="utf-8", errors="replace").read()
    results["train_log_tail"] = txt[-12000:]
    shutil.copy(log_path, os.path.join(OUT, "train.log")) if len(txt) < 8_000_000 else None
    stage("train")

    # keep small run files (metrics, scores, cards), not the checkpoint shards
    keep = os.path.join(OUT, "run_files")
    for p in glob.glob(os.path.join(train_dir, "**", "*"), recursive=True):
        if os.path.isfile(p) and not p.endswith(".pt") and os.path.getsize(p) < 2_000_000:
            dst = os.path.join(keep, os.path.relpath(p, train_dir))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(p, dst)
    tree = []
    for p in sorted(glob.glob(os.path.join(train_dir, "**", "step_*"), recursive=True)):
        if os.path.isdir(p):
            size = sum(os.path.getsize(q) for q in glob.glob(os.path.join(p, "**", "*"), recursive=True) if os.path.isfile(q))
            tree.append([os.path.relpath(p, train_dir), size])
    results["checkpoint_dirs"] = tree
    save()
    if rc != 0:  # keep going: finished checkpoints may exist (stage 4 stops if none)
        results["errors"].append(f"training exited with {rc}; see train_log_tail")

    # 4. checkpoints
    steps = {}
    for p in glob.glob(os.path.join(train_dir, "**", "step_*"), recursive=True):
        m = re.fullmatch(r"step_(\d+)", os.path.basename(p))
        if m and os.path.isdir(os.path.join(p, "model")):
            steps[int(m.group(1))] = p
    results["steps_saved"] = sorted(steps)
    save()
    if not steps:
        results["errors"].append("no checkpoint with a model directory found")
        raise SystemExit(0)
    for k, p in steps.items():
        open(os.path.join(ASSETS, f"gojri_omni_ft_{k}.yaml"), "w", encoding="utf-8").write(
            f"name: gojri_omni_ft_{k}\nbase: {args.model_card}\ncheckpoint: {os.path.join(p, 'model')}\n")

    def upload(step):
        import boto3
        s3 = boto3.client("s3")
        prefix = f"asr/omni-ft/out/{JOB}/step_{step}/"
        for q in glob.glob(os.path.join(steps[step], "**", "*"), recursive=True):
            if os.path.isfile(q):
                s3.upload_file(q, args.bucket, prefix + os.path.relpath(q, steps[step]).replace(os.sep, "/"))
        results.setdefault("checkpoints_s3", []).append(f"s3://{args.bucket}/{prefix}")
        save()

    last = max(steps)
    if args.upload_ckpt:  # first, so that no later problem can lose a finished model
        try:
            upload(last)
        except Exception:
            results["errors"].append("upload of the last checkpoint: " + traceback.format_exc()[-1500:])
            save()

    # 5. score every checkpoint on dev (our scorer), choose the best, score it on test
    # The editable install only reaches interpreters started after it (smoke test 3: ModuleNotFoundError), so add the source folder by hand.
    import importlib
    sys.path.insert(0, os.path.join(REPO, "src"))
    importlib.invalidate_caches()
    import gc
    import numpy as np
    import pyarrow.parquet as pq
    import soundfile as sf
    import jiwer
    import torch
    from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline

    FOLD = str.maketrans({"ك": "ک", "ي": "ی", "ه": "ہ"})

    def norm(s):
        s = unicodedata.normalize("NFC", s)
        s = "".join(c for c in s if not unicodedata.category(c).startswith(("M", "P")))
        return re.sub(r"\s+", " ", s.translate(FOLD)).strip()

    def scr(refs, hyps):
        pairs = [(norm(r), norm(h)) for r, h in zip(refs, hyps) if norm(r)]
        rr, hh = [p[0] for p in pairs], [p[1] for p in pairs]
        return {"wer": round(100 * jiwer.wer(rr, hh), 2), "cer": round(100 * jiwer.cer(rr, hh), 2), "n": len(pairs)}

    def tsv(name):
        return list(csv.DictReader(open(os.path.join(DATA, "splits", name), encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))

    seen = {r["speaker"] for r in tsv("train.tsv")}

    def load_split(split):
        rows = tsv(f"{split}.tsv")
        table = pq.read_table(os.path.join(DATA, f"version=0/corpus=cv/split={split}/language=gju_Arab/part-00000.parquet"))
        assert table.num_rows == len(rows), (split, table.num_rows, len(rows))
        n = args.limit_eval or table.num_rows
        wavs = []
        for i in range(n):
            a = table.column("audio_bytes")[i].as_py()
            x, sr = sf.read(io.BytesIO(np.array(a, dtype=np.int8).tobytes()), dtype="float32")
            assert sr == 16000 and len(x) == table.column("audio_size")[i].as_py()
            wavs.append({"waveform": x, "sample_rate": 16000})
        return rows[:n], wavs

    def transcribe(card, wavs):
        pipe = ASRInferencePipeline(model_card=card)
        hyps = []
        for i in range(0, len(wavs), 4):
            chunk = wavs[i:i + 4]
            hyps += [str(h) for h in pipe.transcribe(chunk, lang=["gju_Arab"] * len(chunk), batch_size=4)]
        del pipe
        gc.collect()
        torch.cuda.empty_cache()
        return hyps

    dev_rows, dev_wavs = load_split("dev")
    dev_refs = [r["sentence"] for r in dev_rows]
    dev_wer = {}
    for k in sorted(steps):
        try:
            hyps = transcribe(f"gojri_omni_ft_{k}", dev_wavs)
            dev_wer[k] = scr(dev_refs, hyps)
            results["dev_wer"] = {str(a): b for a, b in sorted(dev_wer.items())}
            save()
        except Exception:
            results["errors"].append(f"dev scoring of step {k}: " + traceback.format_exc()[-2500:])
            save()
    stage("dev")
    if not dev_wer:
        raise SystemExit(0)
    best = min(sorted(dev_wer), key=lambda k: (dev_wer[k]["wer"], -k))  # lowest dev word error; the later step on a tie
    results["chosen_step"] = best
    save()

    # keep the best checkpoint too (the last one is already uploaded)
    if args.upload_ckpt and best != last:
        try:
            upload(best)
        except Exception:
            results["errors"].append("upload of the best checkpoint: " + traceback.format_exc()[-1500:])
            save()

    test_rows, test_wavs = load_split("test")
    refs = [r["sentence"] for r in test_rows]
    hyps = transcribe(f"gojri_omni_ft_{best}", test_wavs)
    out = {"all": scr(refs, hyps)}
    for name, k in (("seen_speakers", lambda r: r["speaker"] in seen), ("unseen_speakers", lambda r: r["speaker"] not in seen)):
        idx = [i for i, r in enumerate(test_rows) if k(r)]
        if idx:
            out[name] = scr([refs[i] for i in idx], [hyps[i] for i in idx])
    results["test"] = out
    with open(os.path.join(OUT, "test_predictions.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["path", "speaker", "seen", "reference", "hypothesis"])
        for r, h in zip(test_rows, hyps):
            w.writerow([r["path"], r["speaker"], int(r["speaker"] in seen), r["sentence"], h])
    stage("score")

except SystemExit:
    pass
except Exception:
    results["errors"].append(traceback.format_exc()[-4000:])
save()
print("done", json.dumps(results.get("test", {})), flush=True)
