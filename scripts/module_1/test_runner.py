#!/usr/bin/env python3
import argparse
import io
import shutil
import sys
import time
from pathlib import Path

import cv2

# Ép UTF-8 cho Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Trỏ đường dẫn hệ thống về thư mục gốc (VN-Digitize-AIEngine)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from module_1_image_preprocessing import ImagePreprocessor
from module_1_image_preprocessing.visualizer import visualize_result

SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
CONFIG_PATH = PROJECT_ROOT / "configs" / "module1_defaults.yaml"

def clean_output_dir(output_dir: Path) -> None:
    """Xóa sạch thư mục output cũ và tạo lại thư mục trống"""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="Test Runner tổng hợp cho Module 1")
    
    # THIẾT LẬP ĐƯỜNG DẪN MẶC ĐỊNH THEO CẤU TRÚC MỚI CỦA BẠN
    # Mặc định sẽ lấy folder test barcode làm ví dụ, bạn có thể truyền tên folder khác qua Terminal
    default_input = str(PROJECT_ROOT / "tests/data/unit_tests/module_1/module_1_image")
    default_output = str(PROJECT_ROOT / "tests/data/outputs/unit_tests/module_1/module_1_runner_results")
    
    parser.add_argument("--input_dir", type=str, default=default_input)
    parser.add_argument("--output_dir", type=str, default=default_output)
    parser.add_argument("--skip_crop", action="store_true", help="Bỏ qua bước cắt góc AI")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    # 1. DỌN DẸP
    clean_output_dir(output_dir)

    # 2. KHỞI TẠO AI
    processor = ImagePreprocessor.from_yaml(CONFIG_PATH)

    # 3. LOGIC TEST CŨ CỦA BẠN (Đã được ráp vào)
    image_paths = sorted(
        p for p in input_dir.iterdir() if p.suffix.lower() in SUPPORTED
    ) if input_dir.exists() else []

    if not image_paths:
        print(f"[test_runner] Không tìm thấy ảnh trong: {input_dir}")
        return

    col = "{:<24} {:<7} {:<14} {:<9} {:<12} {}"
    sep = "─" * 78
    print(f"\n[test_runner] Đang quét: {input_dir}\n{sep}")
    print(col.format("File", "Blank", "Orientation", "Angle", "Barcodes", "Status"))
    print(sep)

    ok_count = err_count = 0

    for img_path in image_paths:
        t0 = time.perf_counter()
        original = cv2.imread(str(img_path))
        result = processor.process(img_path, skip_crop=args.skip_crop)
        elapsed = time.perf_counter() - t0

        if result.error_code:
            print(col.format(img_path.name, "—", "—", "—", "—", f"✗ {result.error_code}"))
            err_count += 1
            continue

        orientation_str = "WARN_ROTATED" if result.is_wrong_orientation else "OK"
        barcode_str = (
            f"{len(result.barcodes)} ({result.barcodes[0].barcode_type})"
            if result.barcodes else "0"
        )
        print(col.format(
            img_path.name,
            str(result.is_blank),
            orientation_str,
            f"{result.skew_angle:+.1f}°",
            barcode_str,
            f"✓ OK  ({elapsed:.2f}s)",
        ))

        # Lưu ảnh sạch
        cv2.imwrite(str(output_dir / img_path.name), result.processed_image)

        # Lưu ảnh Debug (có khung xanh)
        if original is not None:
            visualize_result(
                original, result,
                save_path=output_dir / f"debug_{img_path.name}",
            )

        ok_count += 1

    print(sep)
    print(f"Đã xử lý: {len(image_paths)} | OK: {ok_count} | Lỗi: {err_count}")
    print(f"Lưu kết quả tại: {output_dir}\n")

if __name__ == "__main__":
    main()