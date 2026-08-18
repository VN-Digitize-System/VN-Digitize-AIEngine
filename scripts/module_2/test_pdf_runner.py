import os
import sys
import time
import json
import cv2
import numpy as np
import fitz  # Thư viện PyMuPDF
import argparse
import dataclasses
from pathlib import Path

# =========================================================================
# 1. THIẾT LẬP ĐƯỜNG DẪN DỰ ÁN
# =========================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from module_2_core_ocr.config import OcrConfig
from module_2_core_ocr.engines.factory import OcrEngineFactory
from module_2_core_ocr.visualizer import draw_ocr_results

class EnhancedJSONEncoder(json.JSONEncoder):
    """Hỗ trợ chuyển đổi Dataclass thành JSON"""
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

def run_pdf_ocr_pipeline(input_pdf_dir: str, output_dir: str):
    in_path = Path(input_pdf_dir)
    out_path = Path(output_dir)
    
    # Khởi tạo thư mục Output
    json_dir = out_path / "jsons"
    img_dir = out_path / "debug_images"
    json_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 [M2-PDF-ADAPTER] Khởi động Động cơ OCR...")
    config_path = PROJECT_ROOT / "configs" / "module2_defaults.yaml"
    config = OcrConfig.from_yaml(config_path)
    
    # Nạp Engine OCR
    engine = OcrEngineFactory.get_engine(config.active_engine, config)

    # Tìm tất cả file PDF trong thư mục
    pdf_files = sorted([f for f in in_path.iterdir() if f.is_file() and f.suffix.lower() == '.pdf'])
    
    if not pdf_files:
        print(f"❌ KHÔNG TÌM THẤY file .pdf nào trong thư mục {in_path}!")
        return

    print(f"📂 Tìm thấy {len(pdf_files)} file PDF. Bắt đầu xử lý...\n")
    t_batch_start = time.perf_counter()
    
    total_pages_processed = 0

    # LẶP QUA TỪNG FILE PDF
    for pdf_file in pdf_files:
        print(f"📄 Đang mở file: {pdf_file.name}")
        doc = fitz.open(str(pdf_file))
        
        # LẶP QUA TỪNG TRANG TRONG FILE PDF
        for page_num in range(len(doc)):
            total_pages_processed += 1
            print(f"   ➔ Đang bóc tách Trang {page_num + 1}/{len(doc)}...", end=" ", flush=True)
            t_page_start = time.perf_counter()

            # --- BƯỚC 1: KẾT XUẤT PDF SANG NUMPY ARRAY (RAM) ---
            page = doc.load_page(page_num)
            
            # Cấu hình Ma trận Phóng to (Zoom = 2.0 theo đúng thiết kế)
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Chuyển đổi dữ liệu thô sang Numpy Array
            img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            
            # Chuyển hệ màu RGB (của PDF) sang BGR (của OpenCV/Paddle)
            if pix.n == 4: # RGBA
                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3: # RGB
                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)

            # --- BƯỚC 2: CHẠY OCR TRỰC TIẾP ---
            ocr_result = engine.process_image(img_np)
            ocr_result.page_number = page_num + 1
            
            t_page_end = time.perf_counter()
            elapsed = t_page_end - t_page_start

            # --- BƯỚC 3: LƯU KẾT QUẢ ---
            base_name = f"{pdf_file.stem}_page_{page_num + 1}"
            
            # Lưu file JSON
            with open(json_dir / f"{base_name}_ocr.json", 'w', encoding='utf-8') as f:
                json.dump(ocr_result, f, cls=EnhancedJSONEncoder, indent=4, ensure_ascii=False)
                
            # Vẽ và lưu ảnh Debug
            draw_ocr_results(img_np, ocr_result, str(img_dir / f"{base_name}_debug.jpg"))

            print(f"✅ Xong ({elapsed:.2f}s)")
            
        doc.close()

    # BÁO CÁO TỔNG KẾT
    t_batch_end = time.perf_counter()
    total_elapsed = t_batch_end - t_batch_start
    avg_time = total_elapsed / total_pages_processed if total_pages_processed else 0

    print("\n" + "="*50)
    print(" 📊 BÁO CÁO HIỆU NĂNG MODULE 2 (PDF ADAPTER)")
    print("="*50)
    print(f"Tổng số file PDF:      {len(pdf_files)}")
    print(f"Tổng số trang đã xử lý: {total_pages_processed} trang")
    print(f"Tổng thời gian:        {total_elapsed:.2f} giây")
    print(f"Tốc độ trung bình:     {avg_time:.2f} giây / trang")
    print("="*50 + "\n")

if __name__ == "__main__":
    # KHAI BÁO THƯ MỤC INPUT/OUTPUT MẶC ĐỊNH
    DEFAULT_INPUT = str(PROJECT_ROOT / "tests/data/unit_tests/module_2/test_11_pdf")
    DEFAULT_OUTPUT = str(PROJECT_ROOT / "tests/data/outputs/unit_tests/module_2/module_2_pdf_test_11_after")

    parser = argparse.ArgumentParser(description="Chạy OCR trực tiếp trên thư mục PDF")
    parser.add_argument("--input_dir", type=str, nargs="?", default=DEFAULT_INPUT, help="Thư mục chứa các file .pdf")
    parser.add_argument("--output_dir", type=str, nargs="?", default=DEFAULT_OUTPUT, help="Thư mục lưu kết quả OCR")
    args = parser.parse_args()

    run_pdf_ocr_pipeline(args.input_dir, args.output_dir)