import re
from typing import Optional
import logging
from ..utils.config import TranslationConfig
from ..utils.fields import is_non_text

class ContentFilter:
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.default_fields = config.default_fields
        self.ignore_fields = config.ignore_fields
        self.non_text_patterns = config.non_text_patterns

    def filter_content(self, key: str, text: str, context: str = "") -> bool:
        """过滤可翻译内容"""
        if not text or not isinstance(text, str):
            return False
        if is_non_text(text):
            return False
        tag = key.split('.')[-1] if '.' in key else key
        if tag in self.ignore_fields:
            return False
        if context == "Keyed" and tag not in self.default_fields:
            return False
        for pattern in self.non_text_patterns:
            if re.match(pattern, text):
                return False
        return True