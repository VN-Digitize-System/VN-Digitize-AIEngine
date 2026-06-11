from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class PaddleConfig:
    det_limit_side_len: int = 2048
    det_db_thresh: float = 0.3
    det_db_box_thresh: float = 0.6

@dataclass
class VietOcrConfig:
    config_name: str = "vgg_transformer"

@dataclass
class HeuristicSortingConfig:
    y_tolerance_ratio: float = 0.5

@dataclass
class OcrConfig:
    active_engine: str = "paddle_vietocr"
    use_gpu: bool = True
    lang: str = "vi"
    
    # Các class lồng nhau
    paddle: PaddleConfig = None
    vietocr: VietOcrConfig = None
    heuristic: HeuristicSortingConfig = None

    def __post_init__(self):
        # Đảm bảo luôn có object con dù không truyền vào
        if self.paddle is None: self.paddle = PaddleConfig()
        if self.vietocr is None: self.vietocr = VietOcrConfig()
        if self.heuristic is None: self.heuristic = HeuristicSortingConfig()

    @classmethod
    def from_yaml(cls, path: str | Path) -> "OcrConfig":
        """Ánh xạ thủ công (Manual Explicit Mapping) từ YAML sang Dataclass"""
        path_obj = Path(path)
        if not path_obj.exists():
            return cls() # Trả về cấu hình mặc định nếu không tìm thấy file

        with open(path_obj, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        engine_data = data.get("engine", {})
        paddle_data = data.get("paddle", {})
        vietocr_data = data.get("vietocr", {})
        heuristic_data = data.get("heuristic_sorting", {})

        return cls(
            active_engine=engine_data.get("active", "paddle_vietocr"),
            use_gpu=engine_data.get("use_gpu", True),
            lang=engine_data.get("lang", "vi"),
            paddle=PaddleConfig(**paddle_data),
            vietocr=VietOcrConfig(**vietocr_data),
            heuristic=HeuristicSortingConfig(**heuristic_data)
        )