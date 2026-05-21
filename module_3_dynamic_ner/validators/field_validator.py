import re
from datetime import datetime
from schemas.template_schema import ExtractedField
from typing import Dict, Any, List

class FieldValidator:
    """
    Tầng kiểm duyệt dữ liệu (Validation Layer).
    Đánh giá kết quả từ lớp Extractor dựa trên cấu hình và gán cờ báo lỗi.
    """
    
    @staticmethod
    def validate(field: ExtractedField, validation_config: Dict[str, Any]) -> ExtractedField:
        # Nếu Admin không cấu hình rule nào cho trường này thì bỏ qua kiểm duyệt
        if not validation_config:
            return field
            
        rules: List[str] = validation_config.get("rules", [])
        errors = []
        
        # 1. Kiểm tra trường bắt buộc (Không được rỗng)
        if "not_empty" in rules:
            if not field.raw_value or field.raw_value.strip() == "":
                errors.append("Giá trị bị rỗng")
                
        # 2. Kiểm tra độ dài chính xác (VD: CCCD phải đủ 12 số)
        if "exact_length" in rules:
            target_length = validation_config.get("target_length")
            # Loại bỏ khoảng trắng khi đếm để tránh lỗi (VD: "079 123 456 789")
            clean_value = field.raw_value.replace(" ", "")
            if target_length and len(clean_value) != target_length:
                errors.append(f"Độ dài không hợp lệ (Yêu cầu: {target_length}, Thực tế: {len(clean_value)})")
                
        # 3. Kiểm tra khớp định dạng Regex chuẩn
        if "regex_format" in rules:
            expected_format = validation_config.get("expected_format")
            if expected_format:
                if not re.match(expected_format, field.raw_value):
                    errors.append("Không khớp định dạng chuẩn")
                    
        # 4. Kiểm tra logic Ngày tháng hợp lệ (VD: Chặn ngày 30/02 hoặc 31/04)
        if "valid_date" in rules:
            if not FieldValidator._is_valid_date_logic(field.raw_value):
                errors.append("Ngày tháng không hợp lệ theo lịch chuẩn")
        
        # TỔNG HỢP LỖI (Option 2): Nếu có lỗi, gom tất cả lại và đánh cờ False
        if errors:
            field.is_valid = False
            field.error_reason = " | ".join(errors)
            
        return field
        
    @staticmethod
    def _is_valid_date_logic(date_str: str) -> bool:
        """Thuật toán trích xuất con số và kiểm tra tính hợp lệ của lịch"""
        # Tìm tất cả các cụm số trong chuỗi (VD: "Ngày 15 tháng 05 năm 2026" -> ['15', '05', '2026'])
        numbers = re.findall(r'\d+', date_str)
        if len(numbers) >= 3:
            try:
                # Giả định thứ tự là Ngày - Tháng - Năm (chuẩn Việt Nam)
                day, month, year = int(numbers[0]), int(numbers[1]), int(numbers[2])
                
                # Giới hạn năm để chặn các lỗi nhận diện OCR quá vô lý
                if year < 1900 or year > 2100:
                    return False
                    
                # Hàm datetime sẽ tự động văng lỗi ValueError nếu ngày không tồn tại (VD: tháng 2 có 30 ngày)
                datetime(year, month, day)
                return True
            except ValueError:
                return False
                
        # Trả về True nếu không đủ 3 con số, nhường quyền phán quyết lại cho QA/LLM
        return True