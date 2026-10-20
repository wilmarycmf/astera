"""Small, explainable OpenCV pipeline for the Astera photo generator.

Bright blobs are image highlights, NOT confirmed astronomical stars.
"""
from __future__ import annotations

from datetime import date
from io import BytesIO
import re
import warnings
from typing import NamedTuple

import cv2
import numpy as np
from PIL import Image, ImageOps

MAX_SIDE = 2000


class Detection(NamedTuple):
    mask: np.ndarray
    points: list[tuple[int, int, int]]  # x, y, radius


def load_photo(data: bytes) -> np.ndarray:
    """Read an uploaded photo with EXIF orientation, return RGB uint8."""
    if len(data) > 20 * 1024 * 1024:
        raise ValueError("Please upload an image smaller than 20 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            im = Image.open(BytesIO(data))
            if im.format not in {"JPEG", "PNG"}:
                raise ValueError("Only JPG and PNG images are supported.")
            if im.width * im.height > 40_000_000:
                raise ValueError("Please use an image with at most 40 megapixels.")
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
            return np.asarray(im, dtype=np.uint8).copy()
    except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("This image could not be read. Please try a JPG or PNG.") from exc


def enhance(rgb: np.ndarray, brightness: int, contrast: float) -> np.ndarray:
    """Image arithmetic: cv2.add/subtract for brightness; cv2.multiply for contrast.

    OpenCV saturates 8-bit arithmetic at 0..255 (prevents wraparound artifacts).
    """
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    amount = np.full_like(bgr, abs(int(brightness)))
    if brightness >= 0:
        adjusted = cv2.add(bgr, amount)
    else:
        adjusted = cv2.subtract(bgr, amount)
    contrasted = cv2.multiply(adjusted, np.ones_like(adjusted), scale=float(contrast))
    return cv2.cvtColor(contrasted, cv2.COLOR_BGR2RGB)


def detect_highlights(rgb: np.ndarray, threshold: int) -> Detection:
    """Threshold grayscale image; identify small connected bright regions."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(blur, int(threshold), 255, cv2.THRESH_BINARY)

    # Remove isolated pixels that usually come from sensor noise.
    clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN,
                             np.ones((2, 2), dtype=np.uint8))
    n_labels, _, stats, centers = cv2.connectedComponentsWithStats(clean, 8)

    h, w = gray.shape
    min_area = max(2, round(w * h / 2_000_000))
    max_area = max(100, round(w * h * 0.001))
    candidates: list[tuple[int, int, int]] = []
    for i in range(1, n_labels):
        x, y, bw, bh, area = map(int, stats[i])
        if not (min_area <= area <= max_area):
            continue
        # Highly elongated regions are more likely branches, wires or streaks.
        if max(bw, bh) / max(1, min(bw, bh)) > 4.5:
            continue
        cx, cy = map(lambda value: int(round(value)), centers[i])
        radius = max(3, int(round(max(bw, bh) / 2)) + 3)
        candidates.append((cx, cy, radius))
    # The alpha layer uses the thresholded light pixels, including large bright areas,
    # not only the small candidates counted above.
    return Detection(mask=clean, points=candidates)


def annotate(rgb: np.ndarray, observed_on: date, location: str,
             candidate_count: int, points: list[tuple[int, int, int]],
             mark_points: bool = False) -> np.ndarray:
    """Draw the observation stamp with OpenCV (drawing/annotation concept)."""
    output = cv2.cvtColor(rgb.copy(), cv2.COLOR_RGB2BGR)
    h, w = output.shape[:2]
    scale = max(0.45, min(1.2, w / 1200.0))
    thickness = max(1, round(scale * 2))
    if mark_points:
        for cx, cy, radius in points[:200]:
            cv2.circle(output, (cx, cy), radius, (230, 195, 125), thickness, cv2.LINE_AA)

    # Render at readable resolution, then fit the stamp to either photo dimension.
    # Pillow preserves Unicode place names; OpenCV handles shape annotation/blending.
    from PIL import ImageDraw, ImageFont
    location_clean = " ".join(location.split())[:65]
    lines = ["ASTERA", observed_on.strftime("%d %b %Y")]
    if location_clean:
        lines.append(location_clean)
    font = ImageFont.load_default(size=24)
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    widths = [measure.textbbox((0, 0), text, font=font)[2] for text in lines]
    pad, line_height = 20, 34
    panel = Image.new("RGB", (max(widths) + 2 * pad, len(lines) * line_height + 2 * pad), (14, 20, 34))
    draw = ImageDraw.Draw(panel)
    for i, text in enumerate(lines):
        draw.text((pad, pad + i * line_height), text, font=font,
                  fill=(219, 201, 160) if i == 0 else (236, 237, 241))
    margin = min(max(1, round(min(w, h) * .03)), (min(w, h) - 1) // 2)
    ratio = min(1.0, w * .55 / panel.width, h * .25 / panel.height,
                (w - 2 * margin) / panel.width, (h - 2 * margin) / panel.height)
    panel = panel.resize((max(1, round(panel.width * ratio)), max(1, round(panel.height * ratio))), Image.Resampling.LANCZOS)
    pw, ph = panel.size
    x, y = w - margin - pw, h - margin - ph
    region = output[y:y + ph, x:x + pw]
    panel_bgr = cv2.cvtColor(np.asarray(panel), cv2.COLOR_RGB2BGR)
    output[y:y + ph, x:x + pw] = cv2.addWeighted(region, .2, panel_bgr, .8, 0)
    return cv2.cvtColor(output, cv2.COLOR_BGR2RGB)


def transparent_light_layer(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Alpha channel: RGBA image keeps only bright regions opaque."""
    alpha = cv2.GaussianBlur(mask, (3, 3), 0)
    return np.dstack((rgb, alpha)).astype(np.uint8)


def png_bytes(img: np.ndarray) -> bytes:
    with BytesIO() as out:
        Image.fromarray(img).save(out, format="PNG", optimize=True)
        return out.getvalue()
