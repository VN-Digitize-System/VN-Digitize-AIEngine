from llm_engine.llm_provider import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    def __init__(self):
        # Không cần API Key thật vì đây là đồ giả
        super().__init__(api_key="fake_key_for_testing")

    def extract_batch_json(self, context_text: str, json_schema: dict, system_prompt: str) -> dict:
        print("🤖 [Mock AI] Đang giả lập quá trình đọc hiểu văn bản...")
        print("🤖 [Mock AI] Đã nhận được System Prompt từ JSON config.")
        
        # KỊCH BẢN EDGE CASE (1B):
        # Trả về Tên Bị Cáo chuẩn, nhưng cố tình bỏ trống Tội Danh
        mock_response = {
            "ten_bi_cao": "Nguyễn Văn A",
            "toi_danh": "" # Cố tình lỗi để kích hoạt Validator
        }
        
        print("✅ [Mock AI] Đã trả về kết quả giả định (Edge Case).")
        return mock_response