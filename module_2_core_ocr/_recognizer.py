from __future__ import annotations

import cv2
import numpy as np

from shared_utils.logger import get_logger
from .config import RecognitionConfig

logger = get_logger(__name__)

_reader = None
_reader_config_key: tuple | None = None


def _get_reader(config: RecognitionConfig):
    global _reader, _reader_config_key

    key = (tuple(config.languages), config.device)
    if _reader is None or _reader_config_key != key:
        logger.info(
            "Loading EasyOCR model (langs=%s, device=%s) — first call may take a moment...",
            config.languages, config.device,
        )
        try:
            import easyocr
            gpu = config.device != "cpu"
            _reader = easyocr.Reader(config.languages, gpu=gpu)
            _reader_config_key = key
            logger.info("EasyOCR model loaded successfully.")
        except Exception as exc:
            raise RuntimeError(str(exc)) from exc

    return _reader


def _resize_for_ocr(image: np.ndarray, max_dim: int) -> tuple[np.ndarray, float]:
    """Downscale so longest side ≤ max_dim. Returns (resized, scale)."""
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return image, 1.0
    scale = max_dim / longest
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    logger.debug("Resized %dx%d → %dx%d (scale=%.3f) for OCR", w, h, new_w, new_h, scale)
    return resized, scale


def recognize_with_regions(
    image: np.ndarray,
    regions: list[dict],
    config: RecognitionConfig,
) -> list[tuple]:
    """
    Fast path: skip EasyOCR's CRAFT detector, run only the recognizer on
    pre-detected regions from OpenCV.

    regions: list of {"x", "y", "width", "height"} in original image coordinates.
    Returns list of (bbox_corners, text, confidence).
    """
    reader = _get_reader(config)
    resized, scale = _resize_for_ocr(image, config.max_image_dimension)

    # EasyOCR recognize() expects horizontal_list as [[x_min, x_max, y_min, y_max]]
    horizontal_list = [
        [
            int(r["x"] * scale),
            int((r["x"] + r["width"]) * scale),
            int(r["y"] * scale),
            int((r["y"] + r["height"]) * scale),
        ]
        for r in regions
    ]

    raw = reader.recognize(resized, horizontal_list=horizontal_list, free_list=[], detail=1)

    filtered = []
    for entry in raw:
        if len(entry) != 3:
            continue
        bbox_scaled, text, conf = entry
        if float(conf) < config.min_confidence or not text.strip():
            continue
        # Scale corners back to original coordinates
        bbox_orig = [[p[0] / scale, p[1] / scale] for p in bbox_scaled]
        filtered.append((bbox_orig, text, float(conf)))

    logger.debug(
        "EasyOCR recognize (regions=%d): %d results → %d after filter",
        len(regions), len(raw), len(filtered),
    )
    return filtered


def recognize_full_page(
    image: np.ndarray,
    config: RecognitionConfig,
) -> list[tuple]:
    """
    Fallback: run EasyOCR full pipeline (CRAFT detection + recognition).
    Used when OpenCV region detection finds nothing.

    Returns list of (bbox_corners, text, confidence).
    """
    reader = _get_reader(config)
    resized, scale = _resize_for_ocr(image, config.max_image_dimension)
    raw = reader.readtext(resized, detail=1, paragraph=False)

    filtered = [
        ([[p[0] / scale, p[1] / scale] for p in bbox], text, float(conf))
        for (bbox, text, conf) in raw
        if float(conf) >= config.min_confidence and text.strip()
    ]
    logger.debug(
        "EasyOCR readtext: %d raw → %d after filter",
        len(raw), len(filtered),
    )
    return filtered


def corners_to_bbox(corners) -> dict:
    """Convert EasyOCR corner list to {"x","y","width","height"}."""
    xs = [int(p[0]) for p in corners]
    ys = [int(p[1]) for p in corners]
    x, y = min(xs), min(ys)
    return {"x": x, "y": y, "width": max(xs) - x, "height": max(ys) - y}
