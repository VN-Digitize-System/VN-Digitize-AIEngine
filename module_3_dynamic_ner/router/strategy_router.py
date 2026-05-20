from typing import Dict, Type, Any, List
from extractors.base_extractor import BaseExtractor
from schemas.template_schema import DocumentInput, ExtractedField

class StrategyRouter:
    """
    Bộ não định tuyến: Nhận cấu hình từ file JSON và tự động điều phối
    công việc cho các Extractor tương ứng mà không cần if/else cứng.
    """
    def __init__(self):
        # Cuốn "từ điển" lưu trữ danh sách các công nhân (Extractor)
        self._registry: Dict[str, Type[BaseExtractor]] = {}

    def register_extractor(self, strategy_type: str, extractor_class: Type[BaseExtractor]):
        """Đăng ký một class Extractor mới vào hệ thống (Open/Closed Principle)."""
        self._registry[strategy_type] = extractor_class
        print(f"⚙️ [Router] Đã đăng ký công nhân xử lý loại: '{strategy_type}'")

    def process_document(self, document: DocumentInput, fields_config: Dict[str, Any]) -> List[ExtractedField]:
        """Duyệt qua các trường cấu hình, gọi đúng Extractor và trả về kết quả."""
        results = []
        
        for field_name, config in fields_config.items():
            strategy_type = config.get("type")
            
            # Xử lý Ngoại lệ: Graceful Degradation (Option 2B)
            if strategy_type not in self._registry:
                print(f"⚠️ [Cảnh báo] Bỏ qua trường '{field_name}': Hệ thống chưa có Extractor loại '{strategy_type}'.")
                continue
                
            # Khởi tạo Extractor từ registry (Từ điển)
            extractor_class = self._registry[strategy_type]
            extractor_instance = extractor_class(field_name, config)
            
            # Kích hoạt bóc tách
            result = extractor_instance.extract(document)
            if result:
                results.append(result)
                
        return results