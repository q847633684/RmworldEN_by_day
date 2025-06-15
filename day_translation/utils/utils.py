import xml.etree.ElementTree as ET
import os
import json
from pathlib import Path
from typing import Dict, List
import logging
import re

def get_language_folder_path(language: str, mod_dir: str) -> str:
    """获取语言文件夹路径"""
    return os.path.join(mod_dir, "Languages", language)

def sanitize_xcomment(text: str) -> str:
    """清理 XML 注释文本"""
    return re.sub(r"-->|--", "-", text.strip())

def sanitize_xml(text: str) -> str:
    """清理 XML 内容，转义特殊字符"""
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("&", "&amp;")  # 必须先转义 &
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    # 移除控制字符
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
    return text

def save_xml_to_file(root: ET.Element, file_path: str, pretty_print: bool = True) -> None:
    """保存 XML 到文件"""
    tree = ET.ElementTree(root)
    if pretty_print:
        ET.indent(root, space="  ")  # Python 3.9+
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        logging.info(f"保存 XML 文件: {file_path}")
    except OSError as e:
        logging.error(f"无法保存 XML 文件 {file_path}: {e}")

def update_history_list(key: str, value: str) -> None:
    """更新历史记录列表"""
    history_file = os.path.join(os.path.expanduser("~"), ".day_translation_history.json")
    history: Dict[str, List[str]] = {}
    
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"历史文件读取失败: {e}")
            history = {}
    
    history_list = history.get(key, [])
    if not isinstance(history_list, list):
        history_list = []
    
    # 移除重复项并添加到开头
    if value in history_list:
        history_list.remove(value)
    history_list.insert(0, value)
    
    # 保留最后 10 条记录
    history[key] = history_list[:10]
    
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logging.warning(f"无法更新历史记录: {e}")

def get_history_list(key: str) -> List[str]:
    """获取历史记录列表"""
    history_file = os.path.join(os.path.expanduser("~"), ".day_translation_history.json")
    
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            history_list = history.get(key, [])
            if isinstance(history_list, list):
                return history_list
        except (json.JSONDecodeError, OSError):
            pass
    
    return []