"""测试 utils.utils.sanitize_xml"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.utils import sanitize_xml


def test_sanitize_xml_escapes_special_chars():
    """测试转义 & < > " '"""
    assert sanitize_xml("a & b") == "a &amp; b"
    assert sanitize_xml("<tag>") == "&lt;tag&gt;"
    assert sanitize_xml('"quoted"') == "&quot;quoted&quot;"
    assert sanitize_xml("'apos'") == "&apos;apos&apos;"


def test_sanitize_xml_removes_control_chars():
    """测试去除 C0 控制符"""
    assert "\x00" not in sanitize_xml("a\x00b")
    assert "\x1f" not in sanitize_xml("a\x1fb")


def test_sanitize_xml_empty_and_none():
    """测试空输入"""
    assert sanitize_xml("") == ""
    assert sanitize_xml(123) == "123"


def test_sanitize_xml_normal_text_unchanged():
    """测试普通文本不变"""
    text = "Hello 世界 normal"
    assert sanitize_xml(text) == text
