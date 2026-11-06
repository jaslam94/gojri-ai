"""Scan-damage augmentations for the synthetic OCR line images.

AUGS lists the clean copy and 14 approved scan-damage types (Pillow + numpy);
synth_generate.py applies them. Seeds are fixed so a rerun gives the same images.
"""
import random

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

random.seed(42)
np.random.seed(42)


def to_rgb(im):
    return im.convert("RGB") if im.mode != "RGB" else im


def rotate(im):
    return im.rotate(random.uniform(-4, 4), expand=True, fillcolor=(255, 255, 255), resample=Image.BICUBIC)


def shear(im):
    k = random.uniform(-0.15, 0.15)
    w, h = im.size
    return im.transform((w, h), Image.AFFINE, (1, k, 0, 0, 1, 0), resample=Image.BICUBIC, fillcolor=(255, 255, 255))


def perspective(im):
    w, h = im.size
    d = random.uniform(0.03, 0.10)
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    dst = [
        (random.uniform(0, w * d), random.uniform(0, h * d)),
        (w - random.uniform(0, w * d), random.uniform(0, h * d)),
        (w - random.uniform(0, w * d), h - random.uniform(0, h * d)),
        (random.uniform(0, w * d), h - random.uniform(0, h * d)),
    ]
    coeffs = []
    A = []
    for (x, y), (X, Y) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
    A = np.array(A)
    b = np.array([c for p in dst for c in p])
    coeffs = np.linalg.solve(A, b).tolist()
    return im.transform((w, h), Image.PERSPECTIVE, coeffs, resample=Image.BICUBIC, fillcolor=(255, 255, 255))


def photometric(im):
    im = ImageEnhance.Brightness(im).enhance(random.uniform(0.75, 0.95))
    im = ImageEnhance.Contrast(im).enhance(random.uniform(0.7, 0.95))
    return im


def gauss_noise(im):
    arr = np.asarray(im.convert("L"), dtype=np.float32)
    noise = np.random.normal(0, random.uniform(8, 25), arr.shape)
    out = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(out).convert(im.mode)


def blur(im):
    return im.filter(ImageFilter.GaussianBlur(random.uniform(0.7, 1.6)))


def motion_blur(im):
    arr = np.asarray(im.convert("L"), dtype=np.float32)
    h, w = arr.shape
    n = 9
    pad = n // 2
    padded = np.pad(arr, ((0, 0), (pad, pad)), mode="edge")
    out = np.zeros_like(arr)
    for i in range(n):
        out += padded[:, i:i + w] * (1 / n)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert(im.mode)


def salt_pepper(im):
    arr = np.asarray(im.convert("L")).copy()
    mask = np.random.random(arr.shape)
    arr[mask < 0.004] = 0
    arr[mask > 0.997] = 255
    return Image.fromarray(arr).convert(im.mode)


def ink_bleed(im):
    im = im.filter(ImageFilter.MaxFilter(3))
    return im.filter(ImageFilter.GaussianBlur(0.4))


def erode(im):
    return im.filter(ImageFilter.MinFilter(3))


def paper_aging(im):
    arr = np.asarray(to_rgb(im), dtype=np.float32)
    low = np.random.uniform(0.94, 1.0, (arr.shape[0], arr.shape[1], 1))  # low-freq stain
    tint = np.array([1.03, 0.98, 0.86], dtype=np.float32)  # yellowed cast
    out = np.clip(arr * tint * low, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def scan_lines(im):
    arr = np.asarray(to_rgb(im), dtype=np.float32)
    rows = np.arange(arr.shape[0]) % 4 == 0
    factor = np.ones((arr.shape[0], 1, 1), dtype=np.float32)
    factor[rows] = random.uniform(0.85, 0.93)
    out = np.clip(arr * factor, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def erase_streak(im):
    arr = np.asarray(to_rgb(im)).copy()
    h, w = arr.shape[:2]
    for _ in range(random.randint(1, 3)):
        x0 = random.randint(0, max(w - 40, 1))
        y0 = random.randint(0, max(h - 12, 1))
        rw, rh = random.randint(15, 45), random.randint(4, 12)
        arr[y0:y0 + rh, x0:x0 + rw] = arr[y0, x0]
    return Image.fromarray(arr)


def shadow(im):
    arr = np.asarray(to_rgb(im), dtype=np.float32)
    h = arr.shape[0]
    g = np.linspace(1.0, random.uniform(0.7, 0.85), h).reshape(h, 1, 1)
    out = np.clip(arr * g, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


AUGS = [
    ("clean", lambda im: im),
    ("rotate", rotate),
    ("shear", shear),
    ("perspective", perspective),
    ("bright/contrast", photometric),
    ("gauss noise", gauss_noise),
    ("blur", blur),
    ("motion blur", motion_blur),
    ("salt-pepper", salt_pepper),
    ("ink bleed", ink_bleed),
    ("erode", erode),
    ("paper aging", paper_aging),
    ("scan lines", scan_lines),
    ("erase streak", erase_streak),
    ("shadow", shadow),
]
