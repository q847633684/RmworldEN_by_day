"""
RimWorld 模组 About 相关工具

从 About/About.xml 读取模组名、packageId，以及模组名转安全路径等，供 batch、ui_style 等复用。
"""

import re
from pathlib import Path
from typing import Optional

from utils.xml_utils import local_tag

# 若仅在本模块解析 XML，可延迟 import 减少循环依赖
import xml.etree.ElementTree as ET


def get_mod_name_from_about(mod_dir: str) -> Optional[str]:
    """从 About/About.xml 读取 <name> 文本；支持带命名空间的 XML。"""
    about_path = Path(mod_dir) / "About" / "About.xml"
    if not about_path.is_file():
        return None
    try:
        tree = ET.parse(about_path)
        root = tree.getroot()
        for elem in root.iter():
            if local_tag(elem.tag) == "name" and elem.text:
                return elem.text.strip()
        name_elem = root.find("name")
        if name_elem is not None and name_elem.text:
            return name_elem.text.strip()
    except (ET.ParseError, OSError, PermissionError, AttributeError):
        pass
    return None


def get_package_id_from_about(mod_dir: str) -> Optional[str]:
    """从 About/About.xml 读取根级 <packageId> 文本（仅 root 的直接子元素）。"""
    about_path = Path(mod_dir) / "About" / "About.xml"
    if not about_path.is_file():
        return None
    try:
        tree = ET.parse(about_path)
        root = tree.getroot()
        for child in root:
            if local_tag(child.tag) == "packageId" and child.text:
                return child.text.strip()
    except (ET.ParseError, OSError, PermissionError, AttributeError):
        pass
    return None


def sanitize_mod_name_for_path(name: str, max_length: int = 64) -> str:
    """将模组名转为安全的目录名（替换非法字符）。"""
    s = re.sub(r'[\\/:*?"<>|]', "_", str(name).strip())
    return s[:max_length] if s else ""
