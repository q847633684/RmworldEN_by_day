import re
from typing import List, Tuple
from .config import TranslationConfig
from xml.etree.ElementTree import Element

CONFIG = TranslationConfig()

def is_non_text(text: str) -> bool:
    """检查文本是否为非翻译内容（如数字、布尔值）"""
    if not text or not isinstance(text, str):
        return True
    return any(re.match(pattern, text.strip()) for pattern in CONFIG.non_text_patterns)

def extract_translatable_fields(def_node: Element) -> List[Tuple[str, str, str]]:
    """
    提取 XML 节点中的可翻译字段

    Args:
        def_node: XML 元素节点

    Returns:
        List of tuples (field_path, text, tag)
    """
    translations = []
    def traverse(node: Element, path: str = "") -> None:
        tag = node.tag
        if tag in CONFIG.ignore_fields:
            return
        new_path = f"{path}.{tag}" if path else tag
        if node.text and node.text.strip() and not is_non_text(node.text):
            if tag in CONFIG.default_fields:
                translations.append((new_path, node.text.strip(), tag))
        for child in node:
            traverse(child, new_path)
    traverse(def_node)
    return translations