"""测试配置加载与验证"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_path_config_defaults():
    """PathConfig 默认值"""
    from user_config.core.user_config import PathConfig
    cfg = PathConfig()
    assert cfg.get_value("remember_paths", False) is True
    assert cfg.get_value("max_history_length", 0) == 10


def test_language_config_defaults():
    """LanguageConfig 默认值"""
    from user_config.core.user_config import LanguageConfig
    cfg = LanguageConfig()
    assert cfg.get_value("cn_language") == "ChineseSimplified"
    assert cfg.get_value("en_language") == "English"
