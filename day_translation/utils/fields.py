import re
import logging
from .config import TranslationConfig

CONFIG = TranslationConfig()

def is_non_text(text: str) -> bool:
    """检查文本是否为非文本内容"""
    if not text or not isinstance(text, str):
        return True
    if text.isspace():
        return True
    if re.match(r'^\d+$', text):
        return True
    if re.match(r'^[0-9\.\-\+]+$', text):
        return True
    for pattern in CONFIG.non_text_patterns:
        if re.match(pattern, text):
            return True
    return False