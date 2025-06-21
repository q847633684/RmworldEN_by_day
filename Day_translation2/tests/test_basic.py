"""
Day Translation 2 - 基础功能测试

测试核心模块的基础导入和初始化功能。
"""

import pytest


class TestBasicImports:
    """测试基础模块导入"""

    def test_core_modules_import(self):
        """测试核心模块导入"""
        try:
            from core import extractors, generators, importers, translation_facade
            from core.exporters import advanced_exporter, csv_exporter

            assert True  # 如果能导入就算成功
        except ImportError as e:
            pytest.fail(f"核心模块导入失败: {e}")

    def test_models_import(self):
        """测试数据模型导入"""
        try:
            from models import exceptions, result_models, translation_data

            assert True
        except ImportError as e:
            pytest.fail(f"数据模型导入失败: {e}")

    def test_services_import(self):
        """测试服务层导入"""
        try:
            from services import config_service, path_service, validation_service

            assert True
        except ImportError as e:
            pytest.fail(f"服务层导入失败: {e}")

    def test_config_system_import(self):
        """测试配置系统导入"""
        try:
            from config import config_manager
            from config.data_models import UnifiedConfig

            assert True
        except ImportError as e:
            pytest.fail(f"配置系统导入失败: {e}")


class TestBasicFunctionality:
    """测试基础功能"""

    def test_config_service_available(self):
        """测试配置服务可用性"""
        from services.config_service import config_service

        assert config_service is not None
        assert hasattr(config_service, "get_unified_config")

    def test_create_operation_result(self):
        """测试创建操作结果"""
        from models.result_models import OperationResult, OperationStatus, OperationType

        result = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="测试成功",
        )

        assert result.status == OperationStatus.SUCCESS
        assert result.operation_type == OperationType.EXTRACTION
        assert result.message == "测试成功"
        assert result.is_success

    def test_translation_data_creation(self):
        """测试翻译数据创建"""
        from models.translation_data import TranslationData

        data = TranslationData(
            key="test.key",
            original_text="Hello",
            translated_text="你好",
            tag="test",
            file_path="test.xml",
        )

        assert data.key == "test.key"
        assert data.original_text == "Hello"
        assert data.translated_text == "你好"
        assert data.tag == "test"
        assert data.file_path == "test.xml"
