import sys
import os
import logging
from pathlib import Path
import numpy as np
import re

# =====================================================================
# THỦ THUẬT VENDORING & QUẢN LÝ BỐI CẢNH (CONTEXT MANAGER)
# =====================================================================
CURRENT_DIR = Path(__file__).parent
VENDOR_PATH = CURRENT_DIR / "deepdoc_vendor"
VIETOCR_PATH = VENDOR_PATH / "vietocr"

sys.path.insert(0, str(VENDOR_PATH.resolve()))
sys.path.insert(0, str(VIETOCR_PATH.resolve()))

# 🌟 BỌC TOÀN BỘ IMPORT VENDOR VÀO TRONG VÙNG DỊCH CHUYỂN CWD
_original_cwd = os.getcwd()
try:
    # Dịch chuyển tức thời vào lõi vietocr
    os.chdir(str(VIETOCR_PATH.resolve()))
    
    # Lúc này, mọi phản ứng dây chuyền import đều diễn ra trong thư mục chuẩn
    from module.layout_recognizer import LayoutRecognizer   # type: ignore
    from module.table_structure_recognizer import TableStructureRecognizer  # type: ignore
    from module.ocr import OCR  # type: ignore
finally:
    # Lập tức trả hệ thống về vị trí làm việc gốc
    os.chdir(_original_cwd) 

from .base_engine import BaseOcrEngine
from ..models import OcrResult, OcrWord, BoundingBox


logger = logging.getLogger(__name__)

def convert_html_table_to_md(html_str: str) -> str:
    """Dịch mã HTML thô của DeepDoc thành Bảng Markdown chuẩn"""
    if not html_str: return ""
    rows = re.findall(r'<tr.*?>(.*?)</tr>', html_str, re.IGNORECASE | re.DOTALL)
    if not rows: return ""
    
    md_table = []
    for i, row in enumerate(rows):
        cells = re.findall(r'<t[dh].*?>(.*?)</t[dh]>', row, re.IGNORECASE | re.DOTALL)
        # Xóa các thẻ HTML thừa bên trong ô
        clean_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
        md_row = "| " + " | ".join(clean_cells) + " |"
        md_table.append(md_row)
        
        # Thêm dòng kẻ phân cách tiêu đề bảng
        if i == 0:
            md_table.append("|" + "|".join(["---"] * len(cells)) + "|")
            
    return "\n" + "\n".join(md_table) + "\n"

def build_markdown_from_words(words_list, img_w, img_h) -> str:
    """Gom cụm không gian (Y-Tolerance, X-Gap) để tạo Markdown"""
    # Ngưỡng động dựa trên kích thước ảnh (Chống hardcode)
    y_tolerance = max(10, int(img_h * 0.012))  # ~1.2% chiều cao ảnh
    x_gap_threshold = max(30, int(img_w * 0.03)) # ~3.0% chiều rộng ảnh
    
    # Sắp xếp toàn bộ các khối (Text + Table) từ trên xuống dưới
    sorted_words = sorted(words_list, key=lambda w: w.bbox.points[0][1])
    
    md_output = []
    current_line = []
    current_y = None
    
    def flush_line():
        if not current_line: return
        # Sắp xếp các từ trong cùng 1 dòng từ trái qua phải
        current_line.sort(key=lambda x: x.bbox.points[0][0])
        line_str = ""
        prev_right = None
        
        for w in current_line:
            txt = w.text.strip()
            if not txt: continue
            
            left, right = w.bbox.points[0][0], w.bbox.points[1][0]
            
            if prev_right is not None:
                gap = left - prev_right
                # Nếu khoảng trống X đủ lớn -> Mô phỏng phân cột bằng ký tự '|'
                if gap > x_gap_threshold:
                    line_str += " \t|  " + txt 
                else:
                    line_str += " " + txt
            else:
                line_str += txt
                
            prev_right = right
        
        if line_str:
            # Gắn thẻ Tiêu đề Markdown nếu DeepDoc phát hiện đó là Title
            if any(w.block_type == 'title' for w in current_line):
                line_str = "## " + line_str
            md_output.append(line_str)
        current_line.clear()

    # Vòng lặp phân luồng
    for w in sorted_words:
        if w.block_type == 'table':
            flush_line() # Đẩy hết chữ đang chờ ra trước
            html_content = w.metadata.get("html", "")
            md_table = convert_html_table_to_md(html_content)
            md_output.append(md_table)
        else:
            y = w.bbox.points[0][1]
            if current_y is None:
                current_y = y
                current_line.append(w)
            elif abs(y - current_y) <= y_tolerance:
                current_line.append(w)
            else:
                flush_line()
                current_y = y
                current_line.append(w)
                
    flush_line() # Đẩy dòng cuối cùng
    return "\n".join(md_output)

class DeepdocEngine(BaseOcrEngine):
    def __init__(self, config):
        super().__init__(config)
        self.cfg = config.deepdoc
        
        # 1. Khởi tạo Layout Recognizer
        # Bắt buộc phải truyền chuỗi "layout" làm tham số domain
        logger.info("Đang nạp mô hình Layout mặc định của Vendor...")
        self.layout_detector = LayoutRecognizer("layout")
        
        # 2. Khởi tạo Table Structure Recognizer
        # Tương tự, nếu hàm này cần domain, ta có thể phải truyền "table", tạm thời để trống thử xem tác giả có gán mặc định không.
        logger.info("Đang nạp mô hình TSR mặc định của Vendor...")
        self.table_recognizer = TableStructureRecognizer() 
        
        # 3. Khởi tạo VietOCR ONNX
        logger.info("Đang nạp mô hình VietOCR ONNX mặc định của Vendor...")
        self.ocr_recognizer = OCR()

    def process_image(self, image: np.ndarray) -> OcrResult:
        logger.info("DeepDoc đang phân tích bố cục hình ảnh...")
        words_list = []
        
        try:
            # 1. DÒ TÌM BỐ CỤC (LAYOUT DETECTION)
            layout_res = self.layout_detector([image], [[]])
            layout_blocks = layout_res[0] if layout_res else []
            
            # 2. XỬ LÝ NẾU CÓ BỐ CỤC (Dành cho PDF, văn bản in chuẩn)
            for block in layout_blocks:
                raw_bbox = block.get('bbox', [])
                if not raw_bbox or len(raw_bbox) < 4:
                    continue
                    
                if isinstance(raw_bbox[0], (int, float)):
                    x1, y1, x2, y2 = map(int, raw_bbox[:4])
                    bbox_points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]] 
                else:
                    x1, y1 = int(raw_bbox[0][0]), int(raw_bbox[0][1])
                    x2, y2 = int(raw_bbox[2][0]), int(raw_bbox[2][1])
                    bbox_points = np.array(raw_bbox).tolist()
                
                h, w = image.shape[:2]
                x1, y1 = max(0, min(x1, w-1)), max(0, min(y1, h-1))
                x2, y2 = max(0, min(x2, w)), max(0, min(y2, h))
                
                if x2 <= x1 or y2 <= y1:
                    continue 
                    
                block_type = block.get('type', 'text').lower()
                
                if block_type == 'table':
                    table_img = image[y1:y2, x1:x2]
                    tsr_res = self.table_recognizer([table_img])
                    html_content = tsr_res[0] if tsr_res else ""
                    
                    word_obj = OcrWord(
                        text="[BẢNG DỮ LIỆU]",
                        confidence=1.0,
                        bbox=BoundingBox(points=bbox_points),
                        block_type="table",
                        metadata={"html": str(html_content)} 
                    )
                    words_list.append(word_obj)
                else:
                    text_img = image[y1:y2, x1:x2]
                    ocr_results = self.ocr_recognizer(text_img)
                    
                    texts, confs = [], []
                    if ocr_results:
                        for res in ocr_results:
                            texts.append(str(res[1][0]))
                            confs.append(float(res[1][1]))
                            
                    if texts:
                        recognized_text = "\n".join(texts)
                        conf = sum(confs) / len(confs)
                        
                        word_obj = OcrWord(
                            text=recognized_text,
                            confidence=conf,
                            bbox=BoundingBox(points=bbox_points),
                            block_type=block_type,
                            metadata={}
                        )
                        words_list.append(word_obj)

            # 3. 🌟 FALLBACK: QUÉT TOÀN BỘ ẢNH (Dành cho ảnh chụp, form viết tay)
            # Nếu mô hình Bố cục không tìm thấy gì, ta dùng thẳng bộ nhận diện DBNet + VietOCR quét lên toàn bộ ảnh gốc!
            if len(words_list) == 0:
                logger.info("Không nhận diện được bố cục khối. Chuyển sang quét OCR toàn bộ ảnh...")
                ocr_results = self.ocr_recognizer(image) 
                
                if ocr_results:
                    for res in ocr_results:
                        box_points = res[0] # Tọa độ 4 góc do AI tự cắt ra
                        text = str(res[1][0]) # Chữ nhận diện được
                        conf = float(res[1][1])
                        
                        word_obj = OcrWord(
                            text=text,
                            confidence=conf,
                            bbox=BoundingBox(points=box_points),
                            block_type="text",
                            metadata={}
                        )
                        words_list.append(word_obj)

            words_list.sort(key=lambda w: w.bbox.points[0][1])
            full_text = "\n".join([w.text for w in words_list if w.text])

            markdown_text = ""
            try:
                h, w = image.shape[:2]
                markdown_text = build_markdown_from_words(words_list, w, h)
                
                # CẮM MÁY TRỢ THÍNH VÀO ĐÂY:
                print(f"\n[DEBUG ENGINE]: Đã sinh ra chuỗi Markdown dài {len(markdown_text)} ký tự.\n")
                
            except Exception as e:
                # Ép lỗi sinh Markdown phải in ra Terminal bằng màu đỏ
                print(f"\n❌ [LỖI TẠO MARKDOWN]: {e}\n")

            # Cập nhật kết quả trả về
            return OcrResult(
                is_success=True,
                words=words_list,
                full_text=full_text,
                markdown_text=markdown_text 
            )

        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            logger.error(f"Lỗi phân tích: \n{err_msg}")
            return OcrResult(is_success=False, words=[], full_text="", error_message=str(e))