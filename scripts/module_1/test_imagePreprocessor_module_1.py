import cv2
import os
import sys
import numpy as np
import argparse
from pathlib import Path

# =========================================================================
# 1. THIẾT LẬP ĐƯỜNG DẪN DỰ ÁN BẰNG PATHLIB (Đồng bộ toàn hệ thống)
# =========================================================================
# Trèo ngược 2 cấp: scripts/module_1/ -> scripts/ -> VN-Digitize-AIEngine/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from module_1_image_preprocessing.preprocessor import ImagePreprocessor

def export_final_results(input_folder, output_folder):
    print(f"--- BẮT ĐẦU XUẤT KẾT QUẢ CODE C (PIPELINE HOÀN CHỈNH) ---")
    
    # Tạo thư mục output nếu chưa có
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Đã tạo thư mục: {output_folder}")

    # Load cấu hình từ file YAML sử dụng đường dẫn tuyệt đối Project Root
    config_path = PROJECT_ROOT / "configs" / "module1_defaults.yaml"
    processor = ImagePreprocessor.from_yaml(config_path)

    # Lấy danh sách ảnh
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    image_paths = [os.path.join(input_folder, f) for f in os.listdir(input_folder) 
                   if f.lower().endswith(image_extensions)]

    for img_path in image_paths:
        filename = os.path.basename(img_path)
        print(f"Đang xử lý: {filename}...", end=" ")

        original_img = cv2.imread(img_path)
        if original_img is None:
            print("Lỗi: Không thể đọc ảnh.")
            continue

        # Chạy qua luồng Code C (Cắt góc + Enhance)
        result = processor.process(original_img)

        if result.error_code is None:
            # Lưu ảnh đã được xử lý (đã crop, deskew và enhance)
            output_path = os.path.join(output_folder, f"processed_{filename}")
            cv2.imwrite(output_path, result.processed_image)
            print(f"✅ Đã lưu.")
        else:
            print(f"❌ Thất bại (Mã lỗi: {result.error_code})")

    print(f"\n--- HOÀN THÀNH! Ảnh kết quả nằm tại: {output_folder} ---")

if __name__ == "__main__":
    # =========================================================================
    # 2. NÂNG CẤP CHUẨN CLI KẾT HỢP GIÁ TRỊ MẶC ĐỊNH
    # =========================================================================
    parser = argparse.ArgumentParser(description="Script xuất kết quả Pipeline hoàn chỉnh")
    
    # Giữ nguyên đường dẫn cũ của bạn làm Default để dễ dàng test nhanh
    default_input = "F:/VN-Digitize-AIEngine/tests/data/unit_tests/module_1/for_demo_video/module_1_image"
    default_output = "F:/VN-Digitize-AIEngine/tests/data/outputs/unit_tests/module_1/for_demo_video/module_1_outputs_rembg"
    
    parser.add_argument("--input_dir", type=str, default=default_input, help="Đường dẫn thư mục chứa ảnh gốc")
    parser.add_argument("--output_dir", type=str, default=default_output, help="Đường dẫn thư mục xuất ảnh")
    
    args = parser.parse_args()
    
    export_final_results(args.input_dir, args.output_dir)