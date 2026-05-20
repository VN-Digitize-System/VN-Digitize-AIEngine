from abc import ABC, abstractmethod
from schemas.template_schema import DocumentInput, ExtractedField
from typing import Optional, Dict, Any

class BaseExtractor(ABC):
    """
    Lớp gốc (Base Class) cho tất cả các thuật toán bóc tách.
    """
    def __init__(self, field_name: str, config: Dict[str, Any]):
        self.field_name = field_name
        self.config = config # Chứa mô tả, pattern lấy từ file rules_hanh_chinh.json

    @abstractmethod
    def extract(self, document: DocumentInput) -> Optional[ExtractedField]:
        """
        Hàm cốt lõi. Nhận vào toàn bộ text của tài liệu, trả về field nếu tìm thấy.
        Nếu không tìm thấy, bắt buộc trả về None.
        """
        pass