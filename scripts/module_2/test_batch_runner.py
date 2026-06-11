import os
import sys
import json
import cv2
import dataclasses
from pathlib import Path

# 1. Định vị thư mục gốc để import không bị lỗi
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from module_2_core_ocr.ocr_pipeline import OcrPipeline
from module_2_core_ocr.config import OcrConfig
from module_2_core_ocr.visualizer import draw_ocr_results

class EnhancedJSONEncoder(json.JSONEncoder):
    """Hỗ trợ chuyển đổi Dataclass thành JSON"""
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

def run_batch_test(input_dir: str, output_dir: str):
    in_path = Path(input_dir)
    out_path = Path(output_dir)

    # 2. CẤU TRÚC THƯ MỤC CON (OPTION B)
    json_dir = out_path / "jsons"
    img_dir = out_path / "debug_images"
    json_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 [M2-TEST] Khởi động Nhạc trưởng OCR Pipeline...")
    
    # Nạp cấu hình từ bảng điều khiển YAML
    config_path = PROJECT_ROOT / "configs" / "module2_defaults.yaml"
    config = OcrConfig.from_yaml(config_path)

    pipeline = OcrPipeline(active_engine_name=config.active_engine, config=config)

    print(f"📂 [M2-TEST] Đang quét thư mục: {in_path}")
    batch_results = pipeline.process_folder(in_path)

    print(f"\n💾 [M2-TEST] Đang lưu kết quả vào các thư mục phân loại...")
    
    success_count = 0
    for filename, data in batch_results.items():
        ocr_result = data["result"]
        rotated_image = data["rotated_image"]
        base_name = os.path.splitext(filename)[0]

        if not ocr_result.is_success:
            print(f"❌ Lỗi xử lý ảnh {filename}: {ocr_result.error_message}")
            continue

        # 3a. Lưu file JSON chuẩn mực
        json_file = json_dir / f"{base_name}_ocr.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(ocr_result, f, cls=EnhancedJSONEncoder, indent=4, ensure_ascii=False)

        # 3b. Vẽ ảnh Debug có Bounding Box
        img_file = img_dir / f"{base_name}_debug.jpg"
        draw_ocr_results(image=rotated_image, ocr_result=ocr_result, save_path=str(img_file))
        
        success_count += 1

    print(f"✅ HOÀN TẤT! Đã xử lý thành công {success_count}/{len(batch_results)} ảnh.")
    print(f"   - JSON lưu tại: {json_dir}")
    print(f"   - Ảnh debug lưu tại: {img_dir}")

if __name__ == "__main__":
    # Thay đổi đường dẫn này theo thư mục test thực tế của bạn
    # INPUT phải là thư mục đã được Module 1 xử lý và có chứa file m1_summary.json
    TEST_INPUT = PROJECT_ROOT / "tests" / "data" / "outputs" / "unit_tests" / "module_1" / "code_c_final_outputs_rembg"
    TEST_OUTPUT = PROJECT_ROOT / "tests" / "data" / "outputs" / "unit_tests" / "module_2" / "test_batch_module_2"
    
    run_batch_test(str(TEST_INPUT), str(TEST_OUTPUT))