import os
import json
import re
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def normalize_text(text: str) -> str:
    """Thuật toán Fuzzy Normalization: Chuẩn hóa chuỗi trước khi so sánh"""
    if text is None: return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_metrics(tp: int, fp: int, fn: int):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return round(precision * 100, 2), round(recall * 100, 2), round(f1 * 100, 2)

def main():
    parser = argparse.ArgumentParser(description="Kịch bản Chấm điểm F1-Score cho Module 3")
    parser.add_argument("--pred_dir", required=True, help="Thư mục chứa kết quả của AI (m3_*.json)")
    parser.add_argument("--gt_dir", required=True, help="Thư mục chứa Đáp án chuẩn (Ground Truth)")
    parser.add_argument("--report_dir", default="logs", help="Thư mục lưu file báo cáo")
    args = parser.parse_args()

    pred_path = Path(args.pred_dir)
    gt_path = Path(args.gt_dir)
    report_path = Path(args.report_dir)
    report_path.mkdir(parents=True, exist_ok=True)
    
    field_stats = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0})
    total_documents = 0
    
    # MẢNG LƯU TRỮ CÁC TRƯỜNG HỢP LỖI CHI TIẾT (SIDE-BY-SIDE ERROR LOG)
    failed_cases = []

    print("📊 [Evaluation] Đang đối chiếu Dữ liệu AI bóc tách với Đáp án chuẩn...")

    for gt_file in gt_path.glob("*.json"):
        pred_file = pred_path / f"m3_{gt_file.name}"
        
        if not pred_file.exists():
            print(f"⚠️ Bỏ qua {gt_file.name}: Không tìm thấy file kết quả từ AI.")
            continue
            
        with open(gt_file, 'r', encoding='utf-8') as f:
            gt_data = json.load(f)
        with open(pred_file, 'r', encoding='utf-8') as f:
            pred_data = json.load(f)
            
        # Chấp nhận cả schema chuẩn của Pydantic lẫn schema của Mock Data
        pred_fields = {}
        for f in pred_data.get("fields", []):
            f_name = f.get("field_name") or f.get("name")
            f_value = f.get("raw_value") or f.get("value")
            # Nếu có tên trường thì lấy (bỏ qua điều kiện is_valid để test được Mock data)
            if f_name:
                pred_fields[f_name] = f_value
                
        total_documents += 1

        for field_name, gt_val in gt_data.items():
            gt_norm = normalize_text(gt_val)
            pred_val = pred_fields.get(field_name, "")
            pred_norm = normalize_text(pred_val)
            
            if gt_norm and gt_norm == pred_norm:
                field_stats[field_name]["TP"] += 1
            elif gt_norm and not pred_norm:
                field_stats[field_name]["FN"] += 1
                failed_cases.append({
                    "document": gt_file.name,
                    "field": field_name,
                    "error_type": "False Negative (Bỏ sót)",
                    "expected_truth": gt_val,
                    "ai_prediction": pred_val if pred_val else "[RỖNG]"
                })
            elif gt_norm and pred_norm and gt_norm != pred_norm:
                field_stats[field_name]["FP"] += 1
                field_stats[field_name]["FN"] += 1
                failed_cases.append({
                    "document": gt_file.name,
                    "field": field_name,
                    "error_type": "False Positive (Sai nội dung)",
                    "expected_truth": gt_val,
                    "ai_prediction": pred_val
                })

    # TỔNG HỢP BÁO CÁO
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = report_path / f"evaluation_report_{timestamp}.json"

    report = {
        "summary": {
            "timestamp": timestamp,
            "total_documents_evaluated": total_documents,
            "evaluation_strategy": "Fuzzy Normalized Match"
        },
        "field_metrics": {},
        "error_log": failed_cases  # THÊM DANH SÁCH LỖI VÀO BÁO CÁO JSON
    }

    print("\n🏆 BẢNG ĐIỂM F1-SCORE THEO TỪNG TRƯỜNG DỮ LIỆU:")
    print("-" * 65)
    print(f"{'Field Name':<25} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 65)

    for field, stats in field_stats.items():
        p, r, f1 = calculate_metrics(stats["TP"], stats["FP"], stats["FN"])
        report["field_metrics"][field] = {
            "Precision": p,
            "Recall": r,
            "F1_Score": f1,
            "Raw_Stats": stats
        }
        print(f"{field:<25} | {p:<8.2f}% | {r:<8.2f}% | {f1:<8.2f}%")

    print("-" * 65)
    print(f"🔍 Số lỗi bóc tách phát hiện được: {len(failed_cases)} lỗi. (Xem chi tiết trong file JSON)")
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    print(f"\n📁 Đã xuất báo cáo chi tiết ra file: {output_filename}")

if __name__ == "__main__":
    main()