from abc import ABC, abstractmethod
import json

class BaseLLMProvider(ABC):
    """
    Lớp giao tiếp trừu tượng. Thay vì dùng LangChain, ta tự viết Wrapper siêu nhẹ.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def extract_batch_json(self, context_text: str, json_schema: dict) -> dict:
        """
        Nhận vào văn bản đã lọc và Schema các trường cần bóc tách.
        Bắt buộc LLM phải trả về định dạng JSON khớp với schema.
        """
        pass