# File Summaries: module_2_core_ocr

## `cli.py`
**Purpose:** Provides a Command Line Interface (CLI) to orchestrate batch OCR processing using the `OcrPipeline`.
**Inputs:** Command line arguments (`--input_dir`, `--output_dir`, `--engine`).
**Outputs:** JSON files containing OCR results for each processed image, saved to the output directory.
**Key Classes:** `EnhancedJSONEncoder`.
**Key Functions:** `main`.
**Dependencies:** `argparse`, `os`, `json`, `dataclasses`, `pathlib`, `.ocr_pipeline`, `.config`.
**Known Issues:** None.

## `config.py`
**Purpose:** Defines configuration data classes for the OCR engine, including parameters for PaddleOCR, VietOCR, and heuristic sorting. Supports loading from YAML.
**Inputs:** YAML file path.
**Outputs:** `OcrConfig` instance.
**Key Classes:** `PaddleConfig`, `VietOcrConfig`, `HeuristicSortingConfig`, `OcrConfig`.
**Key Functions:** `OcrConfig.from_yaml`, `OcrConfig.__post_init__`.
**Dependencies:** `dataclasses`, `pathlib`, `yaml`.
**Known Issues:** None.

## `models.py`
**Purpose:** Defines data structures (dataclasses) to represent OCR outputs, ensuring a standardized data contract.
**Inputs:** None.
**Outputs:** None.
**Key Classes:** `BoundingBox`, `OcrWord`, `OcrResult`.
**Key Functions:** None.
**Dependencies:** `dataclasses`, `typing`.
**Known Issues:** None.

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
**Purpose:** Renders OCR bounding boxes and confidence scores onto images for debugging and visualization.
**Inputs:** Original image (NumPy array), `OcrResult`, output file path.
**Outputs:** NumPy array (annotated image) and saved image file.
**Key Classes:** None.
**Key Functions:** `draw_ocr_results`.
**Dependencies:** `cv2`, `numpy`, `.models`.
**Known Issues:** None.

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
Factory chịu trách nhiệm khởi tạo OCR Engine theo tên được cấu hình. Hỗ trợ kiến trúc plugin thông qua registry và lazy loading để chỉ nạp engine khi thực sự cần sử dụng. 

**Inputs:**
* `engine_name`
  * Tên OCR Engine cần khởi tạo.
* `config`
  * Cấu hình truyền cho OCR Engine khi khởi tạo. 

**Outputs:**
* Instance của lớp kế thừa `BaseOcrEngine`.
* Ném exception hoặc dừng hệ thống nếu engine không hợp lệ hoặc không thể import. 

**Key Classes:**
* `OcrEngineFactory`
  * Factory quản lý registry và tạo OCR Engine động. 

**Key Functions:**
* `get_engine(engine_name, config)`
  * Kiểm tra registry.
  * Lazy-load module OCR tương ứng.
  * Khởi tạo và trả về OCR Engine.
  * Fail-fast khi môi trường hoặc dependency bị lỗi. 

**Dependencies:**
* `importlib`
* `BaseOcrEngine`
* `shared_utils.logger`
* Các OCR Engine được đăng ký trong `_REGISTRY` (ví dụ: Paddle + VietOCR).  

**Known Issues:**
* Mọi OCR Engine mới phải được thêm thủ công vào `_REGISTRY`.
* Chỉ xử lý lỗi `ImportError`; các lỗi khởi tạo khác từ engine sẽ được truyền thẳng ra ngoài.
* Khi import thất bại, hệ thống dừng hoàn toàn bằng `SystemExit`.
* Registry hiện phụ thuộc vào chuỗi đường dẫn class, dễ phát sinh lỗi khi refactor package hoặc đổi tên module.  

## `paddle_vietocr.py`

**Purpose:**
Triển khai OCR Engine lai (Hybrid OCR) kết hợp **PaddleOCR Detection** và **VietOCR Recognition**. Chịu trách nhiệm phát hiện vùng chữ, sắp xếp theo thứ tự đọc, nhận dạng văn bản và trả về kết quả OCR chuẩn hóa.  

**Inputs:**
* `config`
  * Cấu hình PaddleOCR, VietOCR, GPU và heuristic sorting.
* `image: np.ndarray`
  * Ảnh đầu vào cần OCR.  

**Outputs:**
* `OcrResult`
  * Chứa danh sách từ nhận dạng (`OcrWord`), văn bản đầy đủ và trạng thái xử lý.
* Trả về kết quả lỗi chuẩn hóa nếu OCR thất bại. 

**Key Classes:**
* `PaddleVietOcrEngine`
  * OCR Engine chính sử dụng kiến trúc Detect → Sort → Recognize. 

**Key Functions:**
* `__init__(config)`
  * Khởi tạo PaddleOCR detector và VietOCR recognizer.
* `_sort_and_group_boxes(boxes)`
  * Gom box theo dòng bằng heuristic động dựa trên chiều cao trung vị.
  * Sắp xếp theo thứ tự đọc từ trên xuống dưới, trái sang phải.
* `process_image(image)`
  * Detect text box.
  * Sắp xếp/gom dòng.
  * Crop từng vùng chữ.
  * Batch recognition bằng VietOCR.
  * Đóng gói kết quả OCR chuẩn hóa.  

**Dependencies:**
* `PaddleOCR`
* `VietOCR Predictor`
* `numpy`
* `opencv (cv2)`
* `PIL`
* `BaseOcrEngine`
* `OcrResult`
* `OcrWord`
* `BoundingBox`
* `get_rotated_crop`
* `shared_utils.logger` 

**Known Issues:**
* Thứ tự đọc phụ thuộc heuristic grouping, có thể sai với tài liệu nhiều cột hoặc bố cục phức tạp.
* Sử dụng toàn bộ box detection từ PaddleOCR nên chất lượng nhận dạng phụ thuộc mạnh vào bước detection.
* Bounding box được giữ nguyên từ detector, không hiệu chỉnh sau recognition.
* Bỏ qua các kết quả có confidence không hợp lệ hoặc text rỗng, có thể làm mất dữ liệu OCR yếu.
* Khi xảy ra lỗi bất kỳ, toàn bộ OCR request được đánh dấu thất bại thay vì trả về kết quả một phần.
* Hiệu năng phụ thuộc đáng kể vào GPU khi xử lý batch recognition lớn.   


