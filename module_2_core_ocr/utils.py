import cv2
import numpy as np
import math

def get_rotated_crop(image, box, padding=3):
    """
    Cắt ảnh dựa trên 4 điểm tọa độ, nắn thẳng và thêm padding để không rớt dấu.
    box: Danh sách 4 tọa độ [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    """
    pts = np.array(box, dtype="float32")
    
    # Tính toán chiều rộng và chiều cao của khung chữ
    width_1 = np.linalg.norm(pts[0] - pts[1])
    width_2 = np.linalg.norm(pts[2] - pts[3])
    height_1 = np.linalg.norm(pts[0] - pts[3])
    height_2 = np.linalg.norm(pts[1] - pts[2])
    
    max_width = int(max(width_1, width_2)) + padding * 2
    max_height = int(max(height_1, height_2)) + padding * 2
    
    # Định nghĩa 4 góc của bức ảnh nhỏ sau khi cắt (đã cộng padding)
    dst_pts = np.array([
        [padding, padding],
        [max_width - padding - 1, padding],
        [max_width - padding - 1, max_height - padding - 1],
        [padding, max_height - padding - 1]
    ], dtype="float32")
    
    # Ma trận biến đổi phối cảnh (Perspective Transform)
    M = cv2.getPerspectiveTransform(pts, dst_pts)
    
    # Cắt và nắn thẳng
    cropped_img = cv2.warpPerspective(image, M, (max_width, max_height))
    
    return cropped_img