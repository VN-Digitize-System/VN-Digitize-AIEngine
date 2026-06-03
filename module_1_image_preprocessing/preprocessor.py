from __future__ import annotations
from pathlib import Path

import cv2
import numpy as np
import os
import json

from .config import PreprocessConfig
from .models import PreprocessResult
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
        is_wrong_orientation = detect_wrong_orientation(cropped, self._config.detect)

        # LOGIC SMART ENHANCE (Áp dụng có điều kiện)
        if crop_failed or skip_crop:
            logger.info("🔘 Bỏ qua tẩy trắng (Enhance) để giữ nguyên độ sắc nét của bản Scan / Ảnh bypass.")
            processed = cropped 
        else:
            # Gọi hàm enhance_image (Bên trong hàm này sẽ tự động kiểm tra cờ config.enabled)
            processed = enhance_image(cropped, self._config.enhance)
            
            if self._config.enhance.enabled:
                logger.info("🔘 Đã áp dụng thuật toán Enhance (Tẩy trắng/Tương phản).")
            else:
                logger.info("🔘 Công tắc Enhance đang TẮT. Truyền ảnh màu gốc sang Module 2.")

        logger.info(
            f"Done — blank={is_blank}, angle={skew_angle:.1f}°, barcodes={len(barcodes)}"
        )

        # Khởi tạo gói hàng kết quả
        result = PreprocessResult(
            processed_image=processed,
            is_blank=is_blank,
            is_wrong_orientation=is_wrong_orientation, 
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
    
    import os
    import json
    # (Đảm bảo bạn đã import os và json ở đầu file preprocessor.py)

def process_folder(self, input_dir: str | Path, output_dir: str | Path, skip_crop: bool = False) -> None:
        """
        Quét toàn bộ ảnh trong input_dir, gọi self.process() cho từng ảnh,
        lưu ảnh kết quả và xuất file m1_summary.json (Siêu dữ liệu) vào output_dir.
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        summary_data = {}
        logger.info(f"Bắt đầu xử lý hàng loạt thư mục: {input_path}")
        logger.info(f"Trạng thái CÔNG TẮC SKIP_CROP: {skip_crop}")

        if not input_path.exists():
            logger.error(f"Thư mục đầu vào không tồn tại: {input_path}")
            return

        for file_path in input_path.iterdir():
            if file_path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
                continue

            # 1. Gọi lõi xử lý cho 1 ảnh và truyền cờ skip_crop xuống
            result = self.process(str(file_path), skip_crop=skip_crop)

            # 2. Xử lý ghi file ảnh đầu ra
            out_file = output_path / f"{file_path.name}"
            
            if result.processed_image is not None:
                # Nếu có ảnh xử lý thành công, lưu đè bằng ảnh sạch
                cv2.imwrite(str(out_file), result.processed_image)
            elif result.is_blank:
                # Nếu là trang trắng (Passthrough with Empty State), copy nguyên bản ảnh gốc sang
                # để Module 2 vẫn thấy file ảnh tồn tại và giữ nguyên Index
                original_img = cv2.imread(str(file_path))
                cv2.imwrite(str(out_file), original_img)

            # 3. Gom nhặt Siêu dữ liệu (Metadata)
            summary_data[file_path.name] = {
                "is_blank": result.is_blank,
                "is_wrong_orientation": result.is_wrong_orientation,
                "skew_angle": result.skew_angle,
                "barcodes": [bc.data for bc in result.barcodes],
                "error": result.error_code
            }

        # 4. Ghi file bàn giao m1_summary.json
        summary_file = output_path / "m1_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=4, ensure_ascii=False)

        logger.info(f"Hoàn tất! Đã lưu ảnh và file bàn giao tại: {summary_file}")
