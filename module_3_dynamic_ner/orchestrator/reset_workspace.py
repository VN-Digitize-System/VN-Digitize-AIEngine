import os
import glob
import logging

# Cấu hình log
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# CẤU HÌNH ĐƯỜNG DẪN
# =====================================================================
WORKSPACE_DIR = "../module_3_workspace/"
CHECKPOINT_DIR = os.path.join(WORKSPACE_DIR, "checkpoints/")
EXCEL_FILE = os.path.join(WORKSPACE_DIR, "tong_hop_bien_muc.xlsx")

def reset_workspace():
    logger.warning("\n⚠️ BẮT ĐẦU DỌN DẸP KHÔNG GIAN LÀM VIỆC...")
    
    # 1. Xóa toàn bộ Checkpoints
    if os.path.exists(CHECKPOINT_DIR):
        json_files = glob.glob(os.path.join(CHECKPOINT_DIR, "*.json"))
        for f in json_files:
            try:
                os.remove(f)
                logger.info(f"  🗑️ Đã xóa: {os.path.basename(f)}")
            except Exception as e:
                logger.error(f"  ❌ Lỗi khi xóa {f}: {e}")
        logger.info(f"✅ Đã dọn sạch {len(json_files)} file Checkpoint.")
    else:
        logger.info("ℹ️ Thư mục Checkpoints trống hoặc chưa tồn tại.")

    # 2. Xóa file báo cáo Excel
    if os.path.exists(EXCEL_FILE):
        try:
            os.remove(EXCEL_FILE)
            logger.info("✅ Đã xóa file báo cáo Excel cũ.")
        except Exception as e:
            logger.error(f"❌ Lỗi khi xóa file Excel: {e}")
    else:
        logger.info("ℹ️ File Excel chưa tồn tại.")
        
    logger.warning("✨ KHÔNG GIAN LÀM VIỆC ĐÃ SẠCH SẼ! Sẵn sàng cho mẻ chạy mới.\n")

if __name__ == "__main__":
    print("="*60)
    print("🔥 CÔNG CỤ NÚT ĐỎ - RESET MÔI TRƯỜNG MODULE 3 🔥")
    print("="*60)
    confirm = input("Bạn có chắc chắn muốn XÓA SẠCH toàn bộ dữ liệu bóc tách cũ? (y/n): ").strip().lower()
    
    if confirm == 'y':
        reset_workspace()
    else:
        logger.info("\n🛑 Đã hủy thao tác dọn dẹp. Dữ liệu vẫn an toàn.")