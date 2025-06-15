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
    # 硬编码忽略前缀
    ignore_prefixes = ["#", "@", "$", "%", "&"]
    return any(text.startswith(p) for p in ignore_prefixes)

def extract_translatable_fields(node: ET.Element, prefix: str = "", li_indices: List[int] = None) -> List[Tuple[str, str, str]]:
    """
    提取 XML 节点中的可翻译字段，支持 <li> 数字索引和嵌套结构。

    Args:
        node: XML 节点
        prefix: 字段路径前缀
        li_indices: 当前 <li> 的索引列表（支持多层嵌套）

    Returns:
        List of tuples (field_path, text, tag)
    """
    if li_indices is None:
        li_indices = []
    fields = []
    for idx, child in enumerate(node):
        current_indices = li_indices
        new_prefix = prefix
        if child.tag == "li":
            current_indices = li_indices + [idx]
            index_str = ".".join(str(i) for i in current_indices)
            new_prefix = f"{prefix}{index_str}" if prefix else index_str
        else:
            new_prefix = f"{prefix}{child.tag}" if prefix else child.tag
        if child.text and child.text.strip() and not is_non_text(child.text):
            fields.append((new_prefix, child.text.strip(), child.tag))
        if len(child) > 0:
            child_prefix = f"{new_prefix}." if child.tag != "li" else new_prefix
            fields.extend(extract_translatable_fields(child, child_prefix, current_indices))
    return fields