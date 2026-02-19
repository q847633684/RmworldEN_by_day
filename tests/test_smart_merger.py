"""测试 extract.utils.merger.SmartMerger"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from extract.utils import SmartMerger


def test_normalize_tuple_quad():
    """四元组补齐为五元组"""
    m = SmartMerger(
        [("k1", "t1", "tag", "path")],
        []
    )
    assert m.input_data[0] == ("k1", "t1", "tag", "path", "t1")


def test_normalize_tuple_penta():
    """五元组保持"""
    m = SmartMerger(
        [("k1", "t1", "tag", "path", "en1")],
        []
    )
    assert m.input_data[0] == ("k1", "t1", "tag", "path", "en1")


def test_smart_merge_empty_output():
    """输入有数据、输出为空 -> 全部新增"""
    inp = [("key1", "中文1", "tag", "p", "en1")]
    out = []
    merged, stats = SmartMerger.smart_merge_translations(inp, out)
    assert len(merged) == 1
    assert merged[0][0] == "key1"
    assert stats.get("new_count", 0) >= 1


def test_smart_merge_empty_input():
    """输入为空时，输出优先策略保留输出数据"""
    inp = []
    out = [("key1", "old", "tag", "p", "en1", "")]
    merged, stats = SmartMerger.smart_merge_translations(inp, out)
    # output_priority 下输出数据会被保留
    assert len(merged) == 1
    assert merged[0][0] == "key1"
