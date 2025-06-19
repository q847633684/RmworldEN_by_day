#!/usr/bin/env python3
"""
Day Translation 2 - 基本功能测试

测试核心模块的基本导入和初始化功能
"""

import os
import sys


def test_basic_imports():
    """测试基本导入功能"""
    try:
        # 测试核心模块导入 - 使用简单导入
        sys.path.insert(0, os.path.dirname(__file__))

        from core.exporters import DataExporter
        from core.extractors import DataExtractor
        from core.importers import DataImporter
        from core.translation_facade import TranslationFacade

        print("✅ 核心模块导入成功")

        # 测试模型导入
        from models.exceptions import TranslationError
        from models.translation_data import TranslationEntry

        print("✅ 模型模块导入成功")
        # 测试工具模块导入
        from utils.filter_rules import AdvancedFilterRules
        from utils.xml_processor import XMLProcessor

        print("✅ 工具模块导入成功")

        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_basic_functionality():
    """测试基本功能"""
    try:
        from core.extractors import DataExtractor
        from models.translation_data import TranslationEntry, TranslationType

        # 创建提取器实例
        extractor = DataExtractor()
        print("✅ 数据提取器创建成功")

        # 创建翻译条目
        entry = TranslationEntry(
            key="test_key",
            source_text="Test text",
            translation_type=TranslationType.KEYED,
            xml_tag="test",
            file_path="test.xml",
        )
        print(f"✅ 翻译条目创建成功: {entry.key}")

        return True

    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 Day Translation 2 - 基本功能测试")
    print("=" * 50)

    # 测试导入
    if not test_basic_imports():
        print("❌ 导入测试失败，停止测试")
        return False

    print()

    # 测试功能
    if not test_basic_functionality():
        print("❌ 功能测试失败")
        return False

    print()
    print("🎉 所有基本测试通过！Day_translation2 系统基本功能正常")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
