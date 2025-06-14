import os
import xml.etree.ElementTree as ET
from typing import List
from ..utils.config import TranslationConfig

CONFIG = TranslationConfig()

def get_language_folder_path(language: str, root_dir: str) -> str:
    """获取语言文件夹路径"""
    return os.path.join(root_dir, "Languages", language)

def sanitize_xcomment(text: str) -> str:
    """清理 XML 注释内容"""
    return text.replace("--", "- -").replace("\n", " ").strip()

def save_xml_to_file(root: ET.Element, file_path: str) -> None:
    """保存 XML 到文件"""
    tree = ET.ElementTree(root)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
    except OSError as e:
        raise OSError(f"无法保存 XML 文件: {file_path}, 错误: {e}")

def update_history_list(key: str, value: str) -> None:
    """更新历史记录列表"""
    history_file = "history.txt"
    history: List[str] = []
    if os.path.exists(history_file):
        try:
            with open(history_file, encoding="utf-8") as f:
                history = [line.strip() for line in f if line.strip()]
        except OSError as e:
            print(f"无法读取历史文件: {e}")
    if value not in history:
        history.append(value)
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                f.write("\n".join(history) + "\n")
        except OSError as e:
            print(f"无法写入历史文件: {e}")