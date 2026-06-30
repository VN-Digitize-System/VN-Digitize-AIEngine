import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def setup_environment():
    logger.info("🛠️ ĐANG KHỞI TẠO MÔI TRƯỜNG KIỂM THỬ (MOCK DATA)...")
    
    # 1. Tạo thư mục jsons ở thư mục gốc
    jsons_dir = "../jsons/"
    os.makedirs(jsons_dir, exist_ok=True)
    
    # 2. Thiết kế dữ liệu đa kịch bản để thử lửa Lưỡi dao
    mock_ocr_data = {
        "pages": [
            # Trang 1: Có Tiêu ngữ (Kích hoạt Tầng 1 -> Bắt đầu Tài liệu 1)
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc\n\nQUYẾT ĐỊNH\nVề việc phê duyệt dự án",
            
            # Trang 2: Trang nội dung bình thường (Sẽ được gộp vào Tài liệu 1)
            "Điều 1: Phê duyệt dự án đầu tư xây dựng công trình.\nĐiều 2: Chánh văn phòng chịu trách nhiệm thi hành.",
            
            # Trang 3: Không có tiêu ngữ, nhưng có Từ khóa neo (Kích hoạt Tầng 2 -> Bắt đầu Tài liệu 2)
            "HỢP ĐỒNG KINH TẾ\nSố: 123/HĐKT\nHôm nay, chúng tôi gồm có...",
            
            # Trang 4: Dấu hiệu hình thức in hoa (Kích hoạt Tầng 3 -> Bắt đầu Tài liệu 3 + Bật cờ nghi ngờ)
            "DANH SÁCH NHÂN SỰ THAM GIA DỰ ÁN\n1. Nguyễn Văn A\n2. Trần Thị B",
            
            # Trang 5: In hoa + Số La Mã / Từ khóa loại trừ (False Positive Tầng 3 -> Không cắt, gộp vào Tài liệu 3)
            "CHƯƠNG II\nQUYỀN VÀ NGHĨA VỤ CỦA CÁC BÊN\nBên A có quyền yêu cầu Bên B..."
        ]
    }
    
    # 3. Ghi file JSON
    file_path = os.path.join(jsons_dir, "scan_001_ocr.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(mock_ocr_data, f, ensure_ascii=False, indent=4)
        
    logger.info(f"✅ Đã tạo thành công file dữ liệu mẫu tại: {file_path}")
    logger.info("Môi trường đã sẵn sàng! Bạn có thể chạy batch_processor.py.")

if __name__ == "__main__":
    setup_environment()