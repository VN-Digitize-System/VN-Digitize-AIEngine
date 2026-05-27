import os
import time
import re
import calendar
from google import genai
from google.genai import types
from openai import OpenAI
from schemas.template_schema import ExtractedField

class AutoCorrector:
    def __init__(self, api_key: str):
        self.engine = os.getenv("LLM_ENGINE", "gemini").lower()
        
        # Khởi tạo Cloud
        self.gemini_client = genai.Client(api_key=api_key)
        self.primary_model = 'gemini-2.5-flash'
        self.fallback_model = 'gemini-2.0-flash'
        
        # Khởi tạo Local
        self.local_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.local_model = "qwen2.5:7b"

    def _fix_date_logic(self, raw_value: str) -> str:
        """Hàm chặn đầu bằng Python để xử lý lỗi ngày tháng tuyệt đối chính xác"""
        match = re.search(r'Ngày (\d{1,2}) tháng (\d{1,2}) năm (\d{4})', raw_value, re.IGNORECASE)
        if match:
            d, m, y = map(int, match.groups())
            # Giới hạn tháng từ 1 đến 12
            m = max(1, min(12, m))
            # Tìm số ngày tối đa của tháng đó trong năm đó (xử lý cả năm nhuận)
            _, max_days = calendar.monthrange(y, m)
            # Giới hạn ngày trong khoảng hợp lệ
            d = max(1, min(max_days, d))
            return f"Ngày {d:02d} tháng {m:02d} năm {y}"
        return raw_value

    def correct_field(self, field: ExtractedField, context_text: str) -> ExtractedField:
        # --- KÍCH HOẠT CHẶN ĐẦU BẰNG PYTHON (Option 1 & Option B) ---
        if field.field_name == "ngay_thang_nam":
            print(f"⚡ [AutoCorrector] Kích hoạt chặn đầu bằng Python cho trường '{field.field_name}'...")
            fixed_date = self._fix_date_logic(field.raw_value)
            
            if fixed_date != field.raw_value:
                field.raw_value = fixed_date
                field.is_valid = True
                field.error_reason = "Đã được hệ thống Rule-based chặn đầu và lùi về ngày hợp lệ"
            return field

        # --- GỌI AI VỚI FEW-SHOT PROMPT CHO CÁC TRƯỜNG VĂN BẢN (Option A) ---
        prompt = f"""
        Nhiệm vụ của bạn là sửa lỗi chính tả/OCR cho một đoạn dữ liệu ngắn dựa vào ngữ cảnh.
        CẢNH BÁO BẮT BUỘC: Tuyệt đối KHÔNG sửa đổi tên người. Chỉ sửa các lỗi chính tả tiếng Việt phổ biến.
        
        --- VÍ DỤ HƯỚNG DẪN TƯ DUY ---
        [Ngữ cảnh]: "Mức phạt là 50.000.000 đổng"
        [Lỗi]: "50.000.000 đổng"
        [Kết quả đúng]: 50.000.000 đồng
        
        [Ngữ cảnh]: "Quyêt dịnh sơ thẳm số 123"
        [Lỗi]: "Quyêt dịnh sơ thẳm"
        [Kết quả đúng]: Quyết định sơ thẩm
        
        [Ngữ cảnh]: "Cộng hòa xả hội chũ nghĩa"
        [Lỗi]: "Cộng hòa xả hội"
        [Kết quả đúng]: Cộng hòa xã hội
        --- KẾT THÚC VÍ DỤ ---

        [Ngữ cảnh tài liệu]: {context_text}
        [Dữ liệu đang bị lỗi]: "{field.raw_value}"
        [Lý do lỗi]: {field.error_reason}
        
        Hãy trả về DUY NHẤT chuỗi dữ liệu đã được sửa lại cho đúng. Không giải thích, không dùng ngoặc kép.
        """
        
        # --- LUỒNG XỬ LÝ LOCAL ---
        if self.engine == "local":
            try:
                print(f"🔧 [AutoCorrector Local] Đang sửa lỗi chính tả bằng Few-Shot Prompt...")
                response = self.local_client.chat.completions.create(
                    model=self.local_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                field.raw_value = response.choices[0].message.content.strip()
                field.is_valid = True
                field.error_reason = "Đã được Local AI tự động sửa lỗi chính tả"
            except Exception as e:
                print(f"❌ [AutoCorrector Local] Thất bại: {e}")
            return field

        # --- LUỒNG XỬ LÝ CLOUD ---
        max_retries = 3
        wait_time = 2
        for attempt in range(max_retries):
            try:
                print(f"🔧 [AutoCorrector Cloud] Lần thử {attempt + 1}/{max_retries} sửa trường '{field.field_name}'...")
                response = self.gemini_client.models.generate_content(
                    model=self.primary_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                field.raw_value = response.text.strip()
                field.is_valid = True
                field.error_reason = "Đã được Cloud AI sửa lỗi"
                return field
            except Exception as e:
                time.sleep(wait_time)
                
        try:
            print(f"🔄 [AutoCorrector] Chuyển Fallback {self.fallback_model}...")
            response = self.gemini_client.models.generate_content(
                model=self.fallback_model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            field.raw_value = response.text.strip()
            field.is_valid = True
            field.error_reason = "Đã sửa lỗi bằng mô hình dự phòng"
        except Exception:
            pass
            
        return field