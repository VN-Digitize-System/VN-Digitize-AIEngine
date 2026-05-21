import json
from schemas.template_schema import DocumentInput
from extractors.regex_extractor import RegexExtractor
from extractors.layout_regex_extractor import LayoutRegexExtractor
from router.strategy_router import StrategyRouter
from llm_engine.mock_provider import MockLLMProvider

def run_mock_test():
    print("🚀 Bắt đầu Kiểm thử Luồng LLM (Chế độ Mock Offline)...\n")

    # 1. Đọc dữ liệu giả lập (Tái sử dụng file cũ)
    with open("mock_input.json", "r", encoding="utf-8") as f:
        document = DocumentInput(**json.load(f))

    # 2. Đọc file cấu hình Luật (Đã có sẵn system_prompt và llm_batch)
    with open("configs/rules_hanh_chinh.json", "r", encoding="utf-8") as f:
        fields_config = json.load(f).get("fields", {})

    # 3. KHỞI TẠO ROUTER VỚI MOCK PROVIDER
    # Lắp cái não giả vào thay vì GeminiProvider
    mock_ai = MockLLMProvider()
    router = StrategyRouter(llm_provider=mock_ai)
    
    # Đăng ký các Extractor cũ
    router.register_extractor("regex", RegexExtractor)
    router.register_extractor("keyword", RegexExtractor)
    router.register_extractor("layout_regex", LayoutRegexExtractor)
    
    print("\nQuét văn bản và Kích hoạt AI...")
    results = router.process_document(document, fields_config)

    # 4. In báo cáo
    print("\n" + "="*110)
    print(f"{'BÁO CÁO KẾT QUẢ TRÍCH XUẤT (HYBRID: RULE + MOCK LLM)':^110}")
    print("="*110)
    print(f"{'TÊN TRƯỜNG':<18} | {'GIÁ TRỊ BẮT ĐƯỢC':<25} | {'TRẠNG THÁI':<12} | {'GHI CHÚ / LỖI'}")
    print("-" * 110)

    for res in results:
        status = "✅ HỢP LỆ" if res.is_valid else "❌ CẢNH BÁO"
        error_msg = res.error_reason if not res.is_valid else ""
        print(f"{res.field_name:<18} | {res.raw_value:<25} | {status:<12} | {error_msg}")
            
    print("="*110 + "\n")

if __name__ == "__main__":
    run_mock_test()