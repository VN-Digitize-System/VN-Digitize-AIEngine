from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# 1. Định nghĩa Tọa độ
class BoundingBox(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int

# 2. Định nghĩa Dữ liệu của 1 dòng (Từ Module 2 gửi sang)
class LineData(BaseModel):
    page_number: int
    text: str
    confidence: float
    bounding_box: BoundingBox

# 3. Định nghĩa Gói Dữ liệu Tổng thể
class DocumentInput(BaseModel):
    image_width: int
    image_height: int
    lines: List[LineData]

# 4. Định nghĩa Kết quả Bóc tách (Output của Module 3)
class ExtractedField(BaseModel):
    field_name: str
    raw_value: str          # Trả về nguyên văn chuỗi gốc theo yêu cầu của bạn
    confidence: float
    bounding_box: BoundingBox
    page_number: int