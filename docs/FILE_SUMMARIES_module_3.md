# File Summaries: module_3_dynamic_ner/configs

## `document_catalog.json`
Purpose: Đóng vai trò là tệp danh bạ cấu hình trung tâm (registry) cho `DocumentClassifier`. Ánh xạ các loại tài liệu với danh sách regex nhận diện đặc trưng tương ứng, đồng thời chỉ định file quy tắc bóc tách (rule file/schema) cần nạp khi phát hiện tài liệu khớp định dạng.
Inputs: N/A (File cấu hình tĩnh dạng JSON).
Outputs: Cung cấp cấu trúc dữ liệu từ điển bao gồm `name` (tên tài liệu), `regex_patterns` (mảng biểu thức chính quy nhận diện), và `rule_file` (tên file lược đồ) cho hệ thống phân loại.
Key Classes: N/A (JSON Data File).
Key Functions: N/A (JSON Data File).
Dependencies: Được nạp và phân tích cú pháp trực tiếp bởi `classifier.py`.
Known Issues: Dữ liệu hoàn toàn tĩnh, việc thêm mới hoặc cập nhật loại tài liệu yêu cầu chỉnh sửa file thủ công. Các biểu thức regex phức tạp có thể dễ bị lỗi escape character (dấu backslash) do hạn chế định dạng chuỗi của JSON.

## `giay_chung_nhan.json`
Purpose: Đóng vai trò là tệp cấu hình lược đồ (schema/rule file) định nghĩa các quy tắc bóc tách dữ liệu cụ thể cho loại tài liệu "Giấy chứng nhận". File này liệt kê các trường dữ liệu mục tiêu cần trích xuất, phương pháp xử lý tương ứng (ví dụ: `regex` hoặc `llm`), và các điều kiện xác thực (validation rules).
Inputs: N/A (File cấu hình tĩnh dạng JSON).
Outputs: Cung cấp từ điển cấu hình (`fields_config`) làm kim chỉ nam để `strategy_router.py` định tuyến phương pháp bóc tách và chạy màng lọc xác thực.
Key Classes: N/A (JSON Data File).
Key Functions: N/A (JSON Data File).
Dependencies: Nằm trong thư mục `schemas/`, được khởi tạo thông qua `batch_processor.py` và tiêu thụ trực tiếp bởi `strategy_router.py` để xử lý tài liệu tương ứng.
Known Issues: Việc bảo trì và cập nhật các biểu thức regex nội tuyến (inline regex) bên trong JSON có thể khó khăn và dễ dính lỗi escape character (dấu backslash). Bất kỳ sự thay đổi biểu mẫu nào trong thực tế cũng đòi hỏi phải chỉnh sửa file này thủ công.

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

## `muc_luc_van_ban.json`
Purpose: Đóng vai trò là tệp cấu hình lược đồ (schema/rule file) định nghĩa quy tắc bóc tách dữ liệu cho loại tài liệu "Mục lục văn bản" (Table of Contents / Document Index). File này liệt kê các trường thông tin cần lấy (ví dụ: số thứ tự, tên văn bản/trích yếu, số trang) và phương pháp xử lý tương ứng để hệ thống áp dụng.
Inputs: N/A (File cấu hình tĩnh dạng JSON).
Outputs: Cung cấp từ điển cấu hình (`fields_config`) để `strategy_router.py` đọc hiểu và định tuyến quá trình trích xuất dữ liệu.
Key Classes: N/A (JSON Data File).
Key Functions: N/A (JSON Data File).
Dependencies: Nằm trong thư mục `schemas/`, được nạp tự động bởi `batch_processor.py` và tiêu thụ bởi `strategy_router.py`.
Known Issues: Cấu trúc mục lục thường rất đa dạng (dạng bảng, dạng dòng tab), do đó nếu phụ thuộc nhiều vào regex nội tuyến (inline regex) trong file JSON này sẽ rất dễ đứt gãy. Việc cập nhật yêu cầu can thiệp file thủ công.

---

# File Summaries: module_3_dynamic_ner/orchestrator

## `session_manager.py`
Purpose: Manages session lifecycles for a continuous stream of multi-page OCR data. Detects document boundaries using dual-trigger conditions (headers and signatures) and executes structured data extraction algorithms including regex, fuzzy string matching, proximity parsing, and conditional appending.
Inputs: `catalog_config` (dict) for initialization, `stream_of_pages` (Iterable of dicts containing `full_text`, `page_num`, and `words`).
Outputs: List of dicts (`extracted_records`), where each dictionary represents a parsed document with its extracted key-value pairs.
Key Classes: `LineBlock`, `DocumentSession`, `SessionManager`.
Key Functions: `add_page_data` (buffers page tokens), `_cluster_y_overlap` (aggregates characters into lines), `flush_and_extract` (orchestrates multi-method extraction rules), `process_document_stream` (drives the main session state machine).
Dependencies: `re`, `json`, `rapidfuzz` (`process`, `fuzz`).
Known Issues: The `_cluster_y_overlap` method is a blank placeholder that returns an empty list, which causes downstream line-based algorithms like `proximity_number_search` to bypass text evaluation entirely. Configuration paths (`configs/giay_chung_nhan.json`) and specific boundary keyword strings are hardcoded within the session manager logic.


---

# File Summaries: module_3_dynamic_ner

## `cli.py`
**Purpose:**
Cung cấp Command-Line Interface (CLI) cho Module 3 Dynamic NER. Chịu trách nhiệm đọc OCR JSON, tải schema từ Registry, kích hoạt pipeline bóc tách dữ liệu theo template được chọn và ghi kết quả ra file JSON.  

**Inputs:**
* `--input_ocr_json`
  * File kết quả OCR từ Module 2.
* `--registry_file`
  * File Schema Registry chứa danh sách template.
* `--template_name`
  * Tên loại biểu mẫu cần xử lý.
* `--output_file`
  * Đường dẫn lưu kết quả đầu ra. 

**Outputs:**
* File JSON chứa dữ liệu bóc tách cuối cùng.
* Thông báo trạng thái thực thi trên CLI. 

**Key Classes:**
* Không có.

**Key Functions:**
* `main()`
  * Parse tham số dòng lệnh.
  * Kiểm tra sự tồn tại của Registry và OCR JSON.
  * Nạp schema theo template.
  * Khởi tạo `DocumentPipeline`.
  * Gọi pipeline xử lý dữ liệu.
  * Ghi kết quả ra file JSON. 

**Dependencies:**
* `argparse`
* `json`
* `os`
* `DocumentPipeline` 

**Known Issues:**
* Kết quả từ `pipeline.process()` hiện bị ghi đè bởi dữ liệu mock nên output thực tế của pipeline không được sử dụng. 
* Sử dụng `print()` thay vì logging framework.
* Xử lý lỗi bằng `return` đơn giản, không có exit code chuẩn cho automation/CI.
* Không kiểm tra cấu trúc hoặc tính hợp lệ của dữ liệu OCR và Registry sau khi load.
* Không có cơ chế xử lý exception khi đọc/ghi file hoặc khi pipeline thực thi thất bại.  

Tin rất vui cho bạn: **Bạn không cần phải viết thêm một dòng code nào cho `global_regex` nữa, vì hệ thống của bạn ĐÃ hỗ trợ sẵn các chức năng này rồi!**

Cấu trúc kiến trúc OOP mà bạn (hoặc team) đã xây dựng với `BaseStrategy` thực sự là một thiết kế rất xuất sắc và đã áp dụng chuẩn xác nguyên tắc DRY (Don't Repeat Yourself) mà chúng ta vừa bàn tới.

Dưới đây là chi tiết giải đáp cho các câu hỏi của bạn dựa trên mã nguồn bạn vừa cung cấp:

### 1. Hàm `global_regex` có nhận biến `scan_limit` hay `skip_lines` không?

**Câu trả lời là CÓ.** Nó được hỗ trợ một cách tự động và hoàn hảo thông qua kiến trúc Kế thừa (Inheritance).

* **Bằng chứng:** Nếu bạn nhìn vào file `base_strategy.py`, ngay tại hàm `execute` (hàm chạy đầu tiên trước khi bóc tách), hệ thống đã lấy ra `scan_limit` và `skip_lines` từ cấu hình JSON.


* **Cách hoạt động:** Nó tiến hành cắt xén trực tiếp mảng `working_lines` (bỏ qua dòng đầu bằng `skip_lines`, giới hạn số lượng bằng `scan_limit`). Sau đó, nó mới ném cái mảng đã được "khoanh vùng an toàn" này cho `_do_extract` của class `GlobalRegexStrategy`.


* Bản thân file `global_regex_strategy.py` chỉ việc gộp mảng đã được cắt lại và chạy Regex mà không cần quan tâm đến logic giới hạn nữa.



=> **Cách khắc phục ngay lập tức:** Bạn chỉ cần mở file JSON, sửa lại block bóc tách `so_ky_hieu_tai_lieu` thành như sau (không cần đụng vào code Python):

```json
{
    "field_name": "so_ky_hieu_tai_lieu",
    "extraction_method": "global_regex",
    "skip_lines": 1, 
    "scan_limit": 15,
    "pattern": "(?im)^(?!.*mẫu)(?!.*thửa).*?SỐ[\\s\\.]*:[\\s\\.]*([0-9][A-Z0-9/\\.\\-]+)",
    "post_processing": ["clean_targeted_punctuation"],
    "data_type": "string"
}

```

*(Bạn có thể tinh chỉnh số lượng `skip_lines` và `scan_limit` cho phù hợp với vị trí xuất hiện thực tế của văn bản).*

### 2. Method nào ĐANG CÓ và KHÔNG CÓ chức năng `skip_lines` / `scan_limit`?

Dựa vào mã nguồn của bạn, các phương thức đang bị chia làm 2 thế hệ (Thế hệ mới OOP và Thế hệ cũ Procedural).

**Nhóm 1: Hỗ trợ TOÀN DIỆN (scan_direction, skip_lines, scan_limit)**

* `global_regex`

* `proximity_number_search`

* `fixed_value`


*(Ba phương thức này nằm trong kiến trúc Strategy OOP, được hưởng sái tự động từ `BaseStrategy`)*
* `hybrid_dictionary_regex` *(Phương thức cũ nằm ở `session_manager.py` nhưng đã được code tay hỗ trợ đủ 3 chức năng này).*



**Nhóm 2: Hỗ trợ MỘT PHẦN**

* `multiline_dictionary_match`: Chỉ có `scan_limit` (mặc định là 5), **KHÔNG CÓ** `skip_lines`.



**Nhóm 3: HOÀN TOÀN KHÔNG hỗ trợ**

* `global_dictionary_match`

* `fixed_string_with_conditional_append`

* `fuzzy_key_value`

* `extract_between_anchors`

* `inherit_from_context`


### 3. Nếu muốn thêm chức năng vào Method khác thì có phải Copy-Paste không? Cần import thêm gì?

**Tuyệt đối KHÔNG cần copy-paste! Và KHÔNG cần import thư viện gì mới!**

Thiết kế `BaseStrategy` của bạn sinh ra chính là để giải quyết triệt để nỗi đau copy-paste này. Nếu bạn muốn `fuzzy_key_value` hay bất kỳ method cũ nào ở Nhóm 3 có thêm tính năng `skip_lines` và `scan_limit`, bạn chỉ cần:

1. Tạo một class mới (vd: `FuzzyKeyValueStrategy`) trong thư mục `strategies/`.
2. Cho nó kế thừa `BaseStrategy` (tương tự file `global_regex_strategy.py` của bạn).


3. Di dời logic cốt lõi từ `session_manager.py` sang hàm `_do_extract` của class mới.
4. Khai báo class mới vào cuốn sổ Nam Tào `ExtractorFactory`.



Ngay khi bạn thực hiện xong 4 bước trên, method đó sẽ lập tức và tự động sở hữu năng lực `skip_lines` và `scan_limit` từ lớp cha mà không cần viết thêm một dòng if/else nào xử lý cắt mảng.

**Lời khuyên của tôi lúc này:**
Hãy sửa file cấu hình JSON trước để áp dụng `skip_lines` và `scan_limit` cho `global_regex` ngay bây giờ để xử lý dứt điểm lỗi bắt nhầm "Số ký hiệu". Việc đưa nốt các hàm cũ về kiến trúc OOP (Refactor) chúng ta có thể lên lịch thực hiện sau khi luồng dữ liệu chính đã chạy mượt mà!