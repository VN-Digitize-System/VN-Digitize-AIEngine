from llm_engine.local_llm_provider import LocalLLMProvider

def run_local_test():
    print("🚀 BẮT ĐẦU KIỂM THỬ ĐỘC LẬP MÁY CHỦ LOCAL LLM (OLLAMA)...")
    
    # 1. Khởi tạo Provider (Sử dụng Qwen 2.5)
    local_ai = LocalLLMProvider()
    
    # 2. Dữ liệu giả lập (Văn bản chứa thông tin cần bóc)
    sample_text = """
    Tòa án nhân dân quận Bình Thạnh tuyên phạt bị cáo Nguyễn Văn A, sinh năm 1990, 
    mức án 3 năm tù giam về tội lừa đảo chiếm đoạt tài sản.
    """
    
    # 3. Cấu hình JSON Schema mong muốn
    schema = {
        "ten_bi_cao": "Họ và tên của bị cáo",
        "toi_danh": "Tội danh mà bị cáo vi phạm"
    }
    
    system_prompt = "Bạn là chuyên gia bóc tách dữ liệu pháp lý. Hãy trích xuất thông tin chính xác."
    
    # 4. Gọi hàm bóc tách
    print("\n[Hệ thống] Đang chờ LLM Local xử lý (Lần chạy đầu tiên có thể mất 10-30s để load model)...")
    result = local_ai.extract_batch_json(sample_text, schema, system_prompt)
    
    # 5. In kết quả
    print("\n" + "="*50)
    print("KẾT QUẢ BÓC TÁCH TỪ OLLAMA:")
    print("="*50)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("="*50 + "\n")

if __name__ == "__main__":
    run_local_test()