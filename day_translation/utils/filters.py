import re
from typing import Optional
import logging
from .config import get_config
from colorama import Fore, Style

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
    
    # 从配置中获取非文本模式进行检查
    config = get_config()
    for pattern in config.non_text_patterns:
        if re.match(pattern, text):
            return True
    return False

class ContentFilter:
    def __init__(self, config=None):
        if config is None:
            config = get_config()
        self.config = config
        self.default_fields = config.default_fields
        self.ignore_fields = config.ignore_fields
        self.non_text_patterns = config.non_text_patterns
    
    def filter_content(self, key: str, text: str, context: str = "") -> bool:
        """过滤可翻译内容"""
        if not text or not isinstance(text, str):
            logging.debug(f"过滤掉（{key}）: 文本为空或非字符串")
            return False
        if is_non_text(text):
            logging.debug(f"过滤掉（{key}）: 文本（{text}）为非文本内容")
            return False
        tag = key.split('.')[-1] if '.' in key else key
        if tag in self.ignore_fields:
            logging.debug(f"过滤掉（{key}）: 标签（{tag}）在忽略字段中")
            return False
        if context == "Keyed" and tag not in self.default_fields:
            logging.debug(f"过滤掉（{key}）: Keyed 中未在默认字段中")
            return False
        for pattern in self.non_text_patterns:
            if re.match(pattern, text):
                logging.debug(f"过滤掉（{key}）: 文本（{text}）匹配非文本模式")
                return False
        return True