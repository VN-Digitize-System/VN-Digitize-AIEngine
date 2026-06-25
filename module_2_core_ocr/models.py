from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class BoundingBox:
    # Lưu 4 góc: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    points: List[Tuple[int, int]] 

@dataclass
class OcrWord:
    text: str
    confidence: float
    bbox: BoundingBox

@dataclass
class OcrResult:
    is_success: bool
    words: List[OcrWord]
    full_text: str
    page_number: int = 1  # <--- THÊM DÒNG NÀY (Mặc định là 1)
    error_message: str | None = None