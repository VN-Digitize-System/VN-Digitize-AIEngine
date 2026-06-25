# Progress Log

## 2026-06-17

Completed

* Thảo luận và chốt hoàn toàn 14 quyết định thiết kế kiến trúc hệ thống cốt lõi cho Module 3 (Quản lý catalog tập trung, Component Classifier độc lập, API Exception Handling, Regex Matching, Lazy Loading, Fail-Fast, Pre-aggregation, Thư mục cách ly, Heuristic Retrieval, Đo lường hiệu năng kép, và Lưu trữ tách biệt Payload/Metrics).
* Xây dựng thành công tệp cấu hình biểu thức chính quy cho danh mục tài liệu trung tâm `configs/document_catalog.json`.
* Thiết lập mã nguồn cho thành phần "Người gác cổng" độc lập xử lý kiểm tra tài liệu và bẫy lỗi ngoại lệ tại `router/classifier.py`.
* Tái cấu trúc (Refactor) và dọn dẹp các thư viện import thừa (`UnknownDocumentError`, `ReflexionRetryException`) trong file xử lý trung tâm `module_3_dynamic_ner/pipeline.py`.
* Cập nhật tầng giao tiếp API tại `api.py` để tích hợp cơ chế nạp cấu hình động runtime và bắt lỗi tùy chỉnh nhằm phản hồi mã HTTP 400/500 chuẩn RESTful.
* Hoàn thiện mã nguồn siêu kịch bản chạy kiểm thử hiệu năng diện rộng và gộp trang tự động tại `scripts/module_3/test_batch_runner.py`.
* Quy hoạch và đồng bộ hóa cấu trúc cây thư mục dự án toàn cục cho Module 3 để phục vụ mục tiêu phát triển lâu dài.
* Hoàn thành biên soạn nội dung tài liệu cốt lõi phục vụ bàn giao và lưu trữ dự án bao gồm `MASTER_PROJECT_CONTEXT.md` và `ARCHITECTURE.md`.

In Progress

* Khởi chạy thử nghiệm nghiệm thu toàn luồng và đo lường thời gian xử lý thực tế của Module 3 với mô hình Local LLM (Ollama - Qwen 2.5) dựa trên tập dữ liệu thật trích xuất từ Module 2 thông qua file kịch bản `test_batch_runner.py`.

Issues

* Giới hạn số lần gọi (Rate limit) của Cloud API Gemini gây gián đoạn luồng kiểm thử cũ (Đã tạm thời khắc phục bằng cách thiết lập kiến trúc dự phòng chuyển trục sang Local LLM Ollama, cần chạy thực tế trên máy Local để nghiệm thu độ ổn định).

Notes

* Phiên làm việc thực thi chạy tệp kịch bản kiểm thử batch runner và thu thập báo cáo `m3_performance_summary.json` được thống nhất dời sang ngày mai.
* Cần chuẩn bị phương án xây dựng bộ dữ liệu đáp án chuẩn (Ground Truth) để tự động hóa quy trình đánh giá độ chính xác (F1-Score) của mô hình Local LLM ngay sau khi khâu đo lường tốc độ xử lý hoàn tất.

# Progress Log

## 2026-06-18

Completed
- Chuyển hướng chiến lược dữ liệu kiểm thử: Ưu tiên dùng dữ liệu thực tế (văn bản pháp luật từ vbpl.vn) và xây dựng file luật mới (`rules_vbpl.json`) thay vì sinh dữ liệu giả.
- Cập nhật từ điển định tuyến `document_catalog.json` cho nhóm văn bản pháp luật.
- Hoàn thiện bản thiết kế kiến trúc "Lai" (Hybrid Architecture) cho Module 3, phân luồng trích xuất giữa Regex (trường dễ) và Local LLM (trường khó) nhằm tối ưu chạy Offline trên phần cứng yếu (i5, 16GB RAM, No GPU).
- Chốt cấu trúc file Rule `rules_vbpl.json` tích hợp Few-shot examples, mảng nhãn thay thế (`aliases`), và điểm neo nội suy `{LABEL}`.

In Progress
- Triển khai mã nguồn (Step-by-step Integration) cho các module cốt lõi của M3: `OCRNormalizer` (để xử lý Aliases), `RegexExtractor` và `StrategyRouter`.
- Điều chỉnh kịch bản đọc file `test_batch_runner.py` tích hợp thuật toán xén trang Head-and-Tail Truncation (chỉ lấy 2 trang đầu + 2 trang cuối).

Blockers
- Cấu hình phần cứng mục tiêu của khách hàng rất hạn chế (Thiếu VRAM/GPU). Cần theo dõi sát sao mức độ tiêu thụ RAM khi chạy thực tế mô hình lượng tử hóa.

Notes
- Áp dụng nguyên tắc "Bất biến dữ liệu gốc": Không tự động sửa lỗi chính tả toàn văn bản (tránh sửa nhầm tên riêng/nghiệp vụ), chỉ chuẩn hóa ở cấp độ Nhãn (Label Aliasing).


# Progress Log

## 2026-06-19

**Trạng thái:** Hoàn thành xuất sắc toàn bộ kiến trúc lõi của Tầng bóc tách và các kịch bản kiểm thử tự động.

**Các hạng mục đã hoàn thành:**
* **Tái cấu trúc Mã nguồn Lõi:**
  * Hoàn thiện `RegexExtractor` với khả năng **Dual Format Support** (tương thích ngược các file luật cũ) và **Approximate Line Tracing** (truy vết tọa độ siêu tốc).
  * Nâng cấp `StrategyRouter` hỗ trợ bóc tách gom mẻ (LLM Batching) và tự động gán điểm tin cậy tĩnh (Hardcoded Confidence = 0.85) cho các trường dùng AI.
  * Tinh chỉnh `LocalLLMProvider` (Ollama/Qwen) tích hợp cơ chế **Hard Timeout (120s)**, tự động cắt cầu nếu mô hình bị treo để bảo vệ tiến trình.
* **Xây dựng Công cụ Vận hành (CLI Scripts):**
  * Hoàn thành kịch bản chạy lô `test_batch_runner.py` với cơ chế **Early Truncation** (chỉ nạp 2 trang đầu & 2 trang cuối để chống tràn RAM) và **Fail-Safe** (Bắt lỗi và đi tiếp để đảm bảo tiến trình chạy qua đêm).
  * Hoàn thành kịch bản đánh giá `evaluate_metrics.py` tính toán **Field-Level F1-Score** dựa trên thuật toán **Fuzzy Normalized Match** (Chuẩn hóa chữ thường, xóa khoảng trắng và dấu câu).
* **Tài liệu hóa (Documentation):**
  * Đã tạo thành công `CODEBASE_MAP.md` và bộ `FILE_SUMMARIES` để AI và kỹ sư mới có thể nắm bắt hệ thống trong tích tắc.
* **Chiến lược Ground Truth:** * Chốt phương pháp Zero-Code Web AI: Sử dụng "Master Prompt" chuẩn hóa để nhờ ChatGPT/DeepSeek bản Web gán nhãn dữ liệu, sau đó kiểm tra và lưu thủ công thay vì tốn công viết API.

## 2026-06-20

### Completed

* Phân tích và làm rõ yêu cầu nghiệp vụ xử lý "Hồ sơ phức hợp" (Multi-Document Dossier) từ khách hàng dựa trên file mẫu `016986.pdf` (sinh ra bảng Mục lục tổng hợp).


* Hoàn thiện bản thiết kế kiến trúc hệ thống xử lý hồ sơ đa trang:
* Sử dụng cơ chế Document Splitting Pipeline (cắt trang bằng Regex theo cấu hình động từ JSON).
* Xây dựng lớp vỏ bọc điều phối bên ngoài (External Orchestrator Wrapper).
* Áp dụng phương pháp chia tách vật lý (lưu file tạm) và cơ chế chịu lỗi cục bộ (Fault-Tolerant).
* Đóng gói đầu ra thành một file JSON Mục lục duy nhất.


* Thống nhất chiến lược kiểm thử: Tạm dừng phát triển tính năng cắt hồ sơ để ưu tiên test luồng bóc tách lõi (Module 3) sử dụng "Bài test cực hạn" là Trang 7 (Đơn đề nghị đăng ký biến động).


* Chốt lược đồ trích xuất tối giản (Minimum Viable Extraction) phục vụ bảng Mục lục gồm 5 trường: Số ký hiệu, Ngày tháng, Tên tài liệu, Tác giả (dùng Semantic Inference), và Trang số.
* Chốt phương pháp luận đo lường Baseline: Sử dụng "Chuẩn hóa hoàn hảo" (Perfect Normalization) cho Ground Truth và "Descriptive Zero-Shot" cho LLM Prompt.

### In Progress

* Khởi tạo file cấu hình schema chuyên biệt `rules_don_bien_dong.json` cho 5 trường thông tin tối giản.
* Soạn thảo đáp án chuẩn `ground_truth.json` cho Trang 7.
* Thiết lập lệnh chạy nháp (Dry-Run) với `test_batch_runner.py` và `evaluate_metrics.py` để lấy điểm Baseline F1-Score.

### Blockers

* Chất lượng bóc tách văn bản của Module 2 (OCR) đối với chữ viết tay trong hồ sơ khách hàng đang ở mức rất tệ (ví dụ: nhận diện thành chuỗi vô nghĩa như *"TAI SAP - LIỆN VÀ TRẬN..."*). Nút thắt này có rủi ro làm phá vỡ toàn bộ ngữ cảnh đầu vào của Module 3.



### Notes

* Mặc dù Module 2 đang cung cấp dữ liệu rác đối với chữ viết tay, quyết định kỹ thuật được đưa ra là vẫn tiến hành chạy Baseline Test. Mục tiêu là để có được con số định lượng chính xác về mức độ ảnh hưởng của lỗi OCR lên F1-Score tổng thể, làm cơ sở dữ liệu vững chắc cho quyết định nâng cấp/thay thế lõi OCR trong tương lai.

## 2026-06-22

### Completed

* Hoàn thiện cập nhật cấu trúc file đáp án chuẩn `ground_truth.json` với định dạng số trang dạng chuỗi đích (ví dụ: `"01-01"`).
* Thiết lập môi trường kiểm thử hộp cát (Sandbox) cô lập với hai thư mục `sandbox_inputs/` và `sandbox_outputs/` để bảo vệ dữ liệu gốc.
* Thống nhất việc sử dụng tham số dòng lệnh (CLI Arguments thông qua `argparse` có sẵn) trong `test_batch_runner.py` để trỏ luồng dữ liệu vào Sandbox.
* Chèn thành công đoạn code giả lập (Mock data) dạng từ điển thô cho trường `"trang_so"` vào tầng kịch bản `test_batch_runner.py` để vượt qua lỗi báo thiếu trường mà không làm thay đổi luồng lõi.
* Cập nhật file `configs/document_catalog.json` theo chiến lược Tương thích ngược (Backward Compatible Hybrid), kết hợp cấu trúc Object/Dictionary cũ với mảng Regex nhận diện mới cho nhóm `van_ban_phap_luat`.
* Viết bản tóm tắt tài liệu (documentation summaries) cho các file `ground_truth.json`, `document_catalog.json`, và `rules_vbpl.json` để bổ sung vào `FILE_SUMMARIES_module_3.md`.
* Chốt cấu hình hệ thống quan trọng trước khi chạy: LLM Engine (Local), Chế độ tải (Sequential Mode), Temperature (0.0), tắt Auto-Correct, và thực thi đánh giá F1-Score thành một nhịp độc lập.
* Chốt chiến lược khởi động nóng (Warm Start) mô hình `qwen2.5:7b` trên Terminal riêng biệt.

### In Progress

* Khởi chạy kiểm thử End-to-End (Dry-run) luồng bóc tách cơ bản (Baseline) trên file mục tiêu `scan_001_ocr.json`.
* Kiểm tra trực quan file xuất JSON trong thư mục đầu ra.
* Thực thi kịch bản đo lường và tính điểm F1-Score đối chiếu với file Ground Truth.

### Blockers

* Không có trở ngại hoặc lỗi hệ thống nào được ghi nhận trong phiên làm việc hiện tại. Mọi yếu tố phụ thuộc đã được giải quyết xong.

### Notes

* Kỹ thuật "Giả lập Tạm thời" được áp dụng ở tầng kiểm thử giúp bảo vệ nguyên tắc Clean Code cho lớp Điều phối lõi (`pipeline.py`).
* File `test_batch_runner.py` hiện tại đang được cấu hình chỉ quét 1 file duy nhất (Đơn mục tiêu) để tập trung Debug.