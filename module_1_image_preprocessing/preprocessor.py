from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .config import PreprocessConfig
from .models import BarcodeInfo, PreprocessResult
from ._crop_deskew import detect_and_crop
from ._detect import detect_barcodes, detect_blank_page, detect_wrong_orientation
from ._enhance import enhance_image
from shared_utils.logger import get_logger

logger = get_logger(__name__)

_SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


class ImagePreprocessor:
    def __init__(self, config: PreprocessConfig | None = None) -> None:
        self._config = config or PreprocessConfig()

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> ImagePreprocessor:
        return cls(config=PreprocessConfig.from_yaml(config_path))

    def process(self, image: np.ndarray | str | Path) -> PreprocessResult:
        """
        Process a document image through the full preprocessing pipeline.

        Accepts a numpy BGR array or a file path. Always returns a PreprocessResult —
        never raises an exception. Errors are captured in result.error_code.

        Pipeline order:
          1. Load & validate image
          2. Detect (blank page, orientation, barcodes) on the original
          3. Crop & deskew
          4. Enhance (CLAHE → binarize → denoise)
        """
        source = image if not isinstance(image, np.ndarray) else "numpy array"
        logger.info(f"Processing: {source}")

        original, error_code, error_message = self._load_image(image)
        if original is None:
            logger.error(f"{error_code}: {error_message}")
            return PreprocessResult(
                processed_image=None,
                is_blank=False,
                is_wrong_orientation=False,
                skew_angle=0.0,
                barcodes=[],
                warnings=[],
                error_code=error_code,
                error_message=error_message,
            )

        warnings: list[str] = []

        is_blank = detect_blank_page(original, self._config.detect)
        if is_blank:
            warnings.append("BLANK_PAGE")

        # Skip orientation check on blank pages — no content means no reliable gradient
        is_wrong_orientation = (
            detect_wrong_orientation(original, self._config.detect)
            if not is_blank else False
        )
        if is_wrong_orientation:
            warnings.append("WRONG_ORIENTATION")

        barcodes: list[BarcodeInfo] = detect_barcodes(original, self._config.detect)

        cropped, skew_angle = detect_and_crop(original, self._config.crop_deskew)
        processed = enhance_image(cropped, self._config.enhance)

        logger.info(
            f"Done — blank={is_blank}, wrong_orientation={is_wrong_orientation}, "
            f"angle={skew_angle:.1f}°, barcodes={len(barcodes)}"
        )

        return PreprocessResult(
            processed_image=processed,
            is_blank=is_blank,
            is_wrong_orientation=is_wrong_orientation,
            skew_angle=skew_angle,
            barcodes=barcodes,
            warnings=warnings,
            error_code=None,
            error_message=None,
        )

    def _load_image(
        self, image: np.ndarray | str | Path
    ) -> tuple[np.ndarray | None, str | None, str | None]:
        if isinstance(image, np.ndarray):
            if image.size == 0:
                return None, "ERR_EMPTY_ARRAY", "Input numpy array is empty"
            return image, None, None

        path = Path(image)

        if not path.exists():
            return None, "ERR_FILE_NOT_FOUND", f"File not found: {path}"

        if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
            return None, "ERR_UNSUPPORTED_FORMAT", f"Unsupported format: {path.suffix}"

        img = cv2.imread(str(path))
        if img is None:
            return None, "ERR_CORRUPTED", f"Cannot decode image (corrupted or invalid): {path.name}"

        if img.shape[0] < 50 or img.shape[1] < 50:
            return None, "ERR_TOO_SMALL", f"Image too small: {img.shape[1]}x{img.shape[0]}px"

        return img, None, None
