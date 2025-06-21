"""
Day Translation 2 - 异常类测试

测试所有自定义异常类的创建、继承和上下文信息。
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from models.exceptions import (
    ConfigurationError,
    ExportError,
    ImportError,
    ProcessingError,
    TranslationError,
    ValidationError,
)


class TestTranslationError:
    """测试基础异常类"""

    def test_basic_creation(self):
        """测试基本异常创建"""
        error = TranslationError("测试错误")
        assert str(error) == "测试错误"
        assert error.operation is None
        assert error.stage is None

    def test_with_context(self):
        """测试带上下文的异常创建"""
        error = TranslationError("处理失败", operation="test_operation", stage="validation")
        assert str(error) == "处理失败"
        assert error.operation == "test_operation"
        assert error.stage == "validation"

    def test_inheritance(self):
        """测试异常继承关系"""
        error = TranslationError("测试")
        assert isinstance(error, Exception)


class TestProcessingError:
    """测试处理错误异常"""

    def test_processing_error_creation(self):
        """测试处理错误创建"""
        error = ProcessingError(
            "文件处理失败",
            operation="file_processing",
            stage="reading",
            affected_items=["file1.xml", "file2.xml"],
        )
        assert "文件处理失败" in str(error)
        assert error.operation == "file_processing"
        assert error.stage == "reading"
        assert error.affected_items == ["file1.xml", "file2.xml"]

    def test_inheritance(self):
        """测试继承关系"""
        error = ProcessingError("测试")
        assert isinstance(error, TranslationError)


class TestValidationError:
    """测试验证错误异常"""

    def test_validation_error_creation(self):
        """测试验证错误创建"""
        error = ValidationError(
            "参数无效",
            field_name="input_path",
            expected_type="Path",
            actual_value="/invalid/path",
        )
        assert "参数无效" in str(error)
        assert error.field_name == "input_path"
        assert error.expected_type == "Path"
        assert error.actual_value == "/invalid/path"

    def test_inheritance(self):
        """测试继承关系"""
        error = ValidationError("测试")
        assert isinstance(error, TranslationError)


class TestImportError:
    """测试导入错误异常"""

    def test_import_error_creation(self):
        """测试导入错误创建"""
        error = ImportError("文件导入失败", file_path="/test/file.csv", line_number=10)
        assert "文件导入失败" in str(error)
        assert error.file_path == "/test/file.csv"
        assert error.line_number == 10

    def test_inheritance(self):
        """测试继承关系"""
        error = ImportError("测试")
        assert isinstance(error, TranslationError)


class TestExportError:
    """测试导出错误异常"""

    def test_export_error_creation(self):
        """测试导出错误创建"""
        error = ExportError("导出失败", output_path="/test/output.xml", format_type="XML")
        assert "导出失败" in str(error)
        assert error.output_path == "/test/output.xml"
        assert error.format_type == "XML"

    def test_inheritance(self):
        """测试继承关系"""
        error = ExportError("测试")
        assert isinstance(error, TranslationError)


class TestConfigurationError:
    """测试配置错误异常"""

    def test_configuration_error_creation(self):
        """测试配置错误创建"""
        error = ConfigurationError("配置无效", config_key="api.timeout", config_value="invalid")
        assert "配置无效" in str(error)
        assert error.config_key == "api.timeout"
        assert error.config_value == "invalid"

    def test_inheritance(self):
        """测试继承关系"""
        error = ConfigurationError("测试")
        assert isinstance(error, TranslationError)
