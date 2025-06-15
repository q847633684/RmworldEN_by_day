import os
import json
from typing import List, Dict
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path

def get_language_folder_path(language: str, root_dir: str) -> str:
    """获取语言文件夹路径"""
    return os.path.join(root_dir, "Languages", language)

def sanitize_xcomment(comment: str) -> str:
    """清理 XML 注释内容，移除无效字符"""
    if not comment:
        return ""
    return comment.replace("--", "-").strip()

def save_xml_to_file(root: ET.Element, file_path: str, pretty_print: bool = True) -> None:
    """保存 XML 到文件，支持格式化输出"""
    try:
        tree = ET.ElementTree(root)
        if pretty_print:
            # 使用 minidom 进行格式化
            xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent="  ")
            # 移除 <?xml ...?> 声明（如果需要）
            xml_str = '\n'.join(line for line in xml_str.split('\n') if not line.startswith('<?xml'))
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(xml_str)
        else:
            tree.write(file_path, encoding="utf-8", xml_declaration=False)
    except (OSError, ET.ParseError) as e:
        print(f"无法保存 XML 文件 {file_path}: {e}")
        raise

def update_history_list(key: str, value: str) -> None:
    """更新历史记录列表"""
    history_file = "history.json"
    history: Dict[str, List[str]] = {}
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = {}
    history_list = history.get(key, [])
    if value not in history_list:
        history_list.append(value)
        history[key] = history_list[-10:]  # 保留最后 10 条记录
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"无法更新历史记录: {e}")