# TÀI LIỆU KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)

**Dự án:** VN-Digitize-AIEngine (Hệ thống Xử lý & Bóc tách Tài liệu Thông minh)

---

## 1. Cấu trúc Module (Module Specifications)

Hệ thống được thiết kế theo kiến trúc Micro-modules, chia làm 3 thành phần chính hoạt động tuần tự (Pipeline) với mức độ khớp nối lỏng (Loose Coupling).

### Module 1: Smart Preprocessing (Tiền xử lý ảnh thông minh)

* **Chức năng:** Làm sạch và chuẩn hóa ảnh thô đầu vào. Tự động nhận diện vùng tài liệu, cắt mép (Crop), nắn thẳng hình ảnh (Deskew) và lọc bỏ các bức ảnh rỗng, ảnh nhiễu không đủ tiêu chuẩn để giảm tải cho hệ thống phía sau.

### Module 2: Hybrid OCR Engine (Động cơ OCR Lai)

* **Chức năng:** Trích xuất toàn văn bản (Full-text) và tọa độ (Bounding Box) từ hình ảnh.
* **Đặc tính kỹ thuật:**
* Áp dụng thuật toán rẽ nhánh góc xoay 3 miền (Spatial Stratified Sampling).
* Thuật toán gom dòng thông minh (Heuristic Line Grouping) sử dụng ngưỡng động.
* Màng lọc dữ liệu rác: Tự động loại bỏ các tọa độ có `text` rỗng hoặc `confidence` là `NaN`.
* Tự động đánh số trang (Pagination) thông qua cơ chế sắp xếp mảng tệp chuẩn Alphabet.



### Module 3: Dynamic NER & Extraction (Bóc tách Dữ liệu Động)

* **Chức năng:** Trích xuất thông tin phi cấu trúc thành dữ liệu JSON có cấu trúc dựa trên các tệp cấu hình động.
* **Thành phần cốt lõi:**
* **Document Classifier (Người gác cổng):** Phân loại biểu mẫu bằng thuật toán quét Regex siêu tốc trên các dòng đầu của tài liệu. Kích hoạt cơ chế "Từ chối nghiêm ngặt" (Strict Rejection) đối với tài liệu ngoại lệ.
* **Strategy Router:** Bộ định tuyến chịu trách nhiệm điều phối các thuật toán bóc tách (Regex, Layout Regex, LLM Batch).
* **Heuristic Retriever:** Màng lọc CPU đóng vai trò rút gọn ngữ cảnh (Context Reduction). Chỉ trích xuất các đoạn văn chứa từ khóa cấu hình nhằm giải tỏa áp lực bộ nhớ cho AI.
* **Auto-Corrector & Output Validator:** Sửa lỗi OCR lai và tự động sinh lớp Pydantic để kiểm duyệt định dạng đầu ra. Nếu sai, kích hoạt Reflexion để AI tự phản tư và sửa đổi.



---

## 2. Luồng Dữ liệu (Data Flow)

1. **Input Generation:** Dữ liệu ảnh đi qua Module 1 (Tiền xử lý) và Module 2 (OCR), xuất ra các tệp JSON cô lập theo cấu trúc thư mục (Directory-based Isolation: `1 Tài liệu = 1 Thư mục`).
2. **Pre-aggregation:** Kịch bản gom toàn bộ tệp JSON của nhiều trang thành một đối tượng `DocumentInput` duy nhất, duy trì tầm nhìn toàn cảnh (Full Context) cho tài liệu siêu dài.
3. **Classification & Routing:** `DocumentInput` đi qua lớp Classifier. Tên tệp cấu hình quy tắc (Rule) tương ứng được xác định.
4. **Lazy Loading:** Hệ thống nạp tệp cấu hình JSON tại Runtime (tải lười). Áp dụng chiến lược "Fail-Fast": Ném lỗi hệ thống ngay lập tức nếu tệp cấu hình hỏng hoặc bị thiếu.
5. **Extraction:**
* Các trường cơ bản được bóc tách trực tiếp bằng `RegexExtractor` hoặc `LayoutRegexExtractor`.
* Các trường phức tạp được lọc qua `HeuristicRetriever` để lấy đoạn văn chứa dữ liệu, sau đó chuyển tới LLM Provider để bóc tách hàng loạt.


6. **Validation:** Toàn bộ kết quả được `OutputValidator` ép kiểu.
7. **Output:** Hệ thống xuất kết quả bóc tách ra tệp Payload JSON riêng biệt, song song với việc lưu các chỉ số đo lường hiệu năng (Tổng thời gian, Thời gian/Trang) vào tệp Metrics Summary.

---

## 3. Công nghệ và Thư viện (Tech Stack)

* **Ngôn ngữ lõi:** Python 3.x
* **Xử lý ma trận & Thị giác máy tính:** OpenCV, Numpy.
* **Quản trị Hợp đồng Dữ liệu (Data Contracts):** Pydantic (Sử dụng `dataclass` và `create_model` động).
* **Giao tiếp LLM:** `google-genai` (Cloud API SDK), `openai` (Local LLM Wrapper tương thích Ollama).
* **Web Framework:** FastAPI, Uvicorn, Python-dotenv.

---

## 4. Mô hình AI (AI Models)

* **Computer Vision:** Mô hình U2-Net (Ứng dụng cho Background Removal & Document Detection).
* **Động cơ OCR:** Kết hợp PaddleOCR (Đảm nhiệm Text Detection) và VietOCR (Đảm nhiệm Text Recognition).
* **Mô hình Ngôn ngữ Lớn (LLM):**
* **Cloud Environment:** Google Gemini 2.5 Flash (Mô hình chính) và Gemini 2.0 Flash (Mô hình dự phòng - Fallback).
* **Local Environment:** Qwen 2.5:7b (Vận hành thông qua Ollama cho môi trường bảo mật nội bộ/Offline).



---

## 5. Cơ sở dữ liệu và Lưu trữ (Database & Storage)

* Hệ thống kiến trúc theo mô hình **Stateless Pipeline**, toàn bộ giao tiếp dữ liệu nội bộ được truyền trực tiếp qua bộ nhớ RAM.
* **Storage Pattern:** Sử dụng File System (Hệ thống tệp).
* **Master Catalog & Rules:** Lưu trữ cấu trúc phân nhánh dưới dạng tệp `JSON` tĩnh (`configs/document_catalog.json`, `configs/rules_*.json`).
* **Data Store:** Không sử dụng Database quan hệ hay Vector Database. Module 3 áp dụng thuật toán tìm kiếm Heuristic Retrieval bằng CPU trên văn bản thô, thay thế hoàn toàn nhu cầu về quy trình chuyển đổi vector (Embedding) và lưu trữ trên Vector DB.



---

## 6. Giao tiếp API và Backend (API & Backend)

* **Cấu trúc:** RESTful API được xây dựng bằng FastAPI.
* **Endpoint cốt lõi:** `POST /api/v1/extract`
* **Payload Convention:** Trả về dữ liệu chuẩn **JSend** (`status`, `data`, `metadata`).
* **Exception Handling Strategy (Quản lý Ngoại lệ):**
* `HTTP 200 OK`: Bóc tách hoàn tất.
* `HTTP 400 Bad Request`: Bắt lỗi `UnknownDocumentError` ngay tại tầng API, trả về khi tài liệu tải lên không thuộc danh mục hỗ trợ.
* `HTTP 500 Internal Server Error`: Kích hoạt báo động đỏ theo cơ chế Fail-Fast khi xảy ra lỗi nội tại (như thiếu tệp luật `JSON`, lỗi cấu hình).