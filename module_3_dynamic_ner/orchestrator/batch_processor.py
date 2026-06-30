import os
import json
import glob
import logging

# Giả định bạn đã lưu 2 file trước đó vào cùng thư mục hoặc có thể import được
# Tùy thuộc vào cấu trúc, bạn có thể cần điều chỉnh đường dẫn import
from document_splitter import DocumentSplitter
from llm_service import OllamaClient, draw_hitl_dashboard
from export_excel import export_to_excel

# Cấu hình log
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# CẤU HÌNH KHÔNG GIAN LÀM VIỆC (WORKSPACE)
# =====================================================================
INPUT_DIR = "../jsons/" # Thư mục chứa file OCR của Module 2
WORKSPACE_DIR = "../module_3_workspace/"
CHECKPOINT_DIR = os.path.join(WORKSPACE_DIR, "checkpoints/")
SCHEMAS_DIR = "../schemas/"

# Đảm bảo các thư mục tồn tại
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(SCHEMAS_DIR, exist_ok=True)

def load_all_schemas():
    """Đọc tất cả các file Lược đồ hiện có để làm danh sách phân loại"""
    schemas = {}
    for filepath in glob.glob(os.path.join(SCHEMAS_DIR, "*.json")):
        filename = os.path.basename(filepath).replace(".json", "")
        schemas[filename] = filepath
    return schemas

def run_pipeline():
    logger.info("🚀 KHỞI ĐỘNG HỆ THỐNG ORCHESTRATOR MODULE 3...")
    
    # 1. Khởi tạo Công cụ
    splitter = DocumentSplitter()
    llm = OllamaClient() # Sẽ tự động chạy Warm-up Ping
    
    # 2. Đọc file OCR đầu vào (Giả sử đọc file scan_001_ocr.json)
    # Trong thực tế, bạn sẽ dùng vòng lặp glob để đọc nhiều file
    sample_ocr_file = os.path.join(INPUT_DIR, "scan_001_ocr.json")
    if not os.path.exists(sample_ocr_file):
        logger.error(f"[LỖI] Không tìm thấy file {sample_ocr_file}. Vui lòng kiểm tra lại đường dẫn.")
        return

    with open(sample_ocr_file, 'r', encoding='utf-8') as f:
        ocr_data = json.load(f)
        pages_text = ocr_data.get("pages", []) # Mảng chứa text các trang

    # 3. Gọi Lưỡi dao cắt tài liệu
    logger.info(f"\n✂️ Đang phân tách {len(pages_text)} trang văn bản...")
    documents = splitter.split_document(pages_text)
    logger.info(f"✅ Đã cắt thành {len(documents)} tài liệu độc lập.\n")

    # 4. Vòng lặp Bóc tách & Hỏi đáp Động
    for i, doc in enumerate(documents):
        doc_id = f"doc_{i+1}"
        checkpoint_path = os.path.join(CHECKPOINT_DIR, f"{doc_id}.json")

        logger.info("-" * 50)
        logger.info(f"📄 Đang xử lý Tài liệu {doc_id} (Trang {doc['start_page']} - {doc['end_page']})")

        # HƯỚNG 2: BỎ QUA THÔNG MINH (SMART RESUME)
        if os.path.exists(checkpoint_path):
            logger.info(f"[SKIP] ⏩ Đã tìm thấy Checkpoint của {doc_id}. Bỏ qua gọi LLM.")
            continue

        doc_text = doc["stitched_text"]
        available_schemas = load_all_schemas()
        schema_names = list(available_schemas.keys())

        # Kiểm tra HITL (Tài liệu lạ do Tầng 3 báo động)
        if doc.get("is_suspicious"):
            preview_text = "\n".join(doc_text.split('\n')[:5])
            choice = draw_hitl_dashboard(preview_text)
            
            if choice == '3':
                logger.warning("🛑 ĐÃ DỪNG KHẨN CẤP HỆ THỐNG THEO LỆNH NGƯỜI DÙNG!")
                break
            elif choice == '2':
                logger.info(f"⏭️ Bỏ qua tài liệu {doc_id}.\n\n")
                continue
            elif choice == '1':
                # Trong thực tế, bạn sẽ gọi một hàm để người dùng nhập schema mới
                # Để demo, chúng ta giả lập việc tạo schema
                logger.info("🛠️ Đang mở trình tạo Schema... (Tính năng cần code thêm)")
                schema_name = input("Nhập tên loại tài liệu (vd: quyet_dinh_moi): ")
                # Lưu file schema...
                schema_names.append(schema_name)
        
        # Bước Phân loại Siêu nhẹ (Lite Classification)
        prompt_class = f"Văn bản sau thuộc loại nào trong danh sách {schema_names}? Chỉ trả về tên, không giải thích. Văn bản: {doc_text[:500]}"
        # (Lưu ý: Bạn có thể viết thêm một hàm gọi LLM trả text thô, ở đây dùng tạm generate_json)
        # Vì đơn giản hóa, chúng ta giả định đã có schema.
        
        # Bóc tách Zero-shot (Giả lập Prompt)
        logger.info("🧠 Đang gửi dữ liệu cho LLM bóc tách...")
        extraction_prompt = f"Hãy bóc tách thông tin từ văn bản sau thành định dạng JSON. Văn bản:\n{doc_text}"
        result_json = llm.generate_json(extraction_prompt)
        
        # Gắn thêm Metadata
        result_json["_metadata"] = {
            "start_page": doc["start_page"],
            "end_page": doc["end_page"],
            "is_incomplete_scan": doc.get("is_incomplete_scan", False)
        }

        # Lưu Checkpoint
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=4)
        logger.info(f"💾 Đã lưu Checkpoint thành công tại {checkpoint_path}.")
    
    # 5. Xuất báo cáo Excel tự động
    logger.info("-" * 50)
    export_to_excel()

if __name__ == "__main__":
    run_pipeline()