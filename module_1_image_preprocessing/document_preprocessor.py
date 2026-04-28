import cv2
import numpy as np

class DocumentPreprocessor:
    def __init__(self):
        pass

    def order_points(self, pts):
        """
        Hàm phụ trợ: Sắp xếp 4 điểm theo thứ tự chuẩn: 
        Top-Left, Top-Right, Bottom-Right, Bottom-Left
        (Rất quan trọng để kéo phẳng ảnh không bị lộn ngược)
        """
        rect = np.zeros((4, 2), dtype="float32")
        
        # Điểm Top-Left có tổng (x+y) nhỏ nhất, Bottom-Right có tổng lớn nhất
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Điểm Top-Right có hiệu (y-x) nhỏ nhất, Bottom-Left có hiệu lớn nhất
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect

    def deskew_and_crop(self, image_path):
        """Phiên bản nâng cấp: Xử lý nền nhiễu và giấy cong"""
        image = cv2.imread(image_path)
        if image is None:
            print("Lỗi: Không đọc được ảnh.")
            return None
            
        original = image.copy()
        
        # 1. Thu nhỏ ảnh để xử lý nhanh hơn (tùy chọn nhưng khuyên dùng với ảnh lớn)
        # Tính tỷ lệ thu nhỏ để sau khi tìm được góc sẽ map lại vào ảnh gốc
        ratio = image.shape[0] / 500.0
        orig = image.copy()
        image = cv2.resize(image, (int(image.shape[1] / ratio), 500))

        # 2. Xám hóa
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 3. Tăng cường làm mờ để xóa vân xi măng (Dùng bộ lọc Gaussian lớn hơn)
        blurred = cv2.GaussianBlur(gray, (11, 11), 0)
        
        # 4. Dò biên Canny
        edged = cv2.Canny(blurred, 30, 150) # Hạ ngưỡng để bắt viền tốt hơn
        
        # --- BƯỚC NÂNG CẤP: Đóng vùng (Morphological Closing) ---
        # Giúp nối các viền bị đứt đoạn do đổ bóng
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        edged = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
        
        # 5. Tìm đường bao
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        
        screen_cnt = None
        
        for c in contours:
            peri = cv2.arcLength(c, True)
            # --- BƯỚC NÂNG CẤP: Tăng epsilon từ 0.02 lên 0.04 hoặc 0.05 ---
            # Giúp chấp nhận các đường viền bị cong vênh
            approx = cv2.approxPolyDP(c, 0.04 * peri, True)
            
            if len(approx) == 4:
                screen_cnt = approx
                break
                
        if screen_cnt is None:
            print("Cảnh báo: Vẫn không tìm thấy viền tài liệu, trả về ảnh gốc!")
            return original

        # 6. Nhân tọa độ góc với tỷ lệ (ratio) để áp dụng lên ảnh gốc sắc nét
        pts = screen_cnt.reshape(4, 2) * ratio
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect

        # 7. Tính kích thước và Kéo phẳng
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(original, M, (maxWidth, maxHeight))

        return warped

    def enhance_document(self, warped_image):
        """Hàm tẩy trắng nền ố vàng và làm đậm nét chữ"""
        
        # 1. Đảm bảo ảnh đang ở hệ Grayscale (Xám)
        if len(warped_image.shape) == 3:
            gray = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = warped_image

        # 2. Áp dụng Adaptive Thresholding (Thuật toán Gaussian)
        # 255: Màu trắng (nền)
        # ADAPTIVE_THRESH_GAUSSIAN_C: Dùng thuật toán Gaussian cho kết quả mịn hơn
        # THRESH_BINARY: Chữ đen, nền trắng
        # 21: Block Size (Kích thước ô vuông xét duyệt)
        # 10: C (Hằng số bù trừ để lọc nhiễu li ti)
        binary = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            21, 10
        )

        # 3. Khử nhiễu muối tiêu (Salt & Pepper Noise)
        # Giấy cũ thường có các chấm đen li ti. Dùng Median Blur để xóa chúng.
        cleaned = cv2.medianBlur(binary, 3)

        return cleaned

# --- CÁCH SỬ DỤNG ---
# processor = DocumentPreprocessor()
# result_image = processor.deskew_and_crop("0004.jpg")
# cv2.imwrite("output_cropped.jpg", result_image)