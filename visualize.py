import os
import cv2
import json
import numpy as np

def draw_boxes(image_path, json_path, output_path):
    print(f"\nĐang xử lý: {os.path.basename(image_path)}")
    img = cv2.imread(image_path)
    
    if img is None:
        print("❌ Lỗi: Không thể đọc được ảnh gốc. Vui lòng kiểm tra lại đường dẫn.")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi khi đọc file OCR: {e}")
        return

    # 🌟 VÁ LỖI 1: Xuyên qua lớp vỏ "result" để lấy danh sách "words"
    result_data = data.get("result", {})
    words = result_data.get("words", [])
    
    if not words:
        print("⚠️ Cảnh báo: Không tìm thấy tọa độ chữ (words) trong file dữ liệu!")
        return

    # 🌟 VÁ LỖI 2: Tự động scale độ dày nét vẽ theo kích thước ảnh
    h, w = img.shape[:2]
    # Ví dụ: Ảnh 4000px / 500 = Nét vẽ 8px. Đảm bảo nét luôn đậm, rõ ràng.
    thickness = max(2, int(max(h, w) / 500)) 

    # Lặp qua từng khối dữ liệu
    count = 0
    for word in words:
        bbox_dict = word.get("bbox", {})
        pts_list = bbox_dict.get("points", [])
        block_type = word.get("block_type", "text").lower()
        
        if len(pts_list) == 4:
            pts = np.array(pts_list, np.int32)
            pts = pts.reshape((-1, 1, 2))
            
            if block_type == 'table':
                color = (0, 0, 255)      # Đỏ (BGR)
            elif block_type == 'title':
                color = (255, 0, 0)      # Xanh dương
            else:
                color = (0, 255, 0)      # Xanh lá
                
            cv2.polylines(img, [pts], isClosed=True, color=color, thickness=thickness)
            count += 1

    cv2.imwrite(output_path, img)
    print(f"✅ Đã vẽ thành công {count} khung chữ nhật và lưu tại: {output_path}")

def process_folder(img_folder, ocr_folder, output_folder):
    """
    Hàm duyệt qua tất cả ảnh trong thư mục và tìm file OCR tương ứng để vẽ
    """
    # 1. Đảm bảo thư mục đầu ra (output) đã tồn tại, nếu chưa có thì tạo mới
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    # 2. Các định dạng ảnh hỗ trợ
    valid_img_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    
    # 3. Lấy danh sách tất cả các file trong thư mục ảnh
    for filename in os.listdir(img_folder):
        if filename.lower().endswith(valid_img_extensions):
            img_path = os.path.join(img_folder, filename)
            
            # Trích xuất tên gốc của ảnh (VD: 'IMG_4634' từ 'IMG_4634.JPG')
            base_name = os.path.splitext(filename)[0]
            
            # Lên danh sách các kiểu tên file OCR có thể xảy ra để quét
            # Vì bạn nhắc đến file .ocr nhưng code cũ dùng .json, script sẽ tự động thử các trường hợp
            possible_ocr_names = [
                f"{base_name}_ocr.json",  # Ví dụ: IMG_4634_ocr.json
                f"{base_name}.json",      # Ví dụ: IMG_4634.json
                f"{base_name}.ocr"        # Ví dụ: IMG_4634.ocr
            ]
            
            ocr_path = None
            for ocr_name in possible_ocr_names:
                temp_path = os.path.join(ocr_folder, ocr_name)
                if os.path.exists(temp_path):
                    ocr_path = temp_path
                    break # Tìm thấy thì dừng lại
            
            # Nếu tìm thấy file OCR tương ứng, tiến hành vẽ
            if ocr_path:
                output_path = os.path.join(output_folder, f"{base_name}_visual.jpg")
                draw_boxes(img_path, ocr_path, output_path)
            else:
                print(f"⏭️ Bỏ qua {filename}: Không tìm thấy file dữ liệu OCR tương ứng.")

if __name__ == "__main__":
    # Cấu hình các thư mục chứa dữ liệu
    # Lưu ý: Bạn có thể thay đổi đường dẫn này theo cấu trúc thư mục thực tế của bạn
    INPUT_IMG_DIR = r"test_input"        # Thư mục chứa các file ảnh gốc
    INPUT_OCR_DIR = r"test_output"       # Thư mục chứa các file .ocr hoặc .json
    OUTPUT_VISUAL_DIR = r"test_visual"   # Thư mục lưu kết quả sau khi vẽ
    
    print("🚀 BẮT ĐẦU QUÁ TRÌNH XỬ LÝ HÀNG LOẠT...")
    process_folder(INPUT_IMG_DIR, INPUT_OCR_DIR, OUTPUT_VISUAL_DIR)
    print("\n🎉 HOÀN TẤT!")