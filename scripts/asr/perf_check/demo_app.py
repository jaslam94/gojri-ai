"""Step 7 (optional): local Gradio demo of the fine-tuned Whisper model. Localhost only; do not deploy.

Run: python demo_app.py --model D:\\asr-check\\extract\\model
Needs: pip install gradio. The app binds 127.0.0.1 and has no share link. Recordings stay in memory.
"""
import argparse

import gradio as gr
import soundfile as sf
import torch
import torchaudio
from transformers import WhisperForConditionalGeneration, WhisperProcessor

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--port", type=int, default=7860)
args = ap.parse_args()

proc = WhisperProcessor.from_pretrained(args.model)
model = WhisperForConditionalGeneration.from_pretrained(args.model, torch_dtype=torch.float32).eval()


def transcribe(path):
    if not path:
        return ""
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != 16000:
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy()
    feats = proc.feature_extractor([x], sampling_rate=16000, return_tensors="pt").input_features
    with torch.no_grad():
        ids = model.generate(feats, language="urdu", task="transcribe", max_new_tokens=128)
    return proc.batch_decode(ids, skip_special_tokens=True)[0]


demo = gr.Interface(
    fn=transcribe,
    inputs=gr.Audio(sources=["microphone", "upload"], type="filepath", label="Gojri speech (short sentence)"),
    outputs=gr.Textbox(label="Model output (Nastaliq)", rtl=True),
    title="Gojri ASR baseline (research, not for real use)",
    description="Whisper-small fine-tuned on Common Voice Gujari. Spelling is not standard; expect errors.",
)
demo.launch(server_name="127.0.0.1", server_port=args.port, share=False)
