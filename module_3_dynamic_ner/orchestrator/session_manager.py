import re
import json
from pathlib import Path
from rapidfuzz import process, fuzz
import unicodedata
from .post_processors import PostProcessor
from strategies.extractor_factory import ExtractorFactory
from strategies.payload import ExtractionPayload
            

VERBOSE_XRAY = True 

def log_xray(message: str):
    if VERBOSE_XRAY:
        print(f"[X-RAY] {message}")

class LineBlock:
    def __init__(self, text: str, y_min: float, y_max: float, page_num: int):
        self.text = text
        self.y_min = y_min
        self.y_max = y_max
        self.page_num = page_num

class DocumentSession:
    def __init__(self, config: dict):
        self.config = config
        self.document_type = config.get('document_type', 'UNKNOWN_DOCUMENT')
        self.pages_data = [] 
        self.start_page = None
        self.end_page = None

        # Kho chứa cache từ điển sửa lỗi OCR trên RAM (Memory Caching)
        self._typo_caches = {}

    def add_page_data(self, page_num: int, ocr_words: list):
        if self.start_page is None:
            self.start_page = page_num
        self.end_page = page_num
        self.pages_data.append((page_num, ocr_words))

    def _cluster_y_overlap(self, ocr_words: list, page_num: int) -> list:
        if not ocr_words: return []
        boxes = []
        for w in ocr_words:
            pts = w['bbox']['points']
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            boxes.append({'text': w['text'], 'x_min': min(xs), 'x_max': max(xs), 'y_min': min(ys), 'y_max': max(ys)})
            
        boxes.sort(key=lambda b: b['y_min'])
        lines = []
        current_line = [boxes[0]]
        
        for box in boxes[1:]:
            line_y_min = min(b['y_min'] for b in current_line)
            line_y_max = max(b['y_max'] for b in current_line)
            
            overlap = max(0, min(box['y_max'], line_y_max) - max(box['y_min'], line_y_min))
            min_height = min(box['y_max'] - box['y_min'], line_y_max - line_y_min)
            
            # --- TẤM KHIÊN 2 CHIỀU & NGƯỠNG MIỄN TRỪ (Bidirectional Shield & Floor) ---
            box_height = box['y_max'] - box['y_min']
            line_height = line_y_max - line_y_min
            
            # 1. Ngưỡng miễn trừ (Floor) = 12 pixels để cứu dấu câu và nhiễu li ti
            floor_threshold = 12
            safe_box_height = max(box_height, floor_threshold)
            safe_line_height = max(line_height, floor_threshold)
            
            # 2. Tính tỷ lệ lệch 2 chiều (Lớn chia Nhỏ)
            max_h = max(safe_box_height, safe_line_height)
            min_h = min(safe_box_height, safe_line_height)
            
            height_ratio = (max_h / min_h) if min_h > 0 else 999
            is_height_valid = height_ratio <= 2.5
            
            # 3. Chỉ gộp vào dòng NẾU có giao nhau > 30% VÀ vượt qua Tấm khiên chiều cao
            if min_height > 0 and (overlap / min_height) > 0.3 and is_height_valid:
                current_line.append(box)
            else:
                # --- LOG X-RAY DEBUG TẦM NHÌN HỆ THỐNG ---
                # Chỉ bắn log khi 2 khối đè lên nhau > 30% NHƯNG bị Tấm khiên chiều cao chém đứt
                if min_height > 0 and (overlap / min_height) > 0.3 and not is_height_valid:
                    current_text = " ".join([b['text'] for b in current_line])
                    print(f"[X-RAY] [SHIELD_ACTIVATED] Từ chối gộp '{box['text']}' (Cao: {box_height}) vào '{current_text}' (Cao: {line_height}). Tỷ lệ lệch: {height_ratio:.2f} > 2.5")
                
                current_line.sort(key=lambda b: b['x_min'])
                lines.append(LineBlock(" ".join([b['text'] for b in current_line]), line_y_min, line_y_max, page_num))
                current_line = [box]
        
        if current_line:
            current_line.sort(key=lambda b: b['x_min'])
            lines.append(LineBlock(" ".join([b['text'] for b in current_line]), min(b['y_min'] for b in current_line), max(b['y_max'] for b in current_line), page_num))
        return lines

    def flush_and_extract(self, dossier_context: dict = None) -> dict:
        if dossier_context is None:
            dossier_context = {}
            
        log_xray(f"EVENT=SESSION_FLUSH | DOC_TYPE={self.document_type} | START_PAGE={self.start_page} | END_PAGE={self.end_page}")
        all_lines = []
        for page_num, words in self.pages_data:
            all_lines.extend(self._cluster_y_overlap(words, page_num))

        global_text = "\n".join([line.text for line in all_lines])
        
        result = {
            "to_so_trang_so": f"{self.start_page:02d}-{self.end_page:02d}" if self.start_page != self.end_page else f"{self.start_page:02d}"
        }

        for rule in self.config.get('extraction_rules', []):
            field = rule['field_name']
            method = rule['extraction_method']
            log_xray(f"EVENT=EXTRACTION_START | FIELD={field} | METHOD={method}")

            # ==========================================
            # TRẠM TRUNG CHUYỂN (STRATEGY DISPATCHER)
            # ==========================================
            strategy = ExtractorFactory.get_strategy(method)

            if strategy:
                # NẾU CÓ CLASS MỚI: Chạy bằng kiến trúc OOP (Tự động lật mảng, cắt dòng)
                log_xray(f"   -> [Trạm Trung Chuyển] Định tuyến '{method}' sang kiến trúc Strategy OOP.")
                payload = ExtractionPayload(
                    all_lines=all_lines,
                    rule_config=rule,
                    dossier_context=dossier_context,
                    global_text=global_text
                )
                result[field] = strategy.execute(payload, logger=log_xray)
                
            else:
                if method == "fixed_value":
                    result[field] = rule.get('value', "")
                    log_xray(f"EVENT=EXTRACTION_SUCCESS | FIELD={field} | METHOD=fixed_value | VALUE='{result[field]}'")

                elif method == "global_regex":
                    # 1. Đọc cấu hình giới hạn (nếu có), mặc định là an toàn (không giới hạn)
                    scan_direction = rule.get('scan_direction', 'top_down')
                    scan_limit = rule.get('scan_limit', None)
                    
                    # 2. Clone mảng để việc đảo ngược không làm hỏng dữ liệu gốc
                    lines_to_scan = list(all_lines)
                    
                    if scan_direction == 'bottom_up':
                        lines_to_scan.reverse()
                        log_xray("   -> [Debug Regex] Đã đảo chiều mảng OCR (Quét từ Dưới lên Trên).")
                    
                    if scan_limit and isinstance(scan_limit, int) and scan_limit > 0:
                        lines_to_scan = lines_to_scan[:scan_limit]
                        log_xray(f"   -> [Debug Regex] Giới hạn vùng quét: {scan_limit} dòng.")
                    
                    # 3. Gộp dòng thành Scoped Text (Tùy chọn A - Đảm bảo tương thích ngược 100%)
                    scoped_text = "\n".join([line.text for line in lines_to_scan])
                    
                    # 4. Tiến hành truy quét Regex trên vùng đã giới hạn
                    match = re.search(rule['pattern'], scoped_text)
                    if match:
                        result[field] = match.group(1).strip() if match.groups() else match.group(0).strip()
                        log_xray(f"EVENT=EXTRACTION_SUCCESS | FIELD={field} | METHOD=global_regex | VALUE='{result[field]}'")
                    else:
                        result[field] = None
                        log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD=global_regex | REASON=no_match")

                elif method == "proximity_number_search":
                    anchors = rule.get('anchor_keywords', [])
                    result[field] = None
                    found = False
                    
                    for anchor in anchors:
                        for i, line in enumerate(all_lines):
                            if len(line.text.strip()) >= 6:
                                score = fuzz.partial_ratio(anchor.lower(), line.text.lower())
                                if score > 85:
                                    log_xray(f"EVENT=ANCHOR_MATCH | FIELD={field} | METHOD=proximity | ANCHOR='{anchor}' | SCORE={score} | LINE='{line.text}'")
                                    start_idx = max(0, i - rule['look_up_lines'])
                                    context_text = " ".join([l.text for l in all_lines[start_idx:i+1]])
                                    
                                    clean_line = re.sub(r'(?<=\d)[.,]+(?=[\d\s]|$)', '', context_text)
                                    date_matches = re.findall(r'(?:ngày\s*)?(\d{1,2})\s*(?:tháng|/|-|\.)\s*(\d{1,2})\s*(?:năm|/|-|\.)\s*(\d{4})', clean_line, re.IGNORECASE)
                                    
                                    if date_matches:
                                        last_match = date_matches[-1]
                                        result[field] = f"{last_match[0]}/{last_match[1]}/{last_match[2]}"
                                        log_xray(f"EVENT=EXTRACTION_SUCCESS | FIELD={field} | METHOD=proximity | VALUE='{result[field]}'")
                                    else:
                                        log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD=proximity | REASON=no_date_format_in_range")
                                    
                                    found = True
                                    break 
                                    
                        if found:
                            break 

                elif method == "global_dictionary_match":
                    result[field] = None
                    best_score = 0
                    best_value = None
                    dict_list = []
                    
                    raw_data = rule.get('master_data') or rule.get('dictionary_list')
                    
                    if isinstance(raw_data, str):
                        log_xray(f"   -> [Debug] Đang tìm đọc file từ điển tại: '{raw_data}'")
                        try:
                            with open(raw_data, 'r', encoding='utf-8') as f:
                                dict_list = [line.strip() for line in f if line.strip()]
                            log_xray(f"   -> [Debug] Đã đọc thành công {len(dict_list)} dòng từ file.")
                        except Exception as e:
                            log_xray(f"   -> [Lỗi] Không đọc được file từ điển: {e}")
                            
                    elif isinstance(raw_data, list):
                        dict_list = raw_data
                        log_xray(f"   -> [Debug] Đang dùng mảng trực tiếp có {len(dict_list)} phần tử.")
                    else:
                        log_xray("   -> [Lỗi] JSON cấu hình sai, không tìm thấy dữ liệu từ điển.")
                    
                    if not dict_list:
                        log_xray("   -> [Cảnh báo] Danh sách từ điển rỗng, bỏ qua bóc tách.")
                        continue

                    for line in all_lines:
                        if len(line.text.strip()) > 5:
                            match_result = process.extractOne(line.text, dict_list, scorer=fuzz.token_set_ratio)
                            if match_result:
                                match = match_result[0]
                                score = match_result[1]
                                if score > best_score:
                                    best_score = score
                                    best_value = match
                    
                    threshold = rule.get('match_threshold', 85)
                    if isinstance(threshold, float) and threshold < 1:
                        threshold = int(threshold * 100) 
                        
                    if best_score >= threshold:
                        result[field] = best_value
                        log_xray(f"   -> [Debug Dict] Vượt ngưỡng ({best_score}/{threshold}). Chọn: '{best_value}'")
                    else:
                        log_xray(f"   -> [Debug Dict] Thất bại (Điểm cao nhất: {best_score} - '{best_value}')")

                elif method == "hybrid_dictionary_regex":
        
                    result[field] = None
                    dict_list = []
                    
                    # 1. Đọc cấu hình tùy biến từ JSON (Có giá trị mặc định an toàn)
                    scan_direction = rule.get('scan_direction', 'top_down')
                    scan_limit = rule.get('scan_limit', None)
                    skip_lines = rule.get('skip_lines', 0) # Mặc định là 0 nếu không khai báo
                    
                    raw_data = rule.get('master_data') or rule.get('dictionary_list')
                    
                    if isinstance(raw_data, str):
                        log_xray(f"   -> [Debug Hybrid] Đang nạp từ điển từ file: '{raw_data}'")
                        try:
                            with open(raw_data, 'r', encoding='utf-8') as f:
                                dict_list = [line.strip() for line in f if line.strip()]
                            log_xray(f"   -> [Debug Hybrid] Nạp thành công {len(dict_list)} từ khóa.")
                        except Exception as e:
                            log_xray(f"   -> [Lỗi Hybrid] Không đọc được file từ điển: {e}")
                    elif isinstance(raw_data, list):
                        dict_list = raw_data
                        log_xray(f"   -> [Debug Hybrid] Nạp mảng trực tiếp ({len(dict_list)} từ khóa).")
                    else:
                        log_xray("   -> [Lỗi Hybrid] Cấu hình sai, thiếu dữ liệu từ điển.")
                    
                    if dict_list:
                        best_match_value = None
                        
                        # 2. Xử lý Chiều quét và Giới hạn vùng an toàn
                        # Clone mảng để việc đảo ngược/cắt xén không làm hỏng dữ liệu gốc
                        lines_to_scan = list(all_lines) 
                        
                        # [BƯỚC 1]: Thiết lập chiều quét
                        if scan_direction == 'bottom_up':
                            lines_to_scan.reverse()
                            log_xray("   -> [Debug Hybrid] Đã đảo chiều mảng OCR (Quét từ Dưới lên Trên).")
                        else:
                            log_xray("   -> [Debug Hybrid] Chiều quét: Từ Trên xuống Dưới (Mặc định).")
                        
                        # [BƯỚC 2]: Thực thi Dịch khung (Skip Lines) TRƯỚC
                        if isinstance(skip_lines, int) and skip_lines > 0:
                            lines_to_scan = lines_to_scan[skip_lines:]
                            log_xray(f"   -> [Debug Hybrid] Đã bỏ qua {skip_lines} dòng đầu tiên theo chiều quét.")
                            
                        # [BƯỚC 3]: Thực thi Cắt dung lượng (Scan Limit) SAU
                        if scan_limit and isinstance(scan_limit, int) and scan_limit > 0:
                            lines_to_scan = lines_to_scan[:scan_limit]
                            log_xray(f"   -> [Debug Hybrid] Giới hạn quét: {scan_limit} dòng sau khi đã dịch khung.")
                        else:
                            log_xray(f"   -> [Debug Hybrid] Giới hạn quét: Toàn bộ {len(lines_to_scan)} dòng còn lại.")

                        log_xray("   -> [Debug Hybrid] Bắt đầu rà soát Regex (đã ép chuẩn Unicode NFC)...")
                        
                        # 3. Tiến hành truy quét
                        for idx, line in enumerate(lines_to_scan):
                            if len(line.text.strip()) < 5:
                                continue
                                
                            # Ép chuẩn văn bản đầu vào
                            normalized_line = unicodedata.normalize('NFC', line.text)
                            
                            for item in dict_list:
                                # Ép chuẩn từ khóa
                                normalized_item = unicodedata.normalize('NFC', item)
                                
                                # Tạo siêu Regex
                                parts = normalized_item.split()
                                pattern_core = r'[\s\.]+'.join([re.escape(p) for p in parts])
                                full_pattern = f"(?i)({pattern_core})"
                                
                                # So khớp
                                if re.search(full_pattern, normalized_line):
                                    best_match_value = item
                                    log_xray(f"   -> [Debug Hybrid] BẮT TRÚNG ĐÍCH tại dòng {idx + 1}/{len(lines_to_scan)} vùng quét!")
                                    break 
                                    
                            if best_match_value:
                                break # Thoát vòng lặp dòng nếu đã tìm thấy

                        # 4. Chốt kết quả
                        if best_match_value:
                            result[field] = best_match_value
                            log_xray(f"   -> [Debug Hybrid] Kết quả chuẩn hóa cuối cùng: '{best_match_value}'")
                        else:
                            log_xray("   -> [Debug Hybrid] THẤT BẠI. Không tìm thấy từ khóa nào khớp trong vùng quét.")
                
                elif method == "multiline_dictionary_match":
                    
                    dict_path = rule.get("master_data", "")
                    typo_mapping_path = rule.get("typo_mapping", "") # Lấy đường dẫn file sửa lỗi
                    scan_limit = rule.get("scan_limit", 5)
                    
                    result[field] = None
                    matched = False
                    
                    # 1. Xử lý đường dẫn tương thích với cấu trúc thư mục của hệ thống
                    txt_path = Path(__file__).resolve().parents[1] / dict_path
                    
                    if not txt_path.exists():
                        log_xray(f"   -> [WARNING] LỖI: Không tìm thấy file từ điển tại '{txt_path}'")
                        log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD={method} | REASON=missing_dictionary")
                        continue
                        
                    # 2. Nạp file từ điển (Soft Fail nếu rỗng)
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            raw_keywords = [line.strip() for line in f if line.strip()]
                        log_xray(f"   -> [Deep Trace] Nạp thành công {len(raw_keywords)} từ khóa từ '{txt_path.name}'")
                    except Exception as e:
                        log_xray(f"   -> [Lỗi] Không đọc được file từ điển: {e}")
                        log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD={method} | REASON=read_error")
                        continue
                        
                    if not raw_keywords:
                        continue
                        
                    # 3. Ưu tiên từ khóa dài nhất (Longest Match First) để tránh bắt non
                    raw_keywords.sort(key=len, reverse=True)
                    
                    # 4. Gộp dòng bằng khoảng trắng (Space Aggregation)
                    target_lines = all_lines[:scan_limit]
                    aggregated_text = " ".join([line.text for line in target_lines])
                    
                    # 4.5. LỚP LÀM SẠCH DỮ LIỆU (PRE-PROCESSING VỚI MEMORY CACHE)
                    if typo_mapping_path:
                        typo_path = Path(__file__).resolve().parents[1] / typo_mapping_path
                        if typo_path.exists():
                            # Lazy Caching: Nếu chưa có trong RAM thì đọc file
                            if typo_path not in self._typo_caches:
                                try:
                                    with open(typo_path, 'r', encoding='utf-8') as f:
                                        self._typo_caches[typo_path] = json.load(f)
                                    log_xray(f"   -> [Cache] Đã nạp rules sửa lỗi OCR từ '{typo_path.name}' vào RAM.")
                                except Exception as e:
                                    log_xray(f"   -> [Lỗi] Không đọc được file sửa lỗi: {e}")
                            
                            # Áp dụng thay thế cục bộ
                            if typo_path in self._typo_caches:
                                typo_dict = self._typo_caches[typo_path]
                                # Ép kiểu IN HOA để xử lý triệt để biến thể (ỦỦ, ủủ, Ủủ...)
                                clean_text = aggregated_text.upper() 
                                is_cleaned = False
                                
                                for err_word, correct_word in typo_dict.items():
                                    if err_word in clean_text:
                                        clean_text = clean_text.replace(err_word, correct_word)
                                        log_xray(f"   -> [Pre-process] Đã tự động sửa lỗi OCR: '{err_word}' -> '{correct_word}'")
                                        is_cleaned = True
                                        
                                # Cập nhật chuỗi mồi nhử nếu có sự thay đổi
                                if is_cleaned:
                                    aggregated_text = clean_text
                    
                    log_xray(f"   -> [Deep Trace] Giới hạn quét: {scan_limit} dòng đầu tiên.")
                    log_xray(f"   -> [Deep Trace] Chuỗi mồi nhử: '{aggregated_text}'")
                    
                    # 5. Rà soát Regex với neo nhảy cóc '|'
                    for raw_kw in raw_keywords:
                        # Auto-strip: Cắt tỉa khoảng trắng xung quanh dấu '|'
                        parts = [p.strip() for p in raw_kw.split('|')]
                        normalized_value = " ".join(parts)
                        
                        # Biến đổi thành Regex: Chèn lỗ đen '.*?' vào giữa các mảnh
                        escaped_parts = [re.escape(p) for p in parts]
                        regex_pattern = r".*?".join(escaped_parts)
                        
                        # Quét Regex không phân biệt Hoa/Thường (re.IGNORECASE)
                        if re.search(regex_pattern, aggregated_text, re.IGNORECASE):
                            log_xray(f"   -> [Deep Trace] TRÚNG ĐÍCH! Từ khóa gốc: '{raw_kw}'")
                            log_xray(f"   -> [Deep Trace] Regex sinh tự động: '{regex_pattern}'")
                            result[field] = normalized_value
                            log_xray(f"EVENT=EXTRACTION_SUCCESS | FIELD={field} | METHOD={method} | VALUE='{result[field]}'")
                            matched = True
                            break
                            
                    if not matched:
                        log_xray(f"   -> [Deep Trace] THẤT BẠI. Không tìm thấy từ khóa nào khớp trong chuỗi gộp.")
                        log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD={method} | REASON=no_match")
                    
                elif method == "fixed_string_with_conditional_append":
                    val = rule.get('base_string', '')
                    if 'conditions' in rule:
                        for cond in rule['conditions']:
                            score = fuzz.partial_ratio(cond['keyword'].upper(), global_text.upper())
                            threshold = cond.get('threshold', 75)
                            if score > threshold:
                                log_xray(f"EVENT=CONDITION_MET | FIELD={field} | METHOD=conditional | KEYWORD='{cond['keyword']}' | SCORE={score} | THRESHOLD={threshold} | APPENDED='{cond['append_string']}'")
                                val += cond['append_string']
                            else:
                                log_xray(f"EVENT=CONDITION_FAILED | FIELD={field} | METHOD=conditional | KEYWORD='{cond['keyword']}' | SCORE={score} | THRESHOLD={threshold}")
                    result[field] = val

                # [UPGRADED] Logic fuzzy_key_value hỗ trợ line_offset và Regex gọt rác
                elif method == "fuzzy_key_value":
                    anchor = rule.get('anchor_keyword', '')
                    line_offset = rule.get('line_offset', 0)
                    val_regex = rule.get('value_regex', '')
                    threshold = rule.get('match_threshold', 80)
                    
                    result[field] = None
                    best_score = 0
                    matched_line_idx = -1
                    
                    anchor_len = len(anchor.strip())
                    
                    # Quét tìm dòng chứa mỏ neo tốt nhất
                    for i, line in enumerate(all_lines):
                        clean_line = line.text.strip()
                        
                        # [NEW] Dynamic Shield: Bỏ qua dòng rác quá ngắn so với mỏ neo (dưới 30% chiều dài)
                        if len(clean_line) < (anchor_len * 0.3):
                            continue
                            
                        score = fuzz.WRatio(anchor.lower(), clean_line.lower())
                        if score > best_score:
                            best_score = score
                            matched_line_idx = i
                            
                    if best_score > threshold:
                        target_idx = matched_line_idx + line_offset
                        if 0 <= target_idx < len(all_lines):
                            raw_text = all_lines[target_idx].text
                            log_xray(f"EVENT=ANCHOR_MATCH | FIELD={field} | METHOD=fuzzy_key_value | ANCHOR='{anchor}' | OFFSET={line_offset} | SCORE={best_score} | LINE='{raw_text}'")
                            
                            if val_regex:
                                match = re.search(val_regex, raw_text)
                                if match:
                                    result[field] = match.group(1).strip() if match.groups() else match.group(0).strip()
                                    log_xray(f"EVENT=EXTRACTION_SUCCESS | FIELD={field} | METHOD=fuzzy_key_value | VALUE='{result[field]}'")
                                else:
                                    log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD=fuzzy_key_value | REASON=regex_shield_blocked")
                            else:
                                result[field] = raw_text.strip()
                                log_xray(f"EVENT=EXTRACTION_SUCCESS | FIELD={field} | METHOD=fuzzy_key_value | VALUE='{result[field]}'")
                        else:
                            log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD=fuzzy_key_value | REASON=offset_out_of_bounds")
                    else:
                        log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD=fuzzy_key_value | REASON=anchor_not_found | SCORE={best_score}")

                elif method == "extract_between_anchors":
                    start_anchor = rule['start_anchor']
                    end_anchor = rule['end_anchor']
                    strict_start = rule.get('strict_start', False)
                    strict_end = rule.get('strict_end', False)
                    result[field] = None
                    start_idx = -1
                    end_idx = -1
                    
                    for i, line in enumerate(all_lines):
                        if start_idx == -1:
                            start_scorer = fuzz.ratio if strict_start else fuzz.partial_ratio
                            start_score = start_scorer(start_anchor.lower(), line.text.lower())
                            
                            if start_score > rule.get('match_threshold', 85):
                                start_idx = i
                                log_xray(f"EVENT=ANCHOR_MATCH | FIELD={field} | METHOD=extract_between_anchors | TYPE=start | ANCHOR='{start_anchor}' | SCORE={start_score} | LINE='{line.text}'")
                                continue
                                
                        if start_idx != -1 and end_idx == -1:
                            end_scorer = fuzz.ratio if strict_end else fuzz.partial_ratio
                            end_score = end_scorer(end_anchor.lower(), line.text.lower())
                            
                            if end_score > rule.get('match_threshold', 85):
                                end_idx = i
                                log_xray(f"EVENT=ANCHOR_MATCH | FIELD={field} | METHOD=extract_between_anchors | TYPE=end | ANCHOR='{end_anchor}' | SCORE={end_score} | LINE='{line.text}'")
                                break
                                
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        extracted_lines = all_lines[start_idx + 1 : end_idx]
                        if extracted_lines:
                            result[field] = " ".join([l.text for l in extracted_lines]).strip()
                            log_xray(f"EVENT=EXTRACTION_SUCCESS | FIELD={field} | METHOD=extract_between_anchors | LINES_COUNT={len(extracted_lines)} | VALUE='{result[field]}'")
                        else:
                            log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD=extract_between_anchors | REASON=empty_between_anchors")
                    else:
                        log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD=extract_between_anchors | START_IDX={start_idx} | END_IDX={end_idx}")

                # [NEW] Logic Kế thừa từ Vùng nhớ chung
                elif method == "inherit_from_context":
                    context_key = rule.get('context_key')
                    if context_key and context_key in dossier_context:
                        result[field] = dossier_context[context_key]
                        log_xray(f"EVENT=EXTRACTION_SUCCESS | FIELD={field} | METHOD=inherit_from_context | INHERITED_FROM='{context_key}' | VALUE='{result[field]}'")
                    else:
                        result[field] = None
                        log_xray(f"EVENT=EXTRACTION_FAILED | FIELD={field} | METHOD=inherit_from_context | REASON=context_key_not_found_or_empty")

            # [NEW] Xuất dữ liệu ra Vùng nhớ (Nếu cấu hình yêu cầu)
            if 'export_to_context' in rule and result.get(field):
                context_key = rule['export_to_context']
                dossier_context[context_key] = result[field]
                log_xray(f"EVENT=CONTEXT_UPDATE | KEY='{context_key}' | VALUE='{result[field]}'")


        # ==============================================================
        # KIẾN TRÚC MỚI: TÍCH HỢP POST-PROCESSOR Ở CUỐI ĐƯỜNG ỐNG
        # ==============================================================
        # Tiêm hàm log_xray hiện tại vào class độc lập
        post_processor = PostProcessor(logger=log_xray) 
        
        for rule in self.config.get('extraction_rules', []):
            field = rule['field_name']
            
            # Chỉ chạy làm sạch nếu có dữ liệu và rule json có yêu cầu
            if result.get(field) and 'post_processing' in rule:
                processors = rule['post_processing']
                if isinstance(processors, list):
                    old_val = result[field]
                    result[field] = post_processor.run_pipeline(result[field], processors)
                    log_xray(f"EVENT=POST_PROCESSING_APPLIED | FIELD={field} | OLD='{old_val}' | NEW='{result[field]}'")
            
        return result

class SessionManager:
    def __init__(self, catalog_config: dict = None):
        self.active_session = None
        self.extracted_records = []
        self.plugins = []
        self._load_plugins()
        self.dossier_context = {}

    def _load_plugins(self):
        config_dir = Path(__file__).resolve().parents[1] / "configs"
        for file_path in config_dir.glob('*.json'):
            if file_path.name == 'document_catalog.json': continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'extraction_rules' in config:
                        for rule in config['extraction_rules']:
                            if rule.get('extraction_method') == 'global_dictionary_match':
                                master_data = rule.get('master_data')
                                if isinstance(master_data, str) and master_data.endswith('.txt'):
                                    txt_path = Path(__file__).resolve().parents[1] / master_data
                                    if txt_path.exists():
                                        with open(txt_path, 'r', encoding='utf-8') as txt_f:
                                            cached_list = [line.strip() for line in txt_f if line.strip()]
                                        rule['master_data'] = cached_list
                                    else:
                                        rule['master_data'] = []
                    if 'start_triggers' in config and 'end_triggers' in config:
                        self.plugins.append(config)
            except Exception as e:
                log_xray(f"EVENT=PLUGIN_LOAD_ERROR | FILE={file_path.name} | ERROR='{e}'")

    def _check_triggers(self, text: str, triggers: list, threshold: float, exclude_triggers: list = None) -> bool:
        if exclude_triggers:
            for ex_trigger in exclude_triggers:
                if fuzz.partial_ratio(ex_trigger.upper(), text) > threshold:
                    log_xray(f"EVENT=TRIGGER_BLOCKED | TYPE=exclude | KEYWORD='{ex_trigger}'")
                    return False

        for trigger in triggers:
            score = fuzz.partial_ratio(trigger.upper(), text)
            if score > threshold: 
                log_xray(f"EVENT=TRIGGER_MATCH | KEYWORD='{trigger}' | SCORE={score} | THRESHOLD={threshold}")
                return True
        return False
    
    def process_document_stream(self, stream_of_pages):
        for page in stream_of_pages:
            page_text = page['full_text']
            clean_text = page_text.replace('\n', ' ').upper()
            page_num = page['page_num']
            
            log_xray(f"\n\n[DEBUG_ROUTER] === BẮT ĐẦU XỬ LÝ TRANG {page_num} ===")
            
            matched_plugin = None
            is_end_trigger = False
            
            # 1. QUÉT TÌM START TRIGGER (MỞ PHIÊN)
            for plugin in self.plugins:
                radar_limit = plugin.get('radar_lines', 35)
                dynamic_header_text = " ".join(page_text.split('\n')[:radar_limit]).upper()
                
                if self._check_triggers(dynamic_header_text, 
                                        plugin.get('start_triggers', []), 
                                        plugin.get('start_threshold', 85), 
                                        plugin.get('exclude_triggers', [])):
                    matched_plugin = plugin
                    log_xray(f"[DEBUG_ROUTER] MATCHED START_PLUGIN: {plugin.get('document_type')}")
                    break
                    
            # 2. XỬ LÝ XUNG ĐỘT HEADER MỚI (Ngăn chặn gộp sai trang)
            if self.active_session and matched_plugin:
                is_single = matched_plugin.get('is_single_page', False)
                # Đóng phiên cũ bắt buộc nếu Header mới khác loại, HOẶC cùng loại nhưng là tài liệu 1 trang
                if (self.active_session.document_type != matched_plugin.get('document_type')) or is_single:
                    log_xray(f"[DEBUG_ROUTER] PHÁT HIỆN HEADER MỚI TẠI TRANG {page_num} -> BẮT BUỘC ĐÓNG PHIÊN CŨ ({self.active_session.document_type})")
                    record = self.active_session.flush_and_extract(self.dossier_context)
                    self.extracted_records.append(record)
                    self.active_session = None
            
            # 3. KHỞI TẠO PHIÊN MỚI
            if matched_plugin and self.active_session is None:
                doc_type = matched_plugin.get('document_type')
                log_xray(f"[X-RAY] EVENT=SESSION_START | PAGE={page_num} | DOC_TYPE={doc_type}")
                if doc_type == "giay_chung_nhan_qsdd":
                    self.dossier_context.clear()
                    log_xray(f"[X-RAY] EVENT=CONTEXT_RESET | REASON=new_dossier_started | DOC_TYPE={doc_type}")
                self.active_session = DocumentSession(matched_plugin)

            # 4. TRUYỀN DỮ LIỆU & KIỂM TRA END TRIGGER
            if self.active_session:
                # Trang hiện tại thuộc về phiên này (dù là phiên mới hay cũ), phải add data trước
                self.active_session.add_page_data(page_num, page['words'])
                
                current_config = self.active_session.config
                is_end_trigger = self._check_triggers(clean_text, 
                                                      current_config.get('end_triggers', []), 
                                                      current_config.get('end_threshold', 85))
                
                # 5. ĐÓNG PHIÊN NGAY LẬP TỨC NẾU TÌM THẤY ĐIỂM DỪNG
                if is_end_trigger:
                    log_xray(f"[DEBUG_ROUTER] MATCHED END_TRIGGER TẠI TRANG {page_num}")
                    log_xray(f"[X-RAY] EVENT=SESSION_END | PAGE={page_num} | DOC_TYPE={self.active_session.document_type}")
                    record = self.active_session.flush_and_extract(self.dossier_context)
                    self.extracted_records.append(record)
                    self.active_session = None

        if self.active_session:
            log_xray("[X-RAY] EVENT=STREAM_END | ACTION=force_close_session")
            self.extracted_records.append(self.active_session.flush_and_extract(self.dossier_context))
            
        return self.extracted_records