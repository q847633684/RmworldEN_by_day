from typing import List, Tuple
import xml.etree.ElementTree as ET
from functools import lru_cache
import re
from ..utils.config import TranslationConfig

CONFIG = TranslationConfig()

@lru_cache(maxsize=256)
def is_non_text(text: str) -> bool:
    """检查文本是否为非翻译内容（缓存版本）"""
    if not text or not text.strip():
        return True
    text = text.strip()
    
    # 数字检查
    try:
        float(text)
        return True
    except ValueError:
        pass
    
    # 布尔值检查
    if text.lower() in ('true', 'false'):
        return True
    
    # 使用配置中的忽略前缀
    if any(text.startswith(p) for p in CONFIG.ignore_prefixes):
        return True
    
    # 使用配置中的非文本正则模式
    for pattern in CONFIG.non_text_patterns:
        if re.match(pattern, text):
            return True
    
    return False

def is_translatable_text(text: str, tag: str) -> bool:
    """
    判断某个文本及其标签是否应被视为可翻译内容。
    参考 Day_EN 的更复杂判断逻辑。
    """
    if not text or not isinstance(text, str) or not text.strip():
        return False
    
    text = text.strip()
    
    # 检查是否在忽略字段列表中
    if tag.lower() in [f.lower() for f in CONFIG.ignore_fields]:
        return False
    
    # 检查正则模式
    for pattern in CONFIG.non_text_patterns:
        if re.match(pattern, text):
            return False
    
    # 检查是否在默认翻译字段中
    if tag.lower() in [f.lower() for f in CONFIG.default_fields]:
        return True
    
    # 对于多词文本，默认认为可翻译
    words = text.split()
    return len(words) > 1

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