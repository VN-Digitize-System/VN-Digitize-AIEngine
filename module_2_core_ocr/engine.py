from __future__ import annotations

from pathlib import Path

import numpy as np

from shared_utils.logger import get_logger
from .config import OCRConfig
from .models import OCRResult, TextBlock
from ._detector import detect_text_regions
from ._recognizer import recognize_with_regions, recognize_full_page, corners_to_bbox

logger = get_logger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "module2_defaults.yaml"


class OCREngine:

    def __init__(self, config: OCRConfig | None = None) -> None:
        self._config = config or OCRConfig()

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> OCREngine:
        p = Path(path) if path else _DEFAULT_CONFIG_PATH
        return cls(OCRConfig.from_yaml(p))

    def process(self, image: np.ndarray) -> OCRResult:
        if image is None:
            return OCRResult(
                full_text="", text_blocks=[], avg_confidence=0.0, is_upside_down=False,
                error_code="ERR_EMPTY_IMAGE", error_message="Input image is None.",
            )
        if image.size == 0:
            return OCRResult(
                full_text="", text_blocks=[], avg_confidence=0.0, is_upside_down=False,
                error_code="ERR_EMPTY_IMAGE", error_message="Input image is an empty array.",
            )

        try:
            raw = self._run_ocr(image)
        except RuntimeError as exc:
            return OCRResult(
                full_text="", text_blocks=[], avg_confidence=0.0, is_upside_down=False,
                error_code="ERR_MODEL_LOAD_FAILED", error_message=str(exc),
            )
        except Exception as exc:
            return OCRResult(
                full_text="", text_blocks=[], avg_confidence=0.0, is_upside_down=False,
                error_code="ERR_NO_TEXT_DETECTED", error_message=str(exc),
            )

        if not raw:
            return OCRResult(
                full_text="", text_blocks=[], avg_confidence=0.0, is_upside_down=False,
                warnings=["NO_TEXT_FOUND"],
                error_code="ERR_NO_TEXT_DETECTED",
                error_message="No text regions detected in image.",
            )

        sorted_raw = _sort_reading_order(raw)

        text_blocks: list[TextBlock] = []
        for idx, (bbox_corners, text, conf) in enumerate(sorted_raw):
            text_blocks.append(TextBlock(
                text=text.strip(),
                confidence=conf,
                bbox=corners_to_bbox(bbox_corners),
                block_index=idx,
            ))

        avg_confidence = sum(b.confidence for b in text_blocks) / len(text_blocks)
        full_text = "\n".join(b.text for b in text_blocks if b.text)

        warnings: list[str] = []
        is_upside_down = False
        ud = self._config.upside_down
        if (
            ud.enabled
            and len(text_blocks) >= ud.min_blocks_required
            and avg_confidence < ud.confidence_threshold
        ):
            is_upside_down = True
            warnings.append("WARN_UPSIDE_DOWN")
            logger.warning(
                "avg_confidence=%.3f < threshold=%.3f → WARN_UPSIDE_DOWN",
                avg_confidence, ud.confidence_threshold,
            )

        logger.info(
            "OCR done: %d blocks, avg_conf=%.3f, upside_down=%s",
            len(text_blocks), avg_confidence, is_upside_down,
        )
        return OCRResult(
            full_text=full_text,
            text_blocks=text_blocks,
            avg_confidence=avg_confidence,
            is_upside_down=is_upside_down,
            warnings=warnings,
        )

    def _run_ocr(self, image: np.ndarray) -> list[tuple]:
        """
        Hybrid OCR: OpenCV detects regions first (fast), then EasyOCR
        runs only the recognizer on those crops.  Falls back to full-page
        EasyOCR (CRAFT + recognizer) when OpenCV finds no regions.
        """
        if self._config.detection.enabled:
            regions = detect_text_regions(image, self._config.detection)
            if regions:
                logger.debug("Hybrid path: %d OpenCV regions → EasyOCR recognizer", len(regions))
                return recognize_with_regions(image, regions, self._config.recognition)
            logger.debug("OpenCV found no regions — falling back to EasyOCR full-page")

        return recognize_full_page(image, self._config.recognition)


def _sort_reading_order(raw: list[tuple]) -> list[tuple]:
    """Sort EasyOCR detections into top→bottom, left→right reading order."""
    if not raw:
        return raw

    def top_y(item) -> float:
        return min(p[1] for p in item[0])

    def left_x(item) -> float:
        return min(p[0] for p in item[0])

    heights = [max(p[1] for p in item[0]) - min(p[1] for p in item[0]) for item in raw]
    heights.sort()
    median_h = heights[len(heights) // 2] if heights else 20
    tolerance = max(8, int(median_h * 0.6))

    by_y = sorted(raw, key=top_y)
    groups: list[list] = []
    current: list = [by_y[0]]
    ref_y = top_y(by_y[0])

    for item in by_y[1:]:
        y = top_y(item)
        if abs(y - ref_y) <= tolerance:
            current.append(item)
        else:
            groups.append(sorted(current, key=left_x))
            current = [item]
            ref_y = y
    groups.append(sorted(current, key=left_x))

    return [item for group in groups for item in group]
