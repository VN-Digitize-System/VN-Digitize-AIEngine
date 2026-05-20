import re
from extractors.base_extractor import BaseExtractor
from schemas.template_schema import DocumentInput, ExtractedField
from typing import Optional

class RegexExtractor(BaseExtractor):
    
    def extract(self, document: DocumentInput) -> Optional[ExtractedField]:
        patterns = self.config.get("patterns", [])
        
        # Duyệt qua từng mẫu Regex (Từ ưu tiên cao xuống thấp)
        for pattern_str in patterns:
            try:
                # Compile regex để chạy nhanh hơn
                regex = re.compile(pattern_str)
            except re.error:
                print(f"[Cảnh báo] Regex lỗi ở trường {self.field_name}: {pattern_str}")
                continue

            # Duyệt qua từng dòng văn bản từ trên xuống dưới
            for line in document.lines:
                match = regex.search(line.text)
                
                if match:
                    # Lấy chuỗi bắt được (Nếu regex có Group (), lấy cả chuỗi)
                    extracted_text = match.group(0)
                    
                    # Trả về kết quả ngay lập tức (Nguyên văn chuỗi gốc + Tọa độ nguyên bản)
                    return ExtractedField(
                        field_name=self.field_name,
                        raw_value=extracted_text.strip(),
                        confidence=line.confidence,
                        bounding_box=line.bounding_box,
                        page_number=line.page_number
                    )
        
        # Nếu duyệt hết sạch mà không thấy gì, dũng cảm trả về None (Null)
        return None