import json
import time
from google import genai
from google.genai import types
from llm_engine.llm_provider import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = genai.Client(api_key=self.api_key)
        # Khai báo mô hình chính và mô hình dự phòng
        self.primary_model = 'gemini-2.5-flash'
        self.fallback_model = 'gemini-2.0-flash'

    def extract_batch_json(self, context_text: str, json_schema: dict, system_prompt: str) -> dict:
        prompt = f"""
        {system_prompt}
        
        Quy tắc bắt buộc:
        1. Không giải thích gì thêm, trả về duy nhất định dạng JSON.

        [VĂN BẢN CẦN BÓC TÁCH]:
        {context_text}

        [CẤU TRÚC JSON YÊU CẦU]:
        {json.dumps(json_schema, ensure_ascii=False, indent=2)}
        """

        max_retries = 3
        wait_time = 2 # Chờ 2 giây trước khi thử lại

        # BƯỚC 1: CƠ CHẾ AUTO-RETRY (OPTION B)
        for attempt in range(max_retries):
            try:
                print(f"⏳ [Gemini] Lần thử {attempt + 1}/{max_retries} với mô hình {self.primary_model}...")
                response = self.client.models.generate_content(
                    model=self.primary_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                
                extracted_data = json.loads(response.text)
                print("✅ [Gemini] Đã bóc tách thành công!")
                return extracted_data
                
            except json.JSONDecodeError:
                print("❌ [Lỗi] Gemini trả về dữ liệu không phải chuẩn JSON.")
                return {}
            except Exception as e:
                print(f"⚠️ [Cảnh báo API] Lỗi nghẽn mạng (Thử lại sau {wait_time}s): {e}")
                time.sleep(wait_time)

        # BƯỚC 2: CƠ CHẾ MODEL FALLBACK (OPTION C) - Kích hoạt khi hết 3 lần thử
        print(f"🔄 [Fallback] Mô hình chính quá tải. Đang chuyển sang mô hình dự phòng {self.fallback_model}...")
        try:
            response = self.client.models.generate_content(
                model=self.fallback_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            extracted_data = json.loads(response.text)
            print("✅ [Gemini Fallback] Bóc tách thành công bằng mô hình dự phòng!")
            return extracted_data
        except Exception as e:
            print(f"❌ [Lỗi Kép] Cả 2 mô hình đều thất bại. Trả về rỗng. Chi tiết: {e}")
            return {}