import json
from google import genai
from google.genai import types
from llm_engine.llm_provider import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        # Khởi tạo Client theo chuẩn SDK mới của Google
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = 'gemini-2.5-flash'

    def extract_batch_json(self, context_text: str, json_schema: dict, system_prompt: str) -> dict:
        # Thiết kế Prompt (Đã hoàn toàn Dynamic)
        prompt = f"""
        {system_prompt}
        
        Quy tắc bắt buộc:
        1. Không giải thích gì thêm, trả về duy nhất định dạng JSON.

        [VĂN BẢN CẦN BÓC TÁCH]:
        {context_text}

        [CẤU TRÚC JSON YÊU CẦU]:
        {json.dumps(json_schema, ensure_ascii=False, indent=2)}
        """

        try:
            print("⏳ [Gemini] Đang gửi yêu cầu bóc tách Batch Extraction (với SDK mới)...")
            
            # Gọi API với cú pháp hiện đại và tính năng ép kiểu JSON
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1 # Giảm độ sáng tạo để LLM bám sát văn bản gốc
                )
            )
            
            # Parse kết quả trả về thành Dictionary của Python
            extracted_data = json.loads(response.text)
            print("✅ [Gemini] Đã bóc tách thành công!")
            return extracted_data
            
        except json.JSONDecodeError:
            print("❌ [Lỗi] Gemini trả về dữ liệu không phải chuẩn JSON.")
            return {}
        except Exception as e:
            print(f"❌ [Lỗi API Gemini]: {e}")
            return {}