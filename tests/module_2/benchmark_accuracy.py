#!/usr/bin/env python3
import io
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import cv2
from jiwer import cer, wer
from module_2_core_ocr import OCREngine

GT_DIR = Path(__file__).parent / "ground_truth"
IMG_DIR = Path(__file__).parent / "input_images"
REPORT_PATH = Path(__file__).parent / "benchmark_report.txt"
CONFIG = PROJECT_ROOT / "configs" / "module2_defaults.yaml"
SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
TARGET_CER = 0.03


def find_image(stem: str) -> Path | None:
    for ext in SUPPORTED:
        p = IMG_DIR / (stem + ext)
        if p.exists():
            return p
    return None


def _print_and_collect(lines: list[str], *args) -> None:
    line = " ".join(str(a) for a in args)
    print(line)
    lines.append(line)


def run() -> None:
    if not GT_DIR.exists() or not any(GT_DIR.glob("*.txt")):
        print("[benchmark] Chua co ground truth. Tao thu muc va them file .txt:")
        print(f"  {GT_DIR}")
        print("  Moi file .txt tuong ung voi anh cung ten trong input_images/")
        print("  Vi du: 01_normal.txt <-> 01_normal.jpg")
        sys.exit(1)

    engine = OCREngine.from_yaml(CONFIG)

    pairs: list[tuple[Path, Path]] = []
    for txt_path in sorted(GT_DIR.glob("*.txt")):
        img_path = find_image(txt_path.stem)
        if img_path:
            pairs.append((img_path, txt_path))
        else:
            print(f"[benchmark] Khong tim thay anh cho: {txt_path.name} — bo qua")

    if not pairs:
        print("[benchmark] Khong co cap anh/ground-truth nao hop le.")
        sys.exit(1)

    results = []
    for img_path, txt_path in pairs:
        gt_text = txt_path.read_text(encoding="utf-8").strip()
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"[benchmark] Khong doc duoc anh: {img_path.name}")
            continue

        t0 = time.perf_counter()
        ocr_result = engine.process(image)
        elapsed = time.perf_counter() - t0

        if ocr_result.error_code:
            print(f"[benchmark] OCR loi {ocr_result.error_code}: {img_path.name}")
            continue

        ocr_text = ocr_result.full_text.strip()
        c = cer(gt_text, ocr_text)
        w = wer(gt_text, ocr_text)
        results.append({
            "file": img_path.name,
            "cer": c,
            "wer": w,
            "accuracy": 1.0 - c,
            "pass": c <= TARGET_CER,
            "elapsed": elapsed,
        })

    if not results:
        print("[benchmark] Khong co ket qua nao de bao cao.")
        sys.exit(1)

    _print_report(results)


def _print_report(results: list[dict]) -> None:
    W = 65
    col_file = 32
    lines: list[str] = []

    sep_top = "=" * W
    sep_mid = "-" * W
    header = (
        f" {'File':<{col_file}} {'CER':>6}  {'WER':>6}  {'Acc':>7}  Status"
    )
    title = f" Module 2 — Accuracy Benchmark (target: CER <= {TARGET_CER*100:.2f}%)"

    output_lines: list[str] = []
    p = lambda *a: _print_and_collect(output_lines, *a)

    p(sep_top)
    p(title)
    p(sep_top)
    p(header)
    p(sep_mid)

    for r in results:
        name = r["file"][:col_file]
        status = "PASS" if r["pass"] else "FAIL x"
        p(
            f" {name:<{col_file}} {r['cer']*100:>5.1f}%  {r['wer']*100:>5.1f}%"
            f"  {r['accuracy']*100:>6.1f}%  {status}  ({r['elapsed']:.1f}s)"
        )

    p(sep_mid)
    avg_cer = sum(r["cer"] for r in results) / len(results)
    avg_acc = sum(r["accuracy"] for r in results) / len(results)
    overall = "PASS" if avg_cer <= TARGET_CER else "FAIL"
    p(
        f" TONG ({len(results)} anh)   avg CER: {avg_cer*100:.1f}%"
        f"   avg Accuracy: {avg_acc*100:.1f}%   {overall}"
    )
    p(sep_top)
    p(f" Ket qua luu tai: {REPORT_PATH}")

    REPORT_PATH.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    overall_cer = sum(r["cer"] for r in results) / len(results)
    sys.exit(0 if overall_cer <= TARGET_CER else 1)


if __name__ == "__main__":
    run()
