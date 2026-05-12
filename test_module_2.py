import cv2
import os
from module_1_image_preprocessing.preprocessor import ImagePreprocessor
from module_2_core_ocr.ocr_pipeline import OcrEngine
from module_2_core_ocr.visualizer import draw_ocr_results

def test_pipeline_integration(image_path: str):
    print(f"\n{'='*50}")
    print(f"BẮT ĐẦU TEST TÍCH HỢP M1 -> M2 VỚI ẢNH: {image_path}")
    print(f"{'='*50}")

    # Khởi tạo 2 cỗ máy
    print("Khởi tạo cấu hình Module 1 từ YAML...")
    config_path = "configs/module1_defaults.yaml" 
    preprocessor = ImagePreprocessor.from_yaml(config_path)
    
    ocr_engine = OcrEngine()

    # CHẠY MODULE 1
    print("\n[MODULE 1] Đang tiền xử lý...")
    m1_result = preprocessor.process(image_path)
    
    if m1_result.processed_image is None:
        print("❌ Lỗi: Module 1 từ chối xử lý (Có thể do lỗi Crop). Dừng pipeline.")
        return

    # CHẠY MODULE 2 (Nhận output của M1 làm input)
    print("\n[MODULE 2] Đang đọc chữ bằng PaddleOCR...")
    m2_result = ocr_engine.process(m1_result)

    # IN KẾT QUẢ
    if m2_result.is_success:
        print("\n✅ THÀNH CÔNG! TRÍCH XUẤT ĐƯỢC CÁC TRƯỜNG DỮ LIỆU:")
        print("-" * 40)
        for i, word in enumerate(m2_result.words[:5]):
            bbox_str = f"[{word.bbox.points[0]}, ..., {word.bbox.points[2]}]"
            conf_display = f"{word.confidence:.2f}"
            if word.confidence < 0.90:
                conf_display = f"⚠️ {conf_display}"
                
            print(f"Từ #{i+1}: '{word.text}' | Score: {conf_display} | BBox: {bbox_str}")
        print("...")
        print("-" * 40)
        
        # ==========================================
        # GỌI HÀM VẼ BOUNDING BOX VÀ LƯU ẢNH
        # ==========================================
        save_path = "tests/module_2/ocr_result/debug_ocr_output_8.png"
        draw_ocr_results(m1_result.processed_image, m2_result, save_path)
        
    else:
        print(f"❌ LỖI MODULE 2: {m2_result.error_message}")

if __name__ == "__main__":
    # Thay bằng 1 tấm hình bất kỳ có chữ (hóa đơn, sách, CCCD)
    test_pipeline_integration("f:/VN-Digitize-AIEngine/tests/module_2/Image_1/7.png")