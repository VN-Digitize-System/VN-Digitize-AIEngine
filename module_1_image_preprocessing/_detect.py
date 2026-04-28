from __future__ import annotations

import cv2
import numpy as np

from .config import DetectConfig
from .models import BarcodeInfo
from shared_utils.logger import get_logger

logger = get_logger(__name__)


def detect_blank_page(image: np.ndarray, cfg: DetectConfig) -> bool:
    if not cfg.blank_page.enabled:
        return False

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    white_ratio = float(np.sum(binary == 255) / binary.size)
    is_blank = white_ratio >= cfg.blank_page.white_pixel_ratio_threshold

    if is_blank:
        logger.warning(f"Blank page detected (white_ratio={white_ratio:.3f})")
    else:
        logger.debug(f"Blank page check passed: white_ratio={white_ratio:.3f}")

    return is_blank


def detect_wrong_orientation(image: np.ndarray, cfg: DetectConfig) -> bool:
    """
    Detect 90-degree wrong orientation using Sobel gradient energy ratio.

    For a correctly-oriented portrait document, vertical edges (SobelX) are
    >= horizontal edges (SobelY) because text characters have strong vertical
    strokes. When the document is rotated 90°, SobelY dominates instead.

    Threshold: SobelX / SobelY < gradient_xy_threshold → flag WARN_ROTATED.

    Note: 180° (upside-down) cannot be reliably detected by gradient energy
    alone — the ratio is identical for 0° and 180°. Upside-down detection
    requires OCR-level confidence scoring (handled in Module 2).
    """
    if not cfg.orientation.enabled:
        return False

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    energy_x = float(np.mean(np.abs(cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3))))
    energy_y = float(np.mean(np.abs(cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3))))
    ratio = energy_x / (energy_y + 1e-9)

    is_wrong = ratio < cfg.orientation.gradient_xy_threshold
    logger.debug(
        f"Orientation: SobelX={energy_x:.2f}, SobelY={energy_y:.2f}, "
        f"X/Y={ratio:.3f}, threshold={cfg.orientation.gradient_xy_threshold}, wrong={is_wrong}"
    )
    return is_wrong


def detect_barcodes(image: np.ndarray, cfg: DetectConfig) -> list[BarcodeInfo]:
    if not cfg.barcode.enabled:
        return []

    results: list[BarcodeInfo] = []

    # QR Code
    qr = cv2.QRCodeDetector()
    data, points, _ = qr.detectAndDecode(image)
    if data and points is not None:
        pts = points[0].astype(int)
        x, y = int(pts[:, 0].min()), int(pts[:, 1].min())
        w, h = int(pts[:, 0].max()) - x, int(pts[:, 1].max()) - y
        results.append(BarcodeInfo(
            barcode_type="QR_CODE",
            data=data,
            bbox={"x": x, "y": y, "width": w, "height": h},
        ))
        logger.info(f"QR code detected: {data[:60]!r}")

    # 1D Barcodes (Code128, EAN, etc.)
    try:
        bd = cv2.barcode.BarcodeDetector()
        ok, decoded_info, decoded_type, points = bd.detectAndDecodeMulti(image)
        if ok and decoded_info:
            for info, btype, pts in zip(decoded_info, decoded_type, points):
                if not info:
                    continue
                pts = pts.astype(int)
                x, y = int(pts[:, 0].min()), int(pts[:, 1].min())
                w, h = int(pts[:, 0].max()) - x, int(pts[:, 1].max()) - y
                results.append(BarcodeInfo(
                    barcode_type=str(btype),
                    data=info,
                    bbox={"x": x, "y": y, "width": w, "height": h},
                ))
                logger.info(f"Barcode detected ({btype}): {info[:60]!r}")
    except AttributeError:
        logger.debug("cv2.barcode module not available in this OpenCV build, skipping 1D detection")

    logger.debug(f"Barcode scan complete: {len(results)} found")
    return results
