import argparse
import os
import json
import dataclasses
from pathlib import Path

from module_2_core_ocr.ocr_pipeline import OcrPipeline
from module_2_core_ocr.config import OcrConfig

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

def main():
    parser = argparse.ArgumentParser(description="CLI Khởi chạy Module 2 (Core OCR)")
    parser.add_argument("--input_dir", required=True, help="Thư mục chứa ảnh và JSON từ Module 1")
    parser.add_argument("--output_dir", required=True, help="Thư mục lưu file JSON kết quả OCR")
    parser.add_argument("--engine", default="paddle_vietocr", help="Tên Động cơ OCR muốn khởi chạy")
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"[M2-CLI] Khởi tạo Nhạc trưởng Pipeline với động cơ: {args.engine}")
    config = OcrConfig()
    pipeline = OcrPipeline(active_engine_name=args.engine, config=config)
    
    print(f"[M2-CLI] Bắt đầu quét và xử lý thư mục: {input_path}")
    batch_results = pipeline.process_folder(input_path)
    
    # LƯU KẾT QUẢ RA FILE JSON
    for filename, result_obj in batch_results.items():
        base_name = os.path.splitext(filename)[0]
        json_file_path = output_path / f"{base_name}_ocr.json"
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(result_obj, f, cls=EnhancedJSONEncoder, indent=4, ensure_ascii=False)
            
        print(f"✅ Đã lưu kết quả JSON tại: {json_file_path}")

if __name__ == "__main__":
    main()