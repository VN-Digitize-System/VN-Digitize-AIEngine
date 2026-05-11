#!/usr/bin/env python3
"""
Test runner for Module 2 - Core OCR Engine.

Usage:
    python tests/module_2/test_runner.py

Place test images (.jpg / .jpeg / .png) in:
    tests/module_2/input_images/
    (tip: copy processed images from tests/module_1/output_images/)

Results (debug visualisation) are written to:
    tests/module_2/output_images/
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

import cv2

# Force UTF-8 on Windows terminals that default to cp1252
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from module_2_core_ocr import OCREngine
from module_2_core_ocr.visualizer import visualize_result

INPUT_DIR = Path(__file__).parent / "input_images"
OUTPUT_DIR = Path(__file__).parent / "output_images"
CONFIG_PATH = PROJECT_ROOT / "configs" / "module2_defaults.yaml"
SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image_paths = (
        sorted(p for p in INPUT_DIR.iterdir() if p.suffix.lower() in SUPPORTED)
        if INPUT_DIR.exists()
        else []
    )

    if not image_paths:
        print(f"[test_runner] No images found in: {INPUT_DIR}")
        print("[test_runner] Copy .jpg/.png files there and re-run.")
        print("[test_runner] Tip: use output images from tests/module_1/output_images/")
        return

    print("[test_runner] Initializing OCREngine (EasyOCR model load on first image)...")
    engine = OCREngine.from_yaml(CONFIG_PATH)

    col = "{:<28} {:>7} {:>9} {:>12} {}"
    sep = "-" * 72
    print(f"\n[test_runner] Scanning: {INPUT_DIR}\n{sep}")
    print(col.format("File", "Blocks", "AvgConf", "UpsideDown", "Status"))
    print(sep)

    ok_count = err_count = 0

    for img_path in image_paths:
        t0 = time.perf_counter()
        image = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(col.format(img_path.name[:28], "-", "-", "-", "ERR_IMREAD"))
            err_count += 1
            continue

        result = engine.process(image)
        elapsed = time.perf_counter() - t0

        if result.error_code:
            status = f"ERR {result.error_code}"
            print(col.format(img_path.name[:28], "-", "-", "-", status))
            err_count += 1
            continue

        print(col.format(
            img_path.name[:28],
            str(len(result.text_blocks)),
            f"{result.avg_confidence:.3f}",
            str(result.is_upside_down),
            f"OK ({elapsed:.2f}s)",
        ))

        if result.text_blocks:
            preview = result.full_text[:120].replace("\n", " | ")
            print(f"    Preview: {preview}")

        original = cv2.imread(str(img_path))
        if original is not None:
            visualize_result(
                original, result,
                save_path=OUTPUT_DIR / f"debug_{img_path.stem}.png",
            )

        ok_count += 1

    print(sep)
    print(f"Processed: {len(image_paths)} | OK: {ok_count} | Errors: {err_count}")
    print(f"Output saved to: {OUTPUT_DIR}\n")


if __name__ == "__main__":
    run()
