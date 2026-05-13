import cv2
import os
from module_1_image_preprocessing.preprocessor import ImagePreprocessor
from module_2_core_ocr.ocr_pipeline import OcrEngine
from module_2_core_ocr.visualizer import draw_ocr_results

def test_pipeline_integration(image_path: str, skip_crop: bool = False):
    print(f"\n{'='*50}")
    # In ra trạng thái công tắc cho dễ theo dõi
    print(f"BẮT ĐẦU TEST M1 -> M2 (Công tắc skip_crop = {skip_crop})")
    print(f"ẢNH: {image_path}")
    print(f"{'='*50}")

    config_path = "configs/module1_defaults.yaml" 
    preprocessor = ImagePreprocessor.from_yaml(config_path)
    ocr_engine = OcrEngine()

    print("\n[MODULE 1] Đang tiền xử lý...")
    # TRUYỀN CÔNG TẮC VÀO MODULE 1
    m1_result = preprocessor.process(image_path, skip_crop=skip_crop)
    
    if m1_result.processed_image is None:
        print("❌ Lỗi: Module 1 từ chối xử lý. Dừng pipeline.")
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
        save_path = "tests/module_2/ocr_result/debug_ocr_output_4.png"
        draw_ocr_results(m1_result.processed_image, m2_result, save_path)
        
    else:
        print(f"❌ LỖI MODULE 2: {m2_result.error_message}")

    if m2_result.is_success:
        # Cập nhật tên file output để biết file nào đã skip_crop
        status_name = "skipped" if skip_crop else "cropped"
        save_path = f"tests/module_2/ocr_result/debug_ocr_{status_name}.png"
        draw_ocr_results(m1_result.processed_image, m2_result, save_path)

if __name__ == "__main__":
    # KỊCH BẢN 1: Ảnh Digital Scan (như 1.jpg, 1.png) -> Bật công tắc để bỏ qua Crop
    img_scan = "tests/module_2/Image_1/4.png"
    test_pipeline_integration(img_scan, skip_crop=True)

    # KỊCH BẢN 2: Ảnh chụp tay (như 7.jpg) -> Tắt công tắc để nó tìm viền và cắt cỏ, sàn nhà đi
    # img_camera = "tests/module_2/Image_1/7.png"
    # test_pipeline_integration(img_camera, skip_crop=False)