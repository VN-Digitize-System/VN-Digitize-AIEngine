# MASTER_PROJECT_CONTEXT.md

## 1. Mục tiêu tổng thể của dự án (Core Vision)

**Tên dự án:** VN-Digitize-AIEngine (Hệ thống Xử lý & Bóc tách Tài liệu Thông minh - Smart IDP).
**Mục tiêu:** Xây dựng một Data Pipeline tự động hóa hoàn toàn quy trình số hóa tài liệu tiếng Việt. Hệ thống tiếp nhận ảnh scan thô, tiền xử lý, đọc chữ (OCR), và bóc tách thông tin phi cấu trúc thành dữ liệu JSON có cấu trúc (NER) với độ chính xác cao.
**Triết lý thiết kế:** "Khớp nối lỏng" (Loose Coupling), Data-Driven Design (điều khiển bằng file JSON), và Enterprise-grade Architecture (sẵn sàng triển khai thực tế).

## 2. Kiến trúc tổng quan (High-Level Architecture)

Dự án được chia thành 3 Module hoạt động tuần tự (Pipeline). Dữ liệu đầu ra của Module trước là đầu vào của Module sau. Hệ thống sử dụng phương pháp bóc tách lai (Hybrid Extraction), kết hợp giữa Rule-based (tốc độ cao) và LLM (xử lý ngữ nghĩa linh hoạt).

**Cấu trúc dữ liệu:** Luồng dữ liệu giao tiếp giữa các Module được chuẩn hóa nghiêm ngặt thông qua các Hợp đồng dữ liệu (Data Contracts) bằng `Pydantic` và `dataclass` (VD: `DocumentInput`, `ExtractedField`).

## 3. Các module chính (Core Modules)

### Module 1: Tiền xử lý ảnh thông minh (Smart Preprocessing)

* **Nhiệm vụ:** Chuẩn hóa ảnh đầu vào trước khi đưa vào OCR.
* **Tính năng:** Tự động phát hiện vùng tài liệu, cắt mép (Crop), nắn thẳng (Deskew) bằng mô hình Deep Learning (U2-Net), đánh giá chất lượng ảnh, lọc bỏ ảnh rỗng/lỗi.

### Module 2: Động cơ OCR Lai (Hybrid OCR Engine)

* **Nhiệm vụ:** Trích xuất toàn bộ văn bản và tọa độ từ ảnh.
* **Tính năng:**
* Thuật toán rẽ nhánh góc xoay 3 miền (Spatial Stratified Sampling).
* Tích hợp PaddleOCR (Detection) và VietOCR (Recognition).
* Gom dòng thông minh (Heuristic Line Grouping) với ngưỡng động.
* Tự động lọc rác tọa độ (bỏ qua bbox có `text` rỗng hoặc `confidence` NaN).
* Đánh số trang (Pagination) tự động thông qua vòng lặp sắp xếp chuẩn Alphabet.



### Module 3: Bóc tách Dữ liệu Động (Dynamic NER & Extraction)

* **Nhiệm vụ:** Trích xuất các trường thông tin (Số VB, Họ tên, Tội danh...) theo định dạng cấu hình của từng loại tài liệu.
* **Tính năng:**
* **Document Classifier (Người gác cổng):** Phân loại tài liệu bằng Regex siêu tốc (đọc 15 dòng đầu).
* **Strategy Router:** Bộ định tuyến tự động chọn chiến lược trích xuất (Regex, LayoutRegex, LLM Batch).
* **Heuristic Retriever (RAG):** Màng lọc CPU thu hẹp cửa sổ ngữ cảnh, trích xuất đoạn văn chứa từ khóa trước khi đẩy cho LLM nhằm tránh tràn RAM.
* **Auto-Corrector:** Sửa lỗi chính tả/OCR lai (Python cho Logic ngày tháng, LLM Few-shot cho văn bản).
* **Output Validator:** Kiểm duyệt kết quả (Pydantic) và kích hoạt cơ chế tự sửa sai (Reflexion).



## 4. Công nghệ đang sử dụng (Tech Stack)

* **Ngôn ngữ:** Python 3.x
* **Core Frameworks:** OpenCV, Numpy, Pydantic, FastAPI.
* **AI & Deep Learning:** PyTorch, PaddleOCR, VietOCR, U2-Net.
* **LLM Integration:** * Cloud: Google GenAI SDK (Gemini 2.5 Flash làm chính, Gemini 2.0 Flash làm dự phòng).
* Local: OpenAI SDK kết nối với Ollama (Mô hình Qwen 2.5:7b).



## 5. Các quyết định kỹ thuật quan trọng (Key Technical Decisions)

1. **Kiến trúc Thư mục Input M3 (Directory-based Isolation):** Lưu 1 tài liệu/1 thư mục riêng biệt để đảm bảo an toàn dữ liệu và hỗ trợ xử lý đa trang.
2. **Gộp trang (Pre-aggregation):** Gộp toàn bộ các trang của 1 tài liệu thành một đối tượng `DocumentInput` duy nhất trước khi đưa vào M3 để LLM có tầm nhìn toàn cảnh (Full Context).
3. **Từ chối nghiêm ngặt (Strict Rejection):** Hệ thống sẽ ném lỗi 400 Bad Request ngay tại tầng API nếu tài liệu không khớp với Master Catalog (`document_catalog.json`), không dùng LLM để đoán mò.
4. **Tải cấu hình động (Lazy Loading) & Fail-Fast:** M3 nạp luật JSON ngay tại Runtime để hỗ trợ Hot-reload. Nếu file JSON lỗi hoặc bị mất, hệ thống ném HTTP 500 ngay lập tức (Fail-fast) thay vì sinh ra dữ liệu rác.
5. **Đo lường Hiệu năng (Benchmarking):** Đo lường kép (Tính tổng thời gian của toàn bộ tài liệu và thời gian trung bình trên từng trang). Lưu trữ tách biệt file Metrics và file Payload JSON.

## 6. Trạng thái hiện tại (Current Status)

* **Tiến độ:** Module 1 và Module 2 đã hoàn thành, vượt qua benchmark và chạy ổn định. Module 3 đã hoàn thiện toàn bộ mã nguồn lõi (Kiến trúc Router, LLM Provider, Classifier, Batch Runner).
* **Trạng thái M3:** Đã thiết lập xong kịch bản kiểm thử siêu cấp `test_batch_runner.py` tích hợp màng lọc Heuristic Retrieval để chạy Local LLM (Ollama) an toàn.
* **Công việc tiếp theo (Next Action):** 1. Chạy thử nghiệm kịch bản `test_batch_runner.py` trên máy Local với dữ liệu thực tế trích xuất từ Module 2.
2. Triển khai chiến lược Đánh giá chất lượng tự động (Automated Ground Truth Evaluation) để tính điểm độ chính xác (F1-Score) của hệ thống.

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