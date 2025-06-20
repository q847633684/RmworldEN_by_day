#!/usr/bin/env python3
"""
Day汉化项目 - 组件功能测试

测试项目主要组件的功能是否正常工作。
"""

import sys
from pathlib import Path


def test_component_functionality():
    """测试组件功能"""
    print("🔍 开始组件功能测试...")
    # 添加Day_translation2到Python路径
    day_translation2_path = Path(__file__).parent / "Day_translation2"
    if str(day_translation2_path) not in sys.path:
        sys.path.insert(0, str(day_translation2_path))
    test_results = []
    # 测试1: XML处理器
    try:
        from utils.xml_processor import AdvancedXMLProcessor

        processor = AdvancedXMLProcessor()
        assert processor is not None
        test_results.append(("XML处理器", True, ""))
        print("  ✅ XML处理器正常")
    except Exception as e:
        test_results.append(("XML处理器", False, str(e)))
        print(f"  ❌ XML处理器: {e}")
    # 测试2: 翻译数据模型
    try:
        from models.translation_data import TranslationData, TranslationType

        data = TranslationData(key="test.key", text="Test text")
        assert data.key == "test.key"
        test_results.append(("翻译数据模型", True, ""))
        print("  ✅ 翻译数据模型正常")
    except Exception as e:
        test_results.append(("翻译数据模型", False, str(e)))
        print(f"  ❌ 翻译数据模型: {e}")
    # 测试3: 结果模型
    try:
        from models.result_models import OperationResult, OperationStatus, OperationType

        result = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="测试成功",
        )
        assert result.is_success
        test_results.append(("结果模型", True, ""))
        print("  ✅ 结果模型正常")
    except Exception as e:
        test_results.append(("结果模型", False, str(e)))
        print(f"  ❌ 结果模型: {e}")

    # 测试4: 验证服务
    try:
        from services.validation_service import TranslationValidator

        validator = TranslationValidator()
        assert validator is not None
        test_results.append(("验证服务", True, ""))
        print("  ✅ 验证服务正常")
    except Exception as e:
        test_results.append(("验证服务", False, str(e)))
        print(f"  ❌ 验证服务: {e}")

    # 输出测试结果
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    success_rate = passed / total * 100

    print("\n📊 组件功能测试结果:")
    print(f"  通过: {passed}/{total} ({success_rate:.1f}%)")

    if passed == total:
        print("\n🎉 所有组件功能测试通过！")
        return True
    else:
        print("\n⚠️ 部分组件功能测试失败")
        for name, success, error in test_results:
            if not success:
                print(f"  - {name}: {error}")
        return False


if __name__ == "__main__":
    try:
        success = test_component_functionality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        sys.exit(1)
