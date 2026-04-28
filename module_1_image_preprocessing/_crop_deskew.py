from __future__ import annotations

import cv2
import numpy as np

from .config import CropDeskewConfig
from shared_utils.logger import get_logger

logger = get_logger(__name__)

# Thử nhiều epsilon để approxPolyDP dễ tìm ra 4 góc hơn với ảnh chụp tay
_APPROX_EPSILONS = [0.02, 0.03, 0.04, 0.05, 0.06]


def detect_and_crop(
    image: np.ndarray, cfg: CropDeskewConfig
) -> tuple[np.ndarray, float]:
    """
    Attempt perspective warp using 4-corner document contour.
    Falls back to Hough-based deskew if no clear contour is found.
    Returns (processed_image, skew_angle_degrees).
    """
    if not cfg.enabled:
        return image, 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Dùng bilateral filter thay vì GaussianBlur để giữ cạnh sắc nét hơn
    # (quan trọng với ảnh chụp tay có viền tài liệu không đều)
    blurred = cv2.bilateralFilter(gray, 9, 75, 75)
    edges = cv2.Canny(blurred, cfg.canny_threshold1, cfg.canny_threshold2)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (cfg.morph_kernel_size, cfg.morph_kernel_size)
    )
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    corners = _find_document_contour(contours, image.shape, cfg)

    if corners is not None:
        warped = _perspective_transform(image, corners, cfg.perspective_padding)
        ordered = _order_corner_points(corners)
        dx = float(ordered[1][0] - ordered[0][0])
        dy = float(ordered[1][1] - ordered[0][1])
        angle = float(np.degrees(np.arctan2(dy, dx)))
        logger.debug(f"Perspective warp applied: skew_angle={angle:.2f}°")
        return warped, angle

    logger.debug("No 4-corner contour found, falling back to Hough deskew")
    return _deskew_by_hough(image, gray, cfg.max_skew_angle)


def _find_document_contour(
    contours: list, image_shape: tuple, cfg: CropDeskewConfig
) -> np.ndarray | None:
    image_area = image_shape[0] * image_shape[1]
    min_area = image_area * cfg.min_area_ratio

    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:8]:
        if cv2.contourArea(contour) < min_area:
            break

        peri = cv2.arcLength(contour, True)

        # Thử nhiều mức epsilon — ảnh chụp tay thường cần epsilon lớn hơn
        for eps in _APPROX_EPSILONS:
            approx = cv2.approxPolyDP(contour, eps * peri, True)
            if len(approx) == 4:
                area_ratio = cv2.contourArea(contour) / image_area
                logger.debug(
                    f"Document contour found: area_ratio={area_ratio:.2f}, epsilon={eps}"
                )
                return approx.reshape(4, 2).astype(np.float32)

    return None


def _order_corner_points(pts: np.ndarray) -> np.ndarray:
    """Order corners: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _perspective_transform(
    image: np.ndarray, corners: np.ndarray, padding: int
) -> np.ndarray:
    rect = _order_corner_points(corners)
    tl, tr, br, bl = rect

    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))

    p = padding
    dst = np.array(
        [[p, p], [width + p, p], [width + p, height + p], [p, height + p]],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (width + 2 * p, height + 2 * p))


def _deskew_by_hough(
    image: np.ndarray, gray: np.ndarray, max_angle: float
) -> tuple[np.ndarray, float]:
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=80, minLineLength=100, maxLineGap=10
    )

    if lines is None:
        logger.debug("Hough deskew: no lines detected, image unchanged")
        return image, 0.0

    angles = [
        float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        for x1, y1, x2, y2 in (line[0] for line in lines)
        if abs(np.degrees(np.arctan2(y2 - y1, x2 - x1))) <= max_angle
    ]

    if not angles:
        return image, 0.0

    median_angle = float(np.median(angles))
    logger.debug(f"Hough deskew: median_angle={median_angle:.2f}° from {len(angles)} lines")

    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )
    return rotated, median_angle
