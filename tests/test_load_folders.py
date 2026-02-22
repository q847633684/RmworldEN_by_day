"""测试 utils.load_folders"""
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import LOAD_FOLDERS_FILENAME
from utils.load_folders import get_load_folders_versions, get_version_dirs_from_fs


def test_get_load_folders_versions_no_file():
    """无 LoadFolders.xml 时返回空列表"""
    with tempfile.TemporaryDirectory() as d:
        assert get_load_folders_versions(d) == []


def test_get_load_folders_versions_empty_root():
    """LoadFolders.xml 根下无版本标签时返回空列表"""
    with tempfile.TemporaryDirectory() as d:
        xml_path = Path(d) / LOAD_FOLDERS_FILENAME
        root = ET.Element("LoadFolders")
        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        assert get_load_folders_versions(d) == []


def test_get_load_folders_versions_single_version():
    """单版本 v1.6"""
    with tempfile.TemporaryDirectory() as d:
        xml_path = Path(d) / LOAD_FOLDERS_FILENAME
        root = ET.Element("LoadFolders")
        v16 = ET.SubElement(root, "v1.6")
        ET.SubElement(v16, "li").text = "."
        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        assert get_load_folders_versions(d) == ["1.6"]


def test_get_load_folders_versions_multiple_versions():
    """多版本 v1.4、v1.5、v1.6，返回排序后列表"""
    with tempfile.TemporaryDirectory() as d:
        xml_path = Path(d) / LOAD_FOLDERS_FILENAME
        root = ET.Element("LoadFolders")
        for ver in ("v1.6", "v1.4", "v1.5"):
            ET.SubElement(root, ver)
        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        assert get_load_folders_versions(d) == ["1.4", "1.5", "1.6"]


def test_get_version_dirs_from_fs_not_dir():
    """非目录时返回空列表"""
    assert get_version_dirs_from_fs("/nonexistent/path/123") == []


def test_get_version_dirs_from_fs_empty_dir():
    """空目录返回空列表"""
    with tempfile.TemporaryDirectory() as d:
        assert get_version_dirs_from_fs(d) == []


def test_get_version_dirs_from_fs_version_dirs():
    """有 1.5、1.6 子目录时按版本降序返回"""
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "1.5").mkdir()
        (Path(d) / "1.6").mkdir()
        (Path(d) / "other").mkdir()  # 非版本号目录应被忽略
        result = get_version_dirs_from_fs(d)
        assert result == ["1.6", "1.5"]


def test_get_version_dirs_from_fs_v_prefix():
    """v1.5、v1.6 形式也能识别"""
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "v1.5").mkdir()
        (Path(d) / "v1.6").mkdir()
        result = get_version_dirs_from_fs(d)
        assert "v1.5" in result
        assert "v1.6" in result
        assert result[0] == "v1.6"  # 1.6 > 1.5
