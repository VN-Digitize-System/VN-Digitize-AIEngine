from dataclasses import dataclass

@dataclass
class OcrConfig:
    lang: str = "en"             # Bắt buộc dùng tiếng Việt
    use_angle_cls: bool = False  # Đặt False vì Module 1 đã giúp ta đo góc và xoay thẳng rồi!
    use_gpu: bool = True        # Đổi thành True nếu máy bạn có VGA xịn