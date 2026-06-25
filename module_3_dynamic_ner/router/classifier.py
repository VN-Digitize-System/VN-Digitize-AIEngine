import json
import re
from pathlib import Path
from ..schemas.template_schema import DocumentInput

class UnknownDocumentError(Exception):
    """Ngoại lệ văng ra khi không nhận diện được loại tài liệu"""
    pass

class DocumentClassifier:
    def __init__(self, catalog_path: str = None):
        if catalog_path is None:
            # Tự động định vị: __file__ là classifier.py, parent là router, parent.parent là module_3_dynamic_ner
            module_3_dir = Path(__file__).resolve().parent.parent
            self.catalog_path = module_3_dir / "configs" / "document_catalog.json"
        else:
            self.catalog_path = Path(catalog_path)
            
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> dict:
        if not self.catalog_path.exists():
            print(f"⚠️ [Cảnh báo] Không tìm thấy {self.catalog_path}")
            return {}
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            return json.load(f).get("catalog", {})

    def classify(self, document: DocumentInput) -> str:
        """
        Quét 15 dòng đầu tiên để tìm Regex khớp. 
        Trả về tên file rule (vd: rules_hanh_chinh.json).
        """
        # Trích xuất một lượng text vừa đủ ở phần đầu tài liệu (tránh quét toàn bộ gây chậm)
        preview_lines = [line.text for line in document.lines[:15]]
        preview_text = " ".join(preview_lines)

        for doc_type, info in self.catalog.items():
            patterns = info.get("regex_patterns", [])
            for pattern in patterns:
                try:
                    if re.search(pattern, preview_text):
                        print(f"🕵️ [Classifier] Nhận diện thành công: {info['name']} -> Nạp {info['rule_file']}")
                        return info["rule_file"]
                except re.error:
                    print(f"⚠️ [Lỗi Regex] Pattern không hợp lệ: {pattern}")
                    continue
        
        # Nếu duyệt hết danh bạ mà không khớp
        print("❌ [Classifier] Tài liệu rác/Không xác định. Kích hoạt Strict Rejection.")
        raise UnknownDocumentError("Hệ thống từ chối xử lý: Tài liệu không thuộc các danh mục được hỗ trợ.")