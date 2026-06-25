import json
import random
import argparse
from pathlib import Path

def inject_ocr_noise(text: str, noise_level: float = 0.1) -> str:
    """Thuật toán giả lập lỗi OCR vật lý phổ biến trong tiếng Việt"""
    if not text or random.random() > noise_level * 3: 
        # Không phải dòng nào cũng bị lỗi, tỷ lệ dính lỗi toàn dòng phụ thuộc noise_level
        return text

    # Từ điển nhầm lẫn quang học (Optical Confusion Dictionary)
    ocr_mistakes = {
        'o': ['0', 'c', 'e'], 'O': ['0', 'Q', 'C'],
        'i': ['1', 'l', 'j', '!'], 'I': ['1', 'l', '|'],
        'l': ['1', 'I', 'i'], 'L': ['I', '1'],
        'g': ['q', '9'], 'G': ['6', 'C'],
        'B': ['8', '3'], 'S': ['5'],
        's': ['5'], 'z': ['2'],
        'ố': ['ổ', 'ồ', 'ỏ', 'o'], 'Ngày': ['Ngay', 'Ngảy', 'Ngáy'],
        'tháng': ['thang', 'thảng'], 'năm': ['nam', 'nãm'],
        'CỘNG': ['C0NG', 'CÔNG'], 'HÒA': ['H0A', 'HOA']
    }

    chars = list(text)
    for i, char in enumerate(chars):
        # 1. Lỗi thay thế ký tự (Character Substitution)
        if random.random() < noise_level:
            if char in ocr_mistakes:
                chars[i] = random.choice(ocr_mistakes[char])
                
    noisy_text = "".join(chars)

    # 2. Lỗi mất khoảng trắng (Missing Whitespace - Chữ dính vào nhau)
    if random.random() < noise_level and " " in noisy_text:
        parts = noisy_text.split(" ", 1)
        noisy_text = "".join(parts)

    return noisy_text

def main():
    parser = argparse.ArgumentParser(description="Công cụ Tiêm nhiễu OCR giả lập cho Module 3")
    parser.add_argument("--input_dir", required=True, help="Thư mục chứa JSON sạch từ Module 2")
    parser.add_argument("--output_dir", required=True, help="Thư mục lưu JSON đã bị làm nhiễu")
    parser.add_argument("--noise_level", type=float, default=0.15, help="Mức độ nhiễu (0.0 đến 1.0). Mặc định: 0.15 (15%)")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(in_dir.glob("*.json"))
    print(f"🌪️ [Noise Injector] Bắt đầu tiêm nhiễu vào {len(json_files)} file (Level: {args.noise_level*100}%)...")

    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Xử lý nội dung text (Tương thích với schema DocumentInput)
        target_keys = ['lines', 'words'] # Tùy thuộc vào JSON Module 2 đang dùng key nào
        mutated_lines = 0
        
        for key in target_keys:
            if key in data:
                for item in data[key]:
                    if 'text' in item:
                        original_text = item['text']
                        noisy_text = inject_ocr_noise(original_text, args.noise_level)
                        if original_text != noisy_text:
                            mutated_lines += 1
                        item['text'] = noisy_text

        out_file = out_dir / file_path.name
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"  - {file_path.name}: Đã làm hỏng {mutated_lines} dòng.")

    print(f"✅ Hoàn tất! Dữ liệu nhiễu đã lưu tại: {out_dir}")

if __name__ == "__main__":
    main()