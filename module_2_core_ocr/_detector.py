from __future__ import annotations

import cv2
import numpy as np

from shared_utils.logger import get_logger
from .config import DetectionConfig

logger = get_logger(__name__)


def detect_text_regions(image: np.ndarray, config: DetectionConfig) -> list[dict]:
    """
    OpenCV morphological text region detector.

    Returns list of {"x", "y", "width", "height"} bboxes sorted top→bottom.
    Used as a fallback when the primary recognizer returns no regions.
    """
    if image is None or image.size == 0:
        return []

    gray = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (config.dilate_kernel_width, config.dilate_kernel_height),
    )
    dilated = cv2.dilate(binary, kernel)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    max_region_h = int(h * config.max_region_height_ratio)
    regions: list[dict] = []

    for cnt in contours:
        x, y, rw, rh = cv2.boundingRect(cnt)
        if rh < config.min_text_height:
            continue
        if rw < config.min_text_width:
            continue
        if rh > max_region_h:
            continue
        regions.append({"x": x, "y": y, "width": rw, "height": rh})

    regions.sort(key=lambda r: (r["y"], r["x"]))
    logger.debug("OpenCV detector found %d text regions", len(regions))
    return regions
