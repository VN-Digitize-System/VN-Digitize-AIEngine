import os
import sys
import json
import re
from pathlib import Path

# ==========================================
# ⚙️ CÔNG TẮC TÙY BIẾN ĐẦU RA (OUTPUT TOGGLES)
# ==========================================
EXPORT_EXCEL = True   # Đổi thành False nếu không muốn xuất Excel
EXPORT_PDF = True     # Đổi thành False nếu không muốn xuất PDF

# Thêm đường dẫn gốc
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from module_3_dynamic_ner.orchestrator.session_manager import SessionManager
from module_3_dynamic_ner.orchestrator.export_excel import export_to_excel
from module_3_dynamic_ner.orchestrator.export_pdf import export_to_pdf  # <--- Import Động cơ PDF

def extract_page_number(filename: str) -> int:
    match = re.search(r'page_(\d+)', filename.lower())
    if match: return int(match.group(1))
    match = re.search(r'\d+', filename)
    return int(match.group()) if match else 0

def print_rich_console_table(records: list):
    print("\n" + "═" * 85)
    print(f" 🔎 BẢNG ĐỐI CHIẾU TRỰC QUAN - KẾT QUẢ BÓC TÁCH ({len(records)} HỒ SƠ)")
    print("═" * 85)
    for idx, record in enumerate(records, 1):
        print(f"\n 📁 HỒ SƠ SỐ {idx}:")
        print("┌──────────────────────┬──────────────────────────────────────────────────────────────┐")
        print("│ TRƯỜNG THÔNG TIN     │ GIÁ TRỊ BÓC TÁCH ĐƯỢC                                        │")
        print("├──────────────────────┼──────────────────────────────────────────────────────────────┤")
        for key, value in record.items():
            display_val = str(value) if value is not None else "[KHÔNG TÌM THẤY - LỖI/RỖNG]"
            if len(display_val) > 58: display_val = display_val[:55] + "..."
            print(f"│ {key:<20} │ {display_val:<60} │")
        print("└──────────────────────┴──────────────────────────────────────────────────────────────┘")

def main():
    INPUT_JSON_DIR = PROJECT_ROOT / "tests/data/unit_tests/module_3/test_sodo_only"
    OUTPUT_DIR = PROJECT_ROOT / "tests/data/outputs/unit_tests/module_3"
    
    print("==================================================")
    print("🚀 KHỞI ĐỘNG LUỒNG KIỂM THỬ MODULE 3 (VERTICAL SLICE)")
    print("==================================================")

    catalog_config_path = PROJECT_ROOT / "module_3_dynamic_ner" / "configs" / "document_catalog.json"
    if not catalog_config_path.exists():
        return

    with open(catalog_config_path, 'r', encoding='utf-8') as f:
        catalog_config = json.load(f)

    json_files = [f for f in os.listdir(INPUT_JSON_DIR) if f.endswith('.json')]
    json_files.sort(key=extract_page_number)
    print(f"📂 Thứ tự nạp file: {json_files}")

    stream_of_pages = []
    for file_name in json_files:
        with open(INPUT_JSON_DIR / file_name, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
        stream_of_pages.append({
            "page_num": extract_page_number(file_name),
            "full_text": ocr_data.get("full_text", ""),
            "words": ocr_data.get("words", [])
        })

    print("\n🧠 Đang khởi tạo SessionManager và thực thi bóc tách...")
    manager = SessionManager(catalog_config)
    extracted_records = manager.process_document_stream(stream_of_pages)

    if extracted_records:
        print_rich_console_table(extracted_records)
        
        # --- KÍCH HOẠT ĐẦU RA DỰA VÀO CÔNG TẮC ---
        if EXPORT_EXCEL:
            excel_path = OUTPUT_DIR / "muc_luc_quan_ly.xlsx"
            export_to_excel(extracted_records, str(excel_path))
            
        if EXPORT_PDF:
            pdf_path = OUTPUT_DIR / "muc_luc_quan_ly.pdf"
            export_to_pdf(extracted_records, str(pdf_path))
            
        if not EXPORT_EXCEL and not EXPORT_PDF:
            print("\n💡 Đã hoàn tất bóc tách nhưng không lưu file do cả 2 công tắc đều đang TẮT (False).")
    else:
        print("\n⚠️ Cảnh báo: Không bóc được hồ sơ nào!")

if __name__ == "__main__":
    main()