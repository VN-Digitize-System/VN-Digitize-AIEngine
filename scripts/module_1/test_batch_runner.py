import os
import sys
import time
import json
import cv2
import argparse
from pathlib import Path

# =========================================================================
# 1. THIẾT LẬP ĐƯỜNG DẪN DỰ ÁN BẰNG PATHLIB
# =========================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from module_1_image_preprocessing.preprocessor import ImagePreprocessor

def run_module_1_benchmark(input_folder: str, output_folder: str):
    print(f"\n🚀 [M1-BENCHMARK] Bắt đầu khởi chạy luồng Tiền xử lý (Module 1)...")
    
    out_path = Path(output_folder)
    out_path.mkdir(parents=True, exist_ok=True)
    
    config_path = PROJECT_ROOT / "configs" / "module1_defaults.yaml"
    processor = ImagePreprocessor.from_yaml(config_path)

    supported_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_paths = [Path(input_folder) / f for f in os.listdir(input_folder) 
                   if Path(f).suffix.lower() in supported_exts]

    if not image_paths:
        print(f"⚠️ Không tìm thấy ảnh nào trong thư mục: {input_folder}")
        return

    summary_data = {}
    success_count = 0
    
    print(f"📂 Tìm thấy {len(image_paths)} ảnh. Bắt đầu đo lường hiệu năng...\n")
    t_batch_start = time.perf_counter()

    for i, img_path in enumerate(image_paths, 1):
        filename = img_path.name
        print(f"[{i:03d}/{len(image_paths):03d}] Đang xử lý: {filename}...", end=" ", flush=True)
        
        t_img_start = time.perf_counter()
        result = processor.process(str(img_path))
        t_img_end = time.perf_counter()
        
        elapsed_img = t_img_end - t_img_start

        if result.error_code is None:
            save_path = out_path / filename
            cv2.imwrite(str(save_path), result.processed_image)
            
            summary_data[filename] = {
                "is_blank": result.is_blank,
                "orientation_status": result.orientation_status.value,
                "skew_angle": round(result.skew_angle, 2),
                "barcodes": [bc.data for bc in result.barcodes],
                "error_code": None,
                "processing_time_sec": round(elapsed_img, 4)
            }
            print(f"✅ Xong ({elapsed_img:.3f}s)")
            success_count += 1
        else:
            # LỌC BỎ ẢNH LỖI (Option A): Chỉ ghi log, KHÔNG LƯU ẢNH XUỐNG ĐĨA
            summary_data[filename] = {
                "is_blank": False,
                "orientation_status": "LIKELY_CORRECT",
                "skew_angle": 0.0,
                "barcodes": [],
                "error_code": result.error_code,
                "processing_time_sec": round(elapsed_img, 4)
            }
            print(f"❌ Bị lọc bỏ - Lỗi: {result.error_code} ({elapsed_img:.3f}s)")

    t_batch_end = time.perf_counter()
    total_elapsed = t_batch_end - t_batch_start
    avg_time_per_image = total_elapsed / len(image_paths) if image_paths else 0
    fps = 1.0 / avg_time_per_image if avg_time_per_image > 0 else 0

    json_path = out_path / "m1_summary.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)

    print("\n" + "="*50)
    print(" 📊 BÁO CÁO HIỆU NĂNG MODULE 1 (BENCHMARK)")
    print("="*50)
    print(f"Tổng số ảnh đưa vào:   {len(image_paths)}")
    print(f"Xuất sang Module 2:    {success_count} ảnh")
    print(f"Ảnh lỗi bị lọc bỏ:     {len(image_paths) - success_count} ảnh")
    print(f"Tổng thời gian:        {total_elapsed:.2f} giây")
    print(f"Tốc độ trung bình:     {avg_time_per_image:.3f} giây / ảnh")
    print(f"Khung hình/giây (FPS): {fps:.2f} FPS")
    print(f"File Metadata JSON:    {json_path}")
    print("="*50 + "\n")


if __name__ == "__main__":
    DEFAULT_INPUT = str(PROJECT_ROOT / "tests/data/unit_tests/module_1/for_demo_video/module_1_input/scan_images")
    DEFAULT_OUTPUT = str(PROJECT_ROOT / "tests/data/outputs/unit_tests/module_1/for_demo_video/test_result")

    parser = argparse.ArgumentParser(description="Chạy Benchmark Module 1")
    # Sử dụng 'nargs="?"' và 'default=' để hỗ trợ cả 2 cách chạy
    parser.add_argument("--input_dir", type=str, nargs="?", default=DEFAULT_INPUT, help="Thư mục chứa ảnh gốc")
    parser.add_argument("--output_dir", type=str, nargs="?", default=DEFAULT_OUTPUT, help="Thư mục lưu ảnh đã xử lý")
    args = parser.parse_args()

    run_module_1_benchmark(args.input_dir, args.output_dir)