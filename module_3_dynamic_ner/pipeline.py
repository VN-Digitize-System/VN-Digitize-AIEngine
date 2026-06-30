import json
import os
from module_3_dynamic_ner.llm_engine.local_llm_provider import LocalLLMProvider
from module_3_dynamic_ner.schemas.template_schema import DocumentInput

class DocumentPipeline:
    def __init__(self, target_fields_path="target_fields.json", model_name="qwen2.5:14b"):
        """
        Khởi tạo Pipeline mới, chỉ sử dụng Local LLM.
        """
        self.llm_provider = LocalLLMProvider(model_name=model_name)
        self.target_fields_path = target_fields_path

    def _build_native_json_schema(self) -> dict:
        """
        Đọc file target_fields.json và tự động sinh Native JSON Schema.
        """
        if not os.path.exists(self.target_fields_path):
            raise FileNotFoundError(f"Không tìm thấy file cấu hình: {self.target_fields_path}")

        with open(self.target_fields_path, 'r', encoding='utf-8') as f:
            target_fields = json.load(f)

        # Khung JSON Schema chuẩn
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # Bơm các biến từ file cấu hình vào Lược đồ
        for key, description in target_fields.items():
            schema["properties"][key] = {
                "type": "string",
                "description": description
            }
            schema["required"].append(key)

        return schema

    def process(self, document: DocumentInput) -> dict:
        """
        Thực thi luồng bóc tách Full LLM (Zero-shot Extraction).
        """
        # 1. Sinh Schema động
        dynamic_schema = self._build_native_json_schema()

        # 2. Gom toàn bộ văn bản OCR (Không cần Bounding Box nữa)
        full_text = "\n".join([line.text for line in document.lines])

        # 3. Mớm System Prompt
        system_prompt = (
            "Bạn là chuyên gia bóc tách dữ liệu văn bản hành chính tiếng Việt. "
            "Nhiệm vụ của bạn là đọc nội dung OCR sau đây và trích xuất thông tin "
            "chính xác theo định dạng JSON được yêu cầu. Tuyệt đối không bịa đặt dữ liệu."
        )

        # 4. Gửi vào LLM Provider
        extracted_json = self.llm_provider.extract_batch_json(
            context_text=full_text,
            json_schema=dynamic_schema,
            system_prompt=system_prompt
        )

        return extracted_json