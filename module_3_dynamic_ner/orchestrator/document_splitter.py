import logging
import re
import unicodedata

# =====================================================================
# CẤU HÌNH HỆ THỐNG (CONFIGURATIONS)
# =====================================================================
EXCLUSION_KEYWORDS = ["chuong", "dieu", "muc", "phan", "khoan", "can cu"]

# =====================================================================
# HÀM TIỆN ÍCH LÕI (CORE UTILITIES)
# =====================================================================
def remove_vietnamese_accents(text: str) -> str:
    """
    Gỡ dấu tiếng Việt an toàn tuyệt đối sử dụng thư viện chuẩn unicodedata.
    """
    # Bước 1: Chuẩn hóa chuỗi về dạng NFD (tách riêng chữ cái và dấu)
    normalized_text = unicodedata.normalize('NFD', text)
    
    # Bước 2: Loại bỏ tất cả các ký tự thuộc nhóm 'Mn' (Mark, Nonspacing - tức là các dấu)
    stripped_text = ''.join(c for c in normalized_text if unicodedata.category(c) != 'Mn')
    
    # Bước 3: Xử lý riêng biệt chữ Đ/đ (do thuật toán NFD không tách ký tự này)
    stripped_text = re.sub(r'[đĐ]', lambda m: 'd' if m.group(0) == 'đ' else 'D', stripped_text)
    
    return stripped_text

def is_suspicious_header(text: str) -> bool:
    """
    TẦNG 3: Bộ lọc Kép (Dấu hiệu Hình thức + Lọc Cấu trúc Động).
    Trả về True nếu dòng text có khả năng cao là Tiêu đề của một tài liệu lạ.
    """
    clean_text = text.strip()
    
    # 1. Dấu hiệu hình thức: Phải in hoa toàn bộ và có độ dài hợp lý
    if len(clean_text) < 3 or not clean_text.isupper():
        return False

    # 2. Tiền xử lý bản nháp để so khớp
    normalized_text = remove_vietnamese_accents(clean_text.lower())
    
    # 3. Tạo Regex Động từ biến hằng
    keywords_pattern = "|".join(EXCLUSION_KEYWORDS)
    
    # Regex khớp:
    # - Số La Mã đứng đầu có dấu (vd: i., ii-, iii:)
    # - HOẶC Từ khóa loại trừ đi kèm Số La Mã/Số thường (vd: chuong ii, dieu 4)
    exclusion_pattern = rf"^(?:[ivxlcdm]+\s*[\.\-\:]|({keywords_pattern})\b\s+[ivxlcdm0-9]+\b)"
    
    if re.search(exclusion_pattern, normalized_text):
        # Nằm trong danh sách đen -> Là trang nội dung bình thường -> Im lặng đi tiếp
        return False
        
    # In hoa toàn bộ và không bị lọc -> Rất nghi ngờ!
    return True


# Cấu hình logging theo Hướng 2 (Verbose Tracing)
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class DocumentSplitter:
    def __init__(self):
        # Tầng 2: Từ khóa neo (Có thể mở rộng thêm)
        self.anchor_keywords = ["quyet dinh", "hop dong", "to trinh", "giay chung nhan", "ban an"]
        
    def _evaluate_tier_1(self, normalized_text: str) -> int:
        """Tầng 1: Chấm điểm Tiêu ngữ quốc gia"""
        score = 0
        if "cong hoa" in normalized_text: score += 2
        if "xa hoi" in normalized_text: score += 2
        if "doc lap" in normalized_text: score += 1
        if "tu do" in normalized_text: score += 1
        return score

    def _evaluate_tier_2(self, normalized_text: str) -> bool:
        """Tầng 2: Kiểm tra từ khóa neo trong 10 dòng đầu"""
        lines = normalized_text.split('\n')[:10]
        header_text = " ".join(lines)
        return any(keyword in header_text for keyword in self.anchor_keywords)

    def _stitch_and_optimize(self, page_buffer: list) -> str:
        """Cắt Đầu - Chốt Cuối và chèn Delimiter"""
        if len(page_buffer) <= 6:
            # Nếu tài liệu ngắn hơn hoặc bằng 6 trang, giữ nguyên
            return "\n\n".join([text for _, text in page_buffer])
        
        # Nếu dài hơn 6 trang: Lấy 3 trang đầu và 3 trang cuối
        head_pages = page_buffer[:3]
        tail_pages = page_buffer[-3:]
        
        head_text = "\n\n".join([text for _, text in head_pages])
        tail_text = "\n\n".join([text for _, text in tail_pages])
        
        delimiter = f"\n\n\n--- [HỆ THỐNG ĐÃ LƯỢC BỎ {len(page_buffer) - 6} TRANG NỘI DUNG Ở GIỮA ĐỂ TỐI ƯU VRAM] ---\n\n\n"
        
        return head_text + delimiter + tail_text

    def split_document(self, pages: list) -> list:
        """
        Hàm cốt lõi: Nhận vào mảng chữ OCR của n trang, trả về mảng Dict tài liệu.
        pages = ["text trang 1", "text trang 2", ...]
        """
        documents = []
        current_buffer = []  # Hướng B: Lưu Tuple (page_num, text)
        is_current_suspicious = False
        suspicion_reason = ""

        for idx, page_text in enumerate(pages):
            page_num = idx + 1
            clean_text = page_text.strip()
            if not clean_text:
                continue

            # Tiền xử lý bản nháp
            normalized_text = remove_vietnamese_accents(clean_text.lower())
            
            # Đánh giá 3 Tầng
            t1_score = self._evaluate_tier_1(normalized_text)
            t2_matched = self._evaluate_tier_2(normalized_text)
            
            lines = clean_text.split('\n')
            first_line = lines[0] if lines else ""
            t3_suspicious = is_suspicious_header(first_line) # Gọi hàm Chặng 1

            # Quyết định Cắt
            is_new_doc = False
            if t1_score >= 6:
                is_new_doc = True
                logger.info(f"[INFO] 📄 Trang {page_num}: Khớp Tầng 1 (Tiêu ngữ, Điểm: {t1_score}) -> ✂️ BẮT ĐẦU CẮT.")
            elif t2_matched:
                is_new_doc = True
                logger.info(f"[INFO] 📄 Trang {page_num}: Khớp Tầng 2 (Từ khóa neo) -> ✂️ BẮT ĐẦU CẮT.")
            elif t3_suspicious:
                is_new_doc = True
                is_current_suspicious = True
                suspicion_reason = f"Dòng 1 in hoa nghi ngờ: {first_line}"
                logger.warning(f"[WARN] ⚠️ Trang {page_num}: Khớp Tầng 3 (Dấu hiệu Hình thức). Kích hoạt cờ is_suspicious!")

            # Nếu là ranh giới tài liệu mới VÀ buffer đang có dữ liệu -> Đóng gói tài liệu cũ
            if is_new_doc and current_buffer:
                doc_dict = {
                    "start_page": current_buffer[0][0],
                    "end_page": current_buffer[-1][0],
                    "stitched_text": self._stitch_and_optimize(current_buffer),
                    "is_suspicious": is_current_suspicious,
                    "suspicion_reason": suspicion_reason,
                    "is_incomplete_scan": False # Chốt giữa mẻ nên an toàn
                }
                documents.append(doc_dict)
                logger.info(f"[SUCCESS] ✅ Đã đóng gói tài liệu từ trang {doc_dict['start_page']} đến {doc_dict['end_page']}.")
                
                # Reset trạng thái cho tài liệu mới
                current_buffer = []
                is_current_suspicious = t3_suspicious
                suspicion_reason = f"Dòng 1 in hoa nghi ngờ: {first_line}" if t3_suspicious else ""
            elif not is_new_doc:
                logger.info(f"[INFO] 📎 Gộp trang {page_num} vào nội dung hiện tại.")

            # Đưa trang hiện tại vào Giỏ
            current_buffer.append((page_num, clean_text))

        # Khóa sổ tài liệu cuối cùng (Orphan Flag)
        if current_buffer:
            doc_dict = {
                "start_page": current_buffer[0][0],
                "end_page": current_buffer[-1][0],
                "stitched_text": self._stitch_and_optimize(current_buffer),
                "is_suspicious": is_current_suspicious,
                "suspicion_reason": suspicion_reason,
                "is_incomplete_scan": True # Cờ báo động thiếu trang cuối
            }
            documents.append(doc_dict)
            logger.warning(f"[WARN] 🚩 Đóng gói tài liệu cuối cùng (Trang {doc_dict['start_page']} - {doc_dict['end_page']}). Đã bật cờ is_incomplete_scan!")

        return documents