# Kiến trúc Hệ thống Module 3: Dynamic NER & Zero-shot Extraction

Tài liệu này mô tả chi tiết các quyết định kiến trúc, luồng dữ liệu và cơ chế xử lý lỗi của Module 3. Hệ thống được thiết kế theo hướng Full LLM linh hoạt, có khả năng tự động phân tách tài liệu, tối ưu phần cứng và tự học từ người dùng (Human-in-the-Loop).

## 1. Lõi Bóc Tách (Core Extraction Engine)
* **Phương pháp:** Bóc tách Zero-shot (Zero-shot Extraction) trực tiếp từ văn bản OCR.
* **Mô hình:** `qwen2.5:14b` chạy cục bộ qua `LocalLLMProvider`.
* **Cơ chế Lược đồ động (Dynamic Schema):** Chuyển đổi các cấu hình từ `target_fields.json` thành Native JSON Schema Dict (mảng `properties` và `required`). Lược bỏ hoàn toàn sự phụ thuộc vào Pydantic Model động để tối ưu tốc độ và độ tuân thủ của mô hình.

## 2. Quản lý Không gian làm việc & Dữ liệu
* **Đầu vào (Input):** Thuật toán duyệt đệ quy (Recursive Globbing) tự động quét và thu thập các file `ocr.json` từ các thư mục con `jsons/` của Module 2.
* **Không gian độc lập (Isolated Workspace):** Mọi kết quả đầu ra được lưu tại `module_3_workspace/` để đảm bảo tính bất biến (Immutability) của dữ liệu Module 2 gốc.
* **Cơ chế Lưu vết (Checkpointing):** Lưu ngay kết quả JSON của từng tài liệu sau khi bóc tách vào `module_3_workspace/checkpoints/` để chống mất dữ liệu khi tràn RAM (OOM).
* **Xử lý Lỗi (Error Handling):** Áp dụng cơ chế Fail-safe (Bỏ qua lỗi và chạy tiếp). Nếu 1 file bị lỗi, ghi log và vòng lặp tiếp tục xử lý file tiếp theo.

## 3. Hệ thống Tiền xử lý: Lưỡi dao Đa tầng (Multi-tier Splitter)
Giải quyết bài toán chia tách tệp OCR 100 trang hỗn hợp thành các tài liệu độc lập mà không dùng LLM để tiết kiệm VRAM. Thuật toán hoạt động trên một **bản sao văn bản dùng một lần** (đã xóa dấu tiếng Việt và viết thường).

* **Tầng 1 (Quét Tiêu ngữ Quốc gia):** Sử dụng hệ thống chấm điểm từ khóa (Keyword Voting: `cong hoa` +2, `xa hoi` +2, `doc lap` +1...). Trang có tổng điểm >= 6 được xác nhận là điểm khởi đầu tài liệu mới.
* **Tầng 2 (Quét Từ khóa Neo - Anchor Keywords):** Quét các từ khóa đặc trưng của tên tài liệu (VD: `quyet dinh`, `hop dong`) từ danh sách tĩnh hoặc cấu hình động.
* **Tầng 3 (Dấu hiệu Hình thức - Heuristic Suspicion):** Cảnh báo tài liệu lạ. 
    * *Điều kiện kích hoạt:* Dòng 1 hoặc dòng 2 của trang OCR in hoa toàn bộ.
    * *Bộ lọc kép (Kháng nhiễu False Positive):* Dùng Regex cấu trúc động loại trừ các dòng bắt đầu bằng `CHƯƠNG`, `ĐIỀU`, `MỤC`... kết hợp với Số La Mã (I, II, III...). Nếu bị lọc, hệ thống im lặng đi tiếp. Nếu không bị lọc, kích hoạt HITL.

## 4. Tối ưu VRAM: Chiến thuật "Cắt Đầu - Chốt Cuối"
* **Nguyên lý:** Mô hình LLM có giới hạn Context Window.
* **Thực thi:** Đối với mỗi cụm tài liệu sau khi cắt, hệ thống chỉ trích xuất tối đa **3 trang đầu tiên** và **3 trang cuối cùng**. Giảm 70% lượng Token dư thừa (các trang nội dung ở giữa), đảm bảo card đồ họa luôn chạy ổn định.

## 5. Phân loại & Hệ thống Tự học (Self-Evolving System)
Cơ chế xử lý linh hoạt dựa trên nguyên tắc Human-in-the-Loop (HITL).

* **Kiến trúc Micro-configs:** Mỗi loại tài liệu được định nghĩa bằng một file JSON nhỏ gọn nằm trong thư mục `schemas/`.
* **Phân loại Siêu nhẹ (Lite Classification):** Gửi 5 dòng đầu tiên của cụm tài liệu đã cắt cho LLM để định tuyến. LLM sẽ trả về tên loại tài liệu tương ứng với các file trong thư mục `schemas/`.
* **Cơ chế Hỏi đáp Động (Ad-hoc Prompting):** Nếu Lite Classification xác định đây là "Tài liệu lạ" (chưa có Lược đồ) hoặc Tầng 3 (Lưỡi dao) báo động, hệ thống tạm dừng và yêu cầu người dùng nhập các trường cần bóc tách / từ khóa neo.
* **Tự động Tiến hóa (Auto-Schema Generation):** Câu trả lời từ HITL sẽ được tự động đóng gói thành file `.json` mới và lưu vào `schemas/` + `custom_split_anchors.json`. Các tài liệu tương tự ở phía sau sẽ được tự động nhận diện và bóc tách mà không cần hỏi lại.

## 6. Trình bày Báo cáo
* Xuất toàn bộ dữ liệu bóc tách của nhiều Lược đồ khác nhau vào duy nhất **1 file Master Excel** (`tong_hop_bien_muc.xlsx`).
* Dữ liệu của mỗi loại tài liệu được tổ chức thành các Tabs (Sheets) riêng biệt, vuông vức và gọn gàng thông qua thư viện Pandas.