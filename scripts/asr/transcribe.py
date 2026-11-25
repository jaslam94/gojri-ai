"""Transcribe one or more audio files with the fine-tuned Gojri Whisper-small model, on the CPU.

Why: to hear whether the 22.7% word error matches real use. The model is the output of SageMaker job
gojri-asr-whisper-2026-11-20-17-43-55-757 (private; not published). Unpack its model.tar.gz into a folder, then:

  py -3 -X utf8 scripts/asr/transcribe.py MODEL_DIR recording.m4a [more files ...]
  py -3 -X utf8 scripts/asr/transcribe.py MODEL_DIR recording.wav --beams 5

Any format works (wav, mp3, m4a, ogg, flac): PyAV decodes it. Needs: pip install transformers torch av numpy.
Whisper reads at most 30 seconds at once; longer files are cut into 30 second pieces (a cut can split a word, so use
short recordings of one to three sentences for a fair test). Whisper has no Gojri token; the Urdu token is used, as in training.
"""
import argparse
import sys

import av
import numpy as np
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor

SR = 16000


def load_audio(path):
    """Decode any audio file to mono float32 at 16 kHz."""
    out = []
    with av.open(path) as c:
        s = c.streams.audio[0]
        rs = av.AudioResampler(format="flt", layout="mono", rate=SR)
        for frame in c.decode(s):
            for f in rs.resample(frame):
                out.append(f.to_ndarray().reshape(-1))
        for f in rs.resample(None) or []:
            out.append(f.to_ndarray().reshape(-1))
    return np.concatenate(out) if out else np.zeros(0, dtype="float32")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model_dir")
    ap.add_argument("audio", nargs="+")
    ap.add_argument("--beams", type=int, default=1, help="1 = greedy (used for the 22.7% score); 5 = beam search")
    a = ap.parse_args()
    proc = WhisperProcessor.from_pretrained(a.model_dir, language="urdu", task="transcribe")
    model = WhisperForConditionalGeneration.from_pretrained(a.model_dir, torch_dtype=torch.float32).eval()
    for path in a.audio:
        x = load_audio(path)
        secs = len(x) / SR
        print(f"\n{path}  ({secs:.1f} s)")
        for i in range(0, max(len(x), 1), 30 * SR):
            piece = x[i:i + 30 * SR]
            if len(piece) < SR // 4:
                continue
            feats = proc.feature_extractor(piece, sampling_rate=SR, return_tensors="pt").input_features
            with torch.no_grad():
                ids = model.generate(feats, language="urdu", task="transcribe", max_new_tokens=128, num_beams=a.beams)
            print(proc.batch_decode(ids, skip_special_tokens=True)[0].strip())


if __name__ == "__main__":
    sys.exit(main())
