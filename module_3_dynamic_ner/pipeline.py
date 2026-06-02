import os
from typing import Dict, Any, List
from schemas.template_schema import DocumentInput, ExtractedField
from router.strategy_router import StrategyRouter
from llm_engine.gemini_provider import GeminiProvider
from llm_engine.auto_corrector import AutoCorrector
from llm_engine.retriever import HeuristicRetriever
from llm_engine.local_llm_provider import LocalLLMProvider
from validators.output_validator import OutputValidator, ReflexionRetryException

class DocumentPipeline:
    def __init__(self, api_key: str):
        # Đọc biến môi trường, mặc định là gemini nếu không có
        self.engine = os.getenv("LLM_ENGINE", "gemini").lower()
        
        # 1. Khởi tạo Engine bóc tách tương ứng
        if self.engine == "local":
            print("⚙️ [Pipeline] Khởi chạy hệ thống ở chế độ OFFLINE (Local LLM)")
            self.llm_provider = LocalLLMProvider()
        else:
            print("⚙️ [Pipeline] Khởi chạy hệ thống ở chế độ CLOUD (Gemini API)")
            self.llm_provider = GeminiProvider(api_key=api_key)
            
        self.auto_corrector = AutoCorrector(api_key=api_key)
        self.router = StrategyRouter(llm_provider=self.llm_provider)
        
        from extractors.regex_extractor import RegexExtractor
        from extractors.layout_regex_extractor import LayoutRegexExtractor
        self.router.register_extractor("regex", RegexExtractor)
        self.router.register_extractor("keyword", RegexExtractor)
        self.router.register_extractor("layout_regex", LayoutRegexExtractor)
        self.validator = OutputValidator() 

    def process_with_reflexion(self, context_text: str, json_schema: dict, system_prompt: str) -> dict:
        max_retries = 3
        current_attempt = 1
        current_prompt = system_prompt
        last_raw_result = {}
        
        while current_attempt <= max_retries:
            # Bước 1: Gọi LLM (Local hoặc Cloud)
            raw_result = self.llm_provider.extract_batch_json(context_text, json_schema, current_prompt)
            last_raw_result = raw_result
            
            # Bước 2: Đưa qua Tầng Kiểm Duyệt
            try:
                valid_result = self.validator.validate_and_parse(raw_result, json_schema)
                return valid_result # Nếu mượt mà, trả về luôn
                
            except ReflexionRetryException as e:
                print(f"⚠️ [Reflexion] Lần {current_attempt}: AI trả về sai định dạng. Đang yêu cầu AI sửa lại...")
                # Nối thêm lời cảnh báo vào System Prompt để AI tự phản tư (Self-Correction)
                current_prompt = system_prompt + f"\n\n[CẢNH BÁO HỆ THỐNG]: Lần trước bạn đã tạo ra JSON sai cấu trúc. Chi tiết lỗi:\n{e.errors}\nHãy tự sửa lại cho chuẩn xác."
                current_attempt += 1
                
        # Bước 3: Nếu thử 3 lần vẫn thất bại -> Kích hoạt Graceful Degradation
        print("❌ [Reflexion] Đã thử 3 lần thất bại. Kích hoạt Xuống cấp ôn hòa (Graceful Degradation).")
        return last_raw_result