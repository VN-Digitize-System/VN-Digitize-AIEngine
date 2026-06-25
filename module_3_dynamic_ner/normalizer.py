import re

class OCRNormalizer:
    def __init__(self):
        # Dictionary chứa cấu trúc: { "Regex sai": "Chuỗi đúng" }
        self.correction_rules = {
            # Xử lý cụm "Số:"
            r"(?i)\b(so|sỏ|sô|sö|s0|só|sơ)\s*:": "Số:",
            # Xử lý cụm "Ngày ... tháng ... năm"
            r"(?i)\b(ngay|ngảy|ngáy)\b": "Ngày",
            r"(?i)\b(thang|thảng|tháng)\b": "tháng",
            r"(?i)\b(nam|năm)\b": "năm",
            # Xử lý các lỗi đánh máy dính dấu câu phổ biến
            r"(?i)cộng h[oò]a x[aã] hội": "CỘNG HÒA XÃ HỘI"
        }

    def clean_text(self, text: str) -> str:
        cleaned_text = text
        for wrong_pattern, correct_word in self.correction_rules.items():
            cleaned_text = re.sub(wrong_pattern, correct_word, cleaned_text)
        return cleaned_text