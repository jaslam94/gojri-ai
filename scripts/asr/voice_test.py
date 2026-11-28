"""Own-voice test of the Gojri ASR models: sheet, SageMaker job, download, score.

Why: Common Voice is public, so a model may have trained on its clips. Recordings that no dataset holds give a clean test.
All files stay local under local/voice-test/ (gitignored); the audio also goes to private S3 for the job.

Steps (run from the repository root):
  1. Write 20 to 30 short Gojri sentences that are not in Common Voice. Record one file per sentence (01.m4a, 02.m4a, ...), each under
     40 seconds, into local/voice-test/audio/.
  2. py -3 -X utf8 scripts/asr/voice_test.py sheet
     Makes local/voice-test/sheet.tsv (file, corrected_text). Type what was said in corrected_text. Do this before you see any model output.
  3. py -3 -X utf8 scripts/asr/voice_test.py launch      (needs SAGEMAKER_ROLE_ARN; ml.g5.4xlarge; a 4-clip test took 14 billed minutes)
  4. py -3 -X utf8 scripts/asr/voice_test.py fetch JOB   (JOB = the name that launch prints; downloads the predictions)
  5. py -3 -X utf8 scripts/asr/voice_test.py score       (word and character error per model; flags sentences that are in Common Voice)
Option --dir changes local/voice-test. Scorer: scripts/asr/perf_check/asrlib.py (same normalisation as the SageMaker jobs).
20 to 30 sentences from one speaker are an anecdote, not a rate.
"""
import argparse
import json
import os
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUCKET = os.environ.get("GOJRI_BUCKET", "gojri-ai-sagemaker-data")
CKPT = f"s3://{BUCKET}/asr/omni-ft/out/gojri-asr-omni-ft-1b-2026-11-26-12-33-47-861/step_400/"
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".opus", ".aac", ".mp4", ".webm")
LABELS = {"base7b": "Omnilingual LLM-7B, no training", "base1b": "Omnilingual LLM-1B, no training", "ft1b": "Omnilingual LLM-1B, fine-tuned"}


def audio_files(d):
    return sorted(p for p in (d / "audio").glob("*") if p.suffix.lower() in AUDIO_EXT)


def cmd_sheet(d, args):
    files = audio_files(d)
    if not files:
        sys.exit(f"no audio files in {d / 'audio'}")
    sheet = d / "sheet.tsv"
    if sheet.exists():
        sys.exit(f"{sheet} exists; delete it yourself if you want a new one (it may hold your typing)")
    sheet.write_text("file\tcorrected_text\n" + "".join(f"{p.name}\t\n" for p in files), encoding="utf-8")
    print(f"{len(files)} files -> {sheet}")


def cmd_launch(d, args):
    import sagemaker
    from sagemaker.pytorch import PyTorch
    files = audio_files(d)
    if not files:
        sys.exit(f"no audio files in {d / 'audio'}")
    sess = sagemaker.Session(default_bucket=BUCKET)
    stamp = __import__("time").strftime("%Y%m%d-%H%M%S")
    prefix = f"asr/voice/{stamp}"
    for p in files:
        sess.s3_client.upload_file(str(p), BUCKET, f"{prefix}/{p.name}")
    print(f"uploaded {len(files)} files to s3://{BUCKET}/{prefix}/ (private)")
    est = PyTorch(entry_point="voice_entry.py", source_dir=str(ROOT / "scripts/asr/sm_voice"), role=os.environ["SAGEMAKER_ROLE_ARN"],
                  framework_version="2.8", py_version="py312", instance_count=1, instance_type=args.instance, max_run=args.max_run,
                  volume_size=150, hyperparameters={"models": args.models}, code_location=f"s3://{BUCKET}/code",
                  output_path=f"s3://{BUCKET}/asr/output", sagemaker_session=sess, base_job_name="gojri-asr-voice")
    est.fit({"audio": f"s3://{BUCKET}/{prefix}/", "ckpt": args.ckpt}, wait=False)
    print("started:", est.latest_training_job.name)


def cmd_fetch(d, args):
    import boto3
    out = d / "pred" / args.job
    out.mkdir(parents=True, exist_ok=True)
    tar = out / "model.tar.gz"
    boto3.client("s3").download_file(BUCKET, f"asr/output/{args.job}/output/model.tar.gz", str(tar))
    with tarfile.open(tar) as t:
        t.extractall(out, filter="data") if hasattr(tarfile, "data_filter") else t.extractall(out)
    r = json.loads((out / "results.json").read_text(encoding="utf-8"))
    print("files:", len(r["files"]), "| skipped:", r["skipped"], "| runs:", r["runs"])
    for e in r["errors"]:
        print("ERROR", e[-1500:])
    (d / "pred" / "latest.txt").write_text(args.job, encoding="utf-8")


def cmd_score(d, args):
    sys.path.insert(0, str(ROOT / "scripts/asr/perf_check"))
    from asrlib import norm, read_tsv, scores
    job = args.job or (d / "pred" / "latest.txt").read_text(encoding="utf-8").strip()
    sheet = {r["file"]: r["corrected_text"].strip() for r in read_tsv(d / "sheet.tsv") if (r.get("corrected_text") or "").strip()}
    if not sheet:
        sys.exit("the sheet has no corrected_text yet")
    cv_file = ROOT / "datasets/cv-corpus-26.0-2026-06-12/gju/validated.tsv"
    cv = {norm(r["sentence"]) for r in read_tsv(cv_file)} if cv_file.exists() else set()
    in_cv = sorted(f for f, t in sheet.items() if norm(t) in cv)
    print(f"{len(sheet)} sentences with your text; also in Common Voice: {len(in_cv)} {in_cv}")
    preds = {}
    for p in sorted((d / "pred" / job).glob("pred_*.tsv")):
        preds[p.stem[5:]] = {r["path"]: r["hypothesis"] for r in read_tsv(p)}
    common = sorted(f for f in sheet if all(f in v for v in preds.values()))
    missing = sorted(set(sheet) - set(common))
    if missing:
        print("not scored (no output from every model):", missing)
    for key, v in preds.items():
        s = scores([sheet[f] for f in common], [v[f] for f in common])
        print(f"{LABELS.get(key, key):36s} word error {s['wer']:6.2f}%  character error {s['cer']:6.2f}%  ({s['n']} sentences)")
    if args.show:
        for f in common:
            print(f"\n{f}\n  you:    {sheet[f]}")
            for key, v in preds.items():
                print(f"  {key:6s}: {v[f]}")
    print("\nA few sentences from one speaker are an anecdote, not an estimate.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["sheet", "launch", "fetch", "score"])
    ap.add_argument("job", nargs="?")
    ap.add_argument("--dir", default=str(ROOT / "local/voice-test"))
    ap.add_argument("--ckpt", default=CKPT)
    ap.add_argument("--models", default="ft1b,base1b,base7b")
    ap.add_argument("--instance", default="ml.g5.4xlarge", help="the 7B model needs 64 GB of RAM")
    ap.add_argument("--max-run", type=int, default=5400)
    ap.add_argument("--show", action="store_true", help="score: print every sentence with every model's output")
    args = ap.parse_args()
    d = Path(args.dir)
    (d / "audio").mkdir(parents=True, exist_ok=True)
    {"sheet": cmd_sheet, "launch": cmd_launch, "fetch": cmd_fetch, "score": cmd_score}[args.command](d, args)


if __name__ == "__main__":
    main()
