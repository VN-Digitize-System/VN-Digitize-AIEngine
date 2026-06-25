# Next Steps

Priority High

* Khởi chạy kịch bản `test_batch_runner.py` trên máy Local với mô hình Ollama (Qwen 2.5) để kiểm thử toàn luồng End-to-End cho Module 3 bằng dữ liệu thực tế từ Module 2.
* Thu thập và phân tích báo cáo hiệu năng `m3_performance_summary.json` để đánh giá thời gian xử lý tổng thể, tốc độ trên từng trang, và theo dõi các vấn đề liên quan đến giới hạn phần cứng (như tràn bộ nhớ RAM/VRAM).

Priority Medium

* Xây dựng tệp dữ liệu đáp án chuẩn (Ground Truth) thủ công cho các biểu mẫu đang được dùng làm mẫu kiểm thử (đặc biệt là tài liệu 137 trang).
* Phát triển kịch bản đánh giá chất lượng tự động (Automated Evaluation Script) để tính toán điểm số F1-Score, Precision, và Recall dựa trên file Ground Truth vừa tạo.

Priority Low

* Tinh chỉnh lại các biểu thức chính quy (Regex) và tối ưu hóa System Prompt cho Local LLM nếu kết quả đối chiếu độ chính xác (Accuracy) chưa đạt mức kỳ vọng.
* Thiết kế cơ chế điều phối linh hoạt (Load Balancing / Rate Limit Handling) để có thể tích hợp và sử dụng lại Cloud API (Gemini) song song với Local LLM khi cần xử lý khối lượng dữ liệu khổng lồ.

# Next Steps

Priority High
- Tích hợp hàm sửa lỗi theo cụm từ (Context-Aware Aliasing) vào `RegexExtractor`.
- Cập nhật mã nguồn `RegexExtractor` để hỗ trợ điểm neo `{LABEL}`, nối văn bản toàn cục và làm sạch dữ liệu hậu kỳ (Auto-Formatting).
- Viết mã nguồn cho `StrategyRouter` tích hợp logic Fallback, Gom mẻ LLM (Batching) và Regex JSON Healing.
- Ráp nối các module lại và khởi chạy kịch bản kiểm thử `test_batch_runner.py` với file `scan_001_ocr.json` (Thông tư/Nghị định) trên Local.

Priority Medium
- Đo lường và giám sát chặt chẽ mức tiêu thụ RAM/CPU thực tế của mô hình Qwen khi chạy trên kiến trúc Hybrid.
- Thu thập và phân tích báo cáo hiệu năng `m3_performance_summary.json` để tinh chỉnh thời gian chờ.

Priority Low
- Xây dựng bộ dữ liệu đáp án chuẩn (Ground Truth) để tự động hóa đánh giá độ chính xác (F1-Score).
- Tinh chỉnh thêm mảng `aliases` nếu phát hiện các biến thể lỗi OCR mới trong quá trình kiểm thử diện rộng.

# Next Steps

## 🔴 ƯU TIÊN CAO NHẤT (Immediate Action)
1. **[Quyết định Kiến trúc] Chốt Chiến lược LLM Observability:** Quyết định xem sẽ sử dụng Standard Console Logging hay Comprehensive Trace Logging để lưu vết quá trình suy luận của LLM (Đang thảo luận).
2. **Khởi tạo Dữ liệu Ground Truth:**
   - Tạo thư mục `ground_truth/`.
   - Lấy ngẫu nhiên ~10-20 file kết quả OCR từ Module 2.
   - Sử dụng "Master Prompt" cùng Web AI (ChatGPT/DeepSeek) để tạo nhanh các file JSON đáp án. Kiểm duyệt bằng mắt và lưu lại.
3. **Chạy Kiểm thử End-to-End (E2E):**
   - Kích hoạt Ollama (Qwen 2.5).
   - Chạy `python scripts/module_3/test_batch_runner.py` trên tập tài liệu mẫu.
   - Chạy `python scripts/module_3/evaluate_metrics.py` để xuất bảng điểm F1-Score đầu tiên của hệ thống.

## 🟡 ƯU TIÊN TRUNG BÌNH (Vòng lặp Cải tiến)
1. **Phân tích Báo cáo F1-Score:** Nhìn vào kết quả đo lường, xác định các trường có F1-Score thấp (<80%).
2. **Tinh chỉnh Hệ thống (Fine-tuning):**
   - Nếu lỗi ở Regex: Cập nhật thư viện `aliases` hoặc viết lại Regex Pattern trong `rules_vbpl.json`.
   - Nếu lỗi ở LLM: Cập nhật `few_shot_examples` hoặc làm rõ mô tả `description` trong file cấu hình.
3. **Tích hợp UI/API Thực tế:** Kết nối hoàn chỉnh API trả kết quả (`api.py`) vào một giao diện Web đơn giản (Streamlit/Gradio) hoặc Postman để test luồng Upload -> Trả kết quả JSON trực tiếp.

## 🟢 ƯU TIÊN THẤP (Future Scalability)
- Cân nhắc tích hợp một Cloud Provider phụ trợ với rate-limit xử lý tốt (như Groq) phòng trường hợp máy Local quá tải khi scale lên hàng nghìn hồ sơ.

Dưới đây là bản cập nhật nội dung cho file `NEXT_STEPS.md` được thiết kế dưới góc độ của một Project Planner, tập trung giải quyết triệt để nút thắt OCR hiện tại và chuẩn bị lộ trình phát triển kiến trúc Hồ sơ phức hợp.

---

# NEXT_STEPS.md

## 🔴 High Priority (Cần thực hiện ngay)

* **Chốt Chiến lược Định dạng Đầu ra:** Xác nhận quy tắc ép khuôn định dạng chuẩn (Strict Format Constraint) cho các trường dữ liệu trước khi chạy Baseline.
* **Khởi tạo `rules_don_bien_dong.json`:** Tạo file cấu hình schema tối giản dành riêng cho Trang 7 (Đơn đề nghị). Cấu hình giới hạn đúng 5 trường: `so_ky_hieu`, `ngay_thang`, `ten_tai_lieu`, `tac_gia` (áp dụng Semantic Inference), và `trang_so`. Khai báo Prompt theo kỹ thuật Zero-Shot.
* **Xây dựng `ground_truth.json` (Trang 7):** Tạo file đáp án chuẩn hóa hoàn hảo (Perfect Normalization) cho 5 trường thông tin trên, đóng vai trò là "Đề thi" khắt khe nhất để đo lường độ chịu lỗi của hệ thống.
* **Thực thi Baseline Testing:** Chạy lệnh `python test_batch_runner.py` và `python evaluate_metrics.py` đối với file JSON OCR của Trang 7 để thiết lập Điểm cơ sở (Baseline F1-Score), ghi nhận chính xác bằng số liệu mức độ ảnh hưởng của rác OCR lên luồng xử lý lõi.

## 🟡 Medium Priority (Thực hiện sau khi có Baseline)

* **Phân tích Nút thắt Cổ chai (OCR Bottleneck):** Đánh giá báo cáo Baseline. Nếu F1-Score quá thấp do rác chữ viết tay, lập kế hoạch nghiên cứu giải pháp thay thế/nâng cấp cho Module 2 (ví dụ: Google Cloud Vision API hoặc mô hình Multi-modal) trước khi mở rộng cấu hình trích xuất.
* **Phát triển `configs/split_rules.json`:** Định nghĩa các mỏ neo phân tách (Split Markers) sử dụng Regex (ví dụ: Quốc hiệu, Tiêu đề lớn) để chuẩn bị cho kiến trúc xử lý hồ sơ đa trang.
* **Phát triển `DocumentSplitter`:** Viết code cho bộ chia tách tài liệu, tự động load file cấu hình JSON động để nhận diện ranh giới trang.
* **Xây dựng `DossierProcessor` (Lớp Điều phối):**
* Lập trình cơ chế cắt vật lý file JSON gốc thành các file tạm (Physical JSON Splitting).
* Tích hợp luồng chạy vòng lặp an toàn (Fault-Tolerant), bỏ qua các trang lỗi cục bộ.
* Đóng gói toàn bộ kết quả trả về thành một file JSON Mục lục duy nhất (Single Dossier JSON) cho toàn bộ hồ sơ.



## 🟢 Low Priority (Nâng cấp và Tối ưu hóa trong tương lai)

* **Mở rộng Lược đồ Đơn biến động:** Sau khi giải quyết triệt để vấn đề nhiễu OCR chữ viết tay, cập nhật `rules_don_bien_dong.json` để bóc tách toàn diện các trường thông tin sâu hơn (Diện tích, Lý do biến động, Tên người sử dụng, CMND...).
* **Tối ưu hóa Prompt bằng Few-Shot:** Áp dụng các ví dụ mẫu vào câu lệnh hệ thống để tăng độ chính xác của Qwen 2.5 nếu Baseline Zero-Shot chưa đạt kỳ vọng kinh doanh.

---

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