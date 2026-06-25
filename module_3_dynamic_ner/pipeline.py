import os
import json
from pathlib import Path
from typing import Dict, Any, List
from .schemas.template_schema import DocumentInput, ExtractedField
from .router.strategy_router import StrategyRouter
from .router.classifier import DocumentClassifier
from .llm_engine.gemini_provider import GeminiProvider
from .llm_engine.local_llm_provider import LocalLLMProvider
from .llm_engine.auto_corrector import AutoCorrector
from .validators.output_validator import OutputValidator

class DocumentPipeline:
    def __init__(self, api_key: str):
        self.engine = os.getenv("LLM_ENGINE", "gemini").lower()
        
        if self.engine == "local":
            print("⚙️ [Pipeline] Khởi chạy chế độ OFFLINE (Local LLM)")
            self.llm_provider = LocalLLMProvider()
        else:
            print("⚙️ [Pipeline] Khởi chạy chế độ CLOUD (Gemini API)")
            self.llm_provider = GeminiProvider(api_key=api_key)
            
        self.auto_corrector = AutoCorrector(api_key=api_key)
        self.router = StrategyRouter(llm_provider=self.llm_provider)
        
        from .extractors.regex_extractor import RegexExtractor
        from .extractors.layout_regex_extractor import LayoutRegexExtractor
        self.router.register_extractor("regex", RegexExtractor)
        self.router.register_extractor("keyword", RegexExtractor)
        self.router.register_extractor("layout_regex", LayoutRegexExtractor)
        
        self.validator = OutputValidator()
        
        # 1. KHỞI TẠO NGƯỜI GÁC CỔNG
        self.classifier = DocumentClassifier()

    def _load_dynamic_config(self, rule_file_name: str) -> Dict[str, Any]:
        """Nạp cấu hình động (Lazy Loading) và Fail-Fast nếu cấu hình bị lỗi"""
        
        # Tự động định vị: Lấy thư mục hiện tại chứa pipeline.py (chính là module_3_dynamic_ner)
        current_dir = Path(__file__).resolve().parent
        config_path = current_dir / "configs" / rule_file_name
    
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                return config_data.get("fields", {})
        except FileNotFoundError:
            # Chết nhanh: Báo động đỏ nếu thiếu file
            raise RuntimeError(f"Lỗi hệ thống: Không tìm thấy file cấu hình '{rule_file_name}'")
        except json.JSONDecodeError:
            # Chết nhanh: Báo động đỏ nếu file JSON sai cú pháp
            raise RuntimeError(f"Lỗi hệ thống: File '{rule_file_name}' bị sai định dạng JSON")

    def process(self, document: DocumentInput, enable_auto_correct: bool = False) -> List[ExtractedField]:
        # BƯỚC 1: Phân loại tài liệu để lấy tên file cấu hình
        rule_file = self.classifier.classify(document)
        
        # BƯỚC 2: Tải cấu hình động (Lazy Load)
        fields_config = self._load_dynamic_config(rule_file)
        
        # BƯỚC 3: Định tuyến và Bóc tách
        results = self.router.process_document(document, fields_config)
        
        # BƯỚC 4: Tự động sửa lỗi (Auto-Correct) nếu Client yêu cầu
        if enable_auto_correct:
            # Gom chữ của toàn bộ các trang lại thành 1 chuỗi ngữ cảnh duy nhất
            context_text = "\n".join([line.text for line in document.lines])
            for field in results:
                if not field.is_valid:
                    self.auto_corrector.correct_field(field, context_text)
                    
        return results