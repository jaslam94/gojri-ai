"""
One-off generator for notebooks/deepseek_ocr_colab.ipynb. Builds the notebook
programmatically so the long prompt string gets JSON-escaped correctly, rather
than hand-writing notebook JSON. Re-run this if prompts/ocr_transcription_v1.txt
changes and the notebook needs regenerating.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_TEXT = (ROOT / "prompts" / "ocr_transcription_v1.txt").read_text(encoding="utf-8")
OUT_PATH = ROOT / "notebooks" / "deepseek_ocr_colab.ipynb"


def code_cell(source_lines):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": source_lines}


def md_cell(source_lines):
    return {"cell_type": "markdown", "metadata": {}, "source": source_lines}


cells = [
    md_cell([
        "# DeepSeek-OCR test — dict_alif and gojri_adbiyaat\n",
        "\n",
        "Self-hosted, full prompt control (unlike the community Gradio demos, which only\n",
        "expose fixed task buttons). Runtime: **T4 GPU** (Runtime > Change runtime type > T4).\n",
        "\n",
        "**Steps:**\n",
        "1. Run the install cell (first run only, ~2-3 min).\n",
        "2. Run the upload cell, and when prompted, upload both\n",
        "   `dict_alif.png` and `gojri_adbiyaat.png` from your local\n",
        "   `data/gold/images_cropped/` folder.\n",
        "3. Run the remaining cells in order.\n",
        "4. Copy the printed output for each page back to Claude.\n",
    ]),
    code_cell([
        "!pip install -q transformers torch accelerate\n",
        "# flash-attention-2 is optional (faster) but can fail to build on Colab -\n",
        "# the model-loading cell below falls back to eager attention if this fails.\n",
        "!pip install -q flash-attn --no-build-isolation || echo \"flash-attn install failed, will fall back to eager attention\"\n",
    ]),
    code_cell([
        "from google.colab import files\n",
        "print(\"Upload dict_alif.png and gojri_adbiyaat.png (from data/gold/images_cropped/ in the repo)\")\n",
        "uploaded = files.upload()\n",
        "print(\"Uploaded:\", list(uploaded.keys()))\n",
    ]),
    code_cell([
        "# Canonical prompt, prompts/ocr_transcription_v1.txt, embedded verbatim so this\n",
        "# run uses the exact same instructions as every other model already tested.\n",
        f"PROMPT_V1 = {json.dumps(PROMPT_TEXT)}\n",
        "print(PROMPT_V1)\n",
    ]),
    code_cell([
        "from transformers import AutoModel, AutoTokenizer\n",
        "import torch\n",
        "\n",
        "model_name = 'deepseek-ai/DeepSeek-OCR'\n",
        "tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)\n",
        "\n",
        "try:\n",
        "    model = AutoModel.from_pretrained(\n",
        "        model_name, _attn_implementation='flash_attention_2',\n",
        "        trust_remote_code=True, use_safetensors=True,\n",
        "    )\n",
        "    print(\"Loaded with flash_attention_2\")\n",
        "except Exception as e:\n",
        "    print(f\"flash_attention_2 failed ({e}), falling back to eager attention\")\n",
        "    model = AutoModel.from_pretrained(\n",
        "        model_name, _attn_implementation='eager',\n",
        "        trust_remote_code=True, use_safetensors=True,\n",
        "    )\n",
        "\n",
        "model = model.eval().cuda().to(torch.bfloat16)\n",
    ]),
    code_cell([
        "# The model's own prompt format is \"<image>\\n\" followed by the instruction text -\n",
        "# our full v1 prompt goes in as that instruction, unlike the Gradio demos' fixed\n",
        "# task buttons, so this is a genuinely controlled, comparable run.\n",
        "prompt = \"<image>\\n\" + PROMPT_V1\n",
        "\n",
        "for image_file in [\"dict_alif.png\", \"gojri_adbiyaat.png\"]:\n",
        "    print(f\"\\n{'='*20} {image_file} {'='*20}\\n\")\n",
        "    result = model.infer(\n",
        "        tokenizer, prompt=prompt, image_file=image_file,\n",
        "        output_path=\"./\", base_size=1024, image_size=640,\n",
        "        crop_mode=True, save_results=False,\n",
        "    )\n",
        "    print(result)\n",
    ]),
]

notebook = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {OUT_PATH}")
