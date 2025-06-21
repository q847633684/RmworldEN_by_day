"""
Day Translation 2 - 现代化数据模型测试

测试核心数据模型的功能和一致性。
"""

import pytest
from models.exceptions import ProcessingError, ValidationError, TranslationError
from models.result_models import OperationResult, OperationStatus, OperationType
from models.translation_data import TranslationData, TranslationType


@pytest.mark.models
class TestOperationResult:
    """测试操作结果模型"""

    def test_success_result_creation(self):
        """测试成功结果创建"""
        result = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="操作成功",
        )

        assert result.status == OperationStatus.SUCCESS
        assert result.operation_type == OperationType.EXTRACTION
        assert result.message == "操作成功"
        assert result.is_success
        assert not result.has_warnings
        assert isinstance(result.details, dict)

    def test_error_result_creation(self):
        """测试错误结果创建"""
        result = OperationResult(
            status=OperationStatus.ERROR,
            operation_type=OperationType.VALIDATION,
            message="操作失败",
            errors=["错误1", "错误2"],
        )

        assert result.status == OperationStatus.ERROR
        assert not result.is_success
        assert len(result.errors) == 2

    def test_warning_result_creation(self):
        """测试警告结果创建"""
        result = OperationResult(
            status=OperationStatus.WARNING,
            operation_type=OperationType.EXPORT,
            message="有警告",
            warnings=["警告1"],
        )

        assert result.status == OperationStatus.WARNING
        assert result.has_warnings
        assert len(result.warnings) == 1


@pytest.mark.models
class TestTranslationData:
    """测试翻译数据模型"""

    def test_translation_data_creation(self):
        """测试翻译数据创建"""
        data = TranslationData(
            key="test.key",
            original_text="Hello World",
            translated_text="你好世界",
            tag="UI",
            file_path="test.xml",
        )

        assert data.key == "test.key"
        assert data.original_text == "Hello World"
        assert data.translated_text == "你好世界"
        assert data.tag == "UI"
        assert data.file_path == "test.xml"
        assert data.tag == "UI"
        assert data.file_path == "test.xml"

    def test_translation_data_validation(self):
        """测试翻译数据验证"""
        # 正常数据应该验证成功
        data = TranslationData(
            key="valid.key",
            original_text="Valid text",
            translated_text="有效文本",
            tag="test",
            file_path="test.xml",
        )

        # 基本验证：key不能为空
        assert data.key.strip() != ""
        assert data.original_text.strip() != ""
        assert data.translated_text.strip() != ""

    def test_translation_data_type_enum(self):
        """测试翻译类型枚举"""
        assert TranslationType.KEYED.value == "keyed"
        assert TranslationType.DEFINJECTED.value == "definjected"
        assert TranslationType.BACKSTORY.value == "backstory"


@pytest.mark.models
class TestExceptions:
    """测试异常模型"""

    def test_translation_error(self):
        """测试翻译错误"""
        error = TranslationError("翻译出错", context={"key": "test.key"})
        assert "翻译出错" in str(error)
        assert "key=test.key" in str(error)
        assert error.context["key"] == "test.key"

    def test_processing_error(self):
        """测试处理错误"""
        error = ProcessingError("处理失败", stage="validation")
        assert "处理失败" in str(error)
        assert "stage=validation" in str(error)
        assert error.stage == "validation"

    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError("验证失败", field="chinese_text")

        # 验证错误消息包含基本信息和上下文
        assert "验证失败" in str(error)
        assert error.field == "chinese_text"

    def test_exception_inheritance(self):
        """测试异常继承关系"""
        translation_error = TranslationError("test")
        processing_error = ProcessingError("test")
        validation_error = ValidationError("test")

        assert isinstance(translation_error, Exception)
        assert isinstance(processing_error, TranslationError)
        assert isinstance(validation_error, ProcessingError)


@pytest.mark.models
class TestModelConsistency:
    """测试模型一致性"""

    def test_operation_status_values(self):
        """测试操作状态值"""
        assert OperationStatus.SUCCESS.value == "success"
        assert OperationStatus.ERROR.value == "error"
        assert OperationStatus.WARNING.value == "warning"
        assert OperationStatus.PENDING.value == "pending"

    def test_operation_type_values(self):
        """测试操作类型值"""
        assert OperationType.EXTRACTION.value == "extraction"
        assert OperationType.IMPORT.value == "import"
        assert OperationType.EXPORT.value == "export"
        assert OperationType.VALIDATION.value == "validation"
