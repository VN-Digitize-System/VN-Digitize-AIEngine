# NEXT_STEPS.md (Cập nhật: 2026-06-22)

## 🔴 High Priority (Cần thực hiện ngay)

* **Thực thi Baseline Test (Dry-run):** Khởi chạy lệnh kịch bản bóc tách trên Terminal 2 (`python scripts/module_3/test_batch_runner.py --input_dir sandbox_inputs --output_dir sandbox_outputs`) để xử lý file `scan_001_ocr.json` với Temperature = 0.0 và tắt Auto-Correct.
* **Nghiệm thu Trực quan (Visual Inspection):** Kiểm tra file JSON đầu ra trong thư mục `sandbox_outputs/` bằng mắt thường để đảm bảo không có rác markdown từ LLM và cấu trúc Pydantic được giữ nguyên vẹn.
* **Đo lường F1-Score (Đánh giá độc lập):** Khởi chạy kịch bản `evaluate_metrics.py` (đối chiếu với `ground_truth/scan_001_ground_truth.json`) để lấy bảng điểm độ chính xác (Precision/Recall/F1) cho luồng bóc tách lai.

## 🟡 Medium Priority (Thực hiện sau khi luồng cơ bản ổn định)

* **Gỡ bỏ Mã giả lập (Remove Mock Data):** Xóa dòng code tiêm cứng từ điển thô `"trang_so": "01-01"` ra khỏi file `test_batch_runner.py`.
* **Phát triển Logic Hậu kỳ Đếm trang (Pagination Logic):** Viết đoạn code Python thực tế (có thể đặt tại `pipeline.py` hoặc Orchestrator) để tự động gom nhóm tọa độ trang (Metadata Reverse Mapping) và xuất ra chuỗi định dạng `"01-01"`.
* **Kiểm thử Luồng Sửa lỗi (Auto-Correction Testing):** Chạy lại kịch bản test với cờ `--auto_correct` được bật để đánh giá xem lớp `auto_corrector.py` có làm thay đổi (hoặc làm hỏng) kết quả Baseline hay không.
* **Kiểm thử Biên (Edge-case Testing):** Đưa các file có chất lượng OCR kém hoặc file viết tay vào `sandbox_inputs/` để kích hoạt và quan sát hiệu quả thực tế của luồng `LLM Fallback`.

## 🟢 Low Priority (Tối ưu hóa và Mở rộng)

* **Tự động hóa Chuỗi Đánh giá (Auto-Chained Execution):** Tích hợp gọi thẳng hàm của `evaluate_metrics.py` vào cuối kịch bản `test_batch_runner.py` để tiết kiệm thao tác gõ lệnh sau khi hệ thống đã hết lỗi vặt.
* **Mở rộng Thư viện Ground Truth:** Xây dựng thêm các file đáp án chuẩn cho các loại tài liệu khác có trong `document_catalog.json` (Căn cước công dân, Văn bản hành chính).
* **Xóa bỏ Sandbox Tạm thời:** Sau khi mọi luồng chạy Batch đã hoàn hảo, điều chỉnh kịch bản để trỏ thẳng vào các thư mục in/out chính thức của hệ thống.