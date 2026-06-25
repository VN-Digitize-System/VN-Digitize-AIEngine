## 🚀 Hướng dẫn chạy Module 1 (Tiền xử lý ảnh)

Module 1 đảm nhiệm việc tiếp nhận ảnh tài liệu thô, cắt viền, xoay chuẩn và lọc bỏ các ảnh trắng/lỗi trước khi đưa vào hệ thống OCR.

### Bước 1: Tạo và kích hoạt môi trường ảo
Mở Terminal (hoặc Command Prompt / PowerShell) tại thư mục gốc của dự án `VN-Digitize-AIEngine` và chạy lệnh sau để tạo môi trường ảo có tên `venv_m1`:

```bash
python -m venv venv_m1

```

Sau khi tạo xong, bạn cần kích hoạt môi trường ảo này:

* **Trên Windows (Command Prompt / PowerShell):**
```cmd
venv_m1\Scripts\activate

```


* **Trên macOS / Linux:**
```bash
source venv_m1/bin/activate

```

*(Dấu hiệu thành công: Bạn sẽ thấy chữ `(venv_m1)` xuất hiện ở đầu dòng lệnh).*

### Bước 2: Cài đặt thư viện

Sử dụng file requirement đã được xuất sẵn để cài đặt các thư viện xử lý ảnh (như OpenCV) cần thiết cho Module 1:

```bash
pip install -r requirements_module1.txt

```

### Bước 3: Chạy kịch bản kiểm thử (Batch Runner)

Kịch bản test của Module 1 đã được cấu hình sẵn các đường dẫn trỏ tới thư mục dữ liệu mẫu (dành cho demo video).

**Cách 1: Chạy với cấu hình mặc định (Khuyên dùng cho người mới)**
Chỉ cần gõ lệnh sau, hệ thống sẽ tự động lấy ảnh từ `tests/data/unit_tests/...` và lưu kết quả vào thư mục test tương ứng:

```bash
python scripts/module_1/test_batch_runner.py

```

**Kết quả mong đợi:** 
Terminal sẽ in ra quá trình xử lý từng ảnh và cuối cùng hiển thị bảng **BÁO CÁO HIỆU NĂNG MODULE 1** (bao gồm số lượng ảnh thành công, ảnh lỗi, tổng thời gian và tốc độ FPS). Một file metadata `m1_summary.json` cũng sẽ được sinh ra tại thư mục đầu ra.

---

## 🔍 Hướng dẫn chạy Module 2 (Nhận dạng chữ - OCR Core)

Module 2 đóng vai trò là "bộ não" thị giác của hệ thống. Nó sẽ tiếp nhận các ảnh đã được làm sạch từ Module 1, nhận diện văn bản (OCR), tự động lật lại ảnh nếu bị ngược, và xuất kết quả dưới dạng cấu trúc dữ liệu JSON kèm ảnh Debug.

⚠️ **LƯU Ý QUAN TRỌNG:** Kịch bản kiểm thử của Module 2 yêu cầu thư mục Input **bắt buộc phải chứa file `m1_summary.json`** sinh ra từ Module 1. Do đó, bạn cần chạy thành công Module 1 trước khi chạy Module 2.

### Bước 1: Tạo và kích hoạt môi trường ảo riêng cho OCR
Do các thư viện AI/OCR (như PaddleOCR, PyTorch...) thường rất nặng và yêu cầu phiên bản thư viện nghiêm ngặt, chúng ta sẽ tạo một môi trường ảo hoàn toàn mới có tên `venv_m2`.

Mở Terminal tại thư mục gốc của dự án và chạy:
```bash
python -m venv venv_m2

```

Kích hoạt môi trường ảo:

* **Trên Windows (Command Prompt / PowerShell):**
```cmd
venv_m2\Scripts\activate

```


* **Trên macOS / Linux:**
```bash
source venv_m2/bin/activate

```

*(Bạn sẽ thấy chữ `(venv_m2)` xuất hiện ở đầu dòng lệnh).*

### Bước 2: Cài đặt thư viện OCR

Sử dụng file requirement của Module 2:

```bash
pip install -r requirements_module2.txt

```

### Bước 3: Chạy kịch bản nhận dạng (OCR Batch Runner)

**Cách 1: Chạy với luồng dữ liệu mặc định**
Nếu bạn đã chạy Cách 1 ở Module 1, hệ thống đã chuẩn bị sẵn đầu vào. Bạn chỉ cần gõ lệnh:

```bash
python scripts/module_2/test_batch_runner.py

```

**Kết quả mong đợi:** Tại thư mục Output của Module 2, hệ thống sẽ tự động tạo ra:

* Thư mục `jsons/`: Chứa file `_ocr.json` lưu tọa độ và nội dung từng dòng chữ.
* Thư mục `debug_images/`: Chứa ảnh đã được vẽ khung đỏ (bounding box) bao quanh chữ để kiểm tra trực quan.
* File báo cáo hiệu năng `m2_performance_summary.json` và bảng báo cáo in trực tiếp trên Terminal.

---


## 🧠 Hướng dẫn chạy Module 3 (Bóc tách thông tin - Dynamic NER)

Module 3 là khâu cuối cùng, sử dụng kiến trúc Lai (Hybrid: Regex + LLM) để trích xuất các thông tin nghiệp vụ từ file kết quả OCR.

⚠️ **LƯU Ý QUAN TRỌNG VỀ SANDBOX & LOCAL LLM:** Để chạy Module 3 trong môi trường nội bộ (Offline) đúng chuẩn Sandbox, bạn **BẮT BUỘC** phải có một file tên là `.env` đặt tại **thư mục gốc của dự án** (`VN-Digitize-AIEngine/.env`) với nội dung cấu hình tối thiểu như sau:
```env
LLM_ENGINE=local
CHUNK_PROCESSING_MODE=sequential

```

*(Nếu thiếu file `.env` này, code sẽ tự động nhảy sang chế độ Cloud Gemini API và văng lỗi do không có API Key).*

### Bước 1: Tạo và kích hoạt môi trường ảo

Mở Terminal tại thư mục gốc dự án và tạo môi trường `venv_m3`:

```bash
python -m venv venv_m3

```

Kích hoạt môi trường:

* **Trên Windows (Command Prompt / PowerShell):**
```cmd
venv_m3\Scripts\activate

```


* **Trên macOS / Linux:**
```bash
source venv_m3/bin/activate

```

### Bước 2: Cài đặt thư viện

Cài đặt các thư viện lõi cho Module 3 (đã bao gồm `python-dotenv` để đọc file cấu hình):

```bash
pip install -r requirements_module3.txt

```

### Bước 3: Cài đặt Ollama và Model AI (BẮT BUỘC CHO CHẾ ĐỘ OFFLINE)

Hệ thống sử dụng mô hình Qwen chạy cục bộ thông qua Ollama để bóc tách thông tin bảo mật. Để máy tính có thể chạy được AI, bạn cần:

1. Tải và cài đặt phần mềm Ollama từ trang chủ: [https://ollama.com/](https://ollama.com/)
2. Mở một Terminal/Command Prompt mới và chạy lệnh sau để tải mô hình Qwen 2.5 về máy (quá trình này có thể mất vài phút tùy tốc độ mạng):
```bash
ollama pull qwen2.5

```
3. Sau khi tải được mô hình về máy thì tiếp theo chạy lệnh:
```bash
ollama run qwen2.5:7b
```

4. Sau khi chạy lệnh xong, nếu như có kết quả như sau thì chỉ cần hạ Terminal/Command Prompt (không được đóng)
```bash
>> Send a message (/? for help)
```


### Bước 4: Chạy kịch bản bóc tách Sandbox

Sử dụng lệnh sau để bóc tách hàng loạt các file JSON đầu vào:

```bash
python scripts/module_3/test_batch_runner.py --input_dir tests/sandbox_inputs --output_dir tests/sandbox_outputs

```

**Kết quả mong đợi:** Hệ thống sẽ chạy định tuyến (Regex/LLM), in log Terminal và xuất các file kết quả bóc tách (`m3_*.json`) vào thư mục `tests/sandbox_outputs`.

### Bước 5: Đánh giá độ chính xác (F1-Score)

Để kiểm tra độ chính xác của AI so với đáp án chuẩn, chạy lệnh kịch bản chấm điểm:

```bash
python scripts/module_3/evaluate_metrics.py --pred_dir tests/sandbox_outputs --gt_dir module_3_dynamic_ner/ground_truth

```

**Kết quả mong đợi:** Terminal sẽ in ra bảng điểm Precision, Recall và F1-Score cho từng trường dữ liệu. Một file log chi tiết các lỗi sai (`evaluation_report_*.json`) cũng sẽ được tự động lưu vào thư mục `logs\`.




