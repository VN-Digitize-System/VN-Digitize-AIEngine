import cv2
import numpy as np
from pathlib import Path
from .models import OcrResult

def draw_ocr_results(image: np.ndarray, ocr_result: OcrResult, save_path: str = "debug_ocr_result.jpg"):
    """
    Hàm vẽ Bounding Box lên ảnh để trực quan hóa kết quả OCR.
    """
    # Tạo bản sao của ảnh để không làm hỏng ảnh gốc
    vis_img = image.copy()

    # KÍCH HOẠT KÊNH MÀU NẾU LÀ ẢNH TRẮNG ĐEN
    if len(vis_img.shape) == 2:
        vis_img = cv2.cvtColor(vis_img, cv2.COLOR_GRAY2BGR)

    if not ocr_result.is_success or not ocr_result.words:
        print("⚠️ Không có dữ liệu OCR để vẽ.")
        return vis_img

    for i, word in enumerate(ocr_result.words):
        # 1. Chuyển đổi tọa độ thành mảng numpy cho OpenCV
        pts = np.array(word.bbox.points, np.int32)
        pts = pts.reshape((-1, 1, 2))

        # 2. Vẽ khung Bounding Box (Màu xanh lá cây, viền độ dày 2)
        cv2.polylines(vis_img, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

        # 3. Ghi số thứ tự và Confidence Score (Màu đỏ) ở góc trên cùng bên trái của box
        x, y = word.bbox.points[0]
        # Dịch chữ lên trên một chút để không đè vào khung (y - 5)
        label = f"#{i+1} ({word.confidence:.2f})"
        cv2.putText(vis_img, label, (x, max(y - 5, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

    # Lưu ảnh xuống ổ cứng
    cv2.imwrite(save_path, vis_img)
    print(f"📸 Đã xuất ảnh vẽ Bounding Box tại: {save_path}")
    
    return vis_img