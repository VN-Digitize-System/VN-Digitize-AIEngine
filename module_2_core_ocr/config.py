from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class DetectionConfig:
    enabled: bool = True
    min_text_height: int = 8
    min_text_width: int = 30
    dilate_kernel_width: int = 40
    dilate_kernel_height: int = 5
    max_region_height_ratio: float = 0.15


@dataclass
class RecognitionConfig:
    model_name: str = "vgg_transformer"
    device: str = "cpu"
    beam_search: bool = False
    min_confidence: float = 0.0
    max_image_dimension: int = 1600   # resize longest side before OCR to meet SLA
    languages: list[str] = field(default_factory=lambda: ["vi", "en"])


@dataclass
class UpsideDownConfig:
    enabled: bool = True
    min_blocks_required: int = 3
    confidence_threshold: float = 0.40


@dataclass
class OCRConfig:
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    recognition: RecognitionConfig = field(default_factory=RecognitionConfig)
    upside_down: UpsideDownConfig = field(default_factory=UpsideDownConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> OCRConfig:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> OCRConfig:
        config = cls()

        if det := data.get("detection"):
            config.detection = DetectionConfig(
                enabled=det.get("enabled", True),
                min_text_height=det.get("min_text_height", 8),
                min_text_width=det.get("min_text_width", 30),
                dilate_kernel_width=det.get("dilate_kernel_width", 40),
                dilate_kernel_height=det.get("dilate_kernel_height", 5),
                max_region_height_ratio=det.get("max_region_height_ratio", 0.15),
            )

        if rec := data.get("recognition"):
            config.recognition = RecognitionConfig(
                model_name=rec.get("model_name", "vgg_transformer"),
                device=rec.get("device", "cpu"),
                beam_search=rec.get("beam_search", False),
                min_confidence=rec.get("min_confidence", 0.0),
                max_image_dimension=rec.get("max_image_dimension", 1600),
                languages=rec.get("languages", ["vi", "en"]),
            )

        if ud := data.get("upside_down"):
            config.upside_down = UpsideDownConfig(
                enabled=ud.get("enabled", True),
                min_blocks_required=ud.get("min_blocks_required", 3),
                confidence_threshold=ud.get("confidence_threshold", 0.40),
            )

        return config
