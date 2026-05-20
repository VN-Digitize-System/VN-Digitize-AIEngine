import json
from schemas.template_schema import DocumentInput
from extractors.regex_extractor import RegexExtractor
from extractors.layout_regex_extractor import LayoutRegexExtractor
from router.strategy_router import StrategyRouter

def run_automated_test():
    print("🚀 Bắt đầu quá trình Kiểm thử Tự động (Automated Testing)...\n")

    # 1. Đọc dữ liệu giả lập (Mock Data)
    try:
        with open("mock_input.json", "r", encoding="utf-8") as f:
            mock_data = json.load(f)
            # Ép kiểu dữ liệu JSON sang Pydantic Model để Validate
            document = DocumentInput(**mock_data)
            print(f"✅ Đã nạp thành công văn bản gồm {len(document.lines)} dòng text.")
    except Exception as e:
        print(f"❌ Lỗi đọc mock_input.json: {e}")
        return

    # 2. Đọc file cấu hình Luật (Rules)
    try:
        with open("configs/rules_hanh_chinh.json", "r", encoding="utf-8") as f:
            rules_config = json.load(f)
            fields_config = rules_config.get("fields", {})
            print(f"✅ Đã nạp thành công bộ luật: {rules_config.get('domain_name')}")
    except Exception as e:
        print(f"❌ Lỗi đọc configs/rules_hanh_chinh.json: {e}")
        return

   # 3. KÍCH HOẠT ROUTER & CHẠY BÓC TÁCH
    print("\n--- Khởi tạo Bộ Định Tuyến (Strategy Router) ---")
    router = StrategyRouter()
    
    # Đăng ký các Extractor vào hệ thống một cách linh hoạt
    router.register_extractor("regex", RegexExtractor)
    router.register_extractor("keyword", RegexExtractor) # Tạm dùng RegexExtractor để bắt keyword
    router.register_extractor("layout_regex", LayoutRegexExtractor)
    
    # Cố tình đăng ký thiếu một loại (ví dụ llm_extractor) để test cảnh báo 2B
    
    print("\n🚀 Bắt đầu quá trình quét dữ liệu...")
    # Router sẽ tự động phân luồng và xử lý toàn bộ
    results = router.process_document(document, fields_config)

    # 4. In báo cáo đẹp mắt (Tùy chọn 3B)
    print("\n" + "="*85)
    print(f"{'BÁO CÁO KẾT QUẢ TRÍCH XUẤT (MODULE 3 - PHASE 1)':^85}")
    print("="*85)
    print(f"{'TÊN TRƯỜNG':<18} | {'GIÁ TRỊ BẮT ĐƯỢC':<25} | {'ĐỘ TIN CẬY':<10} | {'TỌA ĐỘ (BBOX)'}")
    print("-" * 85)

    for res in results:
        if res:
            bbox_str = f"[{res.bounding_box.x_min}, {res.bounding_box.y_min}, {res.bounding_box.x_max}, {res.bounding_box.y_max}]"
            print(f"{res.field_name:<18} | {res.raw_value:<25} | {res.confidence:<10} | {bbox_str}")
        else:
            # Nếu RegexExtractor trả về None
            print(f"{'UNKNOWN':<18} | {'[Không tìm thấy]':<25} | {'N/A':<10} | N/A")
            
    print("="*85 + "\n")

if __name__ == "__main__":
    run_automated_test()