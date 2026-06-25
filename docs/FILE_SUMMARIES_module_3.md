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
Purpose: Định nghĩa lược đồ cấu hình bóc tách lai (Hybrid Extraction) chuyên dụng cho văn bản pháp luật (van_ban_phap_luat). Phân chia rành mạch nhiệm vụ bóc tách bằng regex (hỗ trợ fallback_to_llm tự động cứu hộ) và llm (bóc tách ngữ nghĩa).
Inputs: None (Static JSON file).
Outputs: Cấu hình chi tiết các trường (fields), chứa từ khóa aliases, regex_pattern tiêm {LABEL}, kiểu dữ liệu và System Prompt.
Key Classes: N/A.
Key Functions: N/A.
Dependencies: Gắn kết chặt chẽ với StrategyRouter, RegexExtractor và các lớp LLMProvider.
Known Issues: None.

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
**Purpose:** Advanced regex-based extraction featuring full-text concatenation to bypass OCR line-breaks, automated whitespace compression, auto-formatting, and dual-format configuration support (legacy `patterns` array vs. modern `aliases` with `{LABEL}` injection).
**Inputs:** `DocumentInput` object.
**Outputs:** `ExtractedField` object with a hardcoded confidence of 1.0, or `None` (triggering LLM fallback).
**Key Classes:** `RegexExtractor`.
**Key Functions:** `__init__` (fail-fast regex compilation), `_compress_whitespace`, `_auto_format_output`, `extract`.
**Dependencies:** `re`, `extractors.base_extractor`, `schemas.template_schema`.
**Known Issues:** Reconstructs bounding boxes using "approximate line tracing" after a full-text search; the resulting bounding box may point to the first line only if the text actually spans multiple lines.

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
**Purpose:** Acts as the gatekeeper for Module 3. Scans the first 15 lines of a document against regex patterns in the catalog to determine its type and load the correct rule file. Enforces a "Strict Rejection" policy if the document type is unknown.
**Inputs:** `DocumentInput` object, optional catalog path string.
**Outputs:** Target rule filename (string) or raises an `UnknownDocumentError`.
**Key Classes:** `UnknownDocumentError`, `DocumentClassifier`.
**Key Functions:** `__init__`, `_load_catalog`, `classify`.
**Dependencies:** `json`, `re`, `pathlib`, `schemas.template_schema.DocumentInput`.
**Known Issues:** Relies exclusively on the first 15 lines; if OCR fails on the header or the identifying keywords are pushed down by long logos/letterheads, classification will fail.

## `strategy_router.py`
**Purpose:** Nhạc trưởng định tuyến quá trình bóc tách. Quét các trường bằng Regex Extractor trước, nếu thất bại (Fallback) hoặc được cấu hình sẵn là "llm", sẽ gom nhóm lại (Batching) để gửi cho LLM xử lý một lần nhằm tiết kiệm tài nguyên. Áp dụng FieldValidator cho mọi kết quả.
**Inputs:** Đối tượng `DocumentInput`, từ điển `fields_config`, đối tượng `BaseLLMProvider`.
**Outputs:** Danh sách các đối tượng `ExtractedField` đã qua kiểm duyệt.
**Key Classes:** `StrategyRouter`.
**Key Functions:** `__init__`, `register_extractor`, `process_document`.
**Dependencies:** `json`, `typing`, `extractors.base_extractor`, `schemas.template_schema`, `validators.field_validator`, `llm_engine.llm_provider.BaseLLMProvider`.
**Known Issues:** Các trường dữ liệu do LLM bóc tách đang bị gán cứng tọa độ không gian `BoundingBox(0,0,0,0)` và độ tự tin tĩnh `0.85`, khiến UI không thể vẽ khung highlight cho các trường này.

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
**Purpose:** Lớp nhạc trưởng (Orchestrator) điều phối toàn bộ luồng chạy của Module 3: Phân loại tài liệu $\rightarrow$ Tải cấu hình (Lazy Load) $\rightarrow$ Định tuyến bóc tách $\rightarrow$ (Tùy chọn) Sửa lỗi chính tả.
**Inputs:** Đối tượng `DocumentInput`, cờ `enable_auto_correct`.
**Outputs:** Danh sách các đối tượng `ExtractedField` chứa dữ liệu cuối cùng.
**Key Classes:** `DocumentPipeline`.
**Key Functions:** `__init__`, `_load_dynamic_config`, `process`.
**Dependencies:** `os`, `json`, `pathlib`, `.router`, `.llm_engine`, `.extractors`, `.validators`.
**Known Issues:** Đường dẫn thư mục `configs` đang bị gán cứng (hardcode) trong hàm `_load_dynamic_config`. Khâu gom văn bản cho Auto-Corrector (`\n".join(...)`) có thể gây tràn Token Context của LLM nếu tài liệu quá dài (hàng trăm trang).