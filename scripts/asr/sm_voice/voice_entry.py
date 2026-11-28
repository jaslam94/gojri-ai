"""SageMaker entry: transcribe a speaker's own recordings with Omnilingual models (the clean test: no dataset holds these recordings).

Channels: `audio` = the audio files (wav, mp3, m4a, ogg, flac; each under 40 s, the model limit);
          `ckpt` = one saved fine-tune checkpoint folder (holds model/pp_00/tp_00/sdp_*.pt), see sm_omni_ft/omni_ft_entry.py.
Models: the fine-tuned LLM-1B, the same LLM-1B without training, and the LLM-7B without training, all with the tag gju_Arab.
Output: one pred_<name>.tsv per model with columns path, hypothesis (the format of scripts/asr/perf_check), and results.json.
The install steps are those of omni_ft_entry.py (the recipe repository at the same tag, so the checkpoint loads the same way).
The AWS user cannot read job logs: every stage writes into results.json and the script always ends cleanly.
"""
import argparse
import csv
import glob
import json
import os
import subprocess
import sys
import time
import traceback

ap = argparse.ArgumentParser()
ap.add_argument("--models", default="ft1b,base1b,base7b")
ap.add_argument("--ft-base-card", default="omniASR_LLM_1B")
ap.add_argument("--repo-ref", default="0.2.0")
ap.add_argument("--fairseq2-index", default="https://fair.pkg.atmeta.com/fairseq2/whl/pt2.8.0/cu128")
args = ap.parse_args()

AUDIO = os.environ.get("SM_CHANNEL_AUDIO", "audio")
CKPT = os.environ.get("SM_CHANNEL_CKPT", "ckpt")
OUT = os.environ.get("SM_MODEL_DIR", "out")
REPO = "/opt/ml/code/omnilingual-asr-repo"
ASSETS = "/opt/ml/user_assets"
os.makedirs(OUT, exist_ok=True)
results = {"args": vars(args), "install_log": "", "errors": [], "files": [], "skipped": [], "runs": {}}


def save():
    with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)


def sh(cmd, tail=2000):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    results["install_log"] += f"\n$ {cmd}\n(exit {r.returncode})\n" + (r.stdout + r.stderr)[-tail:]
    save()


py = sys.executable
try:
    sh(f"{py} -m pip install -q fairseq2==0.6.0 --extra-index-url {args.fairseq2_index}")
    sh(f"git clone -q --depth 1 --branch {args.repo_ref} https://github.com/facebookresearch/omnilingual-asr {REPO}")
    sh(f"{py} -m pip install -q -e {REPO} soundfile av")
    sh(f"{py} -m pip install -q --force-reinstall torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128 --extra-index-url https://pypi.org/simple")
    # fairseq2n needs the system libsndfile at import; apt does not work in this container, so expose the copy bundled with `soundfile`
    # (the same step as sm_omni_ft/omni_ft_entry.py; the first smoke test of this job failed without it)
    sh(f"{py} - <<'E'\nimport soundfile, os, glob\nlib = getattr(soundfile, '_libname', None)\nprint('soundfile lib:', lib)\nif not lib or not os.path.exists(lib):\n    c = glob.glob(os.path.join(os.path.dirname(soundfile.__file__), '_soundfile_data', '*.so*'))\n    lib = c[0] if c else None\nos.makedirs('/opt/ml/libs', exist_ok=True)\nif lib:\n    t = '/opt/ml/libs/libsndfile.so.1'\n    if os.path.lexists(t): os.remove(t)\n    os.symlink(lib, t)\n    open('/etc/ld.so.conf.d/sndfile.conf', 'w').write('/opt/ml/libs\\n')\nE")
    sh("ldconfig && ldconfig -p | grep -i sndfile")

    os.makedirs(ASSETS, exist_ok=True)
    shards = glob.glob(os.path.join(CKPT, "model", "**", "*.pt"), recursive=True)
    results["ckpt_shards"] = len(shards)
    open(os.path.join(ASSETS, "gojri_omni_ft.yaml"), "w", encoding="utf-8").write(
        f"name: gojri_omni_ft\nbase: {args.ft_base_card}\ncheckpoint: {os.path.join(CKPT, 'model')}\n")
    os.environ["FAIRSEQ2_USER_ASSET_DIR"] = ASSETS

    import gc
    import importlib
    sys.path.insert(0, os.path.join(REPO, "src"))  # the editable install is invisible to this running interpreter
    importlib.invalidate_caches()
    import soundfile  # noqa: F401  (loads libsndfile before fairseq2n is imported)
    import av
    import numpy as np
    import torch
    from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline

    def load_audio(path):
        out = []
        with av.open(path) as c:
            rs = av.AudioResampler(format="flt", layout="mono", rate=16000)
            for frame in c.decode(c.streams.audio[0]):
                for f in rs.resample(frame):
                    out.append(f.to_ndarray().reshape(-1))
            for f in rs.resample(None) or []:
                out.append(f.to_ndarray().reshape(-1))
        return np.concatenate(out) if out else np.zeros(0, dtype="float32")

    names, wavs = [], []
    for p in sorted(glob.glob(os.path.join(AUDIO, "*"))):
        name = os.path.basename(p)
        if not name.lower().endswith((".wav", ".mp3", ".m4a", ".ogg", ".flac", ".opus", ".aac", ".mp4", ".webm")):
            results["skipped"].append([name, "not an audio file"])
            continue
        try:
            x = load_audio(p)
        except Exception as e:
            results["skipped"].append([name, f"cannot decode: {e}"[:200]])
            continue
        secs = len(x) / 16000
        if secs < 0.3 or secs >= 40:
            results["skipped"].append([name, f"length {secs:.1f} s is outside 0.3 to 40 s"])
            continue
        names.append(name)
        wavs.append({"waveform": x, "sample_rate": 16000})
        results["files"].append([name, round(secs, 2)])
    save()

    cards = {"ft1b": "gojri_omni_ft", "base1b": "omniASR_LLM_1B", "base7b": "omniASR_LLM_7B"}
    for key in [m for m in args.models.split(",") if m]:
        t0 = time.time()
        try:
            pipe = ASRInferencePipeline(model_card=cards[key])
            hyps = []
            for i in range(0, len(wavs), 4):
                chunk = wavs[i:i + 4]
                hyps += [str(h) for h in pipe.transcribe(chunk, lang=["gju_Arab"] * len(chunk), batch_size=4)]
            with open(os.path.join(OUT, f"pred_{key}.tsv"), "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f, delimiter="\t", lineterminator="\n")
                w.writerow(["path", "hypothesis"])
                for n, h in zip(names, hyps):
                    w.writerow([n, h])
            results["runs"][key] = {"card": cards[key], "n": len(hyps), "seconds": round(time.time() - t0)}
            del pipe
            gc.collect()
            torch.cuda.empty_cache()
        except Exception:
            results["errors"].append(f"{key}: " + traceback.format_exc()[-2500:])
        save()
except Exception:
    results["errors"].append(traceback.format_exc()[-3500:])
save()
print("done", json.dumps(results["runs"]), flush=True)
