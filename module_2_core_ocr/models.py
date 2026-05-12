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
    words: List[OcrWord]       # Danh sách chi tiết từng dòng chữ kèm tọa độ
    full_text: str             # Toàn bộ text thô ghép lại (Dành cho Module 3 xài)
    error_message: str | None = None