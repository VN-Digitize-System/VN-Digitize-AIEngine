import sys
import cv2
from pathlib import Path

# Cấu hình đường dẫn Root để import được các module lõi
ROOT_DIR = Path("F:/VN-Digitize-AIEngine")
sys.path.append(str(ROOT_DIR))

from module_2_core_ocr.engines.deepdoc_engine import DeepdocEngine
from module_2_core_ocr.config import OcrConfig
from shared_utils.logger import get_logger

logger = get_logger(__name__)

def main():
    print("🚀 [SMOKE TEST] Khởi động Kịch bản Test Độc lập...")

    # 1. Nạp cấu hình & Ép kích hoạt Động cơ Ký sinh (DeepDoc + Paddle)
    config = OcrConfig()


    engine = DeepdocEngine(config)

    # 2. Đường dẫn tới bức ảnh chứa Bảng biểu (scan_001.jpg)
    image_path = str(ROOT_DIR / "test_input/scan_014.png")
    img = cv2.imread(image_path)

    if img is None:
        print(f"❌ LỖI: Không tìm thấy ảnh tại {image_path}. Vui lòng kiểm tra lại tên file!")
        return

    print(f"\n📂 Đang nạp ảnh: {image_path}")
    print("⏳ Vui lòng đợi Động cơ phân tích...")
    
    # 3. Kích hoạt toàn bộ luồng xử lý
    result = engine.process_image(img)

    # 4. In Báo cáo Nghiệm thu ra Terminal
    print("\n" + "="*50)
    print("📊 KẾT QUẢ SMOKE TEST (NGHIỆM THU KIẾN TRÚC LẮP GHÉP)")
    print("="*50)
    print(f"Trạng thái chạy: {'✅ Thành công' if result.is_success else '❌ Thất bại'}")
    print(f"Tổng số phần tử (Text + Table) bóc ra: {len(result.words)}")
    
    table_count = sum(1 for w in result.words if w.block_type == 'table')
    text_count = len(result.words) - table_count
    print(f"  + Số Bảng (Table) phát hiện: {table_count}")
    print(f"  + Số Dòng chữ (Text) phát hiện: {text_count}")

    # 5. Lưu Markdown ra file để Debug bằng mắt thường
    output_md_path = ROOT_DIR / "test_output/smoke_test_result.md"
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(result.markdown_text)
        
    print(f"\n📝 Đã xuất file Markdown để đối chiếu tại: {output_md_path}")
    print("="*50)

if __name__ == "__main__":
    main()