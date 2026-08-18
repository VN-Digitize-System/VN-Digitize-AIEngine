# File Summaries: module_2_core_ocr

## `cli.py`
**Purpose:**
Cung cấp Command-Line Interface (CLI) để chạy Module OCR trên thư mục dữ liệu đầu vào, điều phối pipeline OCR, xuất kết quả JSON và Markdown, đồng thời xử lý serialization cho các object OCR phức tạp. 

**Inputs:**
* `--input_dir`
  * Thư mục chứa ảnh và dữ liệu từ Module 1.
* `--output_dir`
  * Thư mục lưu kết quả OCR.
* `--engine` (optional)
  * OCR Engine cần sử dụng; nếu không truyền sẽ lấy từ YAML config.
* File cấu hình `configs/module2_defaults.yaml`.  

**Outputs:**
* File `*_ocr.json`
  * Kết quả OCR đã serialize.
* File `*_layout.md`
  * Kết quả Markdown/Layout được sinh từ pipeline.
* Log và thông báo trạng thái thực thi. 

**Key Classes:**
* `EnhancedJSONEncoder`
  * JSON Encoder tùy chỉnh hỗ trợ:
    * NumPy arrays/scalars.
    * Dataclass objects.
    * Pydantic models.
    * Python objects thông thường. 

**Key Functions:**
* `main()`
  * Parse CLI arguments.
  * Nạp cấu hình YAML.
  * Khởi tạo `OcrPipeline`.
  * Xử lý toàn bộ thư mục đầu vào.
  * Xuất JSON và Markdown output.
* `EnhancedJSONEncoder.default()`
  * Chuyển đổi object OCR sang định dạng JSON serializable.  

**Dependencies:**
* `argparse`
* `os`
* `json`
* `dataclasses`
* `pathlib.Path`
* `numpy`
* `logging`
* `OcrPipeline`
* `OcrConfig` 

**Known Issues:**
* Đường dẫn YAML được hard-code (`configs/module2_defaults.yaml`).
* Chỉ loại bỏ trường `rotated_image`; các dữ liệu lớn khác vẫn có thể làm file JSON phình to.
* Logic trích xuất Markdown phụ thuộc vào nhiều cấu trúc dữ liệu (`dict`, dataclass, wrapper object), làm tăng độ phức tạp bảo trì.
* Không có cơ chế xử lý song song khi xử lý số lượng lớn tài liệu.
* Không có cơ chế retry hoặc phục hồi khi một file OCR thất bại giữa quá trình batch processing.   


## `config.py`
**Purpose:**
Quản lý cấu hình trung tâm cho Module OCR. Định nghĩa schema cấu hình bằng dataclass, nạp cấu hình từ YAML, cung cấp giá trị mặc định và kiểm tra sự tồn tại của model/weight cần thiết khi khởi động hệ thống. 

**Inputs:**
* File YAML cấu hình OCR.
* Đường dẫn model, weight và tham số runtime.
* Tham số cấu hình được truyền khi khởi tạo các dataclass. 

**Outputs:**
* `OcrConfig`
  * Cấu hình OCR hoàn chỉnh đã được ánh xạ từ YAML hoặc giá trị mặc định.
* Log cảnh báo nếu thiếu model hoặc thư mục cần thiết.  

**Key Classes:**
* `PaddleConfig`
  * Cấu hình PaddleOCR Detection.
* `VietOcrConfig`
  * Cấu hình VietOCR Recognition.
* `HeuristicSortingConfig`
  * Cấu hình thuật toán sắp xếp/gom dòng.
* `DeepDocConfig`
  * Cấu hình model Layout Analysis và TSR.
* `OcrConfig`
  * Root configuration object của toàn bộ OCR module. 

**Key Functions:**
* `validate_paths(base_dir)`
  * Kiểm tra sự tồn tại của model và thư mục cần thiết.
* `__post_init__()`
  * Khởi tạo cấu hình con mặc định.
  * Tự động validate đường dẫn model.
* `from_yaml(path)`
  * Nạp cấu hình từ YAML.
  * Ánh xạ thủ công sang hệ thống dataclass.   

**Dependencies:**
* `pathlib.Path`
* `yaml`
* `logging`
* `dataclasses` 

**Known Issues:**
* Chỉ cảnh báo khi thiếu model/weight, không chặn hệ thống khởi động.
* Mapping YAML sang dataclass được thực hiện thủ công, cần cập nhật code khi schema thay đổi.
* Không kiểm tra kiểu dữ liệu hoặc phạm vi giá trị của các tham số cấu hình.
* Nếu file YAML không tồn tại, hệ thống âm thầm sử dụng cấu hình mặc định.
* Đường dẫn model được xử lý tương đối theo vị trí file cấu hình, có thể gây nhầm lẫn khi thay đổi cấu trúc thư mục dự án.   

## `models.py`
**Purpose:**
Định nghĩa các data model cốt lõi dùng để trao đổi dữ liệu giữa các thành phần OCR. Cung cấp cấu trúc chuẩn cho bounding box, từ OCR và kết quả OCR hoàn chỉnh. 

**Inputs:**
* Dữ liệu OCR được tạo bởi OCR Engine:
  * Tọa độ bounding box.
  * Văn bản nhận dạng.
  * Confidence score.
  * Metadata bố cục tài liệu. 

**Outputs:**
* Các đối tượng dữ liệu chuẩn hóa:
  * `BoundingBox`
  * `OcrWord`
  * `OcrResult` 

**Key Classes:**
* `BoundingBox`
  * Lưu tọa độ 4 góc của vùng văn bản.
* `OcrWord`
  * Đại diện cho một đơn vị văn bản OCR.
  * Chứa text, confidence, bounding box và metadata layout.
* `OcrResult`
  * Kết quả OCR hoàn chỉnh của một trang/tài liệu.
  * Chứa danh sách từ OCR, full text và trạng thái xử lý. 

**Key Functions:**
* Không có.
* Module chỉ chứa các dataclass làm DTO/Data Model. 

**Dependencies:**
* `dataclasses`
* `typing`
  * `List`
  * `Tuple`
  * `Dict`
  * `Optional` 

**Known Issues:**
* Không có validation dữ liệu đầu vào.
* `metadata` sử dụng kiểu `Dict` tự do nên thiếu ràng buộc schema.
* `block_type` được lưu dưới dạng string, dễ phát sinh lỗi đánh máy hoặc không đồng nhất giữa các module.
* `OcrResult` được thiết kế chủ yếu cho tài liệu một trang (`page_number` mặc định = 1).
* Không có cơ chế versioning hoặc backward compatibility cho schema dữ liệu.  

## `ocr_pipeline.py`
**Purpose:** Orchestrates the core OCR workflow: reading metadata from Module 1, handling image rotation based on diagnostic flags, invoking the OCR engine factory, and executing the text recognition process.
**Inputs:** Directory path containing images and `m1_summary.json`.
**Outputs:** Dictionary containing `OcrResult` objects and the (potentially rotated) image arrays.
**Key Classes:** `OcrPipeline`.
**Key Functions:** `process_folder`.
**Dependencies:** `os`, `cv2`, `json`, `pathlib`, `typing`, `shared_utils.logger`, `.config`, `.engines.factory`, `.utils`, `shared_utils.models`.
**Known Issues:** None.

## `utils.py`
**Purpose:** Provides image manipulation utilities, specifically focusing on cropping rotated regions and determining the correct page orientation using an AI voting mechanism (Spatial Stratified Sampling).
**Inputs:** NumPy arrays (images), bounding boxes, `OrientationStatus`.
**Outputs:** Cropped/rotated NumPy arrays, rotation angles.
**Key Classes:** None.
**Key Functions:** `get_rotated_crop`, `auto_rotate_page`.
**Dependencies:** `cv2`, `numpy`, `math`, `shared_utils.models`.
**Known Issues:** None.

## `visualizer.py`
**Purpose:**
Cung cấp tiện ích trực quan hóa kết quả OCR bằng cách vẽ bounding box và nhãn phân loại lên ảnh, hỗ trợ debug và đánh giá chất lượng OCR/Layout Analysis. 

**Inputs:**
* `image: np.ndarray`
  * Ảnh gốc cần hiển thị kết quả.
* `ocr_result: OcrResult`
  * Kết quả OCR chứa danh sách từ, bounding box, confidence và block type.
* `output_path`
  * Đường dẫn lưu ảnh đã được annotate (tùy chọn).  

**Outputs:**
* `np.ndarray`
  * Ảnh đã được vẽ bounding box và nhãn.
* Có thể lưu ảnh xuống file nếu cung cấp đường dẫn đầu ra. 

**Key Classes:**
* Không có (Utility Function Module).

**Key Functions:**
* `draw_ocr_results(image, ocr_result, output_path)`
  * Vẽ polygon bounding box.
  * Hiển thị confidence và block type.
  * Áp dụng màu khác nhau cho từng loại block.
  * Lưu ảnh kết quả nếu được yêu cầu. 

**Dependencies:**
* `opencv (cv2)`
* `numpy`
* `pathlib.Path`
* `OcrResult` 

**Known Issues:**
* Phụ thuộc vào thuộc tính `block_type`; nhãn không xác định sẽ dùng màu mặc định.
* Không xử lý trường hợp bounding box bị lỗi hoặc thiếu điểm tọa độ.
* Nhãn hiển thị có thể chồng lấn khi các box nằm quá gần nhau.
* Chỉ phục vụ mục đích trực quan hóa, không tham gia vào pipeline OCR chính.
* Việc lưu file không kiểm tra quyền ghi hoặc lỗi đường dẫn đầu ra.  

---
# File Summaries: module_2_core_ocr/engines
## `base_engine.py`
**Purpose:**
Định nghĩa interface/contract chuẩn cho mọi OCR Engine trong hệ thống. Đảm bảo các OCR plugin triển khai cùng một phương thức xử lý ảnh và trả về kết quả OCR theo định dạng thống nhất. 

**Inputs:**
* `image: np.ndarray`
  * Ảnh đầu vào cần thực hiện OCR. 

**Outputs:**
* `OcrResult`
  * Kết quả OCR chuẩn hóa của hệ thống. 

**Key Classes:**
* `BaseOcrEngine`
  * Abstract Base Class (ABC) cho toàn bộ OCR Engine. 

**Key Functions:**
* `process_image(image)`
  * Hàm trừu tượng bắt buộc mọi OCR Engine phải triển khai.
  * Nhận ảnh đầu vào và trả về kết quả OCR chuẩn hóa. 

**Dependencies:**
* `abc.ABC`
* `abc.abstractmethod`
* `numpy`
* `OcrResult` (module_2_core_ocr.models) 

**Known Issues:**
* Chỉ định nghĩa interface, không chứa logic OCR thực tế.
* Không quy định cách xử lý lỗi, timeout hoặc retry cho OCR Engine.
* Chất lượng OCR phụ thuộc hoàn toàn vào các lớp kế thừa.
* Không có cơ chế validation đầu vào hoặc đầu ra ở tầng interface. 

## `factory.py`
**Purpose:**
Factory quản lý và khởi tạo OCR Engine theo cơ chế plugin. Sử dụng registry tường minh và lazy loading để hỗ trợ nhiều OCR Engine (PaddleVietOCR, DeepDoc, ...) mà không cần import toàn bộ hệ thống khi khởi động. 

**Inputs:**
* `engine_name`
  * Tên OCR Engine cần khởi tạo.
* `config`
  * Cấu hình được truyền vào constructor của Engine. 

**Outputs:**
* Instance của lớp kế thừa `BaseOcrEngine`.
* Ném `ValueError` nếu engine không tồn tại.
* Dừng chương trình (`SystemExit`) nếu không thể import engine.  

**Key Classes:**
* `OcrEngineFactory`
  * Registry trung tâm quản lý toàn bộ OCR Engine của hệ thống. 

**Key Functions:**
* `get_engine(engine_name, config)`
  * Kiểm tra registry.
  * Lazy-load module tương ứng.
  * Khởi tạo OCR Engine.
  * Fail-fast nếu thiếu dependency hoặc plugin không khả dụng. 

**Dependencies:**
* `importlib`
* `BaseOcrEngine`
* `shared_utils.logger`
* OCR Engine plugins:
  * `PaddleVietOcrEngine`
  * `DeepdocEngine`  

**Known Issues:**
* Registry được khai báo thủ công, cần sửa code mỗi khi thêm engine mới.
* Chỉ bắt lỗi `ImportError`; các lỗi khởi tạo khác sẽ được đẩy ra ngoài.
* Khi import thất bại, toàn bộ ứng dụng bị dừng thay vì fallback sang engine khác.
* Phụ thuộc vào chuỗi đường dẫn class trong registry, dễ bị lỗi khi refactor package/module.
* Hiện chưa hỗ trợ cơ chế auto-discovery plugin hoặc đăng ký động runtime.  


## `paddle_vietocr.py`
**Purpose:**
Triển khai OCR Engine lai kết hợp **PaddleOCR (Text Detection)** và **VietOCR (Text Recognition)**. Thực hiện phát hiện vùng văn bản, sắp xếp theo thứ tự đọc tự nhiên, nhận dạng chữ theo lô (batch) và trả về kết quả OCR chuẩn hóa.  

**Inputs:**
* `config`
  * Cấu hình OCR gồm PaddleOCR, VietOCR, GPU và heuristic sorting.
* `image: np.ndarray`
  * Ảnh đầu vào cần thực hiện OCR.  

**Outputs:**
* `OcrResult`
  * Danh sách từ OCR (`OcrWord`), full text, trạng thái thành công/thất bại và thông tin lỗi nếu có. 

**Key Classes:**
* `PaddleVietOcrEngine`
  * OCR Engine chính của hệ thống theo kiến trúc Detect → Sort → Recognize. 

**Key Functions:**
* `__init__(config)`
  * Khởi tạo PaddleOCR detector và VietOCR recognizer.
* `_sort_and_group_boxes(boxes)`
  * Gom các box thành dòng bằng ngưỡng động dựa trên chiều cao trung vị.
  * Sắp xếp theo thứ tự đọc từ trên xuống dưới, trái sang phải.
* `process_image(image)`
  * Detect text boxes.
  * Sắp xếp và gom dòng.
  * Crop vùng văn bản.
  * Batch recognition bằng VietOCR.
  * Chuyển đổi kết quả sang `OcrResult`.  

**Dependencies:**
* `PaddleOCR`
* `VietOCR Predictor`
* `numpy`
* `opencv-python (cv2)`
* `Pillow`
* `BaseOcrEngine`
* `OcrResult`
* `OcrWord`
* `BoundingBox`
* `get_rotated_crop`
* `shared_utils.logger` 

**Known Issues:**
* Heuristic sắp xếp theo dòng có thể hoạt động không chính xác với tài liệu nhiều cột hoặc bố cục phức tạp.
* Chất lượng OCR phụ thuộc mạnh vào chất lượng detection của PaddleOCR.
* Confidence được lấy trực tiếp từ VietOCR, không có bước calibration hoặc hậu kiểm.
* Các kết quả có text rỗng hoặc confidence không hợp lệ sẽ bị loại bỏ hoàn toàn.
* Khi xảy ra exception, toàn bộ ảnh bị đánh dấu thất bại thay vì trả về kết quả OCR một phần.
* Batch recognition giúp tăng tốc nhưng có thể tiêu tốn nhiều bộ nhớ với số lượng box lớn.   

## `deepdoc_engine.py`
**Purpose:**
Triển khai OCR Engine dựa trên DeepDoc. Kết hợp **Layout Detection**, **Table Structure Recognition (TSR)** và **OCR Recognition** để phân tích bố cục tài liệu, nhận dạng bảng biểu, trích xuất văn bản và sinh Markdown có cấu trúc.  

**Inputs:**
* `config`
  * Cấu hình DeepDoc và các model vendor.
* `image: np.ndarray`
  * Ảnh tài liệu đầu vào cần OCR/Layout Analysis.  

**Outputs:**
* `OcrResult`
  * Chứa:
    * `words`
    * `full_text`
    * `markdown_text`
    * trạng thái thành công/thất bại.
* Trả về lỗi chuẩn hóa khi quá trình phân tích thất bại. 

**Key Classes:**
* `DeepdocEngine`
  * OCR Engine chính sử dụng DeepDoc Vendor.
* Kế thừa từ `BaseOcrEngine`. 

**Key Functions:**
* `convert_html_table_to_md(html_str)`
  * Chuyển HTML bảng từ TSR thành Markdown table.
* `build_markdown_from_words(words_list, img_w, img_h)`
  * Gom cụm theo vị trí không gian và dựng Markdown có cấu trúc.
* `__init__(config)`
  * Khởi tạo LayoutRecognizer, TableStructureRecognizer và OCR engine.
* `process_image(image)`
  * Layout Detection.
  * Table Recognition.
  * OCR từng block.
  * Fallback OCR toàn ảnh nếu không phát hiện layout.
  * Sinh `full_text` và `markdown_text`.    

**Dependencies:**
* `numpy`
* `re`
* `logging`
* `pathlib`
* `LayoutRecognizer`
* `TableStructureRecognizer`
* `OCR`
* `BaseOcrEngine`
* `OcrResult`
* `OcrWord`
* `BoundingBox`
* DeepDoc Vendor Package (`deepdoc_vendor`)  

**Known Issues:**
* Thao tác chỉnh sửa `sys.path` và thay đổi thư mục làm việc (CWD) để import vendor làm tăng rủi ro side-effect giữa các module. 
* Markdown được dựng bằng heuristic khoảng cách X/Y nên có thể không chính xác với tài liệu nhiều cột hoặc bố cục phức tạp. 
* Khi Layout Detector phát hiện sai block, toàn bộ OCR downstream có thể bị ảnh hưởng.
* OCR trên block văn bản gộp nhiều dòng thành một chuỗi bằng ký tự xuống dòng, có thể làm mất cấu trúc gốc. 
* Fallback OCR toàn ảnh chỉ được kích hoạt khi không tìm thấy bất kỳ block nào, không hỗ trợ fallback từng vùng lỗi. 
* Chứa lệnh `print()` debug trực tiếp trong production flow thay vì sử dụng logger. 
* Khi xảy ra exception, toàn bộ kết quả bị hủy và trả về trạng thái thất bại thay vì giữ lại dữ liệu đã xử lý được. 

 


