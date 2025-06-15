from typing import List, Tuple
import xml.etree.ElementTree as ET
from ..utils.config import TranslationConfig

CONFIG = TranslationConfig()

def is_non_text(text: str) -> bool:
    """检查文本是否为非翻译内容"""
    if not text or not text.strip():
        return True
    text = text.strip()
    try:
        float(text)
        return True
    except ValueError:
        pass
    return any(text.startswith(p) for p in CONFIG.ignore_prefixes)

def extract_translatable_fields(node: ET.Element, prefix: str = "", li_index: int = -1) -> List[Tuple[str, str, str]]:
    """
    提取 XML 节点中的可翻译字段，处理 <li> 标签的索引。

    Args:
        node: XML 节点
        prefix: 字段路径前缀
        li_index: 当前 <li> 标签的索引（-1 表示非 <li>）

    Returns:
        List of tuples (field_path, text, tag)
    """
    fields = []
    for idx, child in enumerate(node):
        new_prefix = prefix
        if child.tag == "li":
            new_prefix = f"{prefix}li[{idx}]" if prefix else f"li[{idx}]"
        else:
            new_prefix = f"{prefix}{child.tag}" if prefix else child.tag
        if child.text and child.text.strip() and not is_non_text(child.text):
            fields.append((new_prefix, child.text.strip(), child.tag))
        if len(child) > 0:
            child_prefix = f"{new_prefix}." if child.tag != "li" else new_prefix
            fields.extend(extract_translatable_fields(child, child_prefix, idx if child.tag == "li" else -1))
    return fields