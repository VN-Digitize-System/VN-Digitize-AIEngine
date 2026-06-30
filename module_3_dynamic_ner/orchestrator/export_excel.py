import os
import json
import pandas as pd
import logging

# Cấu hình log
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# CẤU HÌNH ĐƯỜNG DẪN
# =====================================================================
CHECKPOINT_DIR = "../module_3_workspace/checkpoints/"
OUTPUT_EXCEL = "../module_3_workspace/tong_hop_bien_muc.xlsx"

def export_to_excel():
    logger.info("📊 ĐANG TỔNG HỢP DỮ LIỆU TỪ CHECKPOINTS...")
    
    all_docs = []
    # 1. Đọc và gom toàn bộ file JSON
    for filename in os.listdir(CHECKPOINT_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(CHECKPOINT_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    # Tách siêu dữ liệu (Metadata) ra khỏi dữ liệu bóc tách
                    metadata = data.pop("_metadata", {})
                    data["start_page"] = metadata.get("start_page", "")
                    data["end_page"] = metadata.get("end_page", "")
                    data["is_incomplete_scan"] = metadata.get("is_incomplete_scan", False)
                    data["file_nguon"] = filename
                    all_docs.append(data)
                except Exception as e:
                    logger.error(f"[LỖI] Không thể đọc file {filename}: {e}")

    if not all_docs:
        logger.warning("[CẢNH BÁO] Không có dữ liệu Checkpoint để xuất Excel.")
        return

    # 2. Hướng B: Phân trang theo Lược đồ (Multi-Tab Pivot)
    # Nhóm các tài liệu có chung tập hợp các trường (Keys) lại với nhau
    grouped_docs = {}
    for doc in all_docs:
        # Lấy danh sách keys làm "chữ ký" schema (loại trừ các cột hệ thống)
        schema_keys = [k for k in doc.keys() if k not in ["start_page", "end_page", "is_incomplete_scan", "file_nguon"]]
        schema_signature = tuple(sorted(schema_keys))
        
        if schema_signature not in grouped_docs:
            grouped_docs[schema_signature] = []
        grouped_docs[schema_signature].append(doc)

    # 3. Ghi ra Excel và Áp dụng Định dạng Trực quan
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='xlsxwriter') as writer:
        workbook = writer.book
        # Định dạng màu vàng phản quang, chữ đỏ cho các lỗi thiếu trang
        warning_format = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C0006'})
        
        for idx, (signature, docs) in enumerate(grouped_docs.items()):
            sheet_name = f"Lược_Đồ_Loại_{idx + 1}"
            df = pd.DataFrame(docs)
            
            # Sắp xếp lại thứ tự cột: Cột hệ thống lên đầu, dữ liệu bóc tách ở sau
            sys_cols = ["file_nguon", "start_page", "end_page", "is_incomplete_scan"]
            data_cols = [c for c in df.columns if c not in sys_cols]
            df = df[sys_cols + data_cols]
            
            # Ghi DataFrame ra Sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            
            # Tính toán và Auto-fit độ rộng cột cho đẹp
            for col_num, col_name in enumerate(df.columns):
                max_len = max(df[col_name].astype(str).map(len).max(), len(col_name)) + 2
                # Giới hạn độ rộng tối đa là 50 để tránh cột quá dài
                worksheet.set_column(col_num, col_num, min(max_len, 50))
            
            # Lấy vị trí chữ cái của cột 'is_incomplete_scan' (Thường là cột D)
            col_idx = df.columns.get_loc("is_incomplete_scan")
            excel_col_letter = chr(65 + col_idx)
            
            # Hướng B: Cài đặt Conditional Formatting
            # Nếu cột is_incomplete_scan == TRUE, tô màu toàn bộ hàng đó
            max_row = len(df) + 1
            worksheet.conditional_format(f'A2:Z{max_row}', {
                'type': 'formula',
                'criteria': f'=${excel_col_letter}2=TRUE',
                'format': warning_format
            })
            
    logger.info(f"✅ ĐÃ XUẤT THÀNH CÔNG BÁO CÁO EXCEL TẠI: {OUTPUT_EXCEL}")

if __name__ == "__main__":
    export_to_excel()