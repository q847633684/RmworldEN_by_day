import re
import logging
import os
from typing import Set, List, Dict, Any

class UnifiedFilterRules:
    DEFAULT_FIELDS = {
        'label', 'description', 'labelShort', 'descriptionShort',
        'title', 'text', 'message', 'tooltip', 'baseDesc',
        'skillDescription', 'backstoryDesc', 'jobString',
        'gerundLabel', 'verb', 'deathMessage', 'summary',
        'note', 'flavor', 'quote', 'caption'
    }
    IGNORE_FIELDS = {
        'defName', 'id', 'cost', 'damage', 'x', 'y', 'z',
        'width', 'height', 'priority', 'count', 'index',
        'version', 'url', 'path', 'file', 'hash', 'key'
    }
    NON_TEXT_PATTERNS = [
        r'^\d+$', r'^-?\d+\.\d+$', r'^[0-9a-fA-F]+$',  # 数字、浮点数、十六进制
        r'^[+-]?(\d+\.?\d*|\.\d+)$', r'^\s*$',  # 数字、空白
        r'^true$|^false$', r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$',
        r'^[A-Za-z0-9_-]+/[A-Za-z0-9_-]+$',
        r'https?://[^\s<>"]+|www\.[^\s<>"]+',
        r'^[A-Za-z0-9_-]+\.xml$'
    ]

    @classmethod
    def get_rules(cls, use_fallback: bool = False):
        if use_fallback:
            return cls
        return cls

    @classmethod
    def from_custom_config(cls, config: Dict[str, Any]):
        class CustomRules:
            DEFAULT_FIELDS = set(config.get('default_fields', cls.DEFAULT_FIELDS))
            IGNORE_FIELDS = set(config.get('ignore_fields', cls.IGNORE_FIELDS))
            NON_TEXT_PATTERNS = config.get('non_text_patterns', cls.NON_TEXT_PATTERNS)
        return CustomRules()