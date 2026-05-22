from typing import Dict, Any, List
from schemas.template_schema import DocumentInput, ExtractedField
from router.strategy_router import StrategyRouter
from llm_engine.gemini_provider import GeminiProvider
from llm_engine.auto_corrector import AutoCorrector
from llm_engine.retriever import HeuristicRetriever

class DocumentPipeline:
    def __init__(self, api_key: str):
        self.llm_provider = GeminiProvider(api_key=api_key)
        self.auto_corrector = AutoCorrector(api_key=api_key)
        
        # Khởi tạo Router và cắm Provider vào
        self.router = StrategyRouter(llm_provider=self.llm_provider)
        
        # Đăng ký các Extractor (Import từ các bài trước)
        from extractors.regex_extractor import RegexExtractor
        from extractors.layout_regex_extractor import LayoutRegexExtractor
        self.router.register_extractor("regex", RegexExtractor)
        self.router.register_extractor("keyword", RegexExtractor)
        self.router.register_extractor("layout_regex", LayoutRegexExtractor)

    def process(self, document: DocumentInput, rules_config: Dict[str, Any], enable_auto_correct: bool) -> List[ExtractedField]:
        print("\n🚀 [Pipeline] BẮT ĐẦU CHẠY ĐƯỜNG ỐNG XỬ LÝ...")
        
        # Bước 1: Trích xuất & Kiểm duyệt (Router lo)
        results = self.router.process_document(document, rules_config)
        
        # Bước 2: Tự động sửa lỗi nếu được Admin yêu cầu (Corrector lo)
        if enable_auto_correct:
            # Lấy ngữ cảnh chung để AI có cơ sở sửa lỗi
            full_context = HeuristicRetriever.retrieve_context(document, []) 
            
            for field in results:
                # Nếu trường bị đánh cờ lỗi và không rỗng
                if not field.is_valid and field.raw_value:
                    self.auto_corrector.correct_field(field, full_context)
                    
        print("✅ [Pipeline] HOÀN TẤT XỬ LÝ!\n")
        return results