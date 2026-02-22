"""测试 extract.batch_extract"""
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from extract.batch_extract import scan_vanilla_mods


def _make_about_xml(mod_dir: Path, name: str) -> None:
    """在 mod_dir/About/About.xml 写入 <name>"""
    about_dir = mod_dir / "About"
    about_dir.mkdir(parents=True, exist_ok=True)
    root = ET.Element("ModMetaData")
    ET.SubElement(root, "name").text = name
    tree = ET.ElementTree(root)
    tree.write(about_dir / "About.xml", encoding="utf-8", xml_declaration=True)


def test_scan_vanilla_mods_not_dir():
    """非目录时返回空列表"""
    assert scan_vanilla_mods("/nonexistent/workshop/path") == []


def test_scan_vanilla_mods_empty_workshop():
    """空 workshop 返回空列表"""
    with tempfile.TemporaryDirectory() as d:
        assert scan_vanilla_mods(d) == []


def test_scan_vanilla_mods_vanilla_prefix():
    """只返回名字以 Vanilla 开头的模组"""
    with tempfile.TemporaryDirectory() as workshop:
        wp = Path(workshop)
        # Vanilla 前缀模组
        (wp / "mod1").mkdir()
        _make_about_xml(wp / "mod1", "Vanilla Expanded - Core")
        # 非 Vanilla 前缀
        (wp / "mod2").mkdir()
        _make_about_xml(wp / "mod2", "HugsLib")
        # 无 About
        (wp / "mod3").mkdir()

        result = scan_vanilla_mods(workshop)
        assert len(result) == 1
        assert result[0][1] == "Vanilla Expanded - Core"
        assert "mod1" in result[0][0]


def test_scan_vanilla_mods_vanilla_whitespace():
    """名字前后空格经 strip 后仍能匹配 Vanilla 前缀"""
    with tempfile.TemporaryDirectory() as workshop:
        wp = Path(workshop)
        (wp / "mod1").mkdir()
        _make_about_xml(wp / "mod1", "  Vanilla Textures  ")

        result = scan_vanilla_mods(workshop)
        assert len(result) == 1
        assert result[0][1].strip().startswith("Vanilla")
