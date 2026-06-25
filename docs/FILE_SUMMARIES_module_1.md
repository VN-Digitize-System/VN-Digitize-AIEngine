# File Summaries: module_1_image_preprocessing

## `__init__.py`
**Purpose:** Exposes core classes and models for external use, establishing the module's public API.
**Inputs:** None (initialization file).
**Outputs:** None.
**Key Classes:** None defined, imports `ImagePreprocessor`, `PreprocessConfig`, `PreprocessResult`, `BarcodeInfo`.
**Key Functions:** None.
**Dependencies:** `.preprocessor`, `.config`, `.models`.
**Known Issues:** None.

## `_crop_deskew.py`
**Purpose:** Implements document isolation, background removal, and perspective correction (deskewing) using a lightweight AI model (U2-Net).
**Inputs:** NumPy array (image), `CropDeskewConfig`.
**Outputs:** Tuple containing the warped image (NumPy array), skew angle (float), and a debug image (NumPy array).
**Key Classes:** None.
**Key Functions:** `detect_and_crop`, `_order_corner_points`, `_perspective_transform`.
**Dependencies:** `cv2`, `numpy`, `rembg` (u2netp model), `.config`, `shared_utils.logger`.
**Known Issues:** None.

## `_detect.py`
**Purpose:** Implements detection logic for blank pages, incorrect document orientation, and barcodes.
**Inputs:** NumPy array (image), `DetectConfig`.
**Outputs:** Boolean (blank page), `OrientationStatus` (orientation), list of `BarcodeInfo` (barcodes).
**Key Classes:** None.
**Key Functions:** `detect_blank_page`, `detect_wrong_orientation`, `detect_barcodes`.
**Dependencies:** `cv2`, `numpy`, `pyzbar.pyzbar`, `.config`, `.models`, `shared_utils.logger`, `shared_utils.models`.
**Known Issues:** OpenCV QR fallback used if PyZbar fails, which might be less reliable for complex barcodes.

## `_enhance.py`
**Purpose:** Handles image enhancement, applying operations like denoising, binarization, or contrast adjustment (CLAHE).
**Inputs:** NumPy array (image), `EnhanceConfig`.
**Outputs:** Enhanced NumPy array (image).
**Key Classes:** None.
**Key Functions:** `enhance_image`.
**Dependencies:** `cv2`, `numpy`, `.config`, `shared_utils.logger`.
**Known Issues:** None.

## `cli.py`
**Purpose:** Provides a Command Line Interface (CLI) wrapper for executing Module 1 batch processing.
**Inputs:** Command line arguments (`--input_dir`, `--output_dir`, `--skip_crop`).
**Outputs:** Console output indicating progress.
**Key Classes:** None.
**Key Functions:** `main`.
**Dependencies:** `argparse`, `.preprocessor`.
**Known Issues:** None.

## `config.py`
**Purpose:** Defines configuration data classes to control the behavior of preprocessing steps. Supports loading configurations from YAML files.
**Inputs:** YAML file path or dictionary.
**Outputs:** `PreprocessConfig` instance.
**Key Classes:** `CropDeskewConfig`, `CLAHEConfig`, `BinarizeConfig`, `DenoiseConfig`, `EnhanceConfig`, `BlankPageConfig`, `OrientationConfig`, `BarcodeConfig`, `DetectConfig`, `PreprocessConfig`.
**Key Functions:** `PreprocessConfig.from_yaml`, `PreprocessConfig._from_dict`.
**Dependencies:** `dataclasses`, `pathlib`, `yaml`.
**Known Issues:** None.

## `models.py`
**Purpose:** Defines data structures (dataclasses) used to represent output from the preprocessing module.
**Inputs:** None.
**Outputs:** None.
**Key Classes:** `BarcodeInfo`, `PreprocessResult`.
**Key Functions:** None.
**Dependencies:** `dataclasses`, `numpy`, `shared_utils.models`.
**Known Issues:** None.

## `preprocessor.py`
Purpose: Điều phối toàn bộ luồng tiền xử lý ảnh (cắt mép, nắn chỉnh, phát hiện trang trắng/hướng sai, tìm mã vạch, tăng cường ảnh). Hỗ trợ xử lý file đơn và xử lý lô (folder) với cơ chế đọc/ghi an toàn cho đường dẫn chứa ký tự Unicode (Tiếng Việt).
Inputs: Đường dẫn file (str/Path) hoặc mảng numpy, đối tượng PreprocessConfig, cờ skip_crop. Với xử lý lô: thư mục đầu vào và đầu ra.
Outputs: Đối tượng PreprocessResult (cho file đơn) hoặc các file ảnh đã xử lý kèm file tóm tắt m1_summary.json (cho xử lý lô).
Key Classes: ImagePreprocessor.
Key Functions: process (chạy luồng lõi), _load_image (nạp ảnh bằng byte stream numpy), process_folder (chạy lô và lưu file bằng byte stream).
Dependencies: cv2, numpy, pathlib, os, json, .config, .models, shared_utils.models, ._crop_deskew, ._detect, ._enhance, shared_utils.logger.
Known Issues: Sử dụng phương thức np.fromfile và cv2.imencode().tofile() để bypass rào cản Unicode của OpenCV trên Windows, có thể tiêu tốn thêm một chút RAM khi xử lý mảng byte đối với các file ảnh dung lượng cực lớn.

## `visualizer.py`
**Purpose:** Provides utilities for rendering and saving visualizations of preprocessing results for debugging and analysis.
**Inputs:** Original image (NumPy array), `PreprocessResult`, optional save path.
**Outputs:** Matplotlib plot display or saved image file.
**Key Classes:** None.
**Key Functions:** `visualize_result`.
**Dependencies:** `pathlib`, `cv2`, `matplotlib.patches`, `matplotlib.pyplot`, `numpy`, `.models`.
**Known Issues:** None.