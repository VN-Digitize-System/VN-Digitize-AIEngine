import argparse
import sys
import os
import json
from ocr_pipeline import OcrEngine

def main():
    parser = argparse.ArgumentParser(description="Màng bọc CLI cho Module 2 (Core OCR)")
    # Các tham số này phải khớp y chang lúc Nhạc trưởng gọi m2_cmd
    parser.add_argument("--input_dir", required=True, help="Thư mục chứa ảnh đã tiền xử lý")
    parser.add_argument("--output_json", required=True, help="Đường dẫn file JSON lưu kết quả OCR")
    args = parser.parse_args()
    
    print(f"[M2-CLI] Đang tải mô hình OCR và quét thư mục: {args.input_dir}")
    
    # === VIẾT LOGIC GỌI HÀM CỦA BẠN Ở ĐÂY ===
    ocr_engine = OcrEngine()
    ocr_result_data = ocr_engine.process_folder(args.input_dir)
    
    # Mock data tạm thời để test luồng
    ocr_result_data = [
        {"page_number": 1, "lines": [{"text": "Cộng hòa xã hội chủ nghĩa Việt Nam", "box": [0,0,100,20]}]}
    ]
    # ========================================

    # Lưu file kết quả để Module 3 đọc
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(ocr_result_data, f, ensure_ascii=False, indent=2)
        
    print(f"[M2-CLI] Đã lưu kết quả OCR tại: {args.output_json}")

if __name__ == "__main__":
    main()