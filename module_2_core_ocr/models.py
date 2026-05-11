from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TextBlock:
    text: str
    confidence: float          # 0.0 → 1.0
    bbox: dict                 # {"x": int, "y": int, "width": int, "height": int}
    block_index: int           # reading order index


@dataclass
class OCRResult:
    full_text: str             # all blocks joined by "\n"
    text_blocks: list[TextBlock]
    avg_confidence: float
    is_upside_down: bool       # True if avg_confidence < threshold
    warnings: list[str] = field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
