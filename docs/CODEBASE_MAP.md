# Codebase Map: VN-Digitize-AIEngine

## 1. Project Overview
**VN-Digitize-AIEngine** là một hệ thống xử lý tài liệu thông minh (Intelligent Document Processing - IDP). Dự án được thiết kế theo kiến trúc Data Pipeline bao gồm nhiều giai đoạn (multi-stage), nhằm mục đích tự động hóa hoàn toàn quy trình số hóa tài liệu: từ khâu tiếp nhận ảnh thô, làm sạch ảnh, nhận dạng chữ viết (OCR), cho đến việc bóc tách thông tin phi cấu trúc (Dynamic NER) thành dữ liệu có cấu trúc. 

Kiến trúc hệ thống đề cao tính module hóa (Modularity), cho phép phát triển, kiểm thử và nâng cấp từng thành phần một cách độc lập.

## 2. Folder Structure
Dưới đây là cấu trúc phân tầng cấp cao của hệ thống:

```text
VN-Digitize-AIEngine/
├── configs/                  # Cấu hình toàn cục & Registry Schema
├── docs/                     # Tài liệu thiết kế & quản lý dự án
├── logs/                     # Nhật ký hoạt động của hệ thống
├── module_1_image_preprocessing/ # Tầng 1: Tiền xử lý ảnh
├── module_2_core_ocr/            # Tầng 2: Nhận dạng ký tự quang học
├── module_3_dynamic_ner/         # Tầng 3: Bóc tách thực thể động (NER)
├── scripts/                  # Kịch bản chạy & Kiểm thử (Test Runners)
└── shared_utils/             # Tiện ích dùng chung toàn hệ thống

```

## 3. Module Responsibilities

### Các Module Lõi (Core Modules)

* **`module_1_image_preprocessing/` (Tiền xử lý ảnh)**
* *Vai trò:* Chịu trách nhiệm làm sạch và chuẩn hóa dữ liệu hình ảnh đầu vào trước khi đưa vào OCR.
* *Thành phần chính:* Phát hiện vùng văn bản (`_detect.py`), cắt góc và nắn chỉnh độ nghiêng (`_crop_deskew.py`), cùng các bộ lọc nâng cao chất lượng ảnh (`_enhance.py`).


* **`module_2_core_ocr/` (Động cơ OCR)**
* *Vai trò:* Trích xuất văn bản (Text) và tọa độ (Bounding Box) từ hình ảnh đã được làm sạch.
* *Thành phần chính:* Quản lý luồng chạy OCR (`ocr_pipeline.py`) và tích hợp các engine nhận dạng mạnh mẽ thông qua Factory Pattern (`engines/factory.py`, `engines/paddle_vietocr.py`).


* **`module_3_dynamic_ner/` (Bóc tách thông tin)**
* *Vai trò:* Động cơ "não bộ" của hệ thống, thực hiện bóc tách các trường dữ liệu cụ thể dựa trên luật hoặc AI.
* *Thành phần chính:* * `router/`: Bộ định tuyến phân loại tài liệu và quyết định chiến lược bóc tách.
* `extractors/`: Chứa các thuật toán bóc tách tốc độ cao dựa trên vị trí và biểu thức chính quy (Rule-based).
* `llm_engine/`: Động cơ gọi AI (Local LLM, Gemini) để xử lý các trường ngữ nghĩa phức tạp và tự động sửa lỗi.
* `validators/`: Lớp màng lọc đối chiếu định dạng (Pydantic) đảm bảo đầu ra JSON tuân thủ Schema.





### Các Module Phụ trợ (Supporting Modules)

* **`shared_utils/`**: Cung cấp các công cụ tiện ích cốt lõi được sử dụng xuyên suốt các module (như hệ thống logging đồng nhất, các model Pydantic dùng chung).
* **`configs/`**: Chứa các file YAML/JSON định nghĩa tham số mặc định cho từng module và hệ thống định tuyến (Schema Registry), giúp tách biệt cấu hình khỏi mã nguồn (Data-Driven Design).
* **`scripts/`**: Chứa các file thực thi (Runner) dùng để chạy kiểm thử hàng loạt (Batch Testing) hoặc kích hoạt các tiến trình độc lập, giúp cô lập môi trường test cho từng module.
* **`docs/`**: Nơi lưu trữ bộ nhớ dự án, bao gồm các quyết định kiến trúc (`DECISIONS.md`), tiến độ (`PROGRESS.md`) và bản đồ code này.

## 4. Data Flow

Luồng dữ liệu của VN-Digitize-AIEngine tuân thủ mô hình ống nước (Pipeline) một chiều, đảm bảo tính nhất quán qua từng giai đoạn:

1. **Ingestion & Stage 1:** Ảnh tài liệu thô (Raw Image) $\rightarrow$ `module_1` $\rightarrow$ Ảnh đã nắn chỉnh, làm sạch (Processed Image).
2. **Stage 2:** Processed Image $\rightarrow$ `module_2` $\rightarrow$ Dữ liệu ký tự thô kèm tọa độ không gian (OCR Raw Text & Bounding Boxes).
3. **Stage 3:** OCR Data $\rightarrow$ `module_3` $\rightarrow$ Phân loại $\rightarrow$ Định tuyến (Regex/LLM) $\rightarrow$ Trích xuất $\rightarrow$ Xác thực $\rightarrow$ **Cấu trúc JSON cuối cùng (Structured Data).**

```

```