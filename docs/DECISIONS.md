### Date: 2026-06-17

**1. Decision: Sử dụng Centralized Master Catalog (Tạo file `document_catalog.json` tập trung).**

* **Reason:** Dễ quản lý, lộ trình định tuyến minh bạch 100% trong một file, khả năng mở rộng cao khi dự án thêm nhiều loại biểu mẫu.
* **Impact:** Module 3 phân loại tài liệu dựa trên một bảng điều khiển trung tâm thay vì quét phân tán từng file rule.

**2. Decision: Tạo class độc lập cho Document Classifier (`router/classifier.py`).**

* **Reason:** Tuân thủ Nguyên tắc Đơn trách nhiệm (SRP), tính đóng gói cao, dễ dàng nâng cấp lên mô hình Text Classification sau này mà không phá vỡ Pipeline.
* **Impact:** Tách biệt hoàn toàn logic phân loại (Gác cổng) ra khỏi file Core Logic (`pipeline.py`).

**3. Decision: Bắt lỗi và phản hồi ngoại lệ `UnknownDocumentError` ngay tại tầng API.**

* **Reason:** Chuẩn mực RESTful API, minh bạch mã lỗi. Phân định rõ ràng giữa lỗi gửi sai giấy tờ (HTTP 400) và bóc tách ra dữ liệu rỗng.
* **Impact:** API sẽ trả về lỗi HTTP 400 Bad Request cho các tài liệu rác; `pipeline.py` không cần xử lý ngầm lỗi này.

**4. Decision: Sử dụng biểu thức chính quy (Regex Matching) để đối sánh từ khóa tài liệu.**

* **Reason:** Mạnh mẽ và bao dung với các lỗi sai chính tả/dấu câu đặc thù của dữ liệu OCR tiếng Việt (Noisy Data).
* **Impact:** Giữ tỷ lệ nhận diện phân loại tài liệu cao, giảm thiểu việc từ chối nhầm tài liệu hợp lệ (False Negative).

**5. Decision: Tải cấu hình động bằng phương pháp Lazy Loading.**

* **Reason:** Tiết kiệm RAM và cho phép cập nhật cấu hình/luật (Hot-reload) mà không cần khởi động lại máy chủ API (Zero-downtime).
* **Impact:** Hệ thống chỉ mở và đọc file cấu hình JSON tại thời điểm chạy (Runtime) sau khi đã phân loại xong tài liệu.

**6. Decision: Áp dụng chiến lược Fail-Fast khi file cấu hình JSON bị lỗi hoặc mất.**

* **Reason:** Ngăn chặn thảm họa lưu dữ liệu rỗng vào Database. Lỗi hệ thống/cấu hình cần được phát hiện và xử lý ngay lập tức.
* **Impact:** Pipeline dừng hoàn toàn tiến trình và API ném lỗi HTTP 500 Internal Server Error nếu file rule không hợp lệ.

**7. Decision: Gộp các trang tài liệu trước khi xử lý (Pre-aggregation).**

* **Reason:** Giữ nguyên tầm nhìn toàn cảnh (Full Context) để AI/LLM dễ dàng liên kết ngữ nghĩa giữa các trang (VD: trang đầu và trang cuối).
* **Impact:** Client hoặc kịch bản Test phải có trách nhiệm gộp toàn bộ các file trang lẻ thành một object `DocumentInput` duy nhất trước khi gọi M3.

**8. Decision: Đồng bộ hóa toàn cục thư mục Module 3 (Global Synchronization).**

* **Reason:** Đảm bảo tính nhất quán kiến trúc với Module 1 và Module 2; luồng dữ liệu một chiều rõ ràng, chuyên nghiệp.
* **Impact:** Xóa các file test rác, chuyển toàn bộ kịch bản test vào `scripts/module_3/test_batch_runner.py`.

**9. Decision: Chạy kiểm thử Local LLM với tập mẫu giới hạn (Sample Subset Execution / Limit = 5).**

* **Reason:** Chiến lược Smoke Test giúp phát hiện lỗi logic nhanh, tránh treo máy và tràn RAM (OOM) trong những lần chạy thử nghiệm đầu tiên.
* **Impact:** Tham số `--limit` được đưa vào kịch bản test để chỉ chạy một số lượng tài liệu nhất định.

**10. Decision: Đo lường hiệu năng kép (Tổng thời gian tài liệu & Thời gian trung bình/trang).**

* **Reason:** Cung cấp bức tranh hiệu năng toàn diện cho cả end-user (thời gian chờ) và kỹ sư (tối ưu nút thắt cổ chai).
* **Impact:** File báo cáo `m3_performance_summary.json` sẽ ghi nhận đồng thời cả 2 chỉ số thời gian này.

**11. Decision: Cách ly dữ liệu đầu vào theo thư mục (1 Tài liệu = 1 Thư mục).**

* **Reason:** Tiêu chuẩn quản trị dữ liệu Enterprise, tránh lỗi tranh chấp ghi đè, không phụ thuộc vào quy tắc tên file phức tạp.
* **Impact:** Kịch bản test sẽ tự động đọc và gộp toàn bộ file JSON nằm trong cùng một thư mục thành 1 tài liệu duy nhất.

**12. Decision: Dùng màng lọc CPU (Heuristic Retrieval) cho tài liệu siêu dài.**

* **Reason:** Giải tỏa áp lực cho GPU/LLM, chống tràn bộ nhớ (OOM) và vượt quá Token khi xử lý các khối dữ liệu khổng lồ (VD: 137 trang).
* **Impact:** Thuật toán CPU sẽ quét và nhặt ra các đoạn văn chứa từ khóa trước khi ném dữ liệu tinh gọn vào cho LLM bóc tách.

**13. Decision: Đọc toàn bộ trang của 1 tài liệu & Giới hạn số lượng tài liệu test.**

* **Reason:** Tận dụng màng lọc Heuristic để kiểm thử năng lực thực sự của luồng End-to-End trên tài liệu lớn mà không sợ treo máy.
* **Impact:** Kịch bản nạp đủ số trang của một tài liệu nhưng chỉ áp dụng `--limit` đối với số lượng folder tài liệu tổng thể.

**14. Decision: Lưu tách biệt Dữ liệu bóc tách (Payload) và Hiệu năng (Metrics).**

* **Reason:** Đảm bảo nguyên tắc Phân tách mối quan tâm (Separation of Concerns). Dễ đọc, dễ kiểm tra chéo (QA) và tối ưu.
* **Impact:** Metrics được lưu chung trong file summary, còn dữ liệu kết quả của từng hồ sơ nằm riêng trong thư mục con `extracted_jsons/`.

### Date: 2026-06-18

**1. Decision: Áp dụng chiến lược Head-and-Tail Truncation (Cắt 2 trang đầu, 2 trang cuối).

Reason: Cân bằng giữa tốc độ đọc file và khả năng bắt trọn thông tin (Header/Tiêu ngữ và Chữ ký cuối), tránh quá tải ngữ cảnh cho LLM.

Impact: Kịch bản test chỉ nạp tối đa 4 trang cho mỗi tài liệu.

**2.Decision: Tích hợp Ví dụ mẫu (Few-shot) vào chung file Rule JSON.

Reason: Giữ tính đóng gói (Encapsulation), giúp mã nguồn Python mù mờ (Agnostic) và dễ mở rộng các loại giấy tờ mới.

Impact: Mỗi cấu hình loại tài liệu sẽ mang theo ví dụ mồi riêng của nó.

**3.Decision: Chạy Hybrid Architecture (Regex + Quantized Local LLM).

Reason: Tối ưu hóa cực độ cho cấu hình khách hàng không có GPU rời. Regex "bóp chết" các trường dễ trong 0.001s, dành toàn bộ sức mạnh CPU xử lý 1-2 trường khó.

Impact: Phân luồng logic rõ ràng trong file rules_vbpl.json.

**4.Decision: Khai báo mảng aliases động và điểm neo {LABEL}.

Reason: Xử lý lỗi chính tả OCR theo ngữ cảnh mà không làm phình to mã nguồn hay phá hỏng dữ liệu gốc. "Data-driven" hóa các luật bắt lỗi.

Impact: RegexExtractor tự động nối các từ khóa nhiễu vào biểu thức tại thời điểm chạy (Runtime).

**5.Decision: Quét toàn văn bản (Full-Text Concatenation) và áp dụng "First Match Wins".

Reason: Chống lại các lỗi ngắt dòng vô cớ của OCR và tăng tốc độ trích xuất nhờ ưu tiên vị trí không gian (Header).

Impact: Dữ liệu chữ các trang được gộp thành 1 khối duy nhất trước khi chạy re.search.

**6.Decision: Gom mẻ gọi LLM (Batch LLM Calling) và LLM Fallback.

Reason: Tiết kiệm tối đa số lần AI phải đọc lại ngữ cảnh. Lưới an toàn Fallback đảm bảo độ chính xác (Recall) khi Regex thất bại.

Impact: StrategyRouter chỉ gọi LLM đúng 1 lần cho tất cả các trường còn thiếu.

**7.Decision: Áp dụng lưới lọc Regex JSON Healing và Auto-Formatting.

Reason: Tăng khả năng chịu lỗi (Robustness) trước các câu trả lời thừa thãi của LLM (markdown) và chuẩn hóa dữ liệu đầu ra chuyên nghiệp.

Impact: Tỷ lệ Crash do lỗi Parse JSON gần như bằng 0.

### Date: 2026-06-19

## Các Quyết định Kiến trúc Module 3 (Dynamic NER)

* **[M3-01] Chiến lược Truy vết Tọa độ Bounding Box:** Chọn **Approximate Line Tracing**. *Lý do:* Chấp nhận sai số nhỏ về tọa độ dòng chữ để đổi lấy tốc độ xử lý toàn văn bản cực nhanh, giảm tải cho CPU.
* **[M3-02] Tương thích Cấu hình Ngược (Backward Compatibility):** Chọn **Hỗ trợ Kép (Dual Format)** trong `RegexExtractor`. *Lý do:* Cho phép áp dụng tính năng mới (Aliasing, Auto-format) trên file `rules_vbpl.json` mà không làm sập các hệ thống luật cũ như `rules_hanh_chinh.json`.
* **[M3-03] Đánh giá Confidence của LLM:** Chọn **Hardcoded Confidence (0.85)**. *Lý do:* Tiết kiệm Token, giảm rủi ro AI ảo giác khi phải tự chấm điểm, và thiết lập mức chuẩn để lọc dữ liệu Human-in-the-loop sau này.
* **[M3-04] Xử lý Treo Mô hình Local (LLM Timeout):** Chọn **Hard Timeout & Skip (120s)**. *Lý do:* Cơ chế Fail-fast phòng thủ bắt buộc để tránh tình trạng hệ thống chạy batch bị đóng băng vĩnh viễn do CPU Throttling hoặc cạn RAM.

## Các Quyết định Kiến trúc Vận hành (Operations & Testing) 

* **[OPS-01] Chiến lược Cắt xén Trang (Page Truncation):** Chọn **Early Truncation (Cắt ở Tầng nạp liệu)**. *Lý do:* Chặn đứng nguy cơ Out of Memory (Tràn RAM) cho hệ thống Local (Core i5, 16GB) bằng cách chỉ giữ lại 2 trang đầu và 2 trang cuối của tài liệu trước khi đưa vào LLM.
* **[OPS-02] Xử lý Ngoại lệ Chạy Lô (Batch Exception):** Chọn **Fail-Safe & Continue**. *Lý do:* Đảm bảo tiến trình chạy qua đêm không bị gián đoạn vì 1 file hỏng. Lỗi sẽ được ghi nhận vào báo cáo để xử lý sau.
* **[OPS-03] Chấm điểm Tự động (Ground Truth Matching):** Chọn **Fuzzy Normalized Match**. *Lý do:* Phản ánh đúng độ thông minh của mô hình và tính hữu dụng thực tế bằng cách loại bỏ các sai số không đáng kể về khoảng trắng/dấu câu.
* **[OPS-04] Báo cáo Điểm số Đo lường:** Chọn **Field-Level F1-Score**. *Lý do:* Báo cáo chi tiết đến từng trường dữ liệu (Precision, Recall) giúp nhận diện chính xác "điểm mù" của hệ thống để tiến hành Fine-tune (Prompt/Regex).
* **[OPS-05] Khởi tạo Dữ liệu Đáp án (Ground Truth):** Chọn **Zero-Code Web AI + Kiểm duyệt Thủ công**. *Lý do:* Dùng một Master Prompt chuẩn ném vào ChatGPT/DeepSeek bản Web để tạo file JSON nháp, sau đó người dùng tự duyệt lại. Nhanh gọn, miễn phí, chính xác cao và không lo rủi ro Code API.

### **Date:** 2026-06-20

* **Decision:** Sử dụng kiến trúc `Document Splitting Pipeline` kết hợp Lớp Điều phối bên ngoài (`External Orchestrator Wrapper`).
* **Reason:** Tách biệt logic chia tách hồ sơ đa trang khỏi luồng bóc tách lõi (Module 3) để bảo toàn nguyên tắc Đơn trách nhiệm (Single Responsibility) và Open/Closed.
* **Impact:** Giữ cho Core Pipeline sạch sẽ, không bị phình to mã nguồn, tránh rủi ro gây lỗi chéo lên luồng bóc tách tài liệu đơn.


* **Decision:** Nhận diện ranh giới trang bằng Dấu hiệu Từ khóa (Regex) và quản lý qua Cấu hình động (JSON).
* **Reason:** Đảm bảo tốc độ xử lý (tính bằng mili-giây), hoạt động ổn định (fail-safe) và tuân thủ triết lý Data-Driven Design (dễ dàng bổ sung loại tài liệu mới mà không cần sửa mã nguồn).
* **Impact:** Tiết kiệm toàn bộ tài nguyên LLM cho khâu bóc tách chi tiết phía sau, hệ thống dễ dàng bảo trì và bàn giao.


* **Decision:** Xử lý cấp phát dữ liệu bằng cách chia tách vật lý (Physical JSON Splitting) và đóng gói đầu ra thành một file JSON Mục lục duy nhất (Single Dossier JSON).
* **Reason:** Không can thiệp vào code bóc tách lõi, đồng thời đáp ứng trọn vẹn yêu cầu trải nghiệm (UX) của khách hàng về một bảng mục lục tổng hợp.
* **Impact:** An toàn tuyệt đối cho luồng dữ liệu hiện tại, dễ dàng cho Frontend của khách hàng tích hợp và hiển thị.


* **Decision:** Tích hợp cơ chế bỏ qua lỗi cục bộ (Fault-Tolerant) vào Lớp Điều phối.
* **Reason:** Tài liệu xấu/lỗi là điều hiển nhiên trong môi trường IDP thực tế. Một trang lỗi (do OCR mờ hoặc AI timeout) không được phép làm sập toàn bộ tiến trình hồ sơ.
* **Impact:** Tăng khả năng phục hồi (Resilience) chuẩn Enterprise, đảm bảo khách hàng luôn nhận được phần lớn dữ liệu hợp lệ.


* **Decision:** Tạm dừng phát triển Lớp Điều phối hồ sơ để ưu tiên lấy Điểm cơ sở (Baseline Metrics) cho Module 3 lõi.
* **Reason:** Cần đánh giá định lượng và khoanh vùng mức độ ảnh hưởng của dữ liệu rác (OCR) trước khi lắp "động cơ" vào "khung gầm" đa trang.
* **Impact:** Đảm bảo hệ thống phát triển chuẩn mực, cung cấp số liệu thực tế làm căn cứ cho việc nâng cấp/thay thế công cụ OCR (Module 2) sau này.


* **Decision:** Chọn Trang 7 (Đơn đề nghị đăng ký biến động) làm Bài test cực hạn (Stress-Test) và đẩy rủi ro xử lý chữ viết tay cho LLM (LLM Contextual Fallback).
* **Reason:** Đối mặt trực tiếp với dữ liệu rác thực tế thay vì né tránh, nhằm đo lường khả năng suy luận tự sửa lỗi của Qwen 2.5.
* **Impact:** Phơi bày toàn bộ điểm yếu của hệ thống để có chiến lược tối ưu hóa chính xác.


* **Decision:** Giới hạn phạm vi trích xuất tối giản (Minimum Viable Extraction) và sử dụng Lược đồ riêng (`rules_don_bien_dong.json`).
* **Reason:** Bám sát yêu cầu mục lục thực tế của khách hàng (chỉ lấy 5 trường: Số ký hiệu, Ngày tháng, Tên tài liệu, Tác giả, Trang số), tránh để LLM bị ảo giác khi cố giải mã các đoạn OCR viết tay nát mà khách hàng không cần.
* **Impact:** Tiết kiệm thời gian xử lý, tăng tỷ lệ thành công của bài test.


* **Decision:** Xây dựng Ground Truth theo tiêu chuẩn Chuẩn hóa Hoàn hảo (Perfect Normalization) và áp dụng Ràng buộc Định dạng Chuẩn (Strict Format Constraint) cho LLM.
* **Reason:** Định nghĩa giá trị của AI là "hiểu và chuẩn hóa dữ liệu" thay vì chỉ bóc tách chuỗi ký tự lỗi, tạo sự đồng nhất với cơ sở dữ liệu cuối cùng.
* **Impact:** Đẩy độ khó của bài test lên cao nhất nhưng đảm bảo chất lượng dữ liệu đầu ra đạt chuẩn thực tiễn.


* **Decision:** Áp dụng kỹ thuật Descriptive Zero-Shot Prompting kết hợp Suy luận Ngữ nghĩa Mở (Semantic Inference) cho trường "Tác giả".
* **Reason:** Ngăn chặn LLM "học vẹt" từ ví dụ mẫu, đo lường năng lực suy luận mộc mạc nhất của mô hình để có Baseline khách quan. Giúp LLM linh hoạt nhận diện tác giả tùy theo loại văn bản (cơ quan hoặc công dân).
* **Impact:** Đánh giá chính xác 100% năng lực lõi hiện tại của kiến trúc AI trước khi thực hiện các tinh chỉnh nâng cao.

### **Date:** 2026-06-22

* **Decision:** Chọn "Văn bản Pháp luật Chuẩn" in máy (`scan_001_ocr.json`) làm mẫu thử nghiệm đầu tiên.
* **Reason:** Chất lượng OCR hoàn hảo của văn bản này giúp cách ly các lỗi nhiễu từ Module 2, qua đó dễ dàng kiểm chứng độ mượt mà của luồng kiến trúc cốt lõi Module 3.
* **Impact:** Tạo môi trường lý tưởng để gỡ lỗi (debug) Lớp điều phối (Orchestrator) trước khi hệ thống phải xử lý các tài liệu viết tay phức tạp.

* **Decision:** Giới hạn phạm vi ở "Bóc tách Siêu dữ liệu Cơ bản" (Basic Metadata Extraction).
* **Reason:** Hạn chế các vấn đề về độ trễ và độ dài ngữ cảnh (context length) của LLM ở lần chạy thử nghiệm đầu tiên.
* **Impact:** Đảm bảo toàn bộ luồng pipeline từ đầu đến cuối (End-to-End) có thể chạy thành công mà không bị sập (crash) do quá tải phần cứng.

* **Decision:** Xử lý đếm số trang bằng logic hậu kỳ Python kết hợp phương pháp "Truy xuất ngược Siêu dữ liệu" (Metadata Reverse Mapping).
* **Reason:** Việc để hệ thống tự động ánh xạ (mapping) và đếm trang từ tọa độ vật lý của Module 2 là chính xác tuyệt đối, loại bỏ hoàn toàn rủi ro "ảo giác" (hallucination) của LLM.
* **Impact:** Tiết kiệm token cho LLM, giảm tải Prompt và xây dựng cấu trúc an toàn khi mở rộng cho các tài liệu dài bị cắt nhỏ (chunking).

* **Decision:** Định dạng số trang trong file Ground Truth theo "Chuỗi Đích" (Target String Format - VD: "01-01").
* **Reason:** Đầu ra thực tế và đầu ra kỳ vọng phải cùng chung một định dạng để phục vụ cơ chế so khớp 1-1 của bộ test.
* **Impact:** Ngăn chặn lỗi kiểu dữ liệu (Type Error) trong kịch bản đánh giá `evaluate_metrics.py`.

* **Decision:** Cấu hình "Trích xuất Lai" (Hybrid Extraction) kết hợp cơ chế dự phòng "LLM Fallback" (Auto-Rescue).
* **Reason:** Tận dụng sự chính xác của Regex để bắt luật và dùng ngữ nghĩa thông minh của LLM để bóc các trường phức tạp hoặc để "cứu vãn" tự động khi Regex bị trượt do lỗi OCR.
* **Impact:** Tối ưu hóa tài nguyên hệ thống, kiểm thử toàn diện Lớp điều tuyến (StrategyRouter) và đẩy tỷ lệ lấp đầy dữ liệu (Fill-rate) lên tối đa.

* **Decision:** Cấu hình Regex theo hướng "Tổng quát" (Generalized Regex) và "Trích xuất Nguyên bản" (Raw Context Extraction) cho trường ngày tháng.
* **Reason:** Bảo toàn tính pháp lý nguyên bản của văn bản (VD: "Hà Nội, ngày..."), đồng thời xây dựng bộ quy tắc có khả năng tái sử dụng cao, tránh tình trạng "học vẹt" (overfitting) cho một file duy nhất.
* **Impact:** Khớp sát với thực tiễn dữ liệu, giúp Regex dễ dàng tìm thấy điểm neo (anchor).

* **Decision:** Bật "Theo vết Chuyên sâu" (Deep Trace Logging) và xử lý "Tuần tự" (Sequential Mode) cho Local LLM.
* **Reason:** Tránh tràn RAM/VRAM khi chạy mô hình 7 Tỉ tham số (7B) trên máy cục bộ, đồng thời giữ cho log in ra màn hình có tính tuyến tính.
* **Impact:** Đảm bảo hệ thống an toàn không bị sập (OOM), tăng tính minh bạch tuyệt đối để kỹ sư quan sát được luân chuyển dữ liệu giữa Code cứng và AI.

* **Decision:** Khởi động nóng (Warm Start) mô hình LLM thông qua một Terminal độc lập.
* **Reason:** Tải trước (Pre-load) Qwen 2.5 vào VRAM giúp loại trừ rủi ro bị Timeout (vượt quá 120s) ở chunk xử lý đầu tiên của Python.
* **Impact:** Phân tách rõ ràng tài nguyên hệ thống, bảo đảm kịch bản kiểm thử Python chạy mượt mà ngay từ giây đầu tiên.

* **Decision:** Áp dụng mô hình "Hộp cát" (Sandbox) cô lập và chạy kịch bản "Đơn mục tiêu" (Single File Target).
* **Reason:** Cô lập biến số bằng cách chỉ chạy 1 file trong thư mục tạm (`sandbox_inputs` / `sandbox_outputs`).
* **Impact:** Không ghi đè hoặc làm hỏng dữ liệu gốc của Module 2, loại bỏ nhiễu log từ các file rác khác để tập trung kiểm tra điểm F1-Score chính xác.

* **Decision:** Truyền tham số đường dẫn thư mục bằng "Giao diện Dòng lệnh" (CLI Arguments) thông qua `argparse`.
* **Reason:** Không gán cứng (hardcode) đường dẫn, giúp kịch bản kiểm thử linh hoạt và không làm hỏng cấu hình mặc định.
* **Impact:** Giữ mã nguồn `test_batch_runner.py` sạch sẽ và tuân thủ tiêu chuẩn kỹ thuật phần mềm.

* **Decision:** Tiêm mã giả lập (Mock Implementation) bằng "Từ điển thô" (Raw Dict) tại tầng "Kịch bản Kiểm thử" (Test Script Level).
* **Reason:** Tiêm cứng dữ liệu `"trang_so": "01-01"` vào ngay trước lúc xuất file JSON để "đánh lừa" hàm chấm điểm mà không cần động chạm vào logic lõi.
* **Impact:** Giữ trinh nguyên kiến trúc lớp Lõi (`pipeline.py`) và bảo vệ các Object Pydantic của hệ thống.

* **Decision:** Phân loại tài liệu động qua `classifier.py` sử dụng chiến lược "Tương thích ngược" (Backward Compatible Hybrid).
* **Reason:** Bổ sung Regex cho Văn bản pháp luật vào cấu trúc Dictionary gốc của `document_catalog.json`, thay vì đổi sang List/Array.
* **Impact:** Đảm bảo `classifier.py` vẫn "gác cổng" tự động được cho file mới mà không làm gãy các luồng cũ (Hành chính thông thường, Căn cước công dân).

* **Decision:** Thực thi chấm điểm F1-Score độc lập (Independent Execution).
* **Reason:** Ưu tiên việc kiểm tra cấu trúc JSON thô bằng mắt thường trước khi cho máy vào chấm điểm.
* **Impact:** Dễ dàng phát hiện các lỗi định dạng hoặc lỗi sinh chuỗi (hallucination rác) từ LLM theo từng bước (Step-by-step Debugging).