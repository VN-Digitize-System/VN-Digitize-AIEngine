from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .config import PreprocessConfig
from .models import PreprocessResult
from ._crop_deskew import detect_and_crop
from ._detect import detect_barcodes, detect_blank_page
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

    def process(self, image: str | np.ndarray, skip_crop: bool = False) -> PreprocessResult:
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

        barcodes = detect_barcodes(original, self._config.detect)

       # ==========================================
        # BƯỚC 1: CẮT GÓC & XOAY PHẲNG (CÓ CÔNG TẮC)
        # ==========================================
        if skip_crop:
            # NẾU BẬT CÔNG TẮC: Bypass hoàn toàn hàm Crop
            logger.info("🔘 CÔNG TẮC BẬT (skip_crop=True): Bỏ qua cắt viền, dùng thẳng ảnh gốc.")
            cropped = original.copy()
            skew_angle = 0.0
            crop_failed = False
            
            # THÊM DÒNG NÀY: Khởi tạo debug_img khi không crop
            debug_img = None 
            
        else:
            # NẾU TẮT CÔNG TẮC: Chạy Crop bình thường cho ảnh chụp
            cropped, skew_angle, debug_img = detect_and_crop(original, self._config.crop_deskew)
            
            crop_area = cropped.shape[0] * cropped.shape[1]
            orig_area = original.shape[0] * original.shape[1]
            crop_ratio = crop_area / orig_area
            
            # Giữ lại lớp phòng thủ kép để bọc lót
            crop_failed = (crop_ratio >= 0.90) or (crop_ratio <= 0.30)
            
            if crop_failed:
                warnings.append("CROP_FAILED_PLEASE_RETAKE")
                logger.warning(f"⚠️ Lỗi Crop (Tỷ lệ: {crop_ratio:.2f}). Kích hoạt Bypass tự động.")
                cropped = original.copy() # Lùi về dùng ảnh gốc
                skew_angle = 0.0

        # ==========================================
        # BƯỚC 2 & 3: TRANG TRẮNG VÀ TẨY TRẮNG
        # ==========================================
        is_blank = detect_blank_page(cropped, self._config.detect)
        
        # Nếu đã skip_crop hoặc crop_failed, BỎ QUA LUÔN ENHANCE
        if crop_failed or skip_crop:
            logger.info("🔘 Bỏ qua tẩy trắng (Enhance) để giữ nguyên độ sắc nét của bản Scan.")
            processed = cropped 
        else:
            # Chỉ tẩy trắng đối với ảnh chụp thật (đã qua crop thành công)
            processed = enhance_image(cropped, self._config.enhance)

        logger.info(
            f"Done — blank={is_blank}, angle={skew_angle:.1f}°, barcodes={len(barcodes)}"
        )

        # Khởi tạo gói hàng kết quả
        result = PreprocessResult(
            processed_image=processed,
            is_blank=is_blank,
            is_wrong_orientation=False, # Gán cứng False để không phá vỡ cấu trúc models.py
            skew_angle=skew_angle,
            barcodes=barcodes,
            warnings=warnings,
            error_code=None
        )
        
        # --- THÊM ĐÚNG 1 DÒNG NÀY ĐỂ NHÉT ẢNH DEBUG VÀO GÓI HÀNG ---
        result.debug_image = debug_img
        
        return result

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
