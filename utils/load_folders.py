"""
LoadFolders 与版本检测工具
从 extract.workflow.manager 抽离，供 user_config、batch、extract 等无循环依赖地调用
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from .constants import LOAD_FOLDERS_FILENAME


def get_load_folders_versions(mod_dir: str) -> List[str]:
    """
    从 LoadFolders.xml 读取所有版本标签（如 <v1.4>、<v1.6>），返回标准化版本名列表 ['1.4', '1.6']。
    无文件或解析失败返回 []。
    """
    xml_path = Path(mod_dir) / LOAD_FOLDERS_FILENAME
    if not xml_path.is_file():
        return []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        versions = []
        for child in root:
            tag = (child.tag or "").strip()
            if tag.startswith("v") and len(tag) > 1:
                ver = tag[1:].strip()
                if re.match(r"^(\d+\.)+\d+$", ver):
                    versions.append(ver)
        return sorted(versions)
    except (ET.ParseError, OSError, IOError):
        return []


def get_version_dirs_from_fs(scan_base: str) -> List[str]:
    """
    扫描模组根下符合版本号形式的子目录名（如 1.6、v1.6、1.5），返回按版本降序的列表。
    用于无 LoadFolders.xml 时根据目录结构选择版本。
    """
    from .version_utils import is_version_number, parse_version_number

    base = Path(scan_base)
    if not base.is_dir():
        return []
    found = [
        p.name
        for p in base.iterdir()
        if p.is_dir() and is_version_number(p.name)
    ]
    return sorted(found, key=parse_version_number, reverse=True)
