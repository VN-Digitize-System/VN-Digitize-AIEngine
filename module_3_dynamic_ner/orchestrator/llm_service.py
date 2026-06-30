import requests
import json
import re
import time
import logging

# Cấu hình log
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# 1. GIAO DIỆN TERMINAL HITL (MINI DASHBOARD)
# =====================================================================
def draw_hitl_dashboard(document_preview: str) -> str:
    """
    Vẽ Bảng điều khiển Mini khi Lưỡi dao phát hiện tài liệu lạ.
    Trả về lựa chọn (1, 2, hoặc 3) của người dùng.
    """
    print("\n" + "═"*70)
    print("⚠️  PHÁT HIỆN TÀI LIỆU LẠ (CHƯA CÓ LƯỢC ĐỒ)")
    print("─"*70)
    print(f"[Nội dung trích xuất]:\n{document_preview}")
    print("─"*70)
    print("Chọn hành động điều hướng:")
    print("  [1] Dạy AI bóc tách (Nhập trường dữ liệu sinh Schema mới)")
    print("  [2] Bỏ qua (Đẩy tài liệu này vào Tab 'Chưa phân loại' trên Excel)")
    print("  [3] Dừng khẩn cấp toàn bộ hệ thống Batch")
    print("═"*70)
    
    while True:
        choice = input("Nhập lựa chọn của bạn (1/2/3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        print("[Lỗi] Vui lòng chỉ nhập số 1, 2, hoặc 3.")

# =====================================================================
# 2. CLIENT GIAO TIẾP OLLAMA REST API (CÓ TÍCH HỢP MOCK TOGGLE)
# =====================================================================
class OllamaClient:
    def __init__(self, model_name="qwen2.5:14b", timeout=90, use_mock=True):
        """
        use_mock=True: Chuyển mạch sang chế độ Giả lập, không gọi mạng qua Ollama.
        """
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        self.timeout = timeout
        self.use_mock = use_mock
        
        self._warmup_ping()

    def _warmup_ping(self):
        """Khởi động lạnh: Ép Ollama load weights vào VRAM"""
        if self.use_mock:
            logger.info("\n[MOCK] Đang làm nóng bộ não Giả lập... (Bỏ qua nạp VRAM thật).")
            logger.info("[MOCK] 🚀 Chế độ Dry Run đã sẵn sàng hành trình!\n")
            return

        logger.info("\n[SYSTEM] Đang làm nóng VRAM cho mô hình qwen2.5:14b... Vui lòng đợi (khoảng 10-15s).")
        try:
            payload = {"model": self.model_name, "prompt": "hi", "stream": False}
            requests.post(self.api_url, json=payload, timeout=120)
            logger.info("[OK] 🚀 Mô hình đã nằm gọn trong VRAM. Tốc độ bóc tách tối đa đã sẵn sàng!\n")
        except Exception as e:
            logger.warning(f"[WARN] Lỗi làm nóng VRAM: {e}. Lượt chạy đầu tiên có thể sẽ bị chậm.\n")

    def _extract_json_from_text(self, text: str) -> str:
        """Thợ săn JSON: Dùng Regex chém bỏ chữ thừa của LLM"""
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match:
            return match.group(0)
        return "{}"

    def generate_json(self, prompt: str, max_retries=3) -> dict:
        """
        Gửi Prompt bóc tách. Có cơ chế Thử lại & Bỏ qua (Retry & Skip Fail-safe)
        """
        # HƯỚNG B: Nếu bật Công tắc Giả lập, tự động trả kết quả Mock cố định
        if self.use_mock:
            time.sleep(0.5) # Giả lập độ trễ xử lý của AI
            return {
                "ten_tai_lieu": "Quyết định hành chính (Giả lập)",
                "so_hieu": "99/QĐ-MOCK",
                "ngay_ban_hanh": "2026-06-28",
                "co_quan_ban_hanh": "Ủy ban Nhân dân Tỉnh",
                "trang_thai_trich_xuat": "Thành công (Mock API)"
            }

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1}
        }

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(self.api_url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                
                raw_text = response.json().get("response", "")
                clean_json_str = self._extract_json_from_text(raw_text)
                
                return json.loads(clean_json_str)

            except requests.exceptions.RequestException as e:
                logger.warning(f"[RETRY {attempt}/{max_retries}] ⚠️ Mạng nội bộ lỗi hoặc Timeout: {e}")
            except json.JSONDecodeError as e:
                logger.warning(f"[RETRY {attempt}/{max_retries}] ⚠️ Lỗi Parse JSON (Mô hình ảo giác): {e}")
            
            if attempt < max_retries:
                time.sleep(5)

        logger.error("[SKIP] ❌ Đã thử lại 3 lần nhưng thất bại. Bỏ qua tài liệu này.")
        return {"error": "LLM Extraction Failed after 3 retries."}