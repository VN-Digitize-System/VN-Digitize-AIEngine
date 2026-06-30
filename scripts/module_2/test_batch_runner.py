import os
import sys
import time
import json
import cv2
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
from module_2_core_ocr.utils import auto_rotate_page

class EnhancedJSONEncoder(json.JSONEncoder):
    """Hỗ trợ chuyển đổi Dataclass thành JSON"""
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

def run_module_2_benchmark(input_dir: str, output_dir: str):
    in_path = Path(input_dir)
    out_path = Path(output_dir)
    
    # Đọc file tổng hợp từ Module 1
    m1_summary_file = in_path / "m1_summary.json"
    if not m1_summary_file.exists():
        print(f"❌ KHÔNG TÌM THẤY file {m1_summary_file}!")
        print("Vui lòng đảm bảo thư mục Input là Output của Module 1.")
        return

    with open(m1_summary_file, 'r', encoding='utf-8') as f:
        m1_data = json.load(f)

    # Khởi tạo thư mục Output (Option B: Categorized Subfolders)
    json_dir = out_path / "jsons"
    img_dir = out_path / "debug_images"
    json_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 [M2-BENCHMARK] Khởi động Động cơ OCR...")
    config_path = PROJECT_ROOT / "configs" / "module2_defaults.yaml"
    config = OcrConfig.from_yaml(config_path)
    
    # Nạp Engine
    engine = OcrEngineFactory.get_engine(config.active_engine, config)

    perf_summary = {}
    success_count = 0
    skip_count = 0
    
    # LẤY DANH SÁCH FILE VÀ SẮP XẾP THEO ALPHABET TRƯỚC KHI LẶP
    sorted_filenames = sorted(m1_data.keys())
    
    print(f"📂 Bắt đầu xử lý {len(sorted_filenames)} ảnh từ Module 1...\n")
    t_batch_start = time.perf_counter()

    # SỬ DỤNG VÒNG LẶP VỚI page_num
    for page_num, filename in enumerate(sorted_filenames, 1):
        meta = m1_data[filename] # Lấy metadata dựa trên tên file đã sort
        img_path = in_path / filename
        
        # In thêm thông tin Trang số mấy ra Terminal để dễ theo dõi
        print(f"[{page_num:03d}/{len(sorted_filenames):03d}] Đang đọc: {filename} (Trang {page_num})...", end=" ", flush=True)

        if not img_path.exists() or meta.get("error_code") is not None:
            print("⏭️ Bỏ qua (Ảnh lỗi từ M1)")
            continue

        # 1. Đọc ảnh
        image = cv2.imread(str(img_path))
        if image is None:
            print("❌ Lỗi đọc file")
            continue

        # --- BẮT ĐẦU BẤM GIỜ OCR ---
        t_img_start = time.perf_counter()
        
        # 2. Xoay ảnh nếu Module 1 báo UNCERTAIN hoặc LIKELY_ROTATED
        orientation_status = meta.get("orientation_status", "LIKELY_CORRECT")
        rotated_image = image
        if orientation_status != "LIKELY_CORRECT":
            # Sử dụng classifier ngầm của Paddle để check lật ngược
            rotated_image = auto_rotate_page(image, classifier=engine.classifier)

        # 3. Chạy OCR
        ocr_result = engine.process_image(rotated_image)
        
        # GÁN SỐ TRANG VÀO KẾT QUẢ OCR
        ocr_result.page_number = page_num
        
        t_img_end = time.perf_counter()
        elapsed_img = t_img_end - t_img_start
        # --- KẾT THÚC BẤM GIỜ OCR ---

        # 4. LỌC ẢNH RỖNG (Option A: Strict Skip)
        if not ocr_result.is_success or not ocr_result.full_text.strip():
            print(f"⚠️ Rỗng/Không có chữ ({elapsed_img:.2f}s) -> Lọc bỏ")
            perf_summary[filename] = {"status": "SKIPPED_EMPTY", "time_sec": round(elapsed_img, 4)}
            skip_count += 1
            continue

        # 5. LƯU KẾT QUẢ
        base_name = os.path.splitext(filename)[0]
        
        # Lưu JSON
        with open(json_dir / f"{base_name}_ocr.json", 'w', encoding='utf-8') as f:
            json.dump(ocr_result, f, cls=EnhancedJSONEncoder, indent=4, ensure_ascii=False)
            
        # Vẽ ảnh Debug
        draw_ocr_results(rotated_image, ocr_result, str(img_dir / f"{base_name}_debug.jpg"))

        perf_summary[filename] = {"status": "SUCCESS", "time_sec": round(elapsed_img, 4)}
        print(f"✅ Xong ({elapsed_img:.2f}s)")
        success_count += 1

    # TỔNG HỢP HIỆU NĂNG
    t_batch_end = time.perf_counter()
    total_elapsed = t_batch_end - t_batch_start
    avg_time = total_elapsed / len(sorted_filenames) if sorted_filenames else 0

    # Lưu file Báo cáo hiệu năng M2
    with open(out_path / "m2_performance_summary.json", 'w', encoding='utf-8') as f:
        json.dump({
            "total_images_processed": len(sorted_filenames),
            "successful_ocr": success_count,
            "skipped_empty": skip_count,
            "total_time_sec": round(total_elapsed, 4),
            "avg_time_per_image_sec": round(avg_time, 4),
            "details": perf_summary
        }, f, indent=4)

    print("\n" + "="*50)
    print(" 📊 BÁO CÁO HIỆU NĂNG MODULE 2 (OCR BENCHMARK)")
    print("="*50)
    print(f"Tổng số ảnh nạp vào:   {len(sorted_filenames)}")
    print(f"Đọc thành công:        {success_count} ảnh")
    print(f"Bị lọc (Rỗng/Lỗi):     {skip_count} ảnh")
    print(f"Tổng thời gian:        {total_elapsed:.2f} giây")
    print(f"Tốc độ trung bình:     {avg_time:.2f} giây / ảnh")
    print(f"Báo cáo hiệu năng:     {out_path / 'm2_performance_summary.json'}")
    print("="*50 + "\n")

if __name__ == "__main__":
    # ĐƯỜNG DẪN MẶC ĐỊNH (Hỗ trợ nút Run VSCode)
    # TRỎ VÀO THƯ MỤC OUTPUT CỦA MODULE 1 MÀ BẠN VỪA CHẠY XONG
    DEFAULT_INPUT = str(PROJECT_ROOT / "tests/data/outputs/unit_tests/module_1/for_demo_video/test_batch_crop_real_2")
    DEFAULT_OUTPUT = str(PROJECT_ROOT / "tests/data/outputs/unit_tests/module_2/test_batch_runner_GPU_crop_real_2")

    parser = argparse.ArgumentParser(description="Chạy Benchmark Module 2")
    parser.add_argument("--input_dir", type=str, nargs="?", default=DEFAULT_INPUT, help="Thư mục chứa ảnh và m1_summary.json")
    parser.add_argument("--output_dir", type=str, nargs="?", default=DEFAULT_OUTPUT, help="Thư mục lưu OCR JSON và Debug")
    args = parser.parse_args()

    run_module_2_benchmark(args.input_dir, args.output_dir)