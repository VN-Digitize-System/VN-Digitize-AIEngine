from __future__ import annotations

import threading
import cv2
import numpy as np

from shared_utils.logger import get_logger
from .config import VietOCRConfig
from ._recognizer import _resize_for_ocr

logger = get_logger(__name__)

_predictor = None
_predictor_model_key: str | None = None
_predictor_lock = threading.Lock()


def _get_predictor(config: VietOCRConfig):
    global _predictor, _predictor_model_key

    key = f"{config.model_name}:{config.device}:beam={config.beam_search}"
    with _predictor_lock:
        if _predictor is None or _predictor_model_key != key:
            logger.info(
                "Loading VietOCR model (model=%s, device=%s) — first call may take a moment...",
                config.model_name, config.device,
            )
            try:
                from vietocr.tool.predictor import Predictor
                from vietocr.tool.config import Cfg
                cfg = Cfg.load_config_from_name(config.model_name)
                cfg["device"] = config.device
                cfg["predictor"]["beamsearch"] = config.beam_search
                _predictor = Predictor(cfg)
                _predictor_model_key = key
                logger.info("VietOCR model loaded successfully.")
            except ImportError as exc:
                raise RuntimeError(
                    "vietocr is not installed. Run: pip install vietocr"
                ) from exc
            except Exception as exc:
                raise RuntimeError(f"VietOCR load failed: {exc}") from exc
        return _predictor


def _crop_region(image: np.ndarray, corners) -> np.ndarray:
    """Crop image to tightest axis-aligned bbox of the 4 corners."""
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]
    h, w = image.shape[:2]
    x1 = max(0, round(min(xs)))
    y1 = max(0, round(min(ys)))
    x2 = min(w, round(max(xs)))
    y2 = min(h, round(max(ys)))
    crop = image[y1:y2, x1:x2]
    return crop if crop.size > 0 else image


def detect_regions_with_craft(
    image: np.ndarray,
    easyocr_reader,
    max_dim: int = 1024,
) -> list[list]:
    """VietOCR is recognition-only; CRAFT provides the detection stage.
    Returns 4-corner lists in original image coordinates."""
    resized, scale = _resize_for_ocr(image, max_dim)

    try:
        horizontal_list, free_list = easyocr_reader.detect(resized)
    except Exception as exc:
        logger.warning("CRAFT detection failed: %s", exc)
        return []

    corners_list: list[list] = []

    # horizontal_list[0]: list of [xmin, xmax, ymin, ymax]
    if horizontal_list and horizontal_list[0]:
        for bbox in horizontal_list[0]:
            xmin, xmax, ymin, ymax = [v / scale for v in bbox]
            corners_list.append([
                [xmin, ymin],
                [xmax, ymin],
                [xmax, ymax],
                [xmin, ymax],
            ])

    # free_list[0]: list of polygon corners (already in [[x,y],...] form)
    if free_list and free_list[0]:
        for poly in free_list[0]:
            corners_list.append([[p[0] / scale, p[1] / scale] for p in poly])

    logger.debug("CRAFT found %d regions for VietOCR", len(corners_list))
    return corners_list


def recognize_handwriting(
    image: np.ndarray,
    corners_list: list[list],
    config: VietOCRConfig,
    min_confidence: float = 0.0,
) -> list[tuple]:
    """Returns (corners, text, confidence) matching EasyOCR format so the rest of the pipeline is unchanged."""
    from PIL import Image

    predictor = _get_predictor(config)
    results: list[tuple] = []

    for corners in corners_list:
        crop = _crop_region(image, corners)
        if crop.size == 0:
            continue

        pil_img = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        try:
            text, prob = predictor.predict(pil_img, return_prob=True)
        except Exception as exc:
            logger.debug("VietOCR prediction error on region: %s", exc)
            continue

        text = (text or "").strip()
        prob = float(prob) if prob is not None else 0.0

        if not text or prob < min_confidence:
            continue

        results.append((corners, text, prob))

    logger.debug(
        "VietOCR handwriting: %d regions → %d results",
        len(corners_list), len(results),
    )
    return results
