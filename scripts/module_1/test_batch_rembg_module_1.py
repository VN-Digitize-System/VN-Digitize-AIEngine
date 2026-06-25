import os
import cv2
import matplotlib.pyplot as plt
from rembg import remove, new_session
from pathlib import Path

def test_batch_background_removal(input_folder: str, output_folder: str):
    # 1. Tạo thư mục output nếu nó chưa tồn tại
    os.makedirs(output_folder, exist_ok=True)
    
    print("Đang nạp mô hình AI U2-Net (Chỉ nạp 1 lần duy nhất)...")
    session = new_session("u2netp")

    # 2. Lấy danh sách tất cả các file ảnh trong thư mục input
    supported_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    image_paths = [
        p for p in Path(input_folder).iterdir() 
        if p.suffix.lower() in supported_extensions
    ]

    if not image_paths:
        print(f"Không tìm thấy ảnh nào trong thư mục: {input_folder}")
        return

    print(f"Tìm thấy {len(image_paths)} ảnh. Bắt đầu xử lý hàng loạt...\n")

    # 3. Duyệt qua từng ảnh để xử lý
    for i, img_path in enumerate(image_paths, 1):
        filename = img_path.name
        print(f"[{i}/{len(image_paths)}] Đang xử lý: {filename}...")
        
        # Đọc ảnh
        image_bgr = cv2.imread(str(img_path))
        if image_bgr is None:
            print(f"  -> Lỗi: Không thể đọc ảnh {filename}")
            continue
            
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # Thu nhỏ ảnh để test nhanh và AI chạy mượt hơn
        target_height = 500.0
        ratio = image_rgb.shape[0] / target_height
        new_width = int(image_rgb.shape[1] / ratio)
        resized_rgb = cv2.resize(image_rgb, (new_width, int(target_height)))

        # Chạy AI bóc tách (Dùng chung session đã khởi tạo ở trên)
        foreground = remove(resized_rgb, session=session)
        mask = remove(resized_rgb, session=session, only_mask=True)

        # 4. Vẽ bảng đối chiếu bằng Matplotlib
        plt.figure(figsize=(15, 6))

        plt.subplot(1, 3, 1)
        plt.title("1. Ảnh gốc (Original)")
        plt.imshow(resized_rgb)
        plt.axis('off')

        plt.subplot(1, 3, 2)
        plt.title("2. Xóa phông (Foreground)")
        plt.imshow(foreground)
        plt.axis('off')

        plt.subplot(1, 3, 3)
        plt.title("3. Mặt nạ (Mask)")
        plt.imshow(mask, cmap='gray')
        plt.axis('off')

        plt.tight_layout()

        # 5. Lưu ảnh vào thư mục Output thay vì hiển thị lên màn hình
        output_path = os.path.join(output_folder, f"rembg_debug_{filename}")
        plt.savefig(output_path, dpi=150) # dpi=150 để ảnh xuất ra rõ nét
        
        # QUAN TRỌNG: Phải đóng figure lại để giải phóng RAM, nếu không chạy nhiều ảnh sẽ tràn RAM
        plt.close()

    print(f"\n✅ Đã hoàn tất! Các ảnh kết quả được lưu tại: {output_folder}")

if __name__ == "__main__":
    # Bạn hãy đổi đường dẫn này thành thư mục chứa ảnh camera
    INPUT_FOLDER = "F:/VN-Digitize-AIEngine/tests/data/unit_tests/module_1/for_demo_video/module_1_rembg" 
    
    # Thư mục xuất kết quả (code sẽ tự tạo nếu chưa có)
    OUTPUT_FOLDER = "F:/VN-Digitize-AIEngine/tests/data/outputs/unit_tests/module_1/for_demo_video/test_batch_module_1_rembg"
    
    test_batch_background_removal(INPUT_FOLDER, OUTPUT_FOLDER)