from typing import List, Tuple, Dict, Optional
import xml.etree.ElementTree as ET
from .config import DEFAULT_FIELDS, IGNORE_FIELDS, NON_TEXT_PATTERNS
import logging
import re

def is_translatable_text(text: str, tag: str) -> bool:
    """
    判断某个文本及其标签是否应被视为可翻译内容。

    Args:
        text (str): 节点文本。
        tag (str): 节点标签。

    Returns:
        bool: True 表示可翻译，False 表示应跳过。
    """
    if not text or not isinstance(text, str) or not text.strip():
        logging.debug(f"排除空文本：{text}")
        return False
    if tag.lower() in [f.lower() for f in IGNORE_FIELDS]:
        logging.debug(f"排除不可翻译标签 {tag}：{text}")
        return False
    for pattern in NON_TEXT_PATTERNS:
        if re.match(pattern, text.strip()):
            logging.debug(f"排除正则匹配 {pattern}：{text}")
            return False
    if tag.lower() in [f.lower() for f in DEFAULT_FIELDS]:
        logging.debug(f"包含可翻译标签 {tag}：{text}")
        return True
    logging.debug(f"包含多词文本：{text}")
    return True

def extract_translatable_fields(
    node: ET.Element,
    path: str = "",
    list_indices: Optional[Dict[str, int]] = None,
    translations: Optional[List[Tuple[str, str, str]]] = None,
    parent_tag: Optional[str] = None
) -> List[Tuple[str, str, str]]:
    """
    递归提取 XML 节点下所有可翻译字段。

    Args:
        node (ET.Element): 当前 XML 节点。
        path (str, optional): 字段路径前缀。
        list_indices (Optional[Dict[str, int]], optional): li 索引跟踪。
        translations (Optional[List[Tuple[str, str, str]]], optional): 结果累加。
        parent_tag (Optional[str], optional): 父节点标签。

    Returns:
        List[Tuple[str, str, str]]: (字段路径, 文本, 标签) 三元组列表。
    """
    if list_indices is None:
        list_indices = {}
    if translations is None:
        translations = []
    node_tag = node.tag
    if node_tag == 'defName':
        return translations
    current_path = f"{path}.{node_tag}" if path else node_tag
    index_key = f"{path}|{node_tag}"
    if node_tag == 'li':
        if index_key in list_indices:
            list_indices[index_key] += 1
        else:
            list_indices[index_key] = 0
        current_path = f"{path}.{list_indices[index_key]}" if path else str(list_indices[index_key])
    if node_tag == 'li':
        if parent_tag and parent_tag.lower() in [f.lower() for f in DEFAULT_FIELDS]:
            if node.text and is_translatable_text(node.text, node_tag):
                translations.append((current_path, node.text, node_tag))
    else:
        if node_tag.lower() in [f.lower() for f in DEFAULT_FIELDS]:
            if node.text and is_translatable_text(node.text, node_tag):
                translations.append((current_path, node.text, node_tag))
    for child in node:
        if child.tag == 'li':
            extract_translatable_fields(child, current_path, list_indices, translations, parent_tag=node_tag)
        else:
            extract_translatable_fields(child, current_path, list_indices.copy(), translations, parent_tag=node_tag)
    return translations
