# File Summaries: module_2_core_ocr

## `cli.py`
**Purpose:** Provides a Command Line Interface (CLI) to orchestrate batch OCR processing using the `OcrPipeline`.
**Inputs:** Command line arguments (`--input_dir`, `--output_dir`, `--engine`).
**Outputs:** JSON files containing OCR results for each processed image, saved to the output directory.
**Key Classes:** `EnhancedJSONEncoder`.
**Key Functions:** `main`.
**Dependencies:** `argparse`, `os`, `json`, `dataclasses`, `pathlib`, `.ocr_pipeline`, `.config`.
**Known Issues:** None.

## `config.py`
**Purpose:** Defines configuration data classes for the OCR engine, including parameters for PaddleOCR, VietOCR, and heuristic sorting. Supports loading from YAML.
**Inputs:** YAML file path.
**Outputs:** `OcrConfig` instance.
**Key Classes:** `PaddleConfig`, `VietOcrConfig`, `HeuristicSortingConfig`, `OcrConfig`.
**Key Functions:** `OcrConfig.from_yaml`, `OcrConfig.__post_init__`.
**Dependencies:** `dataclasses`, `pathlib`, `yaml`.
**Known Issues:** None.

## `models.py`
**Purpose:** Defines data structures (dataclasses) to represent OCR outputs, ensuring a standardized data contract.
**Inputs:** None.
**Outputs:** None.
**Key Classes:** `BoundingBox`, `OcrWord`, `OcrResult`.
**Key Functions:** None.
**Dependencies:** `dataclasses`, `typing`.
**Known Issues:** None.

## `ocr_pipeline.py`
**Purpose:** Orchestrates the core OCR workflow: reading metadata from Module 1, handling image rotation based on diagnostic flags, invoking the OCR engine factory, and executing the text recognition process.
**Inputs:** Directory path containing images and `m1_summary.json`.
**Outputs:** Dictionary containing `OcrResult` objects and the (potentially rotated) image arrays.
**Key Classes:** `OcrPipeline`.
**Key Functions:** `process_folder`.
**Dependencies:** `os`, `cv2`, `json`, `pathlib`, `typing`, `shared_utils.logger`, `.config`, `.engines.factory`, `.utils`, `shared_utils.models`.
**Known Issues:** None.

## `utils.py`
**Purpose:** Provides image manipulation utilities, specifically focusing on cropping rotated regions and determining the correct page orientation using an AI voting mechanism (Spatial Stratified Sampling).
**Inputs:** NumPy arrays (images), bounding boxes, `OrientationStatus`.
**Outputs:** Cropped/rotated NumPy arrays, rotation angles.
**Key Classes:** None.
**Key Functions:** `get_rotated_crop`, `auto_rotate_page`.
**Dependencies:** `cv2`, `numpy`, `math`, `shared_utils.models`.
**Known Issues:** None.

## `visualizer.py`
**Purpose:** Renders OCR bounding boxes and confidence scores onto images for debugging and visualization.
**Inputs:** Original image (NumPy array), `OcrResult`, output file path.
**Outputs:** NumPy array (annotated image) and saved image file.
**Key Classes:** None.
**Key Functions:** `draw_ocr_results`.
**Dependencies:** `cv2`, `numpy`, `.models`.
**Known Issues:** None.