```markdown
# TÀI LIỆU CHUYỂN GIAO DỰ ÁN (PROJECT HANDOVER DOCUMENT)
**Tên dự án:** VN-Digitize-AIEngine (Hệ thống Xử lý & Bóc tách Tài liệu Thông minh)
**Vai trò phát triển:** AI Engineer / System Architect

---

## A. PRD (PRODUCT REQUIREMENTS DOCUMENT)

### 1. Mục tiêu cốt lõi (Core Vision)
Xây dựng một Data Pipeline tự động hóa hoàn toàn quy trình số hóa tài liệu tiếng Việt. Hệ thống có khả năng tiếp nhận ảnh scan thô, tiền xử lý, đọc chữ (OCR) và bóc tách thông tin phi cấu trúc thành dữ liệu JSON có cấu trúc (NER) với độ chính xác cao. Hệ thống được thiết kế theo hướng "Khớp nối lỏng" (Loose Coupling), cho phép tùy biến dễ dàng cho nhiều nghiệp vụ khác nhau (Hành chính pháp lý, Tòa án, Bảo hiểm...).

### 2. Các tính năng chính (Key Features)
* **Module 1 - Smart Preprocessing:** Tự động phát hiện vùng tài liệu, cắt mép (Crop), nắn thẳng (Deskew) bằng AI U2-Net, và lọc bỏ ảnh rỗng/lỗi.
* **Module 2 - Hybrid OCR Engine:** * Bỏ phiếu rẽ nhánh góc xoay 3 miền (Spatial Stratified Sampling).
  * Tích hợp PaddleOCR (Detection) và VietOCR (Recognition).
  * Thuật toán gom dòng thông minh (Heuristic Line Grouping) với ngưỡng động.
  * Tự động nhận diện số trang (Pagination) và lọc bỏ rác tọa độ (NaN filtering).
* **Module 3 - Dynamic Extraction & Routing:**
  * **Rule-based Router:** Phân loại tài liệu siêu tốc để rẽ nhánh bộ cấu hình tương ứng. Khước từ nghiêm ngặt (Strict Rejection) tài liệu rác.
  * **Dynamic Extractors:** Hỗ trợ nhiều chiến lược bóc tách (Regex, LayoutRegex, LLM Batch) điều khiển hoàn toàn qua file JSON cấu hình.
  * **Hybrid LLM Auto-Corrector:** Tự động sửa lỗi OCR/Chính tả với cơ chế Fallback linh hoạt giữa Cloud (Gemini) và Local (Ollama/Qwen).
  * **Validation Layer:** Kiểm duyệt dữ liệu đầu ra và kích hoạt Reflexion (Yêu cầu AI thử lại) nếu sai cấu trúc.

---

## B. TECHNICAL SPECS (ĐẶC TẢ KỸ THUẬT)

### 1. Công nghệ & Thư viện (Tech Stack)
* **Ngôn ngữ:** Python 3.x
* **Core Frameworks:** OpenCV, Numpy, Pydantic, FastAPI.
* **AI / Deep Learning:** PyTorch, PaddleOCR, VietOCR.
* **LLM Integration:** Google GenAI SDK (Gemini), OpenAI SDK (Tương thích Ollama Local).

### 2. Cấu trúc thư mục hiện tại (Project Structure)
Dự án được phân chia theo kiến trúc Micro-modules, chia tách rõ ràng giữa Core Logic và Scripts vận hành:

```text
VN-Digitize-AIEngine/
├── configs/                     (Chứa các file JSON cấu hình luật bóc tách)
├── shared_utils/                (Chứa Logger, Models dùng chung để tránh Magic Strings)
├── module_1_image_preprocessing/(Xử lý ảnh U2-Net)
├── module_2_core_ocr/           (Động cơ đọc chữ lai)
│   ├── engines/                 (Chứa Factory Pattern và các class OCR)
│   ├── ocr_pipeline.py
│   └── models.py                
├── module_3_dynamic_ner/        (Bóc tách dữ liệu)
│   ├── extractors/              (Chứa BaseExtractor, Regex, Layout, LLM)
│   ├── llm_engine/              (Chứa các Provider LLM, AutoCorrector, Retriever)
│   ├── router/                  (StrategyRouter định tuyến)
│   ├── validators/              (OutputValidator, FieldValidator)
│   ├── pipeline.py              (Luồng chạy chính ghép nối các thành phần)
│   └── api.py                   (FastAPI endpoint)
└── scripts/                     (Các kịch bản Test Batch Runner)

```

### 3. Quy tắc viết Code (Coding Conventions)

* **Nguyên tắc Đơn trách nhiệm (SRP):** Mỗi file/class chỉ đảm nhận một nhiệm vụ duy nhất.
* **Thiết kế Data-Driven:** Mọi logic nghiệp vụ (Từ khóa, Regex, System Prompt) bắt buộc phải nằm ở file JSON (vd: `rules_hanh_chinh.json`), tuyệt đối không Hardcode trong file Python.
* **Hợp đồng dữ liệu (Data Contracts):** Sử dụng `dataclass` và `Pydantic` (như `OrientationStatus`, `OcrResult`, `ExtractedField`) để ép kiểu dữ liệu chặt chẽ giữa các Module.
* **Bắt lỗi & Log:** Sử dụng `logger` tập trung, áp dụng "Chết nhanh" (Fail-fast) cho các lỗi môi trường và rẽ nhánh an toàn cho lỗi dữ liệu.

---

## C. CURRENT STATUS (TIẾN ĐỘ & CÔNG VIỆC TIẾP THEO)

### 1. Trạng thái hiện tại

* **Module 1:** Đã hoàn thiện và chạy ổn định.
* **Module 2:** Đã hoàn thiện. Vừa vượt qua bài Test Benchmark với 137 ảnh (Tốc độ ~18.9 FPS). Đã xử lý triệt để lỗi "Ghost Import", lỗi `NaN` rác, và bổ sung cơ chế đếm `page_number` dựa trên thứ tự file chuẩn (sorted loop).
* **Module 3:** Đã xây dựng xong bộ khung kiến trúc siêu linh hoạt (Extractors, Validators, LLM Providers, Router). Đã chốt phương án "Từ chối nghiêm ngặt" (Strict Rejection) đối với các tài liệu không xác định.

### 2. Hành động tiếp theo (Next Actions)

* Cần hoàn thiện cơ chế phân loại (Classification) đầu vào cho `StrategyRouter` của Module 3 để nó biết cách nạp đúng file `rules_*.json` khi nhận diện được loại tài liệu.

```

---
