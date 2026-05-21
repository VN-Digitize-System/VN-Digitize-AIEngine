import os
import json
from dotenv import load_dotenv
from schemas.template_schema import DocumentInput
from extractors.regex_extractor import RegexExtractor
from extractors.layout_regex_extractor import LayoutRegexExtractor
from router.strategy_router import StrategyRouter
from llm_engine.gemini_provider import GeminiProvider

def run_real_ai_test():
    print("🚀 BẮT ĐẦU KIỂM THỬ HỆ THỐNG VỚI GEMINI API THẬT ONLINE...\n")

    # 1. Nạp cấu hình bảo mật từ file .env
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or "BancanDánChuoi" in api_key:
        print("❌ [Lỗi Hệ Thống] Không tìm thấy GEMINI_API_KEY hợp lệ trong file .env!")
        print("Vui lòng kiểm tra lại Bước 2.")
        return

    # 2. Đọc dữ liệu kiểm thử phức tạp (Trang 1, 2, 3 hỗn hợp)
    with open("real_input.json", "r", encoding="utf-8") as f:
        document = DocumentInput(**json.load(f))

    # 3. Đọc file cấu hình Luật
    with open("configs/rules_hanh_chinh.json", "r", encoding="utf-8") as f:
        fields_config = json.load(f).get("fields", {})

    # 4. KHỞI TẠO ROUTER VỚI GEMINI PROVIDER THẬT
    gemini_ai = GeminiProvider(api_key=api_key)
    router = StrategyRouter(llm_provider=gemini_ai)
    
    # Đăng ký các bộ xử lý Rule-based cơ bản
    router.register_extractor("regex", RegexExtractor)
    router.register_extractor("keyword", RegexExtractor)
    router.register_extractor("layout_regex", LayoutRegexExtractor)
    
    print("\n[Hệ thống] Đang chạy chuỗi bóc tách Hybrid...")
    results = router.process_document(document, fields_config)

    # 5. In báo cáo nghiệm thu tính năng
    print("\n" + "="*110)
    print(f"{'BÁO CÁO NGHIỆM THU: KẾT QUẢ TRÍCH XUẤT LIVE TỪ GEMINI API':^110}")
    print("="*110)
    print(f"{'TÊN TRƯỜNG':<18} | {'GIÁ TRỊ BẮT ĐƯỢC':<25} | {'TRẠNG THÁI':<12} | {'GHI CHÚ / LỖI'}")
    print("-" * 110)

    for res in results:
        status = "✅ HỢP LỆ" if res.is_valid else "❌ CẢNH BÁO"
        error_msg = res.error_reason if not res.is_valid else ""
        print(f"{res.field_name:<18} | {res.raw_value:<25} | {status:<12} | {error_msg}")
            
    print("="*110 + "\n")

if __name__ == "__main__":
    run_real_ai_test()