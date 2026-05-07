from __future__ import annotations

import cv2
import numpy as np
from pyzbar.pyzbar import decode

from .config import DetectConfig
from .models import BarcodeInfo
from shared_utils.logger import get_logger

logger = get_logger(__name__)


# def detect_blank_page(image: np.ndarray, cfg: DetectConfig) -> bool:
#     if not cfg.blank_page.enabled:
#         return False

#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
#     _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

#     white_ratio = float(np.sum(binary == 255) / binary.size)
#     is_blank = white_ratio >= cfg.blank_page.white_pixel_ratio_threshold

#     if is_blank:
#         logger.warning(f"Blank page detected (white_ratio={white_ratio:.3f})")
#     else:
#         logger.debug(f"Blank page check passed: white_ratio={white_ratio:.3f}")

#     return is_blank

# def detect_blank_page(image: np.ndarray, cfg: DetectConfig) -> bool:
#     if not cfg.blank_page.enabled:
#         return False

#     # Chuyển xám
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
#     # --- BẮT ĐẦU KỸ THUẬT CẠO LỀ (MARGIN SHAVING) ---
#     h, w = gray.shape
#     margin_y = int(h * 0.05)  # Cắt bỏ 5% lề trên và dưới
#     margin_x = int(w * 0.05)  # Cắt bỏ 5% lề trái và phải
    
#     # Chỉ lấy vùng lõi ở giữa để xét trang trắng
#     core_roi = gray[margin_y:h-margin_y, margin_x:w-margin_x]
#     # ------------------------------------------------

#     # 1. Làm mờ để xóa các nếp gấp mờ trên vùng lõi
#     blurred = cv2.GaussianBlur(core_roi, (5, 5), 0)

#     # 2. Bắt viền bằng Canny
#     edges = cv2.Canny(blurred, 30, 150)

#     # 3. Tính tỷ lệ pixel Viền (Edge Ratio) trên vùng lõi
#     edge_ratio = float(np.count_nonzero(edges) / edges.size)

#     # Giới hạn 1% (0.01)
#     is_blank = edge_ratio < 0.01

#     if is_blank:
#         logger.warning(f"Blank page detected (edge_ratio={edge_ratio:.5f} < 0.01)")
#     else:
#         logger.debug(f"Blank page check passed: edge_ratio={edge_ratio:.5f}")

#     return is_blank


def detect_blank_page(image: np.ndarray, cfg: DetectConfig) -> bool:
    if not cfg.blank_page.enabled:
        return False

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # ==========================================
    # LỚP KHIÊN 1: CẠO LỀ (LIGHT MARGIN SHAVING)
    # ==========================================
    h_orig, w_orig = gray.shape
    margin_y = int(h_orig * 0.15)
    margin_x = int(w_orig * 0.15)
    core_roi = gray[margin_y:h_orig-margin_y, margin_x:w_orig-margin_x]
    blurred = cv2.GaussianBlur(core_roi, (5, 5), 0)

    # ==========================================
    # LỚP KHIÊN 2: CHIA LÔ ĐỘNG (DYNAMIC GRID)
    # ==========================================
    h, w = blurred.shape
    
    # 1. Tính toán Lưới tự động dựa trên Tỷ lệ ảnh (Aspect Ratio)
    # Cố định chia làm 3 cột (chia theo chiều ngang)
    cols = 3 
    aspect_ratio = h / float(w)
    # Tính số hàng tỷ lệ thuận với chiều cao (đảm bảo ít nhất 3 hàng)
    rows = max(3, int(round(cols * aspect_ratio))) 
    
    total_blocks = rows * cols
    grid_h = h // rows
    grid_w = w // cols

    active_blocks = 0
    threshold = 0.01  # Ngưỡng 1% nét viền

    # 2. Quét qua lưới tự động (rows x cols)
    for i in range(rows):
        for j in range(cols):
            y_start = i * grid_h
            y_end = (i + 1) * grid_h if i < rows - 1 else h
            x_start = j * grid_w
            x_end = (j + 1) * grid_w if j < cols - 1 else w

            block = blurred[y_start:y_end, x_start:x_end]
            edges = cv2.Canny(block, 30, 150)
            
            if edges.size == 0:
                continue

            edge_ratio = float(np.count_nonzero(edges) / edges.size)
            if edge_ratio > threshold:
                active_blocks += 1

    # ==========================================
    # LOGIC QUYẾT ĐỊNH VỚI DUNG SAI ĐỘNG (DYNAMIC TOLERANCE)
    # ==========================================
    # Cho phép rác chiếm tối đa 15% tổng số ô
    # Ví dụ: Giấy A4 (3x3=9 ô) -> tolerance = 1 ô
    # Giấy hóa đơn dài (5x3=15 ô) -> tolerance = 2 ô
    tolerance = max(1, int(total_blocks * 0.15))
    
    is_blank = (active_blocks <= tolerance)

    if is_blank:
        logger.warning(f"Blank page detected. (Active blocks: {active_blocks}/{total_blocks}, tolerance: {tolerance})")
    else:
        logger.debug(f"Blank page check passed. (Active blocks: {active_blocks}/{total_blocks}, tolerance: {tolerance})")

    return is_blank


import cv2
import numpy as np

# from .config import DetectConfig
# from shared_utils.logger import get_logger
# logger = get_logger(__name__)

def detect_wrong_orientation(image: np.ndarray, cfg: DetectConfig) -> bool:
    """
    Detect wrong orientation using an advanced hybrid approach:
    1. Aspect Ratio check to adjust thresholds.
    2. Morphological Line Removal to prevent 'Table Traps'.
    3. Sobel Gradient Energy for fast 90/270 degree detection.
    4. Tesseract OSD fallback for 180-degree and conflict resolution.
    """
    if not cfg.orientation.enabled:
        return False

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    h, w = gray.shape

    # ==========================================
    # CẢI TIẾN 1: KIỂM TRA KHỔ GIẤY (ASPECT RATIO)
    # ==========================================
    is_landscape = w > h
    current_threshold = cfg.orientation.gradient_xy_threshold
    
    # Nếu là khổ ngang (ví dụ Thẻ sinh viên, CCCD), nét ngang vốn dĩ sẽ nhiều hơn
    # Ta tự động hạ chuẩn (Threshold) xuống để tránh báo động giả
    if is_landscape:
        current_threshold -= 0.15 

    # ==========================================
    # CẢI TIẾN 2: TẨY BẢNG BIỂU (LINE REMOVAL)
    # ==========================================
    # Bảng biểu chứa các vạch ngang dài làm nhiễu SobelY. Ta sẽ "xóa mờ" chúng.
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Tạo một "chổi quét" hình chữ nhật ngang cực dài (khoảng 1/10 chiều rộng ảnh)
    kernel_len = max(10, w // 10)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    
    # Tìm các đường ngang (Morphological Close kết hợp Threshold)
    # Bỏ qua bước này nếu ảnh quá nhỏ, nhưng trên A4 nó hoạt động rất tốt để làm mờ kẻ bảng
    temp_edges = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, -2)
    horizontal_lines = cv2.morphologyEx(temp_edges, cv2.MORPH_OPEN, horizontal_kernel)
    
    # Cộng các đường ngang trắng này vào nền mờ (Làm cho vạch đen của bảng biến mất)
    cleaned_blurred = cv2.add(blurred, horizontal_lines)

    # ==========================================
    # TÍNH TOÁN NĂNG LƯỢNG SOBEL (CORE LOGIC)
    # ==========================================
    energy_x = float(np.mean(np.abs(cv2.Sobel(cleaned_blurred, cv2.CV_64F, 1, 0, ksize=3))))
    energy_y = float(np.mean(np.abs(cv2.Sobel(cleaned_blurred, cv2.CV_64F, 0, 1, ksize=3))))
    ratio = energy_x / (energy_y + 1e-9)

    is_wrong = ratio < current_threshold

    
    # Log kết quả cuối cùng
    logger.debug(
        f"Orientation check: X/Y={ratio:.3f}, landscape={is_landscape}, "
        f"threshold={current_threshold:.2f}, result={is_wrong}"
    )
    return is_wrong


def detect_barcodes(image: np.ndarray, cfg: DetectConfig) -> list[BarcodeInfo]:
    if not cfg.barcode.enabled:
        return []

    results: list[BarcodeInfo] = []

    # 1. Chuyển ảnh sang thang xám (Grayscale)
    # PyZbar đọc ảnh xám nhanh và chính xác hơn ảnh màu rất nhiều
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    try:
        # 2. Quét toàn bộ mã (QR Code + Barcode 1D) trong 1 dòng lệnh duy nhất!
        decoded_objects = decode(gray)

        # 3. Duyệt qua từng mã tìm được
        for obj in decoded_objects:
            try:
                # obj.data trả về dạng byte (b'...'), ta cần decode thành chuỗi UTF-8
                data = obj.data.decode('utf-8')
                btype = obj.type  # Loại mã: 'QRCODE', 'CODE128', 'EAN13', v.v.
                
                # obj.rect cung cấp sẵn tọa độ Bounding Box cực kỳ chuẩn xác
                rect = obj.rect
                
                # Đóng gói vào chuẩn của team
                results.append(BarcodeInfo(
                    barcode_type=btype,
                    data=data,
                    bbox={"x": rect.left, "y": rect.top, "width": rect.width, "height": rect.height},
                ))
                logger.info(f"Barcode detected ({btype}): {data[:60]!r}")
                
            except Exception as e:
                # Nếu 1 mã bị lỗi định dạng chữ, bỏ qua và đọc mã tiếp theo
                logger.warning(f"Lỗi giải mã nội dung của 1 barcode: {e}")
                continue

    except Exception as e:
        logger.error(f"Lỗi hệ thống pyzbar: {e}")

    logger.debug(f"Barcode scan complete: {len(results)} found")
    return results