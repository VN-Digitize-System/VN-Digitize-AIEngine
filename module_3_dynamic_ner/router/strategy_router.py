import json
from typing import Dict, Type, Any, List
from extractors.base_extractor import BaseExtractor
from schemas.template_schema import DocumentInput, ExtractedField, BoundingBox
from validators.field_validator import FieldValidator
from llm_engine.llm_provider import BaseLLMProvider  # Sửa lỗi Dependency: Dùng Interface trừu tượng

class StrategyRouter:
    def __init__(self, llm_provider: BaseLLMProvider = None):
        self._registry: Dict[str, Type[BaseExtractor]] = {}
        self.llm_provider = llm_provider

    def register_extractor(self, strategy_type: str, extractor_class: Type[BaseExtractor]):
        self._registry[strategy_type] = extractor_class
        print(f"⚙️ [Router] Đã đăng ký công nhân xử lý loại: '{strategy_type}'")

    def process_document(self, document: DocumentInput, fields_config: Dict[str, Any]) -> List[ExtractedField]:
        results = []
        llm_batch_schema = {}
        
        print("\n--- BẮT ĐẦU ĐỊNH TUYẾN VÀ BÓC TÁCH ---")
        
        # PHẦN 1: QUÉT REGEX VÀ GOM NHÓM FALLBACK
        for field_name, config in fields_config.items():
            extraction_method = config.get("extraction_method", "regex") # Mặc định regex (Tương thích ngược)
            
            # 1.1 Trực tiếp chỉ định dùng AI (Các trường quá khó)
            if extraction_method == "llm":
                llm_batch_schema[field_name] = config.get("description", "")
                continue
                
            # 1.2 Xử lý bằng Regex
            strategy_type = extraction_method 
            if strategy_type in self._registry:
                extractor_instance = self._registry[strategy_type](field_name, config)
                result = extractor_instance.extract(document)
                
                if result:
                    # Chạy màng lọc Validator
                    validated_result = FieldValidator.validate(result, config.get("validation", {}))
                    results.append(validated_result)
                else:
                    # LƯỚI AN TOÀN (FALLBACK): Regex trượt -> Ném sang cho AI
                    print(f"⚠️ [Fallback] Regex bắt trượt trường '{field_name}'. Chuyển giao cho LLM...")
                    llm_batch_schema[field_name] = config.get("description", "")

        # PHẦN 2: KÍCH HOẠT LLM BATCH EXTRACTION (GOM MẺ 1 LẦN)
        if llm_batch_schema and self.llm_provider:
            # Lấy toàn bộ văn bản làm ngữ cảnh
            context_text = "\n".join([line.text for line in document.lines])
            
            # Tích hợp JSON Healing ngầm định: Yêu cầu AI tuyệt đối không markdown
            system_prompt = "Bạn là AI bóc tách tài liệu. Chỉ trả về JSON hợp lệ, tuyệt đối không có markdown hay text dư thừa."
            
            print(f"📦 [Batching] Đang gọi LLM đọc 1 lần để bóc tách {len(llm_batch_schema)} trường còn thiếu...")
            llm_results = self.llm_provider.extract_batch_json(context_text, llm_batch_schema, system_prompt)
            
            # PHẦN 3: ĐÓNG GÓI VÀ GÁN CONFIDENCE TĨNH
            for field_name, value in llm_results.items():
                safe_value = str(value) if value is not None else ""
                
                field_obj = ExtractedField(
                    field_name=field_name,
                    raw_value=safe_value.strip(),
                    confidence=0.85, # Điểm tĩnh chốt theo cấu hình hiệu năng cao
                    bounding_box=BoundingBox(x_min=0, y_min=0, x_max=0, y_max=0), 
                    page_number=1
                )
                
                # Chạy Validator cho kết quả của AI
                field_config = fields_config.get(field_name, {})
                validated_obj = FieldValidator.validate(field_obj, field_config.get("validation", {}))
                results.append(validated_obj)

        return results