import numpy as np
from paddleocr import PaddleOCR
from shared_utils.logger import get_logger

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

    def process(self, preprocessor, image_path: str) -> tuple[OcrResult, np.ndarray | None]:
        """
        Nhận đối tượng preprocessor để tự điều phối luồng đi từ M1 sang M2.
        Trả về 2 giá trị: (Kết quả OCR, Ảnh đã qua xử lý để vẽ debug)
        """
        
        # 1. Gọi Module 1 và truyền công tắc lấy từ Config của Module 2
        logger.info(f"Đang thực thi Pipeline với skip_crop={self._config.skip_preprocessing_crop}")
        
        m1_result = preprocessor.process(
            image_path, 
            skip_crop=self._config.skip_preprocessing_crop
        )

        # 2. Kiểm tra nếu Module 1 báo lỗi hoặc trang trắng
        if not m1_result or m1_result.processed_image is None:
            m2_result = OcrResult(is_success=False, words=[], full_text="", error_message="M1 Fail")
            return m2_result, None
            
        if m1_result.is_blank:
            m2_result = OcrResult(is_success=True, words=[], full_text="[BLANK_PAGE]")
            return m2_result, m1_result.processed_image

        # 3. Chạy OCR trên ảnh đã xử lý từ M1
        image = m1_result.processed_image
        
        try:
            raw_result = self.ocr.ocr(image, cls=self._config.use_angle_cls)
            
            words = []
            full_text_parts = []
            
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
            
            # Thay vì return thẳng, ta GÁN kết quả vào biến m2_result
            m2_result = OcrResult(
                is_success=True,
                words=words,
                full_text="\n".join(full_text_parts)
            )
            
        except Exception as e:
            logger.error(f"Lỗi hệ thống OCR: {e}")
            m2_result = OcrResult(is_success=False, words=[], full_text="", error_message=str(e))
        
    
        return m2_result, m1_result.processed_image