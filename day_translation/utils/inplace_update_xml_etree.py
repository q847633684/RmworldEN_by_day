import logging
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, Optional
from .utils import get_language_folder_path, sanitize_xml
from .config import TranslationConfig

CONFIG = TranslationConfig()

def update_all_xml(mod_dir: str, translations: Dict[str, str], language: str = CONFIG.default_language, merge: bool = True) -> None:
    """使用 ElementTree 更新所有 XML 文件"""
    logging.info(f"使用 ElementTree 更新 XML: {mod_dir}, 语言: {language}")
    lang_path = get_language_folder_path(language, mod_dir)
    for dir_name in [CONFIG.def_injected_dir, CONFIG.keyed_dir]:
        dir_path = os.path.join(lang_path, dir_name)
        if not os.path.exists(dir_path):
            continue
        for xml_file in Path(dir_path).rglob("*.xml"):
            update_xml_file(str(xml_file), translations, merge)

def update_xml_file(file_path: str, translations: Dict[str, str], merge: bool = True) -> bool:
    """更新单个 XML 文件"""
    file_path = str(Path(file_path).resolve())
    if not os.path.exists(file_path):
        logging.error(f"文件不存在: {file_path}")
        return False
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        modified = False
        parent_map = {c: p for p in root.iter() for c in p}
        for elem in root.iter():
            if elem.text and elem.text.strip():
                key = generate_element_key(elem, root, parent_map)
                if key in translations:
                    if merge and elem.text.strip() != translations[key]:
                        elem.text = sanitize_xml(translations[key])
                        modified = True
                    elif not merge:
                        elem.text = sanitize_xml(translations[key])
                        modified = True
        if modified:
            with open(file_path, "wb") as f:
                f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
                tree.write(f, encoding="utf-8")
            logging.info(f"更新 XML 文件: {file_path}")
        return modified
    except ET.ParseError as e:
        logging.error(f"XML 解析失败: {file_path}: {e}")
        return False
    except Exception as e:
        logging.error(f"更新 XML 失败: {file_path}: {e}")
        return False

def generate_element_key(elem: ET.Element, root: ET.Element, parent_map: Dict) -> str:
    """生成元素键"""
    key = elem.get("key") or elem.tag
    path_parts = []
    current = elem
    while current is not None and current != root:
        if current.tag != "LanguageData":
            path_parts.append(current.tag)
        current = parent_map.get(current)
    path_parts.reverse()
    return ".".join(path_parts) if path_parts else key