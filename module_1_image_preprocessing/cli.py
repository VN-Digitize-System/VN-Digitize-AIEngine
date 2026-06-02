import argparse
from module_1_image_preprocessing.preprocessor import ImagePreprocessor

def main():
    parser = argparse.ArgumentParser(description="Màng bọc CLI cho Module 1 (Image Preprocessing)")
    parser.add_argument("--input_dir", required=True, help="Thư mục chứa ảnh hồ sơ thô")
    parser.add_argument("--output_dir", required=True, help="Thư mục lưu ảnh đã làm sạch và file summary")
    args = parser.parse_args()
    
    print(f"[M1-CLI] Bắt đầu kích hoạt AI tiền xử lý ảnh...")
    
    # Khởi tạo Class (Chỉ nạp AI 1 lần duy nhất - Tránh lỗi TypeError cũ)
    processor = ImagePreprocessor()
    
    # Bơm thư mục dữ liệu vào xử lý
    processor.process_folder(args.input_dir, args.output_dir)
    
    print("[M1-CLI] Đã hoàn thành toàn bộ thư mục.")

if __name__ == "__main__":
    main()