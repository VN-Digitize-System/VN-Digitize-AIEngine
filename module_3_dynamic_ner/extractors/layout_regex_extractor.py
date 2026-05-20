import re
from extractors.base_extractor import BaseExtractor
from schemas.template_schema import DocumentInput, ExtractedField
from typing import Optional

class LayoutRegexExtractor(BaseExtractor):
    
    def extract(self, document: DocumentInput) -> Optional[ExtractedField]:
        patterns = self.config.get("patterns", [])
        layout_hint = self.config.get("layout_hint", {})
        
        # Lấy giới hạn không gian từ config (mặc định là 1.0 tức 100% nếu không cấu hình)
        x_max_percent = layout_hint.get("x_max_percent", 1.0)
        y_max_percent = layout_hint.get("y_max_percent", 1.0)
        
        # Phòng hờ trường hợp ảnh bị thiếu Width/Height để tránh lỗi chia cho 0
        if document.image_width <= 0 or document.image_height <= 0:
            print(f"[Lỗi] Thiếu kích thước ảnh cho trường {self.field_name}")
            return None

        for pattern_str in patterns:
            try:
                regex = re.compile(pattern_str)
            except re.error:
                continue

            for line in document.lines:
                # 1. TÍNH TOÁN KHÔNG GIAN (Tính tỷ lệ % của tọa độ so với toàn trang)
                rel_x = line.bounding_box.x_min / document.image_width
                rel_y = line.bounding_box.y_min / document.image_height
                
                # 2. KIỂM TRA ĐIỀU KIỆN KHÔNG GIAN
                if rel_x <= x_max_percent and rel_y <= y_max_percent:
                    
                    # 3. NẾU NẰM ĐÚNG VÙNG -> CHẠY REGEX
                    match = regex.search(line.text)
                    if match:
                        extracted_text = match.group(0) # Lấy nguyên văn chuỗi
                        
                        return ExtractedField(
                            field_name=self.field_name,
                            raw_value=extracted_text.strip(),
                            confidence=line.confidence,
                            bounding_box=line.bounding_box,
                            page_number=line.page_number
                        )
                        
        return None