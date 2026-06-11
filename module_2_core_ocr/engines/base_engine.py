from abc import ABC, abstractmethod
import numpy as np
from module_2_core_ocr.models import OcrResult

class BaseOcrEngine(ABC):
    """
    Khuôn đúc trừu tượng. Mọi Plugin OCR (Paddle, VietOCR, Tesseract...) 
    bắt buộc phải kế thừa class này và viết logic bên trong hàm process_image.
    """
    @abstractmethod
    def process_image(self, image: np.ndarray) -> OcrResult:
        pass