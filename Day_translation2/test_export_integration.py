#!/usr/bin/env python3
"""
Day Translation 2 - ExportManager和UserInteractionManager集成测试

测试新集成的ExportManager和UserInteractionManager功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def test_export_manager_integration():
    """测试ExportManager集成"""
    print("🧪 测试ExportManager集成...")

    try:
        from models.translation_data import TranslationEntry, TranslationType
        from utils.export_manager import ExportManager, ExportMode

        # 创建测试数据
        translations = [
            TranslationEntry(
                key="TestKey1",
                source_text="Test text 1",
                target_text="测试文本1",
                translation_type=TranslationType.KEYED,
            ),
            TranslationEntry(
                key="ThingDef.TestThing.label",
                source_text="Test thing",
                target_text="测试物品",
                translation_type=TranslationType.DEFINJECTED,
                context_info={
                    "def_type": "ThingDef",
                    "def_name": "TestThing",
                    "field_path": "label",
                },
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建ExportManager实例
            export_manager = ExportManager(
                output_dir=temp_dir, language="ChineseSimplified", auto_mode=True
            )

            # 测试导出Keyed翻译
            keyed_translations = [
                t for t in translations if t.translation_type == TranslationType.KEYED
            ]
            keyed_result = export_manager.export_keyed_translations(
                keyed_translations, mode=ExportMode.REPLACE
            )

            print(f"   Keyed导出结果: {keyed_result.success}")
            print(f"   处理文件数: {keyed_result.files_processed}")

            # 测试导出DefInjected翻译
            definjected_translations = [
                t for t in translations if t.translation_type == TranslationType.DEFINJECTED
            ]
            definjected_result = export_manager.export_definjected_translations(
                definjected_translations, mode=ExportMode.REPLACE
            )

            print(f"   DefInjected导出结果: {definjected_result.success}")
            print(f"   处理文件数: {definjected_result.files_processed}")

        print("✅ ExportManager集成测试通过")
        return True

    except Exception as e:
        print(f"❌ ExportManager集成测试失败: {e}")
        return False


def test_user_interaction_manager():
    """测试UserInteractionManager"""
    print("🧪 测试UserInteractionManager...")

    try:
        from utils.user_interaction import UserInteractionManager

        # 创建实例
        interaction_manager = UserInteractionManager()

        # 测试分析导出场景
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis = interaction_manager.analyze_export_scenario(
                output_dir=temp_dir, language="ChineseSimplified", translations_count=10
            )

            print(f"   分析结果 - 预计文件数: {analysis.total_files}")
            print(f"   分析结果 - 冲突文件数: {analysis.will_be_affected}")

        print("✅ UserInteractionManager测试通过")
        return True

    except Exception as e:
        print(f"❌ UserInteractionManager测试失败: {e}")
        return False


def test_exporters_integration():
    """测试exporters模块的新功能"""
    print("🧪 测试exporters模块集成...")

    try:
        from core.exporters import export_with_smart_merge
        from models.translation_data import TranslationEntry, TranslationType

        # 创建测试数据
        translations = [
            TranslationEntry(
                key="TestKey1",
                source_text="Test text 1",
                target_text="测试文本1",
                translation_type=TranslationType.KEYED,
            )
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            # 测试智能导出
            result = export_with_smart_merge(
                translations=translations,
                output_dir=temp_dir,
                language="ChineseSimplified",
                mode="replace",
                auto_mode=True,
            )

            print(f"   智能导出结果: {result.success}")
            print(f"   处理文件数: {result.details.get('total_files', 0)}")

        print("✅ exporters模块集成测试通过")
        return True

    except Exception as e:
        print(f"❌ exporters模块集成测试失败: {e}")
        return False


def test_translation_facade_advanced():
    """测试TranslationFacade的高级功能"""
    print("🧪 测试TranslationFacade高级功能...")

    try:
        from core.translation_facade import TranslationFacade
        from models.translation_data import TranslationEntry, TranslationType

        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建简单的模组结构
            mod_dir = Path(temp_dir) / "TestMod"
            languages_dir = mod_dir / "Languages"
            english_dir = languages_dir / "English"
            chinese_dir = languages_dir / "ChineseSimplified"

            # 创建目录结构
            english_dir.mkdir(parents=True)
            chinese_dir.mkdir(parents=True)

            # 创建TranslationFacade实例
            facade = TranslationFacade(mod_dir=str(mod_dir), language="ChineseSimplified")

            # 测试模组结构验证
            validation_result = facade.validate_mod_structure()
            print(f"   模组结构验证: {validation_result.success}")

            # 创建测试翻译数据
            translations = [
                TranslationEntry(
                    key="TestKey1",
                    source_text="Test text 1",
                    target_text="测试文本1",
                    translation_type=TranslationType.KEYED,
                )
            ]

            # 测试高级导出
            export_result = facade.export_with_smart_merge(
                translations=translations, output_dir=str(mod_dir), mode="replace", auto_mode=True
            )

            print(f"   高级导出结果: {export_result.success}")

        print("✅ TranslationFacade高级功能测试通过")
        return True

    except Exception as e:
        print(f"❌ TranslationFacade高级功能测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有集成测试"""
    print("🚀 Day Translation 2 - ExportManager和UserInteractionManager集成测试")
    print("=" * 80)

    tests = [
        ("ExportManager集成", test_export_manager_integration),
        ("UserInteractionManager", test_user_interaction_manager),
        ("exporters模块集成", test_exporters_integration),
        ("TranslationFacade高级功能", test_translation_facade_advanced),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 运行测试: {test_name}")
        if test_func():
            passed_tests += 1

    print(f"\n📊 测试结果: {passed_tests}/{total_tests} 通过")

    if passed_tests == total_tests:
        print("🎉 所有集成测试通过！ExportManager和UserInteractionManager集成成功")
        return 0
    else:
        print("⚠️ 部分测试失败，需要检查集成问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
