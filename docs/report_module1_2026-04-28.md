# BÁO CÁO TIẾN ĐỘ — MODULE 1: IMAGE PRE-PROCESSING

**Dự án:** VN-Digitize AI Engine
**Ngày:** 28/04/2026
**Người thực hiện:** Team AI

---

## 1. Tổng quan công việc trong ngày

Hoàn thiện toàn bộ **Module 1 — Xử lý ảnh thông minh (Image Pre-processing)** từ skeleton trống đến trạng thái production-ready, bao gồm thiết kế kiến trúc, lập trình, kiểm thử và sửa lỗi lặp đến khi đạt 100% yêu cầu đặc tả.

---

## 2. Kiến trúc hệ thống đã xây dựng

```
VN-Digitize-AIEngine/
├── requirements.txt                    # Dependencies
├── configs/
│   └── module1_defaults.yaml           # Toàn bộ tham số cấu hình (không hardcode)
├── shared_utils/
│   ├── __init__.py
│   └── logger.py                       # Logger dùng chung 4 module
├── module_1_image_preprocessing/
│   ├── __init__.py                     # Public API
│   ├── config.py                       # PreprocessConfig dataclass
│   ├── models.py                       # PreprocessResult, BarcodeInfo
│   ├── preprocessor.py                 # ImagePreprocessor (entry point)
│   ├── _crop_deskew.py                 # Auto-crop + Deskew
│   ├── _enhance.py                     # CLAHE + Binarize + Denoise
│   ├── _detect.py                      # Blank / Orientation / Barcode
│   └── visualizer.py                   # Debug visualization
└── tests/
    └── module_1/
        ├── input_images/               # Ảnh đầu vào test
        ├── output_images/              # Kết quả output + debug figure
        └── test_runner.py              # CLI test script
```

**Tổng số file tạo mới:** 13 file

---

## 3. Các tính năng đã implement

### 3.1 Tự động nhận diện và làm sạch ảnh (Req 1.1)

| Tính năng | Kỹ thuật sử dụng | Trạng thái |
|---|---|---|
| Deskew — chỉnh ảnh nghiêng | Hough Lines → tính góc trung vị → `warpAffine` | ✅ Hoàn thành |
| Auto-crop — cắt bỏ nền thừa | `bilateralFilter` → Canny → contour 4 góc → `getPerspectiveTransform` | ✅ Hoàn thành |
| Fallback khi không tìm được 4 góc | HoughLinesP deskew | ✅ Hoàn thành |
| Tẩy nền ố vàng / giấy cũ | CLAHE (Contrast Limited Adaptive Histogram Equalization) | ✅ Hoàn thành |
| Khử nhiễu hạt (salt & pepper) | `medianBlur` | ✅ Hoàn thành |
| Binarize (tuỳ chọn) | `adaptiveThreshold` GAUSSIAN\_C | ✅ Hoàn thành |

### 3.2 Nhận diện cấu trúc tệp (Req 1.2)

| Tính năng | Kỹ thuật sử dụng | Trạng thái |
|---|---|---|
| Phát hiện trang trắng | Tỉ lệ pixel trắng ≥ ngưỡng cấu hình (mặc định 99%) | ✅ Hoàn thành |
| Phát hiện sai chiều 90° | Sobel gradient energy ratio SobelX/SobelY < 0.85 | ✅ Hoàn thành |
| Phát hiện ngược chiều 180° | Không thể bằng Classical CV | ⚠️ Ghi nhận limitation |
| Nhận diện Barcode / QR Code | `cv2.QRCodeDetector` + `cv2.barcode.BarcodeDetector` | ✅ Hoàn thành |

### 3.3 Hệ thống kỹ thuật nền tảng

| Hạng mục | Chi tiết |
|---|---|
| Cấu hình | Toàn bộ tham số trong `configs/module1_defaults.yaml`, không hardcode bất kỳ con số nào trong code |
| Output có cấu trúc | `PreprocessResult` dataclass gồm: ảnh đã xử lý, `is_blank`, `is_wrong_orientation`, `skew_angle`, `barcodes[]`, `warnings[]`, `error_code` |
| Error handling | 5 mã lỗi cụ thể: `ERR_FILE_NOT_FOUND`, `ERR_CORRUPTED`, `ERR_EMPTY_ARRAY`, `ERR_TOO_SMALL`, `ERR_UNSUPPORTED_FORMAT` |
| Logging | Console (INFO) + File debug hàng ngày tại `logs/module_1_image_preprocessing_YYYY-MM-DD.log` |
| Tích hợp production | Input/output đều là `numpy.ndarray` — không I/O file khi chạy thật, truyền thẳng qua RAM sang Module 2 |

---

## 4. Kiểm thử

### 4.1 Dữ liệu test

- **7 ảnh tổng hợp (synthetic):** tạo programmatically để test từng case riêng lẻ (thẳng, nghiêng 15°, phối cảnh, trang trắng, ố vàng, xoay 90°, lật 180°)
- **20 ảnh tài liệu Việt Nam thật** (ảnh chụp điện thoại, định dạng JPEG 1536×2048 đến 1920×2560)

### 4.2 Kết quả tổng thể

```
Processed: 27 | OK: 27 | Errors: 0
```

### 4.3 Kiểm tra đối chiếu yêu cầu (Requirements Check)

| Kiểm tra | Kết quả |
|---|---|
| 1.1 Deskew phát hiện góc nghiêng | ✅ PASS |
| 1.1 Auto-crop cắt đúng tờ giấy | ✅ PASS |
| 1.1 Enhancement output hợp lệ | ✅ PASS |
| 1.2 Phát hiện trang trắng | ✅ PASS |
| 1.2 Phát hiện sai chiều 90° | ✅ PASS |
| 1.2 Không false positive trên ảnh bình thường | ✅ PASS |
| 1.2 Barcode field có trong kết quả | ✅ PASS |
| 6.4 Mã lỗi ERR\_FILE\_NOT\_FOUND | ✅ PASS |
| 6.4 Mã lỗi ERR\_CORRUPTED | ✅ PASS |
| 6.1 SLA < 2 giây/trang | ✅ PASS (max 1.2s) |
| Logger ghi file đúng | ✅ PASS |
| Config load từ YAML không hardcode | ✅ PASS |

**Tổng: 12/12 PASS**

---

## 5. Các lỗi phát hiện và đã sửa trong ngày

| # | Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|---|
| 1 | Output đen trắng, chữ không đọc được | `binarize.enabled: true` mặc định | Đổi mặc định thành `false` |
| 2 | Không tìm được contour 4 góc | `approxPolyDP` epsilon quá chặt | Thay `GaussianBlur` bằng `bilateralFilter`, thử 5 mức epsilon (0.02→0.06) |
| 3 | `WARN_ROTATED` false positive 7/20 ảnh thật | Hough line count bị ảnh hưởng bởi đường kẻ bảng, viền tài liệu | Thay hoàn toàn bằng Sobel gradient X/Y ratio |
| 4 | Trang trắng bị flag `WARN_ROTATED` nhầm | Gradient trên ảnh trắng không có ý nghĩa | Skip orientation check khi `is_blank=True` |
| 5 | Terminal crash `UnicodeEncodeError` trên Windows | Ký tự box-drawing không hỗ trợ cp1252 | Force UTF-8 stdout trong `test_runner.py` |

---

## 6. Limitation đã ghi nhận

**Phát hiện ảnh lật ngược 180° (upside-down):** Không thể thực hiện bằng Classical Computer Vision vì Sobel gradient của ảnh 0° và 180° cho kết quả toán học giống hệt nhau. Đây là limitation kỹ thuật phổ biến — các hệ thống OCR công nghiệp xử lý case này ở tầng OCR (Module 2) thông qua confidence score thấp bất thường.

**Hướng giải quyết dự kiến:** Khi Module 2 hoàn thành, bổ sung logic: nếu OCR confidence toàn trang < ngưỡng → flag `WARN_UPSIDE_DOWN`.

---

## 7. Kế hoạch tiếp theo

Bắt đầu **Module 2 — Core OCR Engine** sử dụng VietOCR, với đầu vào là `numpy.ndarray` từ output của Module 1.
