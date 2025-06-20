#!/usr/bin/env python3
"""
Day Translation 2 - 主流程测试脚本

快速验证核心系统是否能成功运行
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加当前目录到sys.path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))


def test_core_imports():
    """测试核心模块导入"""
    print("🔍 测试核心模块导入...")

    try:
        from config import get_config

        print("✅ 配置模块导入成功")
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False

    try:
        from core.translation_facade import TranslationFacade

        print("✅ 翻译门面导入成功")
    except Exception as e:
        print(f"❌ 翻译门面导入失败: {e}")
        return False

    try:
        from core.exporters import AdvancedExporter

        print("✅ 导出器导入成功")
    except Exception as e:
        print(f"❌ 导出器导入失败: {e}")
        return False

    try:
        from core.extractors import AdvancedExtractor

        print("✅ 提取器导入成功")
    except Exception as e:
        print(f"❌ 提取器导入失败: {e}")
        return False

    return True


def test_basic_functionality():
    """测试基本功能"""
    print("\n🚀 测试基本功能...")

    try:
        from config import get_config

        config = get_config()
        print(f"✅ 配置获取成功: {config.core.default_language}")
    except Exception as e:
        print(f"❌ 配置获取失败: {e}")
        return False

    try:
        from models.translation_data import TranslationData, TranslationType

        # 创建测试翻译数据
        test_data = TranslationData(
            key="test.key",
            original_text="Hello World",
            translated_text="你好世界",
            translation_type=TranslationType.KEYED,
            file_path="test.xml",
        )
        print(f"✅ 翻译数据模型创建成功: {test_data.key}")
    except Exception as e:
        print(f"❌ 翻译数据模型测试失败: {e}")
        return False

    return True


def test_facade_initialization():
    """测试门面初始化"""
    print("\n🏗️ 测试翻译门面初始化...")

    try:
        from core.translation_facade import TranslationFacade

        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建模拟的模组目录结构
            mod_dir = Path(temp_dir) / "TestMod"
            mod_dir.mkdir()
            (mod_dir / "Languages").mkdir()
            (mod_dir / "Languages" / "ChineseSimplified").mkdir()
            (mod_dir / "Languages" / "ChineseSimplified" / "Keyed").mkdir()

            # 测试门面初始化
            facade = TranslationFacade(str(mod_dir))
            print(f"✅ 翻译门面初始化成功: {facade.mod_dir}")

            return True

    except Exception as e:
        print(f"❌ 翻译门面初始化失败: {e}")
        return False


def test_exporter_functionality():
    """测试导出器功能"""
    print("\n📤 测试导出器功能...")

    try:
        from core.exporters import AdvancedExporter
        from models.translation_data import TranslationData, TranslationType

        # 创建导出器
        exporter = AdvancedExporter()
        print("✅ 导出器创建成功")
        # 创建测试数据
        test_translations = [
            TranslationData(
                key="test.key1",
                original_text="Hello",
                translated_text="你好",
                translation_type=TranslationType.KEYED,
                file_path="test.xml",
            ),
            TranslationData(
                key="test.key2",
                original_text="World",
                translated_text="世界",
                translation_type=TranslationType.KEYED,
                file_path="test.xml",
            ),
        ]

        # 测试统计功能
        stats = exporter.get_export_statistics(test_translations)
        print(f"✅ 导出统计成功: {stats['total_translations']} 条翻译")

        return True

    except Exception as e:
        print(f"❌ 导出器功能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🎯 Day Translation 2 - 主流程测试")
    print("=" * 50)

    all_tests = [
        test_core_imports,
        test_basic_functionality,
        test_facade_initialization,
        test_exporter_functionality,
    ]

    passed = 0
    total = len(all_tests)

    for test_func in all_tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 发生异常: {e}")

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有核心功能测试通过！Day_translation2 系统运行正常")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())
