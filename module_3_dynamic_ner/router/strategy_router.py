from typing import Dict, Type, Any, List
from extractors.base_extractor import BaseExtractor
from schemas.template_schema import DocumentInput, ExtractedField, BoundingBox
from validators.field_validator import FieldValidator
from llm_engine.retriever import HeuristicRetriever
from llm_engine.gemini_provider import GeminiProvider

class StrategyRouter:
    def __init__(self, llm_provider: GeminiProvider = None):
        self._registry: Dict[str, Type[BaseExtractor]] = {}
        self.llm_provider = llm_provider # Nhận Provider từ bên ngoài truyền vào

    def register_extractor(self, strategy_type: str, extractor_class: Type[BaseExtractor]):
        self._registry[strategy_type] = extractor_class
        print(f"⚙️ [Router] Đã đăng ký công nhân xử lý loại: '{strategy_type}'")

    def process_document(self, document: DocumentInput, fields_config: Dict[str, Any]) -> List[ExtractedField]:
        results = []
        llm_batch_schema = {}
        llm_keywords = []
        llm_field_configs = {} # SỬA LỖI TẠI ĐÂY: Thêm biến để lưu lại cấu hình của Tầng 2
        
        llm_system_prompt = "Bạn là trợ lý AI bóc tách dữ liệu." 
        
        # PHẦN 1: XỬ LÝ RULE-BASED VÀ GOM NHÓM LLM
        for field_name, config in fields_config.items():
            strategy_type = config.get("type")
            
            if strategy_type == "llm_batch":
                llm_system_prompt = config.get("system_prompt", llm_system_prompt)
                
                # SỬA LỖI TẠI ĐÂY: Lấy danh sách các trường con (Tầng 2)
                nested_fields = config.get("fields", {})
                llm_field_configs = nested_fields # Lưu lại để lát gọi Validator
                
                # Duyệt qua từng trường con (ten_bi_cao, toi_danh...)
                for sub_field, sub_config in nested_fields.items():
                    llm_batch_schema[sub_field] = sub_config.get("description")
                    llm_keywords.extend(sub_config.get("retrieval_keywords", []))
                continue
                
            if strategy_type not in self._registry:
                continue
                
            extractor_instance = self._registry[strategy_type](field_name, config)
            result = extractor_instance.extract(document)
            
            if result:
                validated_result = FieldValidator.validate(result, config.get("validation", {}))
                results.append(validated_result)

        # PHẦN 2: KÍCH HOẠT LLM BATCH EXTRACTION
        if llm_batch_schema and self.llm_provider:
            context = HeuristicRetriever.retrieve_context(document, llm_keywords)
            llm_results = self.llm_provider.extract_batch_json(context, llm_batch_schema, llm_system_prompt)
            
            for sub_field, value in llm_results.items():
                safe_value = str(value) if value is not None else ""
                
                field_obj = ExtractedField(
                    field_name=sub_field,
                    raw_value=safe_value.strip(),
                    confidence=0.85, 
                    bounding_box=BoundingBox(x_min=0, y_min=0, x_max=0, y_max=0), 
                    page_number=1
                )
                
                # SỬA LỖI TẠI ĐÂY: Lấy validation config từ Tầng 2 (llm_field_configs) thay vì Tầng 1
                original_config = llm_field_configs.get(sub_field, {})
                validated_obj = FieldValidator.validate(field_obj, original_config.get("validation", {}))
                results.append(validated_obj)

        return results