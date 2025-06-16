import logging
import os
import re
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable
from functools import wraps
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    logging.warning("lxml 未安装，将使用 ElementTree")

from .config import TranslationConfig

CONFIG = TranslationConfig()

class XMLProcessor:
    """统一的 XML 处理类，支持解析、提取、更新和保存"""

    def __init__(self, use_lxml: bool = True):
        self.use_lxml = use_lxml and LXML_AVAILABLE
        self.parser = etree.XMLParser(remove_comments=False) if self.use_lxml else None

    def parse_xml(self, file_path: str) -> Optional[Any]:
        """安全解析 XML 文件"""
        file_path = str(Path(file_path).resolve())
        if not os.path.exists(file_path):
            logging.error(f"文件不存在: {file_path}")
            return None
        if os.path.getsize(file_path) > 10 * 1024 * 1024:
            logging.warning(f"文件过大: {file_path}")
            return None
        try:
            if self.use_lxml:
                return etree.parse(file_path, self.parser)
            else:
                return ET.parse(file_path)
        except (etree.XMLSyntaxError, ET.ParseError) as e:
            logging.error(f"XML 解析失败: {file_path}: {e}")
            return None
        except Exception as e:
            logging.error(f"处理文件失败: {file_path}: {e}")
            return None

    def save_xml(self, tree: Any, file_path: str, pretty_print: bool = True) -> bool:
        """保存 XML 文件"""
        file_path = str(Path(file_path).resolve())
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        try:
            if self.use_lxml:
                tree.write(file_path, encoding="utf-8", xml_declaration=True, pretty_print=pretty_print)
            else:
                root = tree.getroot()
                new_tree = ET.ElementTree(root)
                with open(file_path, "wb") as f:
                    f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
                    new_tree.write(f, encoding="utf-8")
            logging.info(f"保存 XML 文件: {file_path}")
            return True
        except Exception as e:
            logging.error(f"保存 XML 失败: {file_path}: {e}")
            return False

    def extract_translations(self, tree: Any, context: str = "", filter_func: Optional[Callable] = None) -> List[Tuple[str, str, str]]:
        """提取可翻译内容"""
        translations = []
        root = tree.getroot() if self.use_lxml else tree
        for elem in root.iter() if not self.use_lxml else root.xpath(".//*"):
            if elem.text and elem.text.strip():
                key = elem.tag
                text = elem.text.strip()
                if filter_func and not filter_func(key, text, context):
                    continue
                translations.append((key, text, elem.tag))
        return translations

    def update_translations(self, tree: Any, translations: Dict[str, str], generate_key_func: Callable) -> bool:
        """更新 XML 中的翻译"""
        modified = False
        root = tree.getroot() if self.use_lxml else tree
        parent_map = {c: p for p in root.iter() for c in p} if not self.use_lxml else None
        for elem in root.iter() if not self.use_lxml else root.xpath(".//*"):
            if elem.text and elem.text.strip():
                key = generate_key_func(elem, root, parent_map)
                if key in translations:
                    elem.text = sanitize_xml(translations[key])
                    modified = True
        return modified

    def add_comments(self, tree: Any, comment_prefix: str = "EN") -> None:
        """为 XML 元素添加注释"""
        root = tree.getroot() if self.use_lxml else tree
        parent_map = {c: p for p in root.iter() for c in p} if not self.use_lxml else None
        for elem in root.iter() if not self.use_lxml else root.xpath(".//*"):
            if elem.text and elem.text.strip():
                original = elem.text.strip()
                comment = etree.Comment(sanitize_xcomment(f"{comment_prefix}: {original}")) if self.use_lxml else ET.Comment(sanitize_xcomment(f"{comment_prefix}: {original}"))
                parent = parent_map.get(elem) if not self.use_lxml else elem.getparent()
                if parent is not None:
                    idx = list(parent).index(elem)
                    parent.insert(idx, comment)

def sanitize_xml(text: str) -> str:
    """清理 XML 文本"""
    if not isinstance(text, str):
        return str(text)
    text = re.sub(r'[^\u0020-\uD7FF\uE000-\uFFFD]', '', text)
    text = text.replace('&', '&').replace('<', '<').replace('>', '>')
    return text

def sanitize_xcomment(text: str) -> str:
    """清理 XML 注释"""
    if not isinstance(text, str):
        return str(text)
    return re.sub(r'--+', '-', text)

def save_json(data: Dict, file_path: str) -> None:
    """保存 JSON 文件"""
    import json
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"保存 JSON 文件: {file_path}")
    except Exception as e:
        logging.error(f"保存 JSON 失败: {file_path}: {e}")

def get_language_folder_path(language: str, mod_dir: str) -> str:
    """获取语言文件夹路径"""
    return os.path.join(mod_dir, "Languages", language)

def update_history_list(key: str, value: str) -> None:
    """更新历史记录"""
    import json
    history_file = os.path.join(os.path.dirname(__file__), ".day_translation_history.json")
    try:
        history = get_history_list(key)
        if value in history:
            history.remove(value)
        history.insert(0, value)
        history = history[:10]
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump({key: history}, f, indent=2)
    except Exception as e:
        logging.error(f"更新历史记录失败: {e}")

def get_history_list(key: str) -> List[str]:
    """获取历史记录"""
    import json
    history_file = os.path.join(os.path.dirname(__file__), ".day_translation_history.json")
    try:
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(key, [])
    except Exception as e:
        logging.error(f"读取历史记录失败: {e}")
    return []

def handle_exceptions(default_return=None):
    """异常处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"错误在 {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator

def generate_element_key(elem: Any, root: Any, parent_map: Dict = None) -> str:
    """生成元素键"""
    key = elem.get("key") or elem.tag
    path_parts = []
    current = elem
    if parent_map:  # ElementTree
        while current is not None and current != root:
            if current.tag != "LanguageData":
                path_parts.append(current.tag)
            current = parent_map.get(current)
    else:  # lxml
        while current is not None and current != root:
            if current.tag != "LanguageData":
                path_parts.append(current.tag)
            current = current.getparent()
    path_parts.reverse()
    return ".".join(path_parts) if path_parts else key

def load_translations_from_csv(csv_path: str) -> Dict[str, str]:
    """从 CSV 加载翻译"""
    translations = {}
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("key", "").strip()
                translated = row.get("translated", row.get("text", "")).strip()
                if key and translated:
                    translations[key] = translated
    except Exception as e:
        logging.error(f"CSV 解析失败: {csv_path}: {e}")
    return translations

def save_xml_to_file(tree: Any, file_path: str, use_lxml: bool = LXML_AVAILABLE) -> bool:
    """兼容旧版保存 XML 文件"""
    processor = XMLProcessor(use_lxml=use_lxml)
    return processor.save_xml(tree, file_path)