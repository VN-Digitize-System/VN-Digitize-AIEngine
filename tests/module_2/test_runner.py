from __future__ import annotations
from module_2_core_ocr.visualizer import visualize_result
from module_2_core_ocr import OCREngine
import uuid

import io
import sys
import time
from pathlib import Path

import cv2

# Force UTF-8 on Windows terminals that default to cp1252
sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


INPUT_DIR = Path(__file__).parent / "input_images"
OUTPUT_DIR = Path(__file__).parent / "output_images"
CONFIG_PATH = PROJECT_ROOT / "configs" / "module2_defaults.yaml"
SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


def _check_word_level(result) -> tuple[int, int]:
    """Return (total_words, flagged_words) across all text blocks."""
    total = sum(len(b.words) for b in result.text_blocks)
    flagged = sum(sum(1 for w in b.words if w.is_flagged)
                  for b in result.text_blocks)
    return total, flagged


def _verify_response_schema(result) -> list[str]:
    """
    Verify OCRResponse.to_dict() matches spec contract.
    Returns list of schema violation messages (empty = pass).
    """
    doc_id = str(uuid.uuid4())
    response = result.to_response(doc_id)
    d = response.to_dict()

    errors = []
    for required_key in ("document_id", "classification", "summary",
                         "confidence_overall", "metadata", "sub_documents",
                         "full_text", "text_blocks"):
        if required_key not in d:
            errors.append(f"Missing key: {required_key}")

    if d.get("document_id") != doc_id:
        errors.append("document_id mismatch")

    if not isinstance(d.get("metadata"), list):
        errors.append("metadata must be a list")

    if not isinstance(d.get("sub_documents"), list):
        errors.append("sub_documents must be a list")

    # Verify text_blocks have word-level tokens
    for blk in d.get("text_blocks", []):
        if "words" not in blk:
            errors.append(
                f"TextBlock missing 'words': {blk.get('text', '')[:20]}")
            break
        for w in blk["words"]:
            if not all(k in w for k in ("text", "confidence", "bbox", "is_flagged")):
                errors.append(f"WordToken missing required keys: {w}")
                break

    return errors


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

    col = "{:<28} {:>7} {:>9} {:>6} {:>8} {:>7} {}"
    sep = "-" * 88
    print(f"\n[test_runner] Scanning: {INPUT_DIR}\n{sep}")
    print(col.format("File", "Blocks", "AvgConf",
          "Words", "Flagged", "Schema", "Status"))
    print(sep)

    ok_count = err_count = schema_fail = 0

    for img_path in image_paths:
        t0 = time.perf_counter()
        image = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(col.format(img_path.name[:28],
                  "-", "-", "-", "-", "-", "ERR_IMREAD"))
            err_count += 1
            continue

        result = engine.process(image)
        elapsed = time.perf_counter() - t0

        if result.error_code:
            print(col.format(
                img_path.name[:28], "-", "-", "-", "-", "-", f"ERR {result.error_code}"))
            err_count += 1
            continue

        total_words, flagged_words = _check_word_level(result)
        schema_errors = _verify_response_schema(result)
        schema_status = "PASS" if not schema_errors else f"FAIL({len(schema_errors)})"
        if schema_errors:
            schema_fail += 1

        print(col.format(
            img_path.name[:28],
            str(len(result.text_blocks)),
            f"{result.avg_confidence:.3f}",
            str(total_words),
            str(flagged_words),
            schema_status,
            f"OK ({elapsed:.2f}s)",
        ))

        if result.text_blocks:
            preview = result.full_text[:120].replace("\n", " | ")
            print(f"    Preview: {preview}")

        if schema_errors:
            for e in schema_errors:
                print(f"    [SCHEMA ERR] {e}")

        original = cv2.imread(str(img_path))
        if original is not None:
            visualize_result(
                original, result,
                save_path=OUTPUT_DIR / f"debug_{img_path.stem}.png",
            )

        ok_count += 1

    print(sep)
    print(
        f"Processed: {len(image_paths)} | OK: {ok_count} | Errors: {err_count} | Schema fails: {schema_fail}")
    print(f"Output saved to: {OUTPUT_DIR}\n")


if __name__ == "__main__":
    run()
