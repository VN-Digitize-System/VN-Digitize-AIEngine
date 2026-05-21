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

# 4. Định nghĩa Kết quả Bóc tách (Đã cập nhật tính năng Validation - 2B)
class ExtractedField(BaseModel):
    field_name: str
    raw_value: str
    confidence: float
    bounding_box: BoundingBox
    page_number: int
    is_valid: bool = True                  # Mặc định là True, nếu lỗi sẽ chuyển thành False
    error_reason: Optional[str] = None     # Ghi nhận lý do lỗi chi tiết để đưa lên UI