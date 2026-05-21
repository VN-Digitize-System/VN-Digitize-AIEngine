from schemas.template_schema import DocumentInput
from typing import List

class HeuristicRetriever:
    """
    Thuật toán lọc văn bản siêu nhẹ bằng CPU. 
    Chỉ giữ lại những trang/đoạn văn bản có chứa từ khóa liên quan đến trường cần bóc tách.
    """
    @staticmethod
    def retrieve_context(document: DocumentInput, keywords: List[str], window_size: int = 5) -> str:
        if not keywords:
            # Nếu không có keyword mồi, đành lấy 2 trang đầu và 1 trang cuối làm mặc định
            return HeuristicRetriever._get_default_context(document)
            
        relevant_lines = []
        
        # Chuyển keyword về chữ thường để dễ so sánh
        keywords_lower = [kw.lower() for kw in keywords]
        
        for i, line in enumerate(document.lines):
            line_text_lower = line.text.lower()
            if any(kw in line_text_lower for kw in keywords_lower):
                # Lấy thêm vài dòng trước và sau (window_size) để giữ ngữ cảnh cho LLM hiểu
                start_idx = max(0, i - window_size)
                end_idx = min(len(document.lines), i + window_size + 1)
                
                for j in range(start_idx, end_idx):
                    if document.lines[j].text not in relevant_lines:
                        relevant_lines.append(document.lines[j].text)
                        
        if not relevant_lines:
             return HeuristicRetriever._get_default_context(document)
             
        return "\n".join(relevant_lines)

    @staticmethod
    def _get_default_context(document: DocumentInput) -> str:
        # Lấy trang 1, 2 và trang cuối cùng
        last_page = document.lines[-1].page_number if document.lines else 1
        default_lines = [
            line.text for line in document.lines 
            if line.page_number in [1, 2, last_page]
        ]
        return "\n".join(default_lines)