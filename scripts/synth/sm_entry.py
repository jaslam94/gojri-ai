"""SageMaker entry point: unpack the input channel, then run ocr_train.main().

The train channel holds, per set (line_full, real_pairs): <set>_img.tar plus the
label files named <set>_labels*.jsonl. SageMaker passes hyperparameters as CLI args.
"""
import os
import shutil
import tarfile
from pathlib import Path

CH = Path(os.environ["SM_CHANNEL_TRAIN"])
DST = Path("/tmp/synth")

for name in ("line_full", "real_pairs"):
    d = DST / name
    d.mkdir(parents=True, exist_ok=True)
    with tarfile.open(CH / f"{name}_img.tar") as t:
        t.extractall(d)
    for f in CH.glob(f"{name}_labels*.jsonl"):
        shutil.copy(f, d / f.name[len(name) + 1:])  # line_full_labels_clean.jsonl -> labels_clean.jsonl
    print(name, "ready:", sum(1 for _ in (d / "img").iterdir()), "images", flush=True)

os.environ["GOJRI_SYNTH"] = str(DST)

import ocr_train  # noqa: E402  (after GOJRI_SYNTH is set)

ocr_train.main()
