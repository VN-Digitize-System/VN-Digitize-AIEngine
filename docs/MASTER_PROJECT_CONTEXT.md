# MASTER_PROJECT_CONTEXT.md (updated 22/06/2026)

## 1. Mục tiêu Tổng thể (Project Goal)

Dự án của chúng tôi nhằm xây dựng một hệ thống Xử lý Tài liệu Thông minh (IDP - Intelligent Document Processing) khép kín. Hệ thống có khả năng tự động tiếp nhận hình ảnh tài liệu, tiền xử lý, nhận dạng ký tự quang học (OCR), sau đó phân loại động và bóc tách thông tin (Dynamic NER) thành dữ liệu có cấu trúc (JSON) chuẩn hóa để tích hợp vào các hệ thống nghiệp vụ.

## 2. Các Module Chính (Main Modules)

* **Module 1: Image Preprocessing** (Tiền xử lý ảnh): Xử lý hình ảnh thô, làm sạch, xoay nghiêng và tối ưu hóa chất lượng trước khi đưa vào OCR.
* **Module 2: Core OCR** (Nhận dạng ký tự quang học): Đọc văn bản từ ảnh và xuất ra định dạng JSON chứa dữ liệu thô (words, lines, bounding boxes, confidence score).
* **Module 3: Dynamic NER & Extraction** (Trích xuất thông tin động - Trọng tâm hiện tại):
* Lớp điều phối (Orchestrator) tiếp nhận JSON từ Module 2.
* Phân loại tài liệu động (Classifier).
* Bóc tách lai (Hybrid Extraction) trích xuất siêu dữ liệu (Metadata).
* Hậu kỳ và sửa lỗi (Auto-Corrector & Post-processing).



## 3. Công nghệ Sử dụng (Technologies)

* **Ngôn ngữ & Thư viện:** Python, Pydantic (Data validation), Argparse (CLI routing).
* **Mô hình AI (Local LLM):** Qwen 2.5 (7B parameters) vận hành qua máy chủ nội bộ Ollama.
* **Thuật toán & Xử lý:** Regular Expressions (Regex) nâng cao để đối sánh mẫu và chống nhiễu OCR.
* **Kiến trúc Dữ liệu:** JSON (Đầu vào/Đầu ra/Cấu hình luật bóc tách).

## 4. Kiến trúc Tổng quan (Overall Architecture)

* **Tách biệt Mối quan tâm (Separation of Concerns):** Hệ thống tách bạch hoàn toàn code bóc tách lõi (`pipeline.py`) và code kiểm thử (`test_batch_runner.py`).
* **Định tuyến Động (Dynamic Routing):** Sử dụng `classifier.py` kết hợp với `document_catalog.json` (chứa các Regex chống nhiễu) để tự động nhận dạng loại tài liệu (Văn bản pháp luật, CCCD, Hành chính) ở 15 dòng đầu tiên và gọi bộ luật (`rules_*.json`) tương ứng.
* **Kiến trúc Bóc tách Lai (Hybrid Extraction):** Sử dụng phương pháp "Regex-First" để đảm bảo tốc độ và tính xác định (Deterministic), kết hợp "LLM Fallback" để tự động cứu hộ (Auto-Rescue) và bóc tách ngữ nghĩa đối với các trường phức tạp hoặc lỗi do OCR.
* **Quản lý Tài nguyên (Resource Management):** Tích hợp cơ chế Early Truncation (chỉ giữ trang đầu/cuối) để chống tràn RAM khi xử lý file JSON lớn.

## 5. Trạng thái Hiện tại (Current Status)

* **Giai đoạn:** Đang ở pha kiểm thử End-to-End (Dry-run) luồng bóc tách cốt lõi (Baseline) của Module 3.
* **Hoàn thành:** Đã thiết lập xong toàn bộ cấu hình lõi (`rules_vbpl.json`, `document_catalog.json`), kịch bản kiểm thử hộp cát (`sandbox_inputs/outputs`), và quy chuẩn file đáp án (`ground_truth.json`).
* **Tiếp theo:** Đang thực thi đánh giá hiệu năng (F1-Score, Precision, Recall) trên tệp thử nghiệm "Văn bản Pháp luật" chuẩn in máy (`scan_001_ocr.json`) để xác nhận độ chính xác của kiến trúc Hybrid trước khi chuyển sang tài liệu viết tay hoặc có chất lượng OCR kém.

## 6. Quyết định Kỹ thuật Quan trọng (Key Technical Decisions)

* **Sử dụng Local LLM với Temperature = 0.0:** Đảm bảo tính xác định tuyệt đối (Deterministic), loại bỏ rủi ro ảo giác (Hallucination) phục vụ cho bài toán Information Extraction nghiêm ngặt.
* **Mô hình "Khởi động nóng" (Warm Start) Ollama:** Chạy LLM trên một tiến trình Terminal độc lập để tránh lỗi Timeout 120s trong nhịp gọi API đầu tiên của Python.
* **Thiết lập Môi trường Sandbox Cô lập:** Dùng tham số dòng lệnh (CLI arguments) truyền thư mục `sandbox_inputs` và `sandbox_outputs` để bảo vệ an toàn 100% dữ liệu gốc từ Module 2.
* **Chấm điểm Độc lập (Independent Evaluation):** Tách biệt kịch bản bóc tách (`test_batch_runner.py`) và kịch bản chấm điểm (`evaluate_metrics.py`) để dễ dàng kiểm tra trực quan JSON thô.
* **Tiêm Mã giả lập ở Tầng Kiểm thử (Test-level Mocking):** Giả lập dữ liệu hậu kỳ (ví dụ: chuỗi `"01-01"` cho trường số trang) trực tiếp trong script test thay vì can thiệp vào `pipeline.py`, giữ cho lõi hệ thống sạch sẽ (Clean Code).
* **Catalog Tương thích ngược (Backward Compatible Hybrid):** Cập nhật `document_catalog.json` bằng cách giữ nguyên cấu trúc Object cũ (để bảo vệ luồng CCCD/Hành chính) nhưng tiêm thêm Regex mềm dẻo cho loại tài liệu mới.