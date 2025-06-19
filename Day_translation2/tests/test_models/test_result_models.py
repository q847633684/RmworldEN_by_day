"""
Day Translation 2 - 操作结果模型测试

测试OperationResult及相关枚举类的功能。
"""

import pytest

from ...models.result_models import (OperationResult, OperationStatus,
                                     OperationType)


class TestOperationStatus:
    """测试操作状态枚举"""

    def test_status_values(self):
        """测试状态值"""
        assert OperationStatus.SUCCESS.value == "success"
        assert OperationStatus.ERROR.value == "error"
        assert OperationStatus.WARNING.value == "warning"
        assert OperationStatus.CANCELLED.value == "cancelled"

    def test_status_comparison(self):
        """测试状态比较"""
        assert OperationStatus.SUCCESS != OperationStatus.ERROR
        assert OperationStatus.SUCCESS == OperationStatus.SUCCESS


class TestOperationType:
    """测试操作类型枚举"""

    def test_type_values(self):
        """测试类型值"""
        assert OperationType.EXTRACTION.value == "extraction"
        assert OperationType.TRANSLATION.value == "translation"
        assert OperationType.IMPORT.value == "import"
        assert OperationType.EXPORT.value == "export"
        assert OperationType.VALIDATION.value == "validation"


class TestOperationResult:
    """测试操作结果类"""

    def test_success_result_creation(self):
        """测试成功结果创建"""
        result = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="提取完成",
            processed_count=100,
            success_count=95,
        )

        assert result.status == OperationStatus.SUCCESS
        assert result.operation_type == OperationType.EXTRACTION
        assert result.message == "提取完成"
        assert result.processed_count == 100
        assert result.success_count == 95
        assert result.error_count == 0
        assert result.details == []
        assert result.execution_time is None

    def test_error_result_creation(self):
        """测试错误结果创建"""
        result = OperationResult(
            status=OperationStatus.ERROR,
            operation_type=OperationType.IMPORT,
            message="导入失败",
            error_count=5,
            details=["文件不存在", "格式错误"],
        )

        assert result.status == OperationStatus.ERROR
        assert result.operation_type == OperationType.IMPORT
        assert result.message == "导入失败"
        assert result.error_count == 5
        assert result.details == ["文件不存在", "格式错误"]

    def test_result_with_execution_time(self):
        """测试带执行时间的结果"""
        result = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.TRANSLATION,
            message="翻译完成",
            execution_time=2.5,
        )

        assert result.execution_time == 2.5

    def test_is_success_property(self):
        """测试成功判断属性"""
        success_result = OperationResult(
            status=OperationStatus.SUCCESS, operation_type=OperationType.EXTRACTION, message="成功"
        )
        assert success_result.is_success

        error_result = OperationResult(
            status=OperationStatus.ERROR, operation_type=OperationType.EXTRACTION, message="失败"
        )
        assert not error_result.is_success

    def test_has_warnings_property(self):
        """测试警告判断属性"""
        warning_result = OperationResult(
            status=OperationStatus.WARNING,
            operation_type=OperationType.VALIDATION,
            message="有警告",
        )
        assert warning_result.has_warnings

        success_result = OperationResult(
            status=OperationStatus.SUCCESS, operation_type=OperationType.VALIDATION, message="成功"
        )
        assert not success_result.has_warnings

    def test_success_rate_property(self):
        """测试成功率属性"""
        result = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="提取完成",
            processed_count=100,
            success_count=80,
        )
        assert result.success_rate == 0.8

        # 测试处理数量为0的情况
        empty_result = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="无数据",
            processed_count=0,
        )
        assert empty_result.success_rate == 0.0

    def test_str_representation(self):
        """测试字符串表示"""
        result = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="提取完成",
            processed_count=100,
            success_count=95,
        )

        str_repr = str(result)
        assert "提取完成" in str_repr
        assert "SUCCESS" in str_repr
        assert "95/100" in str_repr
