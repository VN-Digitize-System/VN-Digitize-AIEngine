from __future__ import annotations

import cv2
import numpy as np

from .config import CropDeskewConfig
from shared_utils.logger import get_logger

logger = get_logger(__name__)

# Thử nhiều epsilon để kiên nhẫn dò tìm góc
_APPROX_EPSILONS = [0.02, 0.03, 0.04, 0.05, 0.06]

def detect_and_crop(
    image: np.ndarray, cfg: CropDeskewConfig
) -> tuple[np.ndarray, float, np.ndarray]:
    """
    Code C: Kết hợp Downscaling (Code A) và Iterative Search + Fallback (Code B).
    Trả về: (Ảnh đã crop/deskew, góc nghiêng, Ảnh debug vẽ góc).
    """
    debug_img = image.copy()

    if not cfg.enabled:
        return image, 0.0, debug_img

    # =========================================================================
    # BƯỚC 1: THU NHỎ ẢNH ĐỂ KHỬ NHIỄU VÀ TĂNG TỐC (Tinh hoa của Code A)
    # =========================================================================
    target_height = 500.0
    ratio = image.shape[0] / target_height
    # Tính chiều rộng tương ứng để giữ nguyên tỷ lệ khung hình
    new_width = int(image.shape[1] / ratio)
    resized_image = cv2.resize(image, (new_width, int(target_height)))
    
    gray_resized = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)

    # =========================================================================
    # BƯỚC 2: TÌM CẠNH TRÊN ẢNH ĐÃ THU NHỎ (Kết hợp Bilateral của B và Morph của A)
    # =========================================================================
    blurred = cv2.bilateralFilter(gray_resized, 9, 75, 75)
    edges = cv2.Canny(blurred, cfg.canny_threshold1, cfg.canny_threshold2)

    # Đóng vùng viền (Morphological Closing) từ Code A để nối các nét đứt
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Tìm viền trên ảnh nhỏ
    contours, _ = cv2.findContours(
        closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Tìm 4 góc trên khung hình thu nhỏ
    corners = _find_document_contour(contours, resized_image.shape, cfg)

    # =========================================================================
    # BƯỚC 3: ÁP DỤNG LÊN ẢNH GỐC & TRẢ KẾT QUẢ
    # =========================================================================
    if corners is not None:
        # Nhập môn Toán học: Map tọa độ từ ảnh nhỏ về lại ảnh gốc chất lượng cao
        original_corners = corners * ratio

        # --- Vẽ Debug ---
        int_corners = original_corners.astype(int)
        # Vẽ viền xanh lá (như Code A) để biểu thị Code C đã chạy thành công
        cv2.drawContours(debug_img, [int_corners], -1, (0, 255, 0), 5)
        for point in int_corners:
            cv2.circle(debug_img, tuple(point), 15, (0, 0, 255), -1)

        # Cắt và kéo phẳng trên ẢNH GỐC (chất lượng cao)
        warped = _perspective_transform(image, original_corners, cfg.perspective_padding)
        
        # Tính góc nghiêng
        ordered = _order_corner_points(original_corners)
        dx = float(ordered[1][0] - ordered[0][0])
        dy = float(ordered[1][1] - ordered[0][1])
        angle = float(np.degrees(np.arctan2(dy, dx)))
        
        logger.debug(f"Perspective warp applied: skew_angle={angle:.2f}°")
        return warped, angle, debug_img

    # =========================================================================
    # BƯỚC 4: CƠ CHẾ PHÒNG THỦ KHI THẤT BẠI (Tinh hoa của Code B)
    # =========================================================================
    logger.debug("Không tìm thấy 4 góc, kích hoạt Hough deskew phòng thủ!")
    gray_orig = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    rotated, hough_angle = _deskew_by_hough(image, gray_orig, cfg.max_skew_angle)
    
    return rotated, hough_angle, debug_img


# def _find_document_contour(
#     contours: list, image_shape: tuple, cfg: CropDeskewConfig
# ) -> np.ndarray | None:
#     image_area = image_shape[0] * image_shape[1]
#     min_area = image_area * cfg.min_area_ratio

#     for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:8]:
#         if cv2.contourArea(contour) < min_area:
#             break

#         peri = cv2.arcLength(contour, True)

#         # Iterative Search (Code B)
#         for eps in _APPROX_EPSILONS:
#             approx = cv2.approxPolyDP(contour, eps * peri, True)
#             if len(approx) == 4:
#                 return approx.reshape(4, 2).astype(np.float32)
#     return None

def _find_document_contour(
    contours: list, image_shape: tuple, cfg: CropDeskewConfig
) -> np.ndarray | None:
    image_area = image_shape[0] * image_shape[1]
    
    # Giới hạn dưới: Phải to hơn 10% ảnh (chặn cắt rác nhỏ)
    min_area = image_area * cfg.min_area_ratio
    
    # GIỚI HẠN TRÊN: Phải nhỏ hơn 98% ảnh (Chặn cắt nhầm viền khung camera)
    max_area = image_area * 0.98 

    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:8]:
        area = cv2.contourArea(contour)
        
        # Nếu nhỏ quá thì thuật toán dừng luôn (vì đã sort từ to xuống nhỏ)
        if area < min_area:
            break
            
        # NẾU TO QUÁ 98% -> ĐÂY LÀ KHUNG CAMERA -> BỎ QUA VÀ ĐI TIẾP
        if area > max_area:
            continue

        peri = cv2.arcLength(contour, True)

        # Thử nhiều mức epsilon để uốn góc
        for eps in _APPROX_EPSILONS:
            approx = cv2.approxPolyDP(contour, eps * peri, True)
            if len(approx) == 4:
                area_ratio = area / image_area
                logger.debug(f"Đã tìm thấy giấy: area_ratio={area_ratio:.2f}, epsilon={eps}")
                return approx.reshape(4, 2).astype(np.float32)

    return None

def _order_corner_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def _perspective_transform(
    image: np.ndarray, corners: np.ndarray, padding: int
) -> np.ndarray:
    rect = _order_corner_points(corners)
    tl, tr, br, bl = rect

    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))

    p = padding
    dst = np.array(
        [[p, p], [width + p, p], [width + p, height + p], [p, height + p]],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (width + 2 * p, height + 2 * p))

def _deskew_by_hough(
    image: np.ndarray, gray: np.ndarray, max_angle: float
) -> tuple[np.ndarray, float]:
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=100, maxLineGap=10)

    if lines is None:
        return image, 0.0

    angles = [
        float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        for x1, y1, x2, y2 in (line[0] for line in lines)
        if abs(np.degrees(np.arctan2(y2 - y1, x2 - x1))) <= max_angle
    ]

    if not angles:
        return image, 0.0

    median_angle = float(np.median(angles))
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return rotated, median_angle