import os
import xml.etree.ElementTree as ET
import re
import logging
from typing import Optional

def get_language_folder_path(language: str, root_dir: str) -> str:
    """
    获取指定语言的 Languages 目录路径。
    """
    return os.path.join(root_dir, "Languages", language)

def sanitize_xcomment(text: str) -> str:
    """
    清理 XML 注释中的非法字符。
    """
    try:
        return re.sub(r'-{2,}', ' ', text)
    except TypeError as e:
        logging.error(f"清理注释失败: {text}，错误: {e}")
        return str(text)

def save_xml_to_file(root: ET.Element, path: str) -> None:
    """
    保存 XML Element 到文件，自动缩进并修正特殊字符。
    """
    def indent_xml(elem: ET.Element, level: int = 0) -> None:
        i = "\n" + level * "    "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "    "
            for child in elem:
                indent_xml(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        indent_xml(root)
        tree = ET.ElementTree(root)
        tree.write(path, encoding='utf-8', xml_declaration=True)
        with open(path, 'r+', encoding='utf-8') as f:
            content = f.read()
            content = content.replace('->', '->')
            f.seek(0)
            f.write(content)
            f.truncate()
        logging.info(f"保存 XML 文件：{path}")
    except FileNotFoundError as e:
        logging.error(f"无法保存 XML 文件 {path}: 文件路径无效，错误: {e}")
    except PermissionError as e:
        logging.error(f"无法保存 XML 文件 {path}: 权限不足，错误: {e}")
    except Exception as e:
        logging.error(f"无法保存 XML 文件 {path}: {e}")