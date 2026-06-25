import re
from extractors.base_extractor import BaseExtractor
from ..schemas.template_schema import DocumentInput, ExtractedField
from typing import Optional

class RegexExtractor(BaseExtractor):
    def __init__(self, field_name: str, config: dict):
        # Gọi __init__ của lớp cha để nạp field_name và config
        super().__init__(field_name, config)
        self.compiled_patterns = []
        
        # HỖ TRỢ KÉP (Dual Format Support)
        if "regex_pattern" in self.config:
            # 1. Luồng mới (rules_vbpl.json): Xử lý Aliases và {LABEL}
            raw_pattern = self.config.get("regex_pattern", "")
            aliases = self.config.get("aliases", [])
            
            if aliases:
                # Sử dụng Non-capturing group (?:) để tránh cướp Group 1 của dữ liệu chính
                alias_group = "(?:" + "|".join(aliases) + ")"
                pattern_str = raw_pattern.replace("{LABEL}", alias_group)
            else:
                pattern_str = raw_pattern
            
            self._compile_and_add(pattern_str)
        else:
            # 2. Luồng cũ (rules_hanh_chinh.json): Quét mảng patterns
            for pattern_str in self.config.get("patterns", []):
                self._compile_and_add(pattern_str)

    def _compile_and_add(self, pattern_str: str):
        """Biên dịch Regex và kiểm tra lỗi Fail-Fast"""
        try:
            self.compiled_patterns.append(re.compile(pattern_str))
        except re.error as e:
            # Ném HTTP 500 ngay lúc nạp hệ thống nếu admin cấu hình sai luật
            raise ValueError(f"[Fail-Fast] Lỗi cú pháp Regex ở trường '{self.field_name}': {pattern_str}. Chi tiết: {e}")

    def _compress_whitespace(self, text: str) -> str:
        """Tiền xử lý OCR: Nén nhiều khoảng trắng liên tiếp thành 1 dấu cách"""
        return re.sub(r'[ \t]+', ' ', text)

    def _auto_format_output(self, text: str) -> str:
        """Hậu xử lý đầu ra: Dọn dẹp khoảng trắng thừa quanh các dấu câu"""
        text = text.strip()
        text = re.sub(r'\s*/\s*', '/', text)
        text = re.sub(r'\s*-\s*', '-', text)
        return text

    def extract(self, document: DocumentInput) -> Optional[ExtractedField]:
        if not self.compiled_patterns:
            return None

        # Bước 1: Gộp toàn văn bản và Tiền xử lý
        full_text = "\n".join([line.text for line in document.lines])
        clean_text = self._compress_whitespace(full_text)

        # Bước 2: Tìm kiếm First Match Wins
        best_match_text = None
        for regex in self.compiled_patterns:
            match = regex.search(clean_text)
            if match:
                # Nếu Regex dùng ngoặc tròn () để group dữ liệu, lấy group đầu tiên
                best_match_text = match.group(1) if match.groups() else match.group(0)
                break 
        
        if not best_match_text:
            return None # Trả về None để Router biết mà ném cho LLM

        # Hậu xử lý kết quả
        formatted_text = self._auto_format_output(best_match_text)

        # Bước 3: Truy vết Tọa độ Xấp xỉ (Approximate Line Tracing)
        best_line = None
        
        # Tìm dòng chứa nhiều ký tự khớp với kết quả nhất
        for line in document.lines:
            # Loại bỏ khoảng trắng của dòng gốc để dễ đối chiếu
            clean_line_text = self._compress_whitespace(line.text)
            if best_match_text in clean_line_text or formatted_text in clean_line_text:
                best_line = line
                break
        
        # Fallback an toàn: Nếu thuật toán truy vết bị trượt do gộp dòng, mượn tạm tọa độ dòng đầu tiên
        if not best_line and document.lines:
            best_line = document.lines[0]

        # Đóng gói vào đối tượng ExtractedField chuẩn mực
        return ExtractedField(
            field_name=self.field_name,
            raw_value=formatted_text,
            confidence=1.0, # Regex bắt được thì độ tự tin là 100%
            bounding_box=best_line.bounding_box if best_line else None,
            page_number=best_line.page_number if best_line else 1
        )