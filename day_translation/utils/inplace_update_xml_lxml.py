import logging
import os
from pathlib import Path
from typing import Dict, Optional
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    logging.warning("lxml 未安装，无法使用 lxml 更新 XML")
from .utils import get_language_folder_path, sanitize_xml
from .config import TranslationConfig

CONFIG = TranslationConfig()

def update_all_xml(mod_dir: str, translations: Dict[str, str], language: str = CONFIG.default_language, merge: bool = True) -> None:
    """使用 lxml 更新所有 XML 文件"""
    if not LXML_AVAILABLE:
        logging.error("lxml 未安装，跳过 lxml 更新")
        return
    logging.info(f"使用 lxml 更新 XML: {mod_dir}, 语言: {language}")
    lang_path = get_language_folder_path(language, mod_dir)
    for dir_name in [CONFIG.def_injected_dir, CONFIG.keyed_dir]:
        dir_path = os.path.join(lang_path, dir_name)
        if not os.path.exists(dir_path):
            continue
        for xml_file in Path(dir_path).rglob("*.xml"):
            update_xml_file(str(xml_file), translations, merge)

def update_xml_file(file_path: str, translations: Dict[str, str], merge: bool = True) -> bool:
    """更新单个 XML 文件"""
    if not LXML_AVAILABLE:
        return False
    file_path = str(Path(file_path).resolve())
    if not os.path.exists(file_path):
        logging.error(f"文件不存在: {file_path}")
        return False
    try:
        parser = etree.XMLParser(remove_comments=False)
        tree = etree.parse(file_path, parser)
        root = tree.getroot()
        modified = False
        for elem in root.xpath(".//*"):
            if elem.text and elem.text.strip():
                key = generate_element_key(elem, root)
                if key in translations:
                    if merge and elem.text.strip() != translations[key]:
                        elem.text = sanitize_xml(translations[key])
                        modified = True
                    elif not merge:
                        elem.text = sanitize_xml(translations[key])
                        modified = True
        if modified:
            tree.write(file_path, encoding="utf-8", xml_declaration=True, pretty_print=True)
            logging.info(f"更新 XML 文件: {file_path}")
        return modified
    except etree.XMLSyntaxError as e:
        logging.error(f"XML 解析失败: {file_path}: {e}")
        return False
    except Exception as e:
        logging.error(f"更新 XML 失败: {file_path}: {e}")
        return False

def generate_element_key(elem: etree.Element, root: etree.Element) -> str:
    """生成元素键"""
    key = elem.get("key") or elem.tag
    path_parts = []
    current = elem
    while current is not None and current != root:
        if current.tag != "LanguageData":
            path_parts.append(current.tag)
        current = current.getparent()
    path_parts.reverse()
    return ".".join(path_parts) if path_parts else key