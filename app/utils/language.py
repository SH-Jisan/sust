import re

def detect_is_bangla(text: str) -> bool:
    """
    Checks if a string contains any Bengali characters.
    Bengali Unicode range is \u0980-\u09FF.
    """
    if not text:
        return False
        
    # Search for any character in the Bengali Unicode block
    bengali_pattern = re.compile(r'[\u0980-\u09FF]')
    return bool(bengali_pattern.search(text))
