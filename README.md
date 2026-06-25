## 🚀 Hướng dẫn chạy Module 1 (Tiền xử lý ảnh)

Module 1 đảm nhiệm việc tiếp nhận ảnh tài liệu thô, cắt viền, xoay chuẩn và lọc bỏ các ảnh trắng/lỗi trước khi đưa vào hệ thống OCR.

### Bước 1: Tạo và kích hoạt môi trường ảo
Mở Terminal (hoặc Command Prompt / PowerShell) tại thư mục gốc của dự án `VN-Digitize-AIEngine` và chạy lệnh sau để tạo môi trường ảo có tên `venv_m1`:

```bash
python -m venv venv_m1

```

Sau khi tạo xong, bạn cần kích hoạt môi trường ảo này:

* **Trên Windows (Command Prompt / PowerShell):**
```cmd
venv_m1\Scripts\activate

```


* **Trên macOS / Linux:**
```bash
source venv_m1/bin/activate

```

*(Dấu hiệu thành công: Bạn sẽ thấy chữ `(venv_m1)` xuất hiện ở đầu dòng lệnh).*

### Bước 2: Cài đặt thư viện

Sử dụng file requirement đã được xuất sẵn để cài đặt các thư viện xử lý ảnh (như OpenCV) cần thiết cho Module 1:

```bash
pip install -r requirements_module1.txt

```

### Bước 3: Chạy kịch bản kiểm thử (Batch Runner)

Kịch bản test của Module 1 đã được cấu hình sẵn các đường dẫn trỏ tới thư mục dữ liệu mẫu (dành cho demo video).

**Cách 1: Chạy với cấu hình mặc định (Khuyên dùng cho người mới)**
Chỉ cần gõ lệnh sau, hệ thống sẽ tự động lấy ảnh từ `tests/data/unit_tests/...` và lưu kết quả vào thư mục test tương ứng:

```bash
python scripts/module_1/test_batch_runner.py

```

**Kết quả mong đợi:** 
Terminal sẽ in ra quá trình xử lý từng ảnh và cuối cùng hiển thị bảng **BÁO CÁO HIỆU NĂNG MODULE 1** (bao gồm số lượng ảnh thành công, ảnh lỗi, tổng thời gian và tốc độ FPS). Một file metadata `m1_summary.json` cũng sẽ được sinh ra tại thư mục đầu ra.

```

