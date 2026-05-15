from dataclasses import dataclass

@dataclass
class OcrConfig:
    lang: str = "en"
    use_angle_cls: bool = True
    use_gpu: bool = True
    
    # True: Nếu Đạt đang test folder chứa toàn ảnh Scan/Digital
    # False: Nếu Đạt đang test folder chứa ảnh chụp camera
    skip_preprocessing_crop: bool = False