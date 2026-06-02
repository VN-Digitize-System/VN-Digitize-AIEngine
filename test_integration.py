import os
import sys
import json
import subprocess
from datetime import datetime

# ================= CẤU HÌNH HỆ THỐNG =================
USE_CACHE = True  # Checkpointing
INPUT_BASE_DIR = "tests/test_data"
OUTPUT_BASE_DIR = "tests/output"
TEMP_BASE_DIR = "tests/temp"
REGISTRY_PATH = "configs/schema_registry.json"

# ================= REAL-TIME STREAMING LOG (Option C) =================
def run_module_cli(cmd: list, prefix: str, log_accumulator: list) -> bool:
    """Chạy tiến trình con bằng Popen và stream log thời gian thực ra Console"""
    
    # 1. Bơm thư mục gốc vào PYTHONPATH để Python nhận diện được mọi package (shared_utils, module_...)
    custom_env = os.environ.copy()
    custom_env["PYTHONPATH"] = os.path.abspath(os.getcwd())
    
    # 2. Bật Shell trên Windows để tự động phân giải lệnh 'conda' thành 'conda.bat'
    use_shell = sys.platform.startswith("win")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=custom_env,    # Kích hoạt đường dẫn gốc
            shell=use_shell    # Kích hoạt Shell tự động tìm Conda
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                clean_line = line.strip()
                formatted_log = f"[{prefix}] {clean_line}"
                print(formatted_log)  
                log_accumulator.append(formatted_log)  
                
        return process.returncode == 0
    except Exception as e:
        error_msg = f"[{prefix} CRASH] Lỗi thực thi lệnh: {str(e)}"
        print(error_msg)
        log_accumulator.append(error_msg)
        return False

# ================= INTEGRATION MAIN LUỒNG =================
def main():
    print("=== KHỞI CHẠY HỆ THỐNG KIỂM THỬ TÍCH HỢP ĐỒNG BỘ (CONDA ENV) ===")
    
    if not os.path.exists(REGISTRY_PATH):
        print(f"❌ [LỖI HỆ THỐNG] Không tìm thấy Kho lược đồ tại {REGISTRY_PATH}")
        return
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        schema_registry = json.load(f)

    if not os.path.exists(INPUT_BASE_DIR):
        print(f"Thư mục đầu vào '{INPUT_BASE_DIR}' rỗng. Vui lòng tạo thư mục và nạp hồ sơ.")
        return

    folders = sorted([d for d in os.listdir(INPUT_BASE_DIR) if os.path.isdir(os.path.join(INPUT_BASE_DIR, d))])
    
    for folder_name in folders:
        input_folder_path = os.path.join(INPUT_BASE_DIR, folder_name)
        output_folder_path = os.path.join(OUTPUT_BASE_DIR, folder_name)
        temp_folder_path = os.path.join(TEMP_BASE_DIR, folder_name)
        
        os.makedirs(output_folder_path, exist_ok=True)
        os.makedirs(temp_folder_path, exist_ok=True)
        
        print(f"\n📂 --------------------------------------------------")
        print(f"🚀 Đang xử lý tuần tự hồ sơ: {folder_name}")
        execution_log = [f"--- Nhật ký tiến trình hồ sơ {folder_name} | {datetime.now()} ---"]

        meta_path = os.path.join(input_folder_path, "meta.json")
        if not os.path.exists(meta_path):
            msg = f"❌ [FAIL-FAST] Bỏ qua hồ sơ do thiếu file meta.json tại {input_folder_path}"
            print(msg)
            with open(os.path.join(output_folder_path, "execution_log.txt"), "w", encoding="utf-8") as lf:
                lf.write(msg)
            continue
            
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
        
        template_key = meta_data.get("template")
        
        if template_key not in schema_registry:
            msg = f"❌ [FAIL-FAST] Từ khóa template '{template_key}' không tồn tại trong Registry. Chặn đứng xử lý!"
            print(msg)
            with open(os.path.join(output_folder_path, "execution_log.txt"), "w", encoding="utf-8") as lf:
                lf.write(msg)
            continue
            
        target_schema = schema_registry[template_key]
        execution_log.append(f"Áp dụng thành công Schema loại: {template_key}")

        # 5. CHẠY MODULE 1 (Conda: module_1_HL)
        m1_cmd = [
            "conda", "run", "-n", "module_1_HL", "--no-capture-output", 
            "python", "module_1_image_preprocessing/cli.py", 
            "--input_dir", input_folder_path, 
            "--output_dir", temp_folder_path
        ]
        print(f"⚙️  Đang kích hoạt Conda env 'module_1_HL' xử lý ảnh...")
        m1_success = run_module_cli(m1_cmd, "PREPROCESS", execution_log)
        if not m1_success:
            print("⚠️  Module 1 có lỗi xảy ra. Tiến trình vẫn tiếp tục dựa trên Fault Tolerance...")

        # 6. CHẠY MODULE 2 (Conda: module_2)
        ocr_output_json = os.path.join(temp_folder_path, "ocr_spatial_raw.json")
        m2_cmd = [
            "conda", "run", "-n", "module_2", "--no-capture-output", 
            "python", "module_2_core_ocr/cli.py", 
            "--input_dir", temp_folder_path, 
            "--output_json", ocr_output_json
        ]
        
        if USE_CACHE and os.path.exists(ocr_output_json):
            print("⚡ Đã tìm thấy Cache OCR từ trước. Bỏ qua kích hoạt Module 2 để tiết kiệm thời gian.")
            execution_log.append("Sử dụng dữ liệu OCR có sẵn từ bộ nhớ đệm (Cache).")
        else:
            print(f"⚙️  Đang kích hoạt Conda env 'module_2' nhận diện chữ (OCR)...")
            run_module_cli(m2_cmd, "OCR_CORE", execution_log)

        # 7. CHẠY MODULE 3 (Conda: module_3)
        final_result_json = os.path.join(output_folder_path, "extracted_data.json")
        m3_cmd = [
            "conda", "run", "-n", "module_3", "--no-capture-output", 
            "python", "module_3_dynamic_ner/cli.py",
            "--input_ocr_json", ocr_output_json,
            "--schema", json.dumps(target_schema),
            "--output_file", final_result_json
        ]
        
        print(f"⚙️  Đang kích hoạt Conda env 'module_3' bóc tách thực thể động...")
        run_module_cli(m3_cmd, "DYNAMIC_NER", execution_log)

        # 8. Ghi file nhật ký
        log_file_path = os.path.join(output_folder_path, "execution_log.txt")
        with open(log_file_path, "w", encoding="utf-8") as lf:
            lf.write("\n".join(execution_log))
        print(f"✅ Đã ghi vết lịch sử xử lý tại: {log_file_path}")

    print("\n🎉 === TOÀN BỘ CÁC HỒ SƠ ĐÃ ĐƯỢC QUÉT TUẦN TỰ HOÀN TẤT ===")

if __name__ == "__main__":
    main()