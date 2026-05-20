import os
from module_1_image_preprocessing.preprocessor import ImagePreprocessor
from module_2_core_ocr.ocr_pipeline import OcrEngine
from module_2_core_ocr.config import OcrConfig
from module_2_core_ocr.visualizer import draw_ocr_results

def run_batch_test(input_folder: str, output_folder: str):
    # Khởi tạo Config (Đã bật công tắc Bypass cho ảnh Scan)
    config = OcrConfig() 
    
    preprocessor = ImagePreprocessor.from_yaml("configs/module1_defaults.yaml")
    ocr_engine = OcrEngine(config=config)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(input_folder, filename)
            print(f"\n🚀 Đang xử lý: {filename}")

            # Chạy toàn bộ Pipeline
            m2_result, processed_img = ocr_engine.process(preprocessor, img_path)

            # 1. Xuất ảnh vẽ Bounding Box
            save_img_path = os.path.join(output_folder, f"debug_{filename}")
            draw_ocr_results(processed_img, m2_result, save_img_path)

            # ==========================================
            # 2. XUẤT FILE TEXT ĐỂ KIỂM TRA NỘI DUNG ĐỌC ĐƯỢC
            # ==========================================
            if m2_result.is_success:
                # Lấy tên file gốc bỏ đuôi (VD: '1.jpg' -> '1') và thêm '_text.txt'
                base_name = os.path.splitext(filename)[0]
                txt_filename = f"{base_name}_text.txt"
                save_txt_path = os.path.join(output_folder, txt_filename)
                
                # Mở file ghi với encoding utf-8 để không lỗi font tiếng Việt
                with open(save_txt_path, "w", encoding="utf-8") as f:
                    f.write(f"--- KẾT QUẢ OCR CHO ẢNH: {filename} ---\n\n")
                    
                    f.write("1. TOÀN BỘ VĂN BẢN (FULL TEXT):\n")
                    f.write("-" * 50 + "\n")
                    f.write(m2_result.full_text + "\n\n")
                    
                    f.write("-" * 50 + "\n")
                    f.write("2. CHI TIẾT TỪNG DÒNG (KÈM ĐIỂM TIN CẬY):\n")
                    f.write("-" * 50 + "\n")
                    for i, word in enumerate(m2_result.words):
                        # Ghi số thứ tự, điểm tin cậy và nội dung text
                        f.write(f"#{i+1} [Score: {word.confidence:.2f}]: {word.text}\n")
                        
                print(f"📄 Đã xuất nội dung chữ tại: {save_txt_path}")
            else:
                print(f"❌ Lỗi OCR với ảnh {filename}: {m2_result.error_message}")

if __name__ == "__main__":
    folder_anh_scan = "tests/module_2/Image_Camera_Folder"
    folder_ket_qua = "tests/module_2/Output_Batch_Not_Scan_2"
    run_batch_test(folder_anh_scan, folder_ket_qua)