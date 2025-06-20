#!/usr/bin/env python3
"""
Day汉化项目 - 基础功能测试

测试项目核心功能是否正常工作。
"""

import sys
import os
from pathlib import Path


def test_basic_functionality():
    """测试基础功能"""
    print("🔍 开始基础功能测试...")

    # 添加Day_translation2到Python路径
    day_translation2_path = Path(__file__).parent / "Day_translation2"
    if str(day_translation2_path) not in sys.path:
        sys.path.insert(0, str(day_translation2_path))

    test_results = []

    # 测试1: 配置系统
    try:
        from config import get_config

        config = get_config()
        assert config is not None
        test_results.append(("配置系统", True, ""))
        print("  ✅ 配置系统正常")
    except Exception as e:
        test_results.append(("配置系统", False, str(e)))
        print(f"  ❌ 配置系统: {e}")

    # 测试2: 过滤规则
    try:
        from utils.filter_rules import AdvancedFilterRules

        filter_rules = AdvancedFilterRules()
        assert filter_rules.should_translate_field("label", "Test text")
        test_results.append(("过滤规则", True, ""))
        print("  ✅ 过滤规则正常")
    except Exception as e:
        test_results.append(("过滤规则", False, str(e)))
        print(f"  ❌ 过滤规则: {e}")

    # 测试3: 文件工具
    try:
        from utils.file_utils import validate_mod_directory

        # 测试当前目录
        result = validate_mod_directory(str(day_translation2_path))
        test_results.append(("文件工具", True, ""))
        print("  ✅ 文件工具正常")
    except Exception as e:
        test_results.append(("文件工具", False, str(e)))
        print(f"  ❌ 文件工具: {e}")

    # 测试4: 异常处理
    try:
        from models.exceptions import TranslationError, ValidationError

        error = TranslationError("测试错误")
        assert str(error) == "测试错误"
        test_results.append(("异常处理", True, ""))
        print("  ✅ 异常处理正常")
    except Exception as e:
        test_results.append(("异常处理", False, str(e)))
        print(f"  ❌ 异常处理: {e}")

    # 输出测试结果
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    success_rate = passed / total * 100

    print("\n📊 基础功能测试结果:")
    print(f"  通过: {passed}/{total} ({success_rate:.1f}%)")

    if passed == total:
        print("\n🎉 所有基础功能测试通过！")
        return True
    else:
        print("\n⚠️ 部分基础功能测试失败")
        for name, success, error in test_results:
            if not success:
                print(f"  - {name}: {error}")
        return False


if __name__ == "__main__":
    try:
        success = test_basic_functionality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        sys.exit(1)
