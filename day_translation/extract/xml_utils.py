"""
专用于extract流程的XML处理工具，如extract_translations、注释提取、分组等。
基础的parse_xml/save_xml等仍在utils/utils.py。
"""
from typing import List, Tuple, Callable, Dict, Any, Optional
import xml.etree.ElementTree as ET
import os
import logging
from pathlib import Path
import tempfile
import shutil
import re
from lxml import etree as LET

# 需要外部传入config（如pretty_print/encoding等），或用默认值

def sanitize_xml(text: str) -> str:
    """清理 XML 文本，去除所有非法字符并转义"""
    if not isinstance(text, str):
        text = str(text)
    # 去除所有非法 XML 字符（包括 C0/C1 控制符）
    text = re.sub(
        r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x84\x86-\x9F]', '', text
    )
    # 转义特殊字符
    text = (
        text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;')
    )
    return text

def sanitize_xcomment(text: str) -> str:
    """清理 XML 注释内容，防止非法字符和注释断裂"""
    if not isinstance(text, str):
        text = str(text)
    text = text.replace('--', '- -')
    text = text.replace('<', '＜').replace('>', '＞').replace('&', '＆')
    # 去除所有控制字符
    text = ''.join(c for c in text if c >= ' ' or c == '\n' or c == '\r')
    # 注释不能以 - 结尾
    if text.endswith('-'):
        text += ' '
    return text

def save_xml(tree: Any, file_path: str, pretty_print: Optional[bool] = False,
             encoding: Optional[str] = "utf-8", error_on_invalid: bool = False) -> bool:
    """
    保存 XML 文件，增强健壮性：先写入临时文件，成功后原子性覆盖，失败时不留空文件。
    """
    file_path = str(Path(file_path).resolve())
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xml", dir=os.path.dirname(file_path))
    os.close(tmp_fd)
    try:
        root = tree.getroot() if hasattr(tree, 'getroot') else tree
        if pretty_print:
            try:
                import xml.dom.minidom as minidom
                rough_string = ET.tostring(root, encoding)
                reparsed = minidom.parseString(rough_string)
                pretty_xml = reparsed.toprettyxml(indent="  ", encoding=encoding)
                with open(tmp_path, "wb") as f:
                    f.write(pretty_xml)
            except ImportError:
                new_tree = ET.ElementTree(root)
                with open(tmp_path, "wb") as f:
                    f.write(f'<?xml version="1.0" encoding="{encoding}"?>\n'.encode(encoding))
                    new_tree.write(f, encoding=encoding)
        else:
            new_tree = ET.ElementTree(root)
            with open(tmp_path, "wb") as f:
                f.write(f'<?xml version="1.0" encoding="{encoding}"?>\n'.encode(encoding))
                new_tree.write(f, encoding=encoding)
        shutil.move(tmp_path, file_path)
        logging.info(f"保存 XML 文件: {file_path}")
        return True
    except Exception as e:
        logging.error(f"保存 XML 失败: {file_path}: {e}")
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        if error_on_invalid:
            raise
        return False

def extract_translations(tree: Any, context: str = "",
                        filter_func: Optional[Callable] = None,
                        include_attributes: bool = True) -> List[Tuple[str, str, str]]:
    """
    提取可翻译内容
    """
    translations = []
    root = tree.getroot() if hasattr(tree, 'getroot') else tree
    elements = root.iter()
    for elem in elements:
        if elem.text and elem.text.strip():
            key = elem.tag if not hasattr(elem, 'get') else elem.get('key', elem.tag)
            text = elem.text.strip()
            if filter_func and not filter_func(key, text, context):
                continue
            translations.append((key, text, elem.tag))
        if include_attributes:
            for attr_name, attr_value in elem.attrib.items():
                if isinstance(attr_value, str) and attr_value.strip():
                    key = f"{elem.tag}.{attr_name}"
                    text = attr_value.strip()
                    if filter_func and not filter_func(key, text, context):
                        continue
                    translations.append((key, text, f"{elem.tag}.{attr_name}"))
    return translations

def save_xml_lxml(root, file_path, pretty_print=True, encoding="utf-8"):
    """使用 lxml.etree 保存 XML，兼容 RimWorld DefInjected 原生格式（支持带点号标签名）"""
    tree = LET.ElementTree(root)
    tree.write(file_path, pretty_print=pretty_print, encoding=encoding, xml_declaration=True)
    return True

