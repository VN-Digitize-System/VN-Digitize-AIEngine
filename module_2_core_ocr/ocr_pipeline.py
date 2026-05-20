import numpy as np
import cv2
from PIL import Image
import torch
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

from shared_utils.logger import get_logger
from module_1_image_preprocessing.preprocessor import ImagePreprocessor
from .models import OcrResult, OcrWord, BoundingBox
from .config import OcrConfig
from .utils import get_rotated_crop  # Import hàm cắt ảnh vừa tạo

logger = get_logger(__name__)

class OcrEngine:
    def __init__(self, config: OcrConfig | None = None):
        self._config = config or OcrConfig()
        
        # 1. KHỞI TẠO PADDLE OCR (CHỈ DÙNG DETECTION)
        logger.info("Đang khởi tạo PaddleOCR (Chỉ chế độ Detection)...")
        self.detector = PaddleOCR(
            use_angle_cls=self._config.use_angle_cls, 
            lang="en", 
            rec=False,
            
            # --- BỘ PARAMETER CHUYÊN TRỊ VĂN BẢN DÀY ĐẶC (DENSE TEXT) ---
            
            # 1. Tăng trần độ phân giải từ 2048 lên 3072 hoặc 4096 (Tùy VRAM)
            # Giúp các dòng chữ nhỏ xíu không bị dính vào nhau khi AI phân tích
            det_limit_side_len=3072, 
            
            # 2. Bật Dilation (Cực kỳ quan trọng)
            # Thuật toán sẽ làm "đậm/mập" các nét chữ thanh mảnh lên trước khi tìm Box,
            # giúp nó không bỏ sót các nét chữ nhỏ trên nền giấy to.
            use_dilation=False,
            
            # 3. Hạ ngưỡng nhạy cảm của bản đồ xác suất (0.3 -> 0.1)
            det_db_thresh=0.1,
            
            # 4. Hạ ngưỡng loại bỏ Box (0.6 -> 0.4)
            # PaddleOCR hay có tật "hơi nghi ngờ" là vứt luôn Box.
            # Ta ép nó giữ lại kể cả khi nó chỉ tự tin 40% đó là dòng chữ.
            det_db_box_thresh=0.2, 

            det_db_unclip_ratio=1.0
        )

        # 2. KHỞI TẠO VIETOCR (CHUYÊN GIA ĐỌC CHỮ)
        logger.info("Đang khởi tạo VietOCR (vgg_transformer)...")
        v_config = Cfg.load_config_from_name('vgg_transformer')
        
        # 🟢 CƠ CHẾ CHUYỂN ĐỔI THÔNG MINH (SMART FALLBACK)
        v_config['device'] = 'cpu'
        
        if self._config.use_gpu:
            if torch.cuda.is_available():
                v_config['device'] = 'cuda:0'
                logger.info("Đã kích hoạt GPU (CUDA) cho VietOCR.")
            else:
                logger.warning("Cảnh báo: Config yêu cầu GPU nhưng PyTorch hiện tại là bản CPU. Tự động chuyển về CPU.")
            
        self.recognizer = Predictor(v_config)

    def process(self, preprocessor: ImagePreprocessor, image_path: str) -> tuple[OcrResult, np.ndarray | None]:
        logger.info(f"Đang thực thi Pipeline với skip_crop={self._config.skip_preprocessing_crop}")
        
        m1_result = preprocessor.process(image_path, skip_crop=self._config.skip_preprocessing_crop)

        if not m1_result or m1_result.processed_image is None:
            m2_result = OcrResult(is_success=False, words=[], full_text="", error_message="M1 Fail")
            return m2_result, None
            
        if m1_result.is_blank:
            m2_result = OcrResult(is_success=True, words=[], full_text="[BLANK_PAGE]")
            return m2_result, m1_result.processed_image

        image = m1_result.processed_image
        
        try:
            # BƯỚC 1: DÙNG PADDLE OCR TÌM BOUNDING BOX
            # Bổ sung det=True (Bật bắt Box) và rec=False (Tắt đọc chữ) ngay tại đây!
            boxes_result = self.detector.ocr(image, cls=self._config.use_angle_cls, det=True, rec=False)
            
            words = []
            full_text_parts = []
            
            if boxes_result and boxes_result[0]:
                
                # ======================================================
                # 1. THU THẬP TẤT CẢ TỌA ĐỘ VÀ LỌC DỮ LIỆU RÁC
                # ======================================================
                raw_boxes = []
                for line in boxes_result[0]:
                    if len(line) == 2 and isinstance(line[1], tuple):
                        raw_boxes.append(line[0]) # Chỉ lấy tọa độ
                    else:
                        raw_boxes.append(line)
                        
                # ======================================================
                # 2. SẮP XẾP BOX TỪ TRÊN XUỐNG DƯỚI (SPATIAL SORTING)
                # ======================================================
                # Lấy tọa độ Y nhỏ nhất (điểm cao nhất) của mỗi box làm chuẩn để xếp
                sorted_boxes = sorted(raw_boxes, key=lambda b: min(p[1] for p in b))

                # ======================================================
                # 3. GOM TẤT CẢ ẢNH VÀO MỘT LÔ (BATCHING)
                # ======================================================
                pil_images = []
                for box_coords in sorted_boxes:
                    # Cắt ảnh và chuyển sang PIL như cũ, nhưng CHƯA ĐỌC vội
                    cropped_img = get_rotated_crop(image, box_coords, padding=3)
                    cropped_img_rgb = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)
                    pil_images.append(Image.fromarray(cropped_img_rgb))

                # ======================================================
                # 4. ĐƯA CẢ LÔ VÀO VIETOCR XỬ LÝ 1 LẦN DUY NHẤT
                # ======================================================
                if pil_images:
                    logger.info(f"Đang đọc {len(pil_images)} dòng chữ bằng Batch Processing...")
                    # Dùng hàm predict_batch thay vì predict
                    texts, probs = self.recognizer.predict_batch(pil_images, return_prob=True)
                    
                    # Ghép kết quả trả về tương ứng với từng tọa độ Box
                    for i, box_coords in enumerate(sorted_boxes):
                        text = texts[i]
                        prob = probs[i]
                        
                        words.append(OcrWord(
                            text=text,
                            confidence=prob,
                            bbox=BoundingBox(points=[(int(p[0]), int(p[1])) for p in box_coords])
                        ))
                        full_text_parts.append(text)
                        
                logger.info(f"Hoàn tất. Trích xuất được {len(words)} dòng chữ bằng VietOCR.")
            
            m2_result = OcrResult(
                is_success=True,
                words=words,
                full_text="\n".join(full_text_parts)
            )
            
        except Exception as e:
            logger.error(f"Lỗi hệ thống OCR: {e}")
            m2_result = OcrResult(is_success=False, words=[], full_text="", error_message=str(e))
        
        return m2_result, m1_result.processed_image