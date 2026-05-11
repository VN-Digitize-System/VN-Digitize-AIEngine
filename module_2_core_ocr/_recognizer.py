from __future__ import annotations

import threading
import cv2
import numpy as np

from shared_utils.logger import get_logger
from .config import RecognitionConfig
from .models import WordToken

logger = get_logger(__name__)

_reader = None
_reader_config_key: tuple | None = None
_reader_lock = threading.Lock()


def _get_reader(config: RecognitionConfig):
    global _reader, _reader_config_key

    key = (tuple(config.languages), config.device)
    with _reader_lock:
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
    xs = [round(p[0]) for p in corners]
    ys = [round(p[1]) for p in corners]
    x, y = min(xs), min(ys)
    return {"x": x, "y": y, "width": max(xs) - x, "height": max(ys) - y}


def build_word_tokens(
    text: str,
    conf: float,
    bbox: dict,
    flag_threshold: float,
) -> list[WordToken]:
    """
    EasyOCR provides only block-level confidence, so all words in a block share
    the same confidence score. Bbox is estimated by distributing block width
    proportionally to each word's character count (approximate, sufficient for
    UI highlighting — character-level estimation requires a future spec).
    """
    words_text = [w for w in text.split() if w]
    if not words_text:
        return []

    block_x = bbox["x"]
    block_y = bbox["y"]
    block_w = bbox["width"]
    block_h = bbox["height"]

    # Distribute width: word chars + inter-word spaces (~1 char-width each)
    total_chars = sum(len(w) for w in words_text)
    total_units = total_chars + max(0, len(words_text) - 1)
    unit_w = block_w / total_units if total_units > 0 else block_w

    conf_pct = min(100, round(conf * 100))
    flagged = conf < flag_threshold

    tokens: list[WordToken] = []
    cur_x = float(block_x)
    for word_text in words_text:
        word_w = max(1, round(len(word_text) * unit_w))
        # Clamp last word to avoid overflowing block bbox due to float rounding
        word_w = min(word_w, block_x + block_w - round(cur_x))
        tokens.append(WordToken(
            text=word_text,
            confidence=conf,
            confidence_pct=conf_pct,
            bbox={"x": round(cur_x), "y": block_y, "width": word_w, "height": block_h},
            is_flagged=flagged,
        ))
        cur_x += word_w + unit_w

    return tokens
