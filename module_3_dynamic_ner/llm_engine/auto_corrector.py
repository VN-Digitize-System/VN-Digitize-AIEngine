import time
from google import genai
from google.genai import types
from schemas.template_schema import ExtractedField

class AutoCorrector:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.primary_model = 'gemini-2.5-flash'
        self.fallback_model = 'gemini-2.0-flash'

    def correct_field(self, field: ExtractedField, context_text: str) -> ExtractedField:
        prompt = f"""
        Nhiệm vụ của bạn là sửa lỗi chính tả/OCR cho một đoạn dữ liệu ngắn dựa vào ngữ cảnh văn bản.
        
        [Ngữ cảnh tài liệu]: {context_text}
        [Dữ liệu đang bị lỗi]: "{field.raw_value}"
        [Lý do lỗi]: {field.error_reason}
        
        Hãy trả về DUY NHẤT chuỗi dữ liệu đã được sửa lại cho đúng. Không giải thích, không dùng ngoặc kép, không định dạng JSON.
        Nếu không thể sửa, hãy trả về chính xác chuỗi bị lỗi ban đầu.
        """
        
        max_retries = 3
        wait_time = 2

        # CƠ CHẾ AUTO-RETRY
        for attempt in range(max_retries):
            try:
                print(f"🔧 [AutoCorrector] Lần thử {attempt + 1}/{max_retries} sửa trường '{field.field_name}'...")
                response = self.client.models.generate_content(
                    model=self.primary_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                
                field.raw_value = response.text.strip()
                field.is_valid = True
                field.error_reason = "Đã được AI tự động sửa lỗi (Auto-corrected)"
                return field
            except Exception as e:
                print(f"⚠️ [AutoCorrector] Lỗi mạng, chờ {wait_time}s... ({e})")
                time.sleep(wait_time)
                
        # CƠ CHẾ MODEL FALLBACK
        print(f"🔄 [AutoCorrector] Chuyển sang mô hình dự phòng {self.fallback_model}...")
        try:
            response = self.client.models.generate_content(
                model=self.fallback_model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            field.raw_value = response.text.strip()
            field.is_valid = True
            field.error_reason = "Đã sửa lỗi bằng mô hình dự phòng (Fallback)"
            return field
        except Exception as e:
            print(f"❌ [AutoCorrector] Thất bại toàn tập. Giữ nguyên giá trị gốc.")
            return field