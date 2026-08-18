from .proximity_strategy import ProximityNumberStrategy
from .fixed_value_strategy import FixedValueStrategy
from .global_regex_strategy import GlobalRegexStrategy

class ExtractorFactory:
    _dispatch_table = {
        "proximity_number_search": ProximityNumberStrategy(),
        "fixed_value": FixedValueStrategy(),
        "global_regex": GlobalRegexStrategy(),
    }
    
    @classmethod
    def get_strategy(cls, method_name: str):
        # Trả về Strategy nếu có, nếu không trả về None (rất quan trọng cho bước sau)
        return cls._dispatch_table.get(method_name)