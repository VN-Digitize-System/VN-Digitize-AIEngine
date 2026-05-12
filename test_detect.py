import cv2
import os
import sys

# Đảm bảo import được module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module_1_image_preprocessing.preprocessor import ImagePreprocessor

# def test_detection_features(input_folder):
#     print("=== BẮT ĐẦU TEST CHỨC NĂNG NHẬN DIỆN (MODULE 1.2) ===")
    
#     # Load cấu hình chuẩn của team
#     config_path = "configs/module1_defaults.yaml"
#     processor = ImagePreprocessor.from_yaml(config_path)

#     image_paths = [os.path.join(input_folder, f) for f in os.listdir(input_folder) 
#                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

#     for img_path in image_paths:
#         filename = os.path.basename(img_path)
#         print(f"\n📄 Đang phân tích: {filename}")
#         print("-" * 40)

#         image = cv2.imread(img_path)
#         if image is None:
#             print("Lỗi đọc ảnh!")
#             continue

#         # Chạy ảnh qua toàn bộ Pipeline (nó sẽ tự động gọi _detect.py)
#         result = processor.process(image)
        
#        # Trích xuất các cờ (flags) và cảnh báo từ kết quả trả về
#         is_blank = getattr(result, 'is_blank', False)
#         is_wrong_orientation = getattr(result, 'is_wrong_orientation', False) # Lưu ý tên biến
#         barcodes = getattr(result, 'barcodes', [])
#         warnings_list = getattr(result, 'warnings', [])

#         # --- XỬ LÝ LOGIC UNKNOWN NẾU CROP THẤT BẠI ---
#         crop_failed = "CROP_FAILED_PLEASE_RETAKE" in warnings_list
        
#         if crop_failed:
#             # Nếu Crop hỏng, các kết quả hình học đều là Ẩn số
#             blank_status = "⚠️ Unknown (Lỗi Crop)"
#             orient_status = "⚠️ Unknown (Lỗi Crop)"
#         else:
#             # Nếu Crop thành công, in kết quả bình thường
#             blank_status = "❌ CÓ" if is_blank else "✅ Không"
#             orient_status = "❌ CÓ" if is_wrong_orientation else "✅ Không"

#         # --- IN KẾT QUẢ TRỰC QUAN ---
#         print(f" ⚪ Trang trắng: \t{blank_status}")
#         print(f" 🔄 Sai chiều: \t{orient_status}")
        
#         if barcodes:
#             print(f" 🏷️  Mã vạch (Tìm thấy {len(barcodes)}):")
#             for bc in barcodes:
#                 print(f"    - [{bc.barcode_type}] Nội dung: {bc.data}")
#         else:
#             print(f" 🏷️  Mã vạch: \t\t✅ Không tìm thấy")
            
#         # Vẫn giữ lại dòng cảnh báo đỏ chóe cuối cùng để người dùng chú ý
#         if crop_failed:
#             print(f" ⚠️ CẢNH BÁO: \t\t❌ Xin hãy chụp lại hình do không thể nhận diện được góc tài liệu!")

def test_detection_features(input_folder):
    print("=== BẮT ĐẦU TEST CHỨC NĂNG NHẬN DIỆN (MODULE 1.2) ===")
    
    # Load cấu hình chuẩn của team
    config_path = "configs/module1_defaults.yaml"
    processor = ImagePreprocessor.from_yaml(config_path)

    image_paths = [os.path.join(input_folder, f) for f in os.listdir(input_folder) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    for img_path in image_paths:
        filename = os.path.basename(img_path)
        print(f"\n📄 Đang phân tích: {filename}")
        print("-" * 40)

        image = cv2.imread(img_path)
        if image is None:
            print("Lỗi đọc ảnh!")
            continue

        # Chạy ảnh qua toàn bộ Pipeline (nó sẽ tự động gọi _detect.py)
        result = processor.process(image)
        
        # Trích xuất các cờ (flags) và cảnh báo từ kết quả trả về
        is_blank = getattr(result, 'is_blank', False)
        skew_angle = getattr(result, 'skew_angle', 0.0) # Lấy góc nghiêng (đã có sẵn trong kết quả)
        barcodes = getattr(result, 'barcodes', [])
        warnings_list = getattr(result, 'warnings', [])

        # --- XỬ LÝ LOGIC UNKNOWN NẾU CROP THẤT BẠI ---
        crop_failed = "CROP_FAILED_PLEASE_RETAKE" in warnings_list
        
        if crop_failed:
            blank_status = "⚠️ Unknown (Lỗi Crop)"
            orient_status = "⚠️ Unknown (Lỗi Crop)"
        elif is_blank:
            blank_status = "❌ CÓ"
            orient_status = "⚠️ Trang trắng không có nội dung"
        else:
            blank_status = "✅ Không"
            
            # --- LOGIC MỚI DO BẠN ĐỀ XUẤT ---
            if abs(skew_angle) > 10.0:
                orient_status = f"⚠️  Nghiêng - Xin chỉnh thẳng lại tài liệu!"
            else:
                orient_status = f"✅ Ổn định"
            # -------------------------------

        # --- IN KẾT QUẢ TRỰC QUAN ---
        print(f" ⚪ Trang trắng: \t{blank_status}")
        print(f" 📐 Chiều tài liệu:\t{orient_status}")
        
        # --- CẬP NHẬT TRẠNG THÁI MÃ VẠCH (Tách khỏi crop_failed) ---
        if barcodes:
            print(f" 🏷️  Mã vạch (Tìm thấy {len(barcodes)}):")
            for bc in barcodes:
                print(f"    - [{bc.barcode_type}] Nội dung: {bc.data}")
        else:
            print(f" 🏷️  Mã vạch: \t\t✅ Không tìm thấy")
            
        if crop_failed:
            print(f" ⚠️ CẢNH BÁO: \t\t❌ Xin hãy chụp lại hình do không thể nhận diện được góc tài liệu!")

if __name__ == "__main__":
    # Trỏ vào thư mục chứa tấm hình mồi nhử của bạn
    INPUT_DIR = "tests/module_1/Barcode_images"
    test_detection_features(INPUT_DIR)