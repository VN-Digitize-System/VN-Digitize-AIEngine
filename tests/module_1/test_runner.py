from __future__ import annotations
from module_1_image_preprocessing.visualizer import visualize_result
from module_1_image_preprocessing import ImagePreprocessor

import io
import sys
import time
from pathlib import Path

import cv2

# Force UTF-8 output on Windows terminals that default to cp1252
sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


INPUT_DIR = Path(__file__).parent / "input_images"
OUTPUT_DIR = Path(__file__).parent / "output_images"
CONFIG_PATH = PROJECT_ROOT / "configs" / "module1_defaults.yaml"
SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(
        p for p in INPUT_DIR.iterdir() if p.suffix.lower() in SUPPORTED
    ) if INPUT_DIR.exists() else []

    if not image_paths:
        print(f"[test_runner] No images found in: {INPUT_DIR}")
        print("[test_runner] Place .jpg / .jpeg / .png files there and re-run.")
        return

    processor = ImagePreprocessor.from_yaml(CONFIG_PATH)

    col = "{:<24} {:<7} {:<14} {:<9} {:<12} {}"
    sep = "─" * 78
    print(f"\n[test_runner] Scanning: {INPUT_DIR}\n{sep}")
    print(col.format("File", "Blank", "Orientation", "Angle", "Barcodes", "Status"))
    print(sep)

    ok_count = err_count = 0

    for img_path in image_paths:
        t0 = time.perf_counter()
        original = cv2.imread(str(img_path))
        result = processor.process(img_path)
        elapsed = time.perf_counter() - t0

        if result.error_code:
            print(col.format(img_path.name, "—", "—",
                  "—", "—", f"✗ {result.error_code}"))
            err_count += 1
            continue

        orientation_str = "WARN_ROTATED" if result.is_wrong_orientation else "OK"
        barcode_str = (
            f"{len(result.barcodes)} ({result.barcodes[0].barcode_type})"
            if result.barcodes else "0"
        )
        print(col.format(
            img_path.name,
            str(result.is_blank),
            orientation_str,
            f"{result.skew_angle:+.1f}°",
            barcode_str,
            f"✓ OK  ({elapsed:.2f}s)",
        ))

        cv2.imwrite(str(OUTPUT_DIR / img_path.name), result.processed_image)

        if original is not None:
            visualize_result(
                original, result,
                save_path=OUTPUT_DIR / f"debug_{img_path.name}",
            )

        ok_count += 1

    print(sep)
    print(
        f"Processed: {len(image_paths)} | OK: {ok_count} | Errors: {err_count}")
    print(f"Output saved to: {OUTPUT_DIR}\n")


if __name__ == "__main__":
    run()
