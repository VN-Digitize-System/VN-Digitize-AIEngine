import numpy as np
from paddleocr import PaddleOCR
from shared_utils.logger import get_logger

# Kế thừa Gói hàng từ Module 1
from module_1_image_preprocessing.models import PreprocessResult

# Nhập nội bộ
from .models import OcrResult, OcrWord, BoundingBox
from .config import OcrConfig

logger = get_logger(__name__)

class OcrEngine:
    def __init__(self, config: OcrConfig | None = None):
        self._config = config or OcrConfig()
        logger.info("Đang khởi tạo PaddleOCR...")
        
        # Khởi tạo mô hình (Đã xóa tham số show_log)
        self.ocr = PaddleOCR(
            use_angle_cls=self._config.use_angle_cls, 
            lang=self._config.lang,
        )

    def process(self, preprocessed_data: PreprocessResult) -> OcrResult:
        # 1. Kiểm tra đầu vào từ Module 1
        if not preprocessed_data or preprocessed_data.processed_image is None:
            return OcrResult(is_success=False, words=[], full_text="", error_message="Ảnh đầu vào trống hoặc bị lỗi Crop.")
        
        # 2. Cơ chế tiết kiệm tài nguyên (Kế thừa trí tuệ Module 1)
        if preprocessed_data.is_blank:
            logger.warning("Trang trắng. Bỏ qua chạy OCR AI để tiết kiệm CPU.")
            return OcrResult(is_success=True, words=[], full_text="[TRANG_TRẮNG]")

        # 3. Kích hoạt AI
        image = preprocessed_data.processed_image
        logger.info("Đang chạy OCR Detection & Recognition...")
        
        try:
            # PaddleOCR trả về format khá lằng nhằng: [[[[x,y],[x,y],[x,y],[x,y]], ("text", confidence)], ...]
            raw_result = self.ocr.ocr(image, cls=self._config.use_angle_cls)
            
            words = []
            full_text_parts = []
            
            # Đảm bảo có kết quả trả về
            if raw_result and raw_result[0]:
                for line in raw_result[0]:
                    box = line[0]           # Tọa độ 4 góc
                    text = line[1][0]       # Nội dung chữ
                    score = float(line[1][1]) # Độ tự tin
                    
                    words.append(OcrWord(
                        text=text,
                        confidence=score,
                        bbox=BoundingBox(points=[(int(p[0]), int(p[1])) for p in box])
                    ))
                    full_text_parts.append(text)
                    
            logger.info(f"Hoàn tất. Trích xuất được {len(words)} dòng chữ.")
            return OcrResult(
                is_success=True,
                words=words,
                full_text="\n".join(full_text_parts)
            )
            
        except Exception as e:
            logger.error(f"Lỗi hệ thống OCR: {e}")
            return OcrResult(is_success=False, words=[], full_text="", error_message=str(e))