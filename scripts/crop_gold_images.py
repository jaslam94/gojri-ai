"""
Crop gold-set page images to their content bounding box, to avoid paying vision-model
image tokens for blank margins (most providers tokenize by pixel area, not content).

Originals in data/gold/images/ are left untouched. Cropped versions are written to
data/gold/images_cropped/<same filename>.png for side-by-side comparison before
deciding whether to use them for the model test batch.

Usage:
    py -3 scripts/crop_gold_images.py
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "data" / "gold" / "images"
OUT_DIR = ROOT / "data" / "gold" / "images_cropped"

WHITE_THRESHOLD = 245  # grayscale value below which a pixel counts as "content"
PADDING = 50            # safety margin in px kept around the detected content bbox


def content_bbox(img):
    gray = img.convert("L")
    mask = gray.point(lambda p: 255 if p < WHITE_THRESHOLD else 0)
    return mask.getbbox()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in sorted(SRC_DIR.glob("*.png")):
        img = Image.open(path)
        w, h = img.size
        bbox = content_bbox(img)

        if bbox is None:
            print(f"{path.name}: no content detected, copying unchanged")
            img.save(OUT_DIR / path.name)
            continue

        left, top, right, bottom = bbox
        left = max(0, left - PADDING)
        top = max(0, top - PADDING)
        right = min(w, right + PADDING)
        bottom = min(h, bottom + PADDING)

        cropped = img.crop((left, top, right, bottom))
        cw, ch = cropped.size
        cropped.save(OUT_DIR / path.name)

        orig_area, new_area = w * h, cw * ch
        orig_tok_est, new_tok_est = orig_area / 750, new_area / 750
        pct = 100 * new_area / orig_area
        print(
            f"{path.name:35s} {w}x{h:<5d} -> {cw}x{ch:<5d} "
            f"({pct:5.1f}% area, ~{orig_tok_est:.0f} -> ~{new_tok_est:.0f} est. Claude image tokens)"
        )

    print(f"\nCropped images written to {OUT_DIR}")


if __name__ == "__main__":
    main()
