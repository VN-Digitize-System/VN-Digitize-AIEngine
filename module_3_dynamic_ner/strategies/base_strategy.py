from abc import ABC, abstractmethod
from typing import Any
from .payload import ExtractionPayload

class BaseStrategy(ABC):
    def execute(self, payload: ExtractionPayload, logger=None) -> Any:
        """Hàm Template Method: Không được phép ghi đè (override) ở Class Con"""
        rule = payload.rule_config
        scan_direction = rule.get('scan_direction', 'top_down')
        scan_limit = rule.get('scan_limit', None)
        skip_lines = rule.get('skip_lines', 0)
        
        # 1. Bắt đầu Tiền xử lý dữ liệu không gian
        working_lines = list(payload.all_lines)
        
        if scan_direction == 'bottom_up':
            working_lines.reverse()
            if logger: logger(f"   -> [Strategy] Đã lật mảng OCR: Quét từ Dưới lên Trên.")
            
        if skip_lines > 0:
            working_lines = working_lines[skip_lines:]
            
        if scan_limit and isinstance(scan_limit, int) and scan_limit > 0:
            working_lines = working_lines[:scan_limit]
            
        # 2. Bàn giao mảng đã xử lý cho Class Con (Hàm nội bộ)
        return self._do_extract(working_lines, payload, logger)
        
    @abstractmethod
    def _do_extract(self, working_lines: list, payload: ExtractionPayload, logger=None) -> Any:
        """
        Class Con BẮT BUỘC phải triển khai logic bóc tách ở hàm này.
        - Dùng 'working_lines': Nếu thuật toán đơn giản, cần mảng đã được lật/cắt sẵn (scan_direction, skip_lines).
        - Dùng 'payload.all_lines': Nếu thuật toán (như Proximity) cần tọa độ Index tuyệt đối gốc của tài liệu.
        """
        pass