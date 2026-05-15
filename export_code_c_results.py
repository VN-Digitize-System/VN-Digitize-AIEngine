import cv2
import os
import sys
import numpy as np

# Thiết lập đường dẫn hệ thống
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module_1_image_preprocessing.preprocessor import ImagePreprocessor

def export_final_results(input_folder, output_folder):
    print(f"--- BẮT ĐẦU XUẤT KẾT QUẢ CODE C (PIPELINE HOÀN CHỈNH) ---")
    
    # Tạo thư mục output nếu chưa có
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Đã tạo thư mục: {output_folder}")

    # Load cấu hình từ file YAML
    config_path = "configs/module1_defaults.yaml"
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
        # Kết quả trả về là một đối tượng PreprocessResult
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
    # Cấu hình đường dẫn
    INPUT_DIR = "tests/module_1/detect_images" # Folder chứa ảnh gốc của bạn
    OUTPUT_DIR = "tests/module_1/code_c_final_outputs_rembg" # Folder sẽ chứa ảnh đã tẩy trắng
    
    export_final_results(INPUT_DIR, OUTPUT_DIR)