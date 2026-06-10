import cv2
import matplotlib.pyplot as plt
import os
import sys
import numpy as np
from pathlib import Path

# =========================================================================
# 1. THIẾT LẬP ĐƯỜNG DẪN DỰ ÁN BẰNG PATHLIB
# =========================================================================
# Trèo ngược 2 cấp thư mục: scripts/module_1/ -> scripts/ -> VN-Digitize-AIEngine/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from module_1_image_preprocessing.preprocessor import ImagePreprocessor

def batch_compare_with_corners(input_folder, output_folder):
    print(f"--- BẮT ĐẦU CHẠY BATCH A/B TESTING (CÓ VẼ GÓC) ---")
    os.makedirs(output_folder, exist_ok=True)
    
    # Sử dụng PROJECT_ROOT để trỏ đường dẫn tuyệt đối đến file YAML
    config_path = PROJECT_ROOT / "configs" / "module1_defaults.yaml"
    processor_B = ImagePreprocessor.from_yaml(config_path)

    image_paths = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    for idx, img_path in enumerate(image_paths):
        filename = os.path.basename(img_path)
        print(f"Đang xử lý: {filename}")

        original_img = cv2.imread(img_path)
        original_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)

        # --- CHẠY CODE B ---
        result_B = processor_B.process(original_img.copy())
        debug_B_img = getattr(result_B, 'debug_image', None) 
        
        result_B_crop_img = result_B.processed_image if result_B.error_code is None else np.zeros_like(original_img)
        result_B_crop_rgb = cv2.cvtColor(result_B_crop_img, cv2.COLOR_BGR2RGB) if len(result_B_crop_img.shape) == 3 else cv2.cvtColor(result_B_crop_img, cv2.COLOR_GRAY2RGB)
        debug_B_rgb = cv2.cvtColor(debug_B_img, cv2.COLOR_BGR2RGB) if debug_B_img is not None else original_rgb.copy()

        # --- HIỂN THỊ LƯỚI 2x2 ---
        plt.figure(figsize=(16, 12))

        plt.subplot(2, 2, 2)
        # SỬA DÒNG NÀY: Lấy skew_angle từ result_B và chèn vào tiêu đề
        plt.title(f"Góc detect bởi Code C (Góc nghiêng: {result_B.skew_angle:+.2f}°)", fontsize=14, fontweight='bold')
        plt.imshow(debug_B_rgb)
        plt.axis("off")

        plt.subplot(2, 2, 4)
        plt.title("Kết quả Crop - Code C", fontsize=14, fontweight='bold')
        plt.imshow(result_B_crop_rgb)
        plt.axis("off")

        plt.tight_layout()
        
        output_path = os.path.join(output_folder, f"corner_crop_visualise_{filename}")
        plt.savefig(output_path, dpi=150, bbox_inches='tight') 
        plt.close() 

    print("\n--- HOÀN THÀNH ---")

# Chạy Test
INPUT_DIR = "F:/VN-Digitize-AIEngine/tests/data/unit_tests/module_1/for_demo_video/module_1_rotate_crop_demo"
OUTPUT_DIR = "F:/VN-Digitize-AIEngine/tests/data/outputs/unit_tests/module_1/for_demo_video/module_1_corner_crop_visualise_less_30_rembg"
batch_compare_with_corners(INPUT_DIR, OUTPUT_DIR)