"""测试 utils.utils.sanitize_xml"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.utils import sanitize_xml, normalize_xml_entities_in_text


def test_sanitize_xml_preserves_rulepack_syntax():
    """测试保留 RulePack 语法（如 memeAdjective->吞食的），避免双重转义"""
    # 包含 -> 的 RimWorld RulePack 语法应原样保留
    assert sanitize_xml("memeAdjective->吞食的") == "memeAdjective->吞食的"
    assert sanitize_xml("monster->terror") == "monster->terror"


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


def test_sanitize_xml_preserves_xml_special_chars():
    """测试不预转义 & < > \" '，由 XML 库在 write 时处理，避免双重编码"""
    assert sanitize_xml("a & b") == "a & b"
    assert sanitize_xml("<tag>") == "<tag>"
    assert sanitize_xml('"quoted"') == '"quoted"'


def test_normalize_xml_entities_in_text():
    """读取时把 &gt; 等实体还原，&amp;gt; 解析后得到的字面量 &gt; 会变为 >"""
    assert normalize_xml_entities_in_text("memeAdjective-&gt;吞食的") == "memeAdjective->吞食的"
    assert normalize_xml_entities_in_text("a &amp; b") == "a & b"
    assert normalize_xml_entities_in_text("&lt;tag&gt;") == "<tag>"
