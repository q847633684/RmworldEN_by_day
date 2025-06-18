"""
Day Translation 2 - 基础功能测试

测试基本的模块导入和类定义。
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_basic_import():
    """测试基本模块导入"""
    # 测试异常模块
    from Day_translation2.models.exceptions import TranslationError, ConfigError
    
    # 验证异常类
    assert issubclass(TranslationError, Exception)
    assert issubclass(ConfigError, TranslationError)
    
    # 测试创建异常实例
    error = TranslationError("测试错误")
    assert str(error) == "测试错误"
    
    config_error = ConfigError("配置错误", config_path="/test/path")
    assert "配置错误" in str(config_error)
    
    print("✅ 异常模块导入和基本功能测试通过")


def test_result_models():
    """测试结果模型"""
    from Day_translation2.models.result_models import OperationResult, OperationStatus, OperationType
    
    # 测试枚举
    assert OperationStatus.SUCCESS
    assert OperationType.EXTRACTION
    
    # 测试创建操作结果
    result = OperationResult(
        status=OperationStatus.SUCCESS,
        operation_type=OperationType.EXTRACTION,
        message="测试成功"
    )
    
    assert result.status == OperationStatus.SUCCESS
    assert result.operation_type == OperationType.EXTRACTION
    assert result.message == "测试成功"
    
    print("✅ 结果模型测试通过")


def test_translation_data():
    """测试翻译数据模型"""
    from Day_translation2.models.translation_data import TranslationData, TranslationType
    
    # 测试枚举
    assert TranslationType.KEYED
    assert TranslationType.DEFINJECTED
    
    print("✅ 翻译数据模型测试通过")


if __name__ == "__main__":
    test_basic_import()
    test_result_models()
    test_translation_data()
    print("\n🎉 所有基础测试通过！Day_translation2核心模块正常工作")
