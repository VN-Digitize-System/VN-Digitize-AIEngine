import cv2
import matplotlib.pyplot as plt
from document_preprocessor import DocumentPreprocessor

def test_deskew_only(image_path):
    print(f"Đang test chức năng Deskew cho ảnh: {image_path}...")
    
    processor = DocumentPreprocessor()
    
    # Đọc ảnh gốc
    original = cv2.imread(image_path)
    original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
    
    # Chỉ chạy hàm cắt và căn chỉnh độ lệch
    warped = processor.deskew_and_crop(image_path)
    
    # Hiển thị so sánh
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1)
    plt.title("1. Ảnh chụp cố tình để nghiêng lệch")
    plt.imshow(original_rgb)
    plt.axis("off")
    
    plt.subplot(1, 2, 2)
    plt.title("2. Kết quả Deskew & Auto-crop")
    plt.imshow(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    
    plt.tight_layout()
    plt.show()

# Thay tên file bằng ảnh nghiêng bạn vừa chụp
test_deskew_only("test_images/f1.jpg")

#Better: 2, 0006, 0007, 0008, 0012, 0014, 0015, 0016, ~0018,0024, 0025

#Error: 3, 4, 0004, 0009, 0010, 0011, 0013, 0017, 0020