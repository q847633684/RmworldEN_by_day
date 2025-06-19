"""
Day Translation 2 - 测试配置和夹具

提供测试所需的公共配置、夹具和工具函数。
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

# 修复导入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from models.exceptions import ProcessingError, ValidationError
from models.result_models import (OperationResult, OperationStatus,
                                  OperationType)
from models.translation_data import TranslationData, TranslationType


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config():
    """提供测试用配置"""
    return {
        "extraction": {"include_keys": True, "include_definjected": True, "filter_empty": True},
        "translation": {"source_language": "en", "target_language": "zh", "api_timeout": 30},
        "validation": {
            "check_terminology": True,
            "check_length_ratio": True,
            "max_length_ratio": 3.0,
        },
    }


@pytest.fixture
def sample_translation_entry():
    """提供测试用翻译条目"""
    return TranslationData(
        key="TestKey.Sample",
        english_text="Hello World",
        chinese_text="你好世界",
        tag="UI",
        file_path="test.xml",
    )


@pytest.fixture
def sample_translation_data():
    """提供测试用翻译数据列表"""
    return [
        ("Keyed.Welcome", "Welcome to the game", "欢迎来到游戏"),
        ("Keyed.Start", "Start Game", "开始游戏"),
        ("Keyed.Settings", "Settings", "设置"),
        ("DefInjected.Thing.Name", "Item Name", "物品名称"),
        ("DefInjected.Thing.Description", "Item description", "物品描述"),
    ]


@pytest.fixture
def mock_xml_content():
    """提供测试用XML内容"""
    return """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
    <Welcome>Welcome to the game</Welcome>
    <Start>Start Game</Start>
    <Settings>Settings</Settings>
</LanguageData>"""


@pytest.fixture
def mock_csv_content():
    """提供测试用CSV内容"""
    return """key,text,translated
Keyed.Welcome,Welcome to the game,欢迎来到游戏
Keyed.Start,Start Game,开始游戏
Keyed.Settings,Settings,设置"""


# 测试辅助函数
def create_test_file(temp_dir: Path, filename: str, content: str) -> Path:
    """创建测试文件"""
    file_path = temp_dir / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def assert_operation_success(result: OperationResult, expected_message: str = None):
    """断言操作成功"""
    assert result.status == OperationStatus.SUCCESS
    if expected_message:
        assert expected_message in result.message


def assert_operation_error(result: OperationResult, expected_error: str = None):
    """断言操作失败"""
    assert result.status in [OperationStatus.ERROR, OperationStatus.WARNING]
    if expected_error:
        assert expected_error in result.message
