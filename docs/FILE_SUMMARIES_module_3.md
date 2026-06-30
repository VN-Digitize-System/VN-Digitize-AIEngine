# File Summaries: module_3_dynamic_ner/configs

## `document_catalog.json`
Purpose: Đóng vai trò là sổ đăng ký trung tâm (Registry) để phân loại tài liệu đầu vào dựa trên tập hợp Regex và ánh xạ chúng đến các file cấu hình tương ứng. Sử dụng cấu trúc Dictionary giúp giữ tính tương thích ngược với các luồng cũ.
Inputs: None (Static JSON file).
Outputs: Định nghĩa danh mục ánh xạ phân loại (ví dụ: van_ban_phap_luat trỏ đến rules_vbpl.json).
Key Classes: N/A.
Key Functions: N/A.
Dependencies: Được tiêu thụ trực tiếp bởi classifier.py ở tầng định tuyến.
Known Issues: None (Kỹ thuật dùng dấu . trong Regex giúp chống lỗi OCR khá an toàn).

## `regex_rules.json`
**Purpose:** Serves as a global, reusable dictionary of standard regular expressions for common entities like dates, ID cards (CCCD), tax codes, phone numbers, and emails.
**Inputs:** None (Static configuration file).
**Outputs:** Arrays of regex strings for generalized text matching.
**Key Classes:** N/A.
**Key Functions:** N/A.
**Dependencies:** Can be referenced by base extraction logic.
**Known Issues:** None.

## `rules_hanh_chinh.json`
**Purpose:** Defines the legacy extraction schema for administrative and legal documents (`hanh_chinh_phap_ly`).
**Inputs:** None (Static configuration file).
**Outputs:** Defines fields, extraction methods (`keyword`, `layout_regex`, `regex`, `llm_batch`), and validation rules (e.g., `not_empty`, `exact_length`).
**Key Classes:** N/A.
**Key Functions:** N/A.
**Dependencies:** Compatible with the older `BaseExtractor` and `LayoutRegexExtractor` architecture.
**Known Issues:** Uses the older `patterns` array structure instead of the new `{LABEL}` and `aliases` injection format.

## `rules_vbpl.json`
**Purpose:**
Cấu hình trích xuất dữ liệu cho nhóm tài liệu **Văn bản pháp luật (VBPL)**. Định nghĩa danh sách field cần lấy, phương pháp trích xuất, regex, alias OCR và quy tắc fallback sang LLM. 

**Inputs:**
* Nội dung tài liệu VBPL đã được OCR.
* Được nạp động bởi `DocumentPipeline` sau khi tài liệu được classifier nhận diện là VBPL. 

**Outputs:**
* Cấu hình `fields` dùng cho extractor và router.
* Metadata hướng dẫn LLM hoặc RegexExtractor thực hiện bóc tách dữ liệu. 

**Key Classes:**
* Không có (JSON Configuration File).

**Key Functions:**
* Không có.
* Chứa cấu hình cho các field:
  * `co_quan_ban_hanh`
  * `so_hieu_van_ban`
  * `ngay_thang_ban_hanh`
  * `ten_loai_van_ban` 

**Dependencies:**
* `DocumentPipeline`
* `StrategyRouter`
* `RegexExtractor`
* LLM Provider (Gemini hoặc Local LLM)
* `document_catalog.json` để được định tuyến đúng loại tài liệu. 

**Known Issues:**
* Regex được thiết kế cho định dạng VBPL chuẩn, có thể giảm độ chính xác với văn bản OCR nhiễu nặng hoặc bố cục bất thường.
* Alias OCR hiện chỉ bao phủ một số biến thể lỗi phổ biến.
* Prompt sửa lỗi trong field `ten_loai_van_ban` phụ thuộc chất lượng suy luận của LLM.
* Nếu cấu hình field, regex hoặc alias sai, toàn bộ pipeline sẽ trích xuất sai nhưng không tự phát hiện được lỗi cấu hình nghiệp vụ.  

---

# File Summaries: module_3_dynamic_ner/extractors

## `base_extractor.py`
**Purpose:** Defines the abstract base class and standard data contract for all information extraction algorithms in Module 3.
**Inputs:** Field name (string), configuration rules (dictionary).
**Outputs:** N/A (Abstract class).
**Key Classes:** `BaseExtractor`.
**Key Functions:** `extract` (abstract method).
**Dependencies:** `abc`, `schemas.template_schema`.
**Known Issues:** None.

## `layout_regex_extractor.py`
**Purpose:** Extracts information by applying regular expressions strictly within predefined spatial boundaries (relative X/Y percentages) to prevent false positives in structured documents.
**Inputs:** `DocumentInput` object containing parsed lines and bounding boxes.
**Outputs:** `ExtractedField` object containing the matched text and bounding box, or `None`.
**Key Classes:** `LayoutRegexExtractor`.
**Key Functions:** `extract`.
**Dependencies:** `re`, `extractors.base_extractor`, `schemas.template_schema`.
**Known Issues:** Processes text line-by-line; vulnerable to extraction failures if the target text is split across multiple lines due to OCR formatting errors.

## `regex_extractor.py`

**Purpose:**
Extractor dựa trên Regex dùng để bóc tách dữ liệu từ văn bản OCR. Hỗ trợ cả cấu hình rule cũ và mới, xử lý alias OCR, truy vết vị trí dòng dữ liệu và trả về kết quả chuẩn hóa. 

**Inputs:**
* `field_name`
  * Tên field cần trích xuất.
* `config`
  * Cấu hình regex, alias, patterns.
* `DocumentInput document`
  * Tài liệu OCR chứa text, bounding box và page number.  

**Outputs:**
* `ExtractedField`
  * Kết quả trích xuất kèm confidence, tọa độ và số trang.
* `None`
  * Khi không tìm thấy dữ liệu phù hợp. 

**Key Classes:**
* `RegexExtractor`
  * Extractor chính sử dụng Regex matching để lấy dữ liệu từ tài liệu. 

**Key Functions:**
* `__init__(field_name, config)`
  * Nạp và biên dịch regex từ cấu hình.
  * Hỗ trợ cả rule format cũ và mới.
* `_compile_and_add(pattern_str)`
  * Compile regex và kiểm tra lỗi fail-fast.
* `_compress_whitespace(text)`
  * Chuẩn hóa khoảng trắng OCR.
* `_auto_format_output(text)`
  * Làm sạch dữ liệu sau khi match.
* `extract(document)`
  * Tìm dữ liệu bằng Regex.
  * Truy vết dòng nguồn.
  * Đóng gói thành `ExtractedField`.  

**Dependencies:**
* `re`
* `BaseExtractor`
* `DocumentInput`
* `ExtractedField`
* Rule JSON chứa regex, aliases hoặc patterns. 

**Known Issues:**
* Áp dụng chiến lược "First Match Wins", có thể bỏ qua kết quả tốt hơn xuất hiện phía sau.
* Truy vết bounding box dựa trên so khớp chuỗi nên chỉ mang tính xấp xỉ.
* Khi truy vết thất bại sẽ dùng tọa độ dòng đầu tiên làm fallback.
* Confidence luôn bằng 1.0 nếu regex match, không phản ánh chất lượng thực tế của OCR.
* Lỗi cấu hình regex sẽ làm hệ thống fail-fast ngay khi khởi tạo extractor.    

---
# File Summaries: module_3_dynamic_ner/ground_truth
## `ground_truth.json`
Purpose: Đóng vai trò là đáp án chuẩn (baseline) để đánh giá độ chính xác bóc tách (F1-Score) của luồng Module 3 đối với tài liệu kiểm thử scan_001_ocr.json.
Inputs: None (Static JSON data file).
Outputs: Định nghĩa các cặp key-value kỳ vọng cho siêu dữ liệu văn bản pháp luật (co_quan_ban_hanh, so_hieu_van_ban, ngay_thang_ban_hanh, ten_loai_van_ban) và định dạng chuỗi đích cho số trang (trang_so).
Key Classes: N/A.
Key Functions: N/A.
Dependencies: Được gọi và tiêu thụ bởi kịch bản chấm điểm đánh giá (ví dụ: evaluate_metrics.py).
Known Issues: Trường ten_loai_van_ban cố ý giữ nguyên các lỗi chính tả quang học OCR (ví dụ: "Uy ban nhân dần", "trung tương"), đòi hỏi module chấm điểm hoặc LLM phải có cơ chế đối chiếu/nắn lỗi phù hợp.

---

# File Summaries: module_3_dynamic_ner/llm_engine

## `auto_corrector.py`
**Purpose:** Handles post-extraction error correction (OCR/spelling) using a hybrid approach: strict Python rule-based logic for dates, followed by LLM-based few-shot prompting for text fields (supports both Cloud Gemini and Local Ollama).
**Inputs:** `ExtractedField` object, document context string.
**Outputs:** Corrected `ExtractedField` object with updated `raw_value`, `is_valid` flag, and `error_reason`.
**Key Classes:** `AutoCorrector`.
**Key Functions:** `_fix_date_logic`, `correct_field`.
**Dependencies:** `os`, `time`, `re`, `calendar`, `google.genai`, `openai`, `schemas.template_schema.ExtractedField`.
**Known Issues:** Rule-based date fixing is hardcoded to a specific Vietnamese regex format.

## `gemini_provider.py`
**Purpose:** Implements the `BaseLLMProvider` using Google's Gemini Cloud API. Handles batch JSON extraction with built-in auto-retry and automatic model fallback (Flash 2.5 -> Flash 2.0) on failure.
**Inputs:** Context text, JSON schema dictionary, system prompt string.
**Outputs:** Extracted data as a Python dictionary.
**Key Classes:** `GeminiProvider`.
**Key Functions:** `extract_batch_json`.
**Dependencies:** `json`, `time`, `google.genai`, `llm_engine.llm_provider.BaseLLMProvider`.
**Known Issues:** Relies on external network stability and API rate limits.

## `llm_provider.py`
**Purpose:** Defines the abstract base interface for all LLM providers (Cloud, Local, Mock), ensuring a standardized contract for batch JSON extraction without relying on heavy external frameworks like LangChain.
**Inputs:** API key string.
**Outputs:** N/A (Abstract interface).
**Key Classes:** `BaseLLMProvider`.
**Key Functions:** `extract_batch_json` (abstract).
**Dependencies:** `abc`, `json`.
**Known Issues:** None.

## `local_llm_provider.py`
Purpose: Cung cấp lớp giao tiếp với Local LLM (Ollama - model mặc định qwen2.5:7b) để bóc tách dữ liệu JSON. Tích hợp sẵn cơ chế chia nhỏ văn bản (semantic chunking), hỗ trợ xử lý đa luồng/tuần tự (parallel/sequential), và ghi log chi tiết (trace logging).
Inputs: context_text (str), json_schema (dict), system_prompt (str).
Outputs: Dictionary (dict) chứa dữ liệu JSON đã được gộp lại từ tất cả các khối văn bản (chunks).
Key Classes: LocalLLMProvider (kế thừa từ BaseLLMProvider).
Key Functions: extract_batch_json (hàm gọi chính), _semantic_chunking, _process_single_chunk, _log_trace.
Dependencies: json, time, re, os, datetime, concurrent.futures, openai (OpenAI client), llm_engine.llm_provider.BaseLLMProvider.
Known Issues: Sử dụng Regex (\{.*\}) để trích xuất JSON có thể gặp lỗi nếu LLM trả về chuỗi JSON rác hoặc bị bọc trong markdown phức tạp; Timeout được fix cứng ở 120s cho mỗi chunk có thể gây gián đoạn nếu phần cứng tải chậm.

## `mock_provider.py`
**Purpose:** Provides a dummy LLM implementation for rapid unit testing and pipeline validation without incurring API costs or local inference delays. Simulates specific edge cases (e.g., missing fields).
**Inputs:** Context text, JSON schema, system prompt.
**Outputs:** Pre-defined, hardcoded Python dictionary.
**Key Classes:** `MockLLMProvider`.
**Key Functions:** `extract_batch_json`.
**Dependencies:** `llm_engine.llm_provider.BaseLLMProvider`.
**Known Issues:** Outputs static data; completely ignores the input context.

## `retriever.py`
**Purpose:** Acts as a lightweight, CPU-based heuristic RAG (Retrieval-Augmented Generation) filter. Shrinks the context window by extracting only lines containing specific keywords (and a surrounding window) to save LLM tokens/RAM.
**Inputs:** `DocumentInput` object, list of keywords, window size.
**Outputs:** Filtered context string.
**Key Classes:** `HeuristicRetriever`.
**Key Functions:** `retrieve_context`, `_get_default_context`.
**Dependencies:** `schemas.template_schema.DocumentInput`, `typing`.
**Known Issues:** Uses simple substring matching; might fail to retrieve context if OCR output contains typos breaking the target keywords.

---

# File Summaries: module_3_dynamic_ner/router

## `classifier.py`
**Purpose:**
Xác định loại tài liệu dựa trên nội dung đầu tài liệu bằng Regex và trả về file rule tương ứng để xử lý tiếp. 
**Inputs:**
* `DocumentInput document`
  * Chứa danh sách các dòng văn bản (`document.lines`)
* `catalog_path` (optional)
  * Đường dẫn tới `document_catalog.json` 
**Outputs:**
* `str`
  * Tên file rule JSON tương ứng (ví dụ: `rules_hanh_chinh.json`)
* Hoặc ném `UnknownDocumentError` nếu không nhận diện được tài liệu. 

**Key Classes:**
* `UnknownDocumentError`
  * Exception dùng khi tài liệu không thuộc danh mục hỗ trợ.
* `DocumentClassifier`
  * Bộ phân loại tài liệu dựa trên Regex. 

**Key Functions:**
* `__init__(catalog_path=None)`
  * Khởi tạo classifier và nạp catalog.
* `_load_catalog()`
  * Đọc `document_catalog.json`.
* `classify(document)`
  * Quét tối đa 15 dòng đầu.
  * So khớp Regex với catalog.
  * Trả về file rule phù hợp hoặc từ chối tài liệu. 

**Dependencies:**
* `json`
* `re`
* `pathlib.Path`
* `DocumentInput`
* `document_catalog.json` (external config) 

**Known Issues:**
* Chỉ kiểm tra 15 dòng đầu tiên nên có thể bỏ sót tín hiệu nhận diện nằm sâu trong tài liệu.
* Regex lỗi chỉ được log và bỏ qua, không chặn hệ thống.
* Nếu catalog không tồn tại sẽ trả catalog rỗng, dẫn tới mọi tài liệu bị từ chối.
* Hiệu quả nhận diện phụ thuộc hoàn toàn vào chất lượng Regex trong catalog.  


## `strategy_router.py`

**Purpose:**
Điều phối chiến lược trích xuất dữ liệu. Quyết định field nào xử lý bằng Regex/Extractor, field nào xử lý bằng LLM, đồng thời quản lý cơ chế fallback từ Regex sang LLM và thực hiện validation kết quả. 

**Inputs:**
* `DocumentInput document`
  * Nội dung tài liệu đã OCR.
* `fields_config`
  * Cấu hình field được nạp từ rule JSON.
* `llm_provider`
  * Provider dùng cho batch extraction bằng AI.  

**Outputs:**
* `List[ExtractedField]`
  * Danh sách field đã được trích xuất và xác thực.  

**Key Classes:**
* `StrategyRouter`
  * Registry và orchestration layer cho toàn bộ extractor. 

**Key Functions:**
* `register_extractor(strategy_type, extractor_class)`
  * Đăng ký extractor theo tên chiến lược.
* `process_document(document, fields_config)`
  * Điều phối toàn bộ quá trình trích xuất.
  * Chạy extractor tương ứng.
  * Thực hiện validation.
  * Fallback sang LLM khi extractor thất bại.
  * Gom nhiều field thành một lần gọi LLM (batch extraction).  

**Dependencies:**
* `BaseExtractor`
* `FieldValidator`
* `BaseLLMProvider`
* `DocumentInput`
* `ExtractedField`
* `BoundingBox`
* Các extractor được đăng ký động từ bên ngoài. 

**Known Issues:**
* Confidence của kết quả từ LLM được gán giá trị tĩnh (0.85), không phản ánh độ tin cậy thực tế.
* Bounding box của kết quả LLM là giá trị giả (0,0,0,0), không hỗ trợ truy vết vị trí trong tài liệu.
* Nếu extractor không được đăng ký trong registry, field tương ứng sẽ không được xử lý.
* Toàn bộ tài liệu được gửi vào LLM khi batch extraction, có thể làm tăng token và chi phí xử lý đối với tài liệu lớn.
* Validation phụ thuộc hoàn toàn vào cấu hình rule JSON.   

---

# File Summaries: module_3_dynamic_ner/schemas

## `template_schema.py`
**Purpose:** Defines the strict Pydantic data contracts for inter-module communication, establishing the foundational structures for OCR input handling and standardized NER output validation.
**Inputs:** N/A (Data structure definitions).
**Outputs:** N/A (Data structure definitions).
**Key Classes:** `BoundingBox`, `LineData`, `DocumentInput`, `ExtractedField`.
**Key Functions:** N/A.
**Dependencies:** `pydantic`, `typing`.
**Known Issues:** `DocumentInput` relies on a single `image_width` and `image_height` for the entire document, which could cause spatial calculation errors for multi-page PDFs where individual pages have varying dimensions.

---

# File Summaries: module_3_dynamic_ner/validators

## `field_validator.py`
**Purpose:** Evaluates extracted data fields against predefined rules (such as non-empty, exact length, regex format matching, and calendar date validation) to determine their validity.
**Inputs:** An `ExtractedField` object and a `validation_config` dictionary.
**Outputs:** The modified `ExtractedField` object, with `is_valid` set to `False` and `error_reason` populated if any rule violations occur.
**Key Classes:** `FieldValidator`.
**Key Functions:** `validate`, `_is_valid_date_logic`.
**Dependencies:** `re`, `datetime`, `schemas.template_schema.ExtractedField`, `typing`.
**Known Issues:** The `_is_valid_date_logic` method strictly assumes a "Day - Month - Year" sequence and automatically returns `True` (bypassing validation) if it extracts fewer than three numbers from the string.

## `output_validator.py`
**Purpose:** Validates the final LLM-extracted JSON output by dynamically generating a Pydantic model from the target JSON schema, initiating a self-correction loop if the structure is violated.
**Inputs:** The extracted `data` dictionary and the target `json_schema` dictionary.
**Outputs:** A cleaned data dictionary with `None` values excluded, or raises a `ReflexionRetryException` if validation fails.
**Key Classes:** `ReflexionRetryException`, `OutputValidator`.
**Key Functions:** `_generate_dynamic_model`, `validate_and_parse`.
**Dependencies:** `typing`, `pydantic` (`BaseModel`, `create_model`, `ValidationError`).
**Known Issues:** The dynamic model wraps all schema fields as `Optional[Any]` to prevent crashes from missing fields, which bypasses strict data type enforcement.

---

# File Summaries: module_3_dynamic_ner

## `api.py`
**Purpose:** Cung cấp REST API endpoint (FastAPI) để nhận diện và bóc tách tài liệu từ xa, đóng gói `DocumentPipeline` và xử lý vòng đời Request/Response cùng các ngoại lệ HTTP.
**Inputs:** JSON Request body chứa `DocumentInput` và `ExtractionOptions` (công tắc auto-correct).
**Outputs:** JSON Response chứa danh sách các trường bóc tách thành công, thời gian xử lý và siêu dữ liệu.
**Key Classes:** `ExtractionOptions`, `ExtractionRequest`.
**Key Functions:** `extract_document`.
**Dependencies:** `fastapi`, `pydantic`, `dotenv`, `.pipeline`, `.router.classifier`.
**Known Issues:** Yêu cầu `GEMINI_API_KEY` cứng trong `.env` ngay lúc khởi động, ngay cả khi người dùng cấu hình chạy `LLM_ENGINE=local`. Lỗi Catch-all cuối cùng (Exception) có thể che giấu traceback thực sự của lỗi hệ thống.

## `cli.py`
**Purpose:** Giao diện dòng lệnh (CLI) giúp kỹ sư chạy kiểm thử hoặc chạy batch xử lý Module 3 trực tiếp trên terminal với các file JSON lưu ở Local.
**Inputs:** Tham số dòng lệnh (`--input_ocr_json`, `--registry_file`, `--template_name`, `--output_file`).
**Outputs:** Ghi file JSON kết quả bóc tách ra ổ cứng.
**Key Classes:** None.
**Key Functions:** `main`.
**Dependencies:** `argparse`, `json`, `os`, `.pipeline`.
**Known Issues:** Dòng code gán `final_result` hiện tại đang bị hardcode dữ liệu Mock (giả lập), làm vô hiệu hóa kết quả chạy thực tế của lõi Pipeline. Cần gỡ bỏ Mock trước khi dùng thật.

## `normalizer.py`
**Purpose:** Tầng tiền xử lý văn bản chuyên dụng, sử dụng Regex để "tẩy rửa" và chuẩn hóa các lỗi nhận diện OCR phổ biến trong tiếng Việt trước khi đưa vào các biểu thức bóc tách.
**Inputs:** Chuỗi văn bản thô (Raw text string).
**Outputs:** Chuỗi văn bản đã được chuẩn hóa.
**Key Classes:** `OCRNormalizer`.
**Key Functions:** `clean_text`.
**Dependencies:** `re`.
**Known Issues:** Bộ luật sửa lỗi (correction_rules) bị fix cứng trong code. Nếu văn bản gốc tình cờ chứa các ký tự giống lỗi OCR, chúng có thể bị thay thế nhầm (False Positive).

## `pipeline.py`
**Purpose:**
Điều phối toàn bộ luồng xử lý tài liệu: phân loại tài liệu, nạp cấu hình động, chọn extractor phù hợp, trích xuất dữ liệu, kiểm tra kết quả và tự động sửa lỗi bằng LLM khi cần. 

**Inputs:**
* `api_key`
  * Khóa truy cập Gemini và Auto-Corrector.
* `DocumentInput document`
  * Tài liệu OCR đã được chuẩn hóa.
* `enable_auto_correct`
  * Bật/tắt bước sửa lỗi hậu xử lý.  

**Outputs:**
* `List[ExtractedField]`
  * Danh sách trường dữ liệu đã được trích xuất và kiểm tra. 

**Key Classes:**
* `DocumentPipeline`
  * Orchestrator chính của Module 3. 

**Key Functions:**
* `__init__(api_key)`
  * Khởi tạo LLM provider, router, validator, auto-corrector và classifier.
* `_load_dynamic_config(rule_file_name)`
  * Lazy-load file rule JSON tương ứng với loại tài liệu.
* `process(document, enable_auto_correct=False)`
  * Thực thi pipeline hoàn chỉnh từ phân loại → trích xuất → sửa lỗi.  

**Dependencies:**
* `DocumentClassifier`
* `StrategyRouter`
* `GeminiProvider`
* `LocalLLMProvider`
* `AutoCorrector`
* `OutputValidator`
* `RegexExtractor`
* `LayoutRegexExtractor`
*  Rule JSON trong thư mục `configs/`  

**Known Issues:**
* Khởi tạo thất bại nếu file rule JSON bị thiếu hoặc sai cú pháp.
* Auto-correct chỉ chạy với các field không hợp lệ.
* Toàn bộ context tài liệu được ghép thành một chuỗi khi sửa lỗi, có thể làm tăng chi phí LLM với tài liệu lớn.
* Chế độ hoạt động phụ thuộc biến môi trường `LLM_ENGINE`.   
