from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class BarcodeInfo:
    barcode_type: str
    data: str
    bbox: dict  # {"x": int, "y": int, "width": int, "height": int}


@dataclass
class PreprocessResult:
    processed_image: np.ndarray | None
    is_blank: bool
    is_wrong_orientation: bool
    skew_angle: float
    barcodes: list[BarcodeInfo] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
