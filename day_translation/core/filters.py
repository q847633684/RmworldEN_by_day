import re
from typing import Optional
import logging
from ..utils.config import TranslationConfig
from ..utils.fields import is_non_text
from colorama import Fore, Style

class ContentFilter:
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.default_fields = config.default_fields
        self.ignore_fields = config.ignore_fields
        self.non_text_patterns = config.non_text_patterns

    def filter_content(self, key: str, text: str, context: str = "") -> bool:
        """过滤可翻译内容，并打印交互提示"""
        if not text or not isinstance(text, str):
            print(f"{Fore.YELLOW}过滤掉（{key}）: 文本为空或非字符串{Style.RESET_ALL}")
            return False
        if is_non_text(text):
            print(f"{Fore.YELLOW}过滤掉（{key}）: 文本（{text}）为非文本内容{Style.RESET_ALL}")
            return False
        tag = key.split('.')[-1] if '.' in key else key
        if tag in self.ignore_fields:
            print(f"{Fore.YELLOW}过滤掉（{key}）: 标签（{tag}）在忽略字段中{Style.RESET_ALL}")
            return False
        if context == "Keyed" and tag not in self.default_fields:
            print(f"{Fore.YELLOW}过滤掉（{key}）: Keyed 中未在默认字段中{Style.RESET_ALL}")
            return False
        for pattern in self.non_text_patterns:
            if re.match(pattern, text):
                print(f"{Fore.YELLOW}过滤掉（{key}）: 文本（{text}）匹配非文本模式{Style.RESET_ALL}")
                return False
        return True