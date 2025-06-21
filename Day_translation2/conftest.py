"""
pytest配置文件 - Day汉化项目测试框架

不考虑向后兼容，全面现代化的测试框架
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """pytest配置"""
    # 设置测试环境变量
    os.environ["DAY_TRANSLATION_TEST_MODE"] = "1"
    os.environ["DAY_TRANSLATION_LOG_LEVEL"] = "DEBUG"

    # 注册自定义标记
    config.addinivalue_line("markers", "unit: 单元测试标记")
    config.addinivalue_line("markers", "integration: 集成测试标记")
    config.addinivalue_line("markers", "service: 服务层测试标记")
    config.addinivalue_line("markers", "config: 配置模块测试标记")
    config.addinivalue_line("markers", "slow: 耗时测试标记")


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def temp_config_dir(tmp_path_factory):
    """临时配置目录"""
    return tmp_path_factory.mktemp("config")


@pytest.fixture
def mock_config_data() -> Dict[str, Any]:
    """模拟配置数据"""
    return {
        "version": "2.0.0",
        "core": {
            "version": "2.0.0",
            "default_language": "zh_CN",
            "source_language": "en",
            "debug_mode": True,
            "log_file": "test.log",
            "log_format": "%(asctime)s - %(levelname)s - %(message)s",
            "max_workers": 4,
            "chunk_size": 1000,
        },
        "user": {
            "extraction": {
                "extract_comments": True,
                "extract_descriptions": True,
                "exclude_patterns": [],
            },
            "general": {
                "auto_mode": False,
                "remember_paths": True,
                "confirm_operations": True,
                "max_history_items": 10,
            },
            "api": {
                "baidu_app_id": "",
                "baidu_secret_key": "",
                "aliyun_access_key_id": "",
                "aliyun_access_key_secret": "",
            },
            "remembered_paths": {},
            "path_history": {},
        },
    }


@pytest.fixture
def clean_services():
    """清理服务层状态"""
    yield
    # 测试后清理
    # 这里可以添加服务层的清理逻辑


# 性能测试配置 - 需要pytest-benchmark插件
# def pytest_benchmark_update_json(config, benchmarks, output_json):
#     """更新基准测试结果"""
#     output_json["project"] = "Day汉化项目"
#     output_json["version"] = "2.0.0"


# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 自动添加标记
        if "test_services" in str(item.fspath):
            item.add_marker(pytest.mark.service)
        elif "test_config" in str(item.fspath):
            item.add_marker(pytest.mark.config)
        elif "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


# 跳过条件 - 自定义钩子
# def pytest_configure_node(node):
#     """配置测试节点"""
#     # 可以根据环境动态跳过某些测试
#     pass
