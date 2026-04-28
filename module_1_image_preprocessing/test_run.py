import cv2
import matplotlib.pyplot as plt
from document_preprocessor import DocumentPreprocessor

def test_pipeline(image_path):
    print(f"Đang xử lý ảnh: {image_path}...")
    
    # 1. Khởi tạo class
    processor = DocumentPreprocessor()
    
    # 2. Đọc ảnh gốc (để hiển thị so sánh)
    original = cv2.imread(image_path)
    original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
    
    # 3. Bước 1: Cắt viền và kéo thẳng
    warped = processor.deskew_and_crop(image_path)
    
    # 4. Bước 2: Tẩy trắng và làm đậm chữ
    final_result = processor.enhance_document(warped)
    
    # --- HIỂN THỊ KẾT QUẢ BẰNG MATPLOTLIB ---
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.title("1. Ảnh gốc")
    plt.imshow(original_rgb)
    plt.axis("off")
    
    plt.subplot(1, 3, 2)
    plt.title("2. Sau khi cắt (Warped)")
    # Chuyển BGR sang RGB để matplotlib hiển thị đúng màu
    plt.imshow(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)) 
    plt.axis("off")
    
    plt.subplot(1, 3, 3)
    plt.title("3. Sau khi tẩy trắng (Final)")
    plt.imshow(final_result, cmap='gray')
    plt.axis("off")
    
    plt.tight_layout()
    plt.show()

# Thay tên file bằng ảnh bạn vừa chụp nhé!
test_pipeline("test_images/1.jpg")