import re
from typing import List

def extract_amounts(text: str) -> List[float]:
    """
    Extracts potential numeric amounts from a string.
    Handles Bangla numbers and standard English digits.
    """
    # Translate Bangla digits to English digits
    bangla_to_english = {
        '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
        '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
    }
    
    translated_text = ""
    for char in text:
        translated_text += bangla_to_english.get(char, char)
        
    # Find all number sequences (including decimals)
    # We look for sequences of digits, possibly separated by commas, optional decimal point
    raw_matches = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', translated_text)
    
    amounts = []
    for match in raw_matches:
        clean_match = match.replace(',', '')
        try:
            val = float(clean_match)
            # Avoid matching extremely small numbers or years like 2026 unless they are amounts
            if val > 10 and val < 1000000:
                amounts.append(val)
        except ValueError:
            continue
            
    return list(set(amounts))
