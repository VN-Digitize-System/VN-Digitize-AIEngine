from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, create_model, ValidationError

class ReflexionRetryException(Exception):
    """Ngoại lệ tùy chỉnh báo hiệu cần chạy vòng lặp Reflexion"""
    def __init__(self, message: str, errors: str):
        super().__init__(message)
        self.errors = errors

class OutputValidator:
    def _generate_dynamic_model(self, json_schema: Dict[str, Any]) -> Type[BaseModel]:
        """Tự động sinh Pydantic class từ JSON Schema (Flexible Optional Mode)"""
        fields = {}
        for field_name in json_schema.keys():
            # Bọc tất cả các trường thành Optional[Any] để hệ thống không bị crash 
            # nếu AI không tìm thấy dữ liệu (Missing Fields), chỉ bắt lỗi sai định dạng Type.
            fields[field_name] = (Optional[Any], None) 
            
        return create_model('DynamicDocumentModel', **fields)

    def validate_and_parse(self, data: Dict[str, Any], json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Kiểm duyệt JSON đầu ra"""
        DynamicModel = self._generate_dynamic_model(json_schema)
        try:
            # Pydantic sẽ tự động ép kiểu và làm sạch dữ liệu
            validated_data = DynamicModel(**data)
            # Trả về dictionary, loại bỏ các trường bị Null để tối ưu dung lượng
            return validated_data.dict(exclude_none=True) 
        
        except ValidationError as e:
            # Gom toàn bộ thông báo lỗi để chuẩn bị "mắng" AI
            error_msgs = [f"- Trường '{err['loc'][0]}': {err['msg']}" for err in e.errors()]
            error_detail = "\n".join(error_msgs)
            raise ReflexionRetryException("Dữ liệu bóc tách vi phạm cấu trúc", error_detail)