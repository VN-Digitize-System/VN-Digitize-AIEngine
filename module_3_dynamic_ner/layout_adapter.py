import json
import logging

# Cấu hình log
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def build_lines_from_ocr(ocr_words: list) -> list:
    """
    Giai đoạn 1 (v3.0): Gom dòng bằng Mỏ neo Tĩnh & Phân cụm Rút ruột (Anchor Extraction)
    Khắc phục triệt để lỗi "Hố đen phình dòng" và giữ vững đường dóng trục Ox.
    """
    if not ocr_words:
        return []

    # 1. Trích xuất thuộc tính hình học cho từng từ
    boxes = []
    for word_data in ocr_words:
        text = word_data.get('text', '')
        pts = word_data['bbox']['points']
        
        y_coords = [p[1] for p in pts]
        x_coords = [p[0] for p in pts]
        
        boxes.append({
            'text': text,
            'y_min': min(y_coords),
            'y_max': max(y_coords),
            'x_min': min(x_coords),
            'x_max': max(x_coords),
            'height': max(y_coords) - min(y_coords)
        })

    # 2. Sắp xếp toàn bộ chữ từ trên xuống dưới theo y_min
    boxes.sort(key=lambda b: b['y_min'])

    # 3. Thuật toán Phân cụm Rút ruột (Extraction Clustering)
    lines = []
    while boxes:
        # Lấy phần tử trên cùng làm Mỏ neo (Anchor) và xóa nó khỏi danh sách chờ
        anchor = boxes.pop(0)
        current_line = [anchor]
        
        # Danh sách chứa những từ không thuộc dòng của Mỏ neo này
        remaining_boxes = []
        
        for box in boxes:
            # Tính toán Giao thoa Trục Y so với MỎ NEO (không so sánh bắc cầu)
            top = max(anchor['y_min'], box['y_min'])
            bottom = min(anchor['y_max'], box['y_max'])
            overlap = bottom - top
            
            # Dùng chiều cao nhỏ hơn để tính tỷ lệ
            min_height = min(anchor['height'], box['height'])
            
            # Nếu đè lên Mỏ neo >= 30% -> Hút vào dòng hiện tại
            if overlap > 0 and (overlap / min_height) >= 0.3:
                current_line.append(box)
            else:
                # Không dính vào Mỏ neo -> Đẩy vào danh sách chờ cho vòng lặp sau
                remaining_boxes.append(box)
                
        # Cập nhật lại danh sách chờ (đã rút ruột các từ thuộc dòng hiện tại)
        boxes = remaining_boxes
        
        # 4. Sắp xếp các từ trong dòng vừa gom được theo thứ tự từ trái sang phải
        current_line.sort(key=lambda b: b['x_min'])
        lines.append(current_line)

    return lines

if __name__ == "__main__":
    # Đường dẫn tĩnh trỏ thẳng đến file JSON test
    test_file_path = r"F:\VN-Digitize-AIEngine\tests\data\outputs\unit_tests\module_2\test_batch_runner_GPU_crop_real_2\jsons\IMG_4635_ocr.json"    
    try:
        logger.info(f"🚀 Đang đọc dữ liệu thực tế từ: {test_file_path}")
        with open(test_file_path, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
        
        words_list = ocr_data.get("words", [])
        logger.info(f"📦 Đã nạp thành công {len(words_list)} khối từ. Đang khởi chạy Lưới không gian v3.0...\n")
        
        # Kích hoạt thuật toán Giai đoạn 1 v3.0
        grouped_lines = build_lines_from_ocr(words_list)
        
        print("="*70)
        print(" 🖨️ KẾT QUẢ GOM DÒNG (PHASE 1 - V3.0: ANCHOR EXTRACTION) ")
        print("="*70)
        for i, line in enumerate(grouped_lines):
            line_text = " | ".join([box['text'] for box in line])
            print(f"[Dòng {i+1:02d}] {line_text}")
        print("="*70)

    except FileNotFoundError:
        logger.error("❌ LỖI: Không tìm thấy file JSON. Kiểm tra lại đường dẫn.")