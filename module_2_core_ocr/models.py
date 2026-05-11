from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WordToken:
    text: str
    confidence: float        # 0.0–1.0
    confidence_pct: int      # 0–100 for API / UI
    bbox: dict
    is_flagged: bool


@dataclass
class TextBlock:
    text: str
    confidence: float
    bbox: dict
    block_index: int
    words: list[WordToken] = field(default_factory=list)


@dataclass
class MetadataField:
    """One structured field extracted by Module 3 NER."""
    field_name: str
    value: str
    confidence: float
    bounding_box: dict  # spec format: {"x1", "y1", "x2", "y2"}


@dataclass
class SubDocument:
    """One logical sub-document identified by Module 4 PDF splitting."""
    type: str
    page_start: int
    page_end: int


@dataclass
class OCRResponse:
    """
    API contract object. Module 2 fills OCR fields; Module 3 fills metadata;
    Module 4 fills classification, summary, and sub_documents.
    """
    document_id: str
    confidence_overall: float
    full_text: str
    text_blocks: list[TextBlock]
    warnings: list[str] = field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    classification: str | None = None
    summary: str | None = None
    metadata: list[MetadataField] = field(default_factory=list)
    sub_documents: list[SubDocument] = field(default_factory=list)

    def to_dict(self) -> dict:
        def word_to_dict(w: WordToken) -> dict:
            return {
                "text": w.text,
                "confidence": w.confidence_pct,
                "bbox": w.bbox,
                "is_flagged": w.is_flagged,
            }

        def block_to_dict(b: TextBlock) -> dict:
            return {
                "text": b.text,
                "confidence": min(100, round(b.confidence * 100)),
                "bbox": b.bbox,
                "block_index": b.block_index,
                "words": [word_to_dict(w) for w in b.words],
            }

        return {
            "document_id": self.document_id,
            "classification": self.classification,
            "summary": self.summary,
            "confidence_overall": round(self.confidence_overall, 4),
            "metadata": [
                {
                    "field_name": m.field_name,
                    "value": m.value,
                    "confidence": round(m.confidence, 4),
                    "bounding_box": m.bounding_box,
                }
                for m in self.metadata
            ],
            "sub_documents": [
                {"type": s.type, "page_start": s.page_start, "page_end": s.page_end}
                for s in self.sub_documents
            ],
            "full_text": self.full_text,
            "text_blocks": [block_to_dict(b) for b in self.text_blocks],
            "warnings": self.warnings,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


@dataclass
class OCRResult:
    full_text: str
    text_blocks: list[TextBlock]
    avg_confidence: float
    is_upside_down: bool
    warnings: list[str] = field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None

    def to_response(self, document_id: str) -> OCRResponse:
        """Wrap internal result into the API-contract OCRResponse."""
        return OCRResponse(
            document_id=document_id,
            confidence_overall=self.avg_confidence,
            full_text=self.full_text,
            text_blocks=self.text_blocks,
            warnings=self.warnings,
            error_code=self.error_code,
            error_message=self.error_message,
        )
