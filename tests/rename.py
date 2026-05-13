import os

def rename_images(folder_path, new_prefix):
    # Kiểm tra xem thư mục có tồn tại không
    if not os.path.exists(folder_path):
        print("Thư mục không tồn tại!")
        return

    # Liệt kê tất cả các file trong thư mục
    files = os.listdir(folder_path)
    
    # Sắp xếp file theo tên để đổi tên thứ tự (không bắt buộc)
    files.sort()
    
    count = 1
    # Danh sách các định dạng ảnh cần đổi tên
    valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

    for filename in files:
        # Kiểm tra xem file có phải là file ảnh không
        if filename.lower().endswith(valid_extensions):
            # Lấy phần mở rộng của file (vd: .jpg)
            file_ext = os.path.splitext(filename)[1]
            
            # Tạo tên mới: ví dụ img_001.jpg
            new_name = f"{new_prefix}_{count:03d}{file_ext}"
            
            # Đường dẫn cũ và mới
            old_file = os.path.join(folder_path, filename)
            new_file = os.path.join(folder_path, new_name)
            
            # Đổi tên
            try:
                os.rename(old_file, new_file)
                print(f"Đã đổi: {filename} -> {new_name}")
                count += 1
            except Exception as e:
                print(f"Lỗi khi đổi tên {filename}: {e}")

    print(f"Hoàn thành! Đã đổi tên {count-1} file.")

# --- CẤU HÌNH Ở ĐÂY ---
# Sử dụng r'' trước đường dẫn để tránh lỗi ký tự đặc biệt trên Windows
folder_to_rename = "F:/VN-Digitize-AIEngine/tests/module_2/Image_Scan_Folder"


new_name_prefix = 'scan'

# Chạy hàm
rename_images(folder_to_rename, new_name_prefix)
