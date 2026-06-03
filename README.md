# VN-Digitize AI Engine Project

```markdown
# 📖 CẨM NANG VẬN HÀNH HỆ THỐNG (RUN GUIDE)
**Dự án:** VN-Digitize-AIEngine
**Kiến trúc:** Micro-Environments & Modular CLI

Tài liệu này hướng dẫn cách thiết lập môi trường và chạy các module trong luồng xử lý tài liệu. Hệ thống được thiết kế theo chuẩn Enterprise, hỗ trợ chạy tự động hàng loạt và có thể tùy biến linh hoạt qua Terminal.

---

## 🛠 1. QUẢN LÝ MÔI TRƯỜNG (ENVIRONMENT SETUP)
Để đảm bảo không xung đột thư viện giữa các module (ví dụ: Module 1 dùng AI cắt góc, Module 2 dùng mô hình OCR chuyên biệt), hệ thống sử dụng các môi trường Conda phân lập.

**Trước khi chạy bất kỳ Module nào, bạn BẮT BUỘC phải kích hoạt đúng môi trường của Module đó:**
```bash
# Đối với Module 1:
conda activate module_1_HL

# (Các môi trường cho Module 2, 3 sẽ được cập nhật sau)

```

---

## 🖼 2. MODULE 1: TIỀN XỬ LÝ ẢNH (IMAGE PREPROCESSING)

**Mục tiêu:** Dọn dẹp ảnh gốc, cắt viền, nắn thẳng, lọc trang trắng và nhận diện mã vạch.

### 2.1. Chạy Thử nghiệm bằng Cổng Phụ (Dành cho Developer)

Sử dụng công cụ `test_runner.py` để quét một thư mục bất kỳ và in ra bảng thống kê chi tiết kèm ảnh debug (có vẽ khung xanh).

**Lệnh tiêu chuẩn (Khuyên dùng):**

```bash
python scripts/module_1/test_runner.py

```

> 💡 **Giải thích Mặc định:** Nếu không truyền tham số, hệ thống sẽ tự động lấy ảnh từ `tests/data/unit_tests/module_1/module_1_image` và lưu kết quả ra `tests/data/outputs/unit_tests/module_1/module_1_runner_results`. Thư mục output sẽ bị dọn sạch (Auto-Clean) trước khi chạy để tránh rác.

**Lệnh tùy biến (Test một thư mục khác):**

```bash
python scripts/module_1/test_runner.py --input_dir "đường_dẫn_vào" --output_dir "đường_dẫn_ra"

```

> 💡 **Giải thích Tham số:**
> * `--input_dir`: Thư mục chứa ảnh gốc bạn muốn test.
> * `--output_dir`: Thư mục lưu ảnh đã xử lý và ảnh debug.
> 
> 

### 2.2. Chạy Thực tế bằng Cổng Chính (Production Pipeline)

Khi tích hợp vào luồng chạy thật, sử dụng `cli.py`. File này không in bảng màu mè mà tập trung xuất ra file ảnh sạch và file `m1_summary.json` bàn giao cho Module 2.

**Lệnh chạy tiêu chuẩn:**

```bash
python module_1_image_preprocessing/cli.py --input_dir "data/raw_hoso" --output_dir "data/processed_hoso"

```

### 2.3. 🎛 CÔNG TẮC ĐẶC BIỆT: `--skip_crop`

Cả `test_runner.py` và `cli.py` đều hỗ trợ một công tắc bí mật để tối ưu hóa thời gian khi gặp dữ liệu sạch.

**Lệnh sử dụng:**
Thêm `--skip_crop` vào cuối bất kỳ câu lệnh nào ở trên.
*Ví dụ:* `python module_1_image_preprocessing/cli.py --input_dir "..." --output_dir "..." --skip_crop`

> 💡 **Khi nào nên dùng `--skip_crop`?**
> * **Mặc định (Không ghi gì):** Hệ thống luôn gọi AI U2-Net để tìm mép giấy và nắn góc. Dành cho **Ảnh chụp từ điện thoại**.
> * **Bật công tắc (`--skip_crop`):** Hệ thống bỏ qua bước cắt góc, dùng thẳng ảnh gốc. Siêu nhanh. Dành cho **File PDF chuẩn hoặc ảnh Scan từ máy photocopy** đã vuông vức sẵn.
> 
> 

---

## 🗄 3. LƯU TRỮ LỊCH SỬ KIỂM THỬ (ARCHIVING)

Hệ thống có cơ chế tự động xóa sạch thư mục `outputs/` mỗi khi chạy lệnh mới để tiết kiệm ổ cứng. Nếu bạn chạy được một kết quả test quá ưng ý và muốn lưu lại làm chuẩn (Golden Record):

1. Mở thư mục `tests/data/outputs/...`
2. **Copy thủ công** thư mục kết quả đó.
3. Dán vào `tests/data/archive/module_1/`.
4. Đổi tên thư mục thành một cái tên gợi nhớ (VD: `test_barcode_pass_03_06_2026`).

---

*Cẩm nang sẽ tiếp tục được cập nhật khi kiến trúc Module 2 và Module 3 hoàn thiện.*

```

---

```