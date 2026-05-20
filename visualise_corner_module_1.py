import cv2
import matplotlib.pyplot as plt
import os
import sys
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module_1_image_preprocessing.preprocessor import ImagePreprocessor

def batch_compare_with_corners(input_folder, output_folder):
    print(f"--- BẮT ĐẦU CHẠY BATCH A/B TESTING (CÓ VẼ GÓC) ---")
    os.makedirs(output_folder, exist_ok=True)
    
    config_path = "configs/module1_defaults.yaml"
    processor_B = ImagePreprocessor.from_yaml(config_path)

    image_paths = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    for idx, img_path in enumerate(image_paths):
        filename = os.path.basename(img_path)
        print(f"Đang xử lý: {filename}")

        original_img = cv2.imread(img_path)
        original_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)

      

        # --- CHẠY CODE B ---
        # Truyền ma trận ảnh numpy vào thay vì đường dẫn string. 
        # Dùng .copy() để đảm bảo Code B không làm biến đổi ảnh gốc đang dùng để hiển thị.
        result_B = processor_B.process(original_img.copy())
        # Tùy thuộc vào cách bạn gán debug_img_B ở Bước 2, hãy gọi nó ra ở đây.
        # Giả sử bạn đã nhét nó vào thuộc tính debug_image của PreprocessResult:
        debug_B_img = getattr(result_B, 'debug_image', None) 
        
        result_B_crop_img = result_B.processed_image if result_B.error_code is None else np.zeros_like(original_img)
        result_B_crop_rgb = cv2.cvtColor(result_B_crop_img, cv2.COLOR_BGR2RGB) if len(result_B_crop_img.shape) == 3 else cv2.cvtColor(result_B_crop_img, cv2.COLOR_GRAY2RGB)
        debug_B_rgb = cv2.cvtColor(debug_B_img, cv2.COLOR_BGR2RGB) if debug_B_img is not None else original_rgb.copy()

        # --- HIỂN THỊ LƯỚI 2x2 ---
        plt.figure(figsize=(16, 12))


        plt.subplot(2, 2, 2)
        plt.title("Góc detect bởi Code C")
        plt.imshow(debug_B_rgb)
        plt.axis("off")

   
        plt.subplot(2, 2, 4)
        plt.title("Kết quả Crop - Code C")
        plt.imshow(result_B_crop_rgb)
        plt.axis("off")

        plt.tight_layout()
        
        output_path = os.path.join(output_folder, f"corner_compare_{filename}")
        plt.savefig(output_path, dpi=150, bbox_inches='tight') 
        plt.close() 

    print("\n--- HOÀN THÀNH ---")

# Chạy Test
INPUT_DIR = "tests/module_1/detect_images"
OUTPUT_DIR = "tests/module_1/corner_less_30_rembg"
batch_compare_with_corners(INPUT_DIR, OUTPUT_DIR)