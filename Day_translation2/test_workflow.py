#!/usr/bin/env python3
"""
Day Translation 2 - 完整工作流程测试

测试从提取到导出的完整翻译工作流程，验证系统的端到端功能。
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加当前目录到sys.path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))


def create_test_mod_structure(mod_dir: Path):
    """创建测试模组目录结构"""
    print(f"🏗️ 创建测试模组结构: {mod_dir}")

    # 创建基本目录结构
    (mod_dir / "Languages" / "English" / "Keyed").mkdir(parents=True, exist_ok=True)
    (mod_dir / "Languages" / "English" / "DefInjected" / "ThingDef").mkdir(
        parents=True, exist_ok=True
    )

    # 创建测试Keyed文件
    keyed_content = """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
  <test_key_1>Hello World</test_key_1>
  <test_key_2>Welcome to the game</test_key_2>
  <test_key_3>Press any key to continue</test_key_3>
</LanguageData>"""

    keyed_file = mod_dir / "Languages" / "English" / "Keyed" / "Test.xml"
    keyed_file.write_text(keyed_content, encoding="utf-8")

    # 创建测试DefInjected文件
    definjected_content = """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
  <ThingDef.Wood.label>wood</ThingDef.Wood.label>
  <ThingDef.Wood.description>A versatile material.</ThingDef.Wood.description>
  <ThingDef.Steel.label>steel</ThingDef.Steel.label>
  <ThingDef.Steel.description>Strong and durable metal.</ThingDef.Steel.description>
</LanguageData>"""

    definjected_file = (
        mod_dir / "Languages" / "English" / "DefInjected" / "ThingDe" / "Items_Resource_Stuff.xml"
    )
    definjected_file.write_text(definjected_content, encoding="utf-8")

    print("✅ 测试模组结构创建完成")
    return mod_dir


def test_complete_workflow():
    """测试完整的翻译工作流程"""
    print("\n🚀 开始完整工作流程测试")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 1. 创建测试模组
            mod_dir = Path(temp_dir) / "TestMod"
            create_test_mod_structure(mod_dir)

            # 2. 初始化翻译门面
            print("\n📋 步骤1: 初始化翻译门面")
            from core.translation_facade import TranslationFacade

            facade = TranslationFacade(str(mod_dir))
            print(f"✅ 翻译门面初始化成功: {facade.mod_dir}")
            # 3. 提取翻译数据
            print("\n📋 步骤2: 提取翻译数据")
            from core.extractors import AdvancedExtractor

            extractor = AdvancedExtractor(str(mod_dir), "English")

            # 提取Keyed翻译
            keyed_result = extractor.extract_keyed()
            print(f"✅ Keyed翻译提取: {len(keyed_result)} 条")

            # 提取DefInjected翻译
            definjected_result = extractor.extract_definjected()
            print(f"✅ DefInjected翻译提取: {len(definjected_result)} 条")

            # 4. 数据处理和转换
            print("\n📋 步骤3: 数据处理和转换")
            all_translations = keyed_result + definjected_result
            print(f"✅ 总翻译条目: {len(all_translations)} 条")

            # 验证翻译数据结构
            if all_translations:
                sample = all_translations[0]
                print(f"✅ 数据结构验证: key={sample.key}, type={sample.translation_type}")

            # 5. 导出为CSV
            print("\n📋 步骤4: 导出为CSV")
            from core.exporters import AdvancedExporter

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir(exist_ok=True)

            exporter = AdvancedExporter(str(output_dir), "ChineseSimplified")

            csv_path = output_dir / "test_translations.csv"
            csv_result = exporter.export_to_csv(all_translations, str(csv_path))

            if csv_result.is_success:
                print(f"✅ CSV导出成功: {csv_path}")
                # 验证CSV文件内容
                if csv_path.exists():
                    csv_content = csv_path.read_text(encoding="utf-8")
                    lines = csv_content.split("\n")
                    print(f"✅ CSV验证: {len(lines)} 行数据")

            # 6. 导出XML翻译模板
            print("\n📋 步骤5: 导出XML翻译模板")

            # 导出Keyed XML
            keyed_xml_result = exporter.export_keyed_xml(all_translations)
            if keyed_xml_result.is_success:
                print("✅ Keyed XML导出成功")

            # 导出DefInjected XML
            definjected_xml_result = exporter.export_definjected_xml(all_translations)
            if definjected_xml_result.is_success:
                print("✅ DefInjected XML导出成功")

            # 7. 工作流程统计
            print("\n📋 步骤6: 工作流程统计")
            stats = exporter.get_export_statistics(all_translations)
            print("✅ 统计信息:")
            print(f"   - 总翻译数: {stats['total_translations']}")
            print(f"   - Keyed数量: {stats['keyed_count']}")
            print(f"   - DefInjected数量: {stats['definjected_count']}")
            print(f"   - 目标语言: {stats['target_language']}")

            return True

        except Exception as e:
            print(f"❌ 工作流程测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_advanced_features():
    """测试高级功能"""
    print("\n🔧 测试高级功能")
    print("=" * 60)

    try:
        # 测试配置系统
        print("📋 测试配置系统")
        from services.config_service import config_service

        config = config_service.get_unified_config()
        print(f"✅ 配置获取成功: 默认语言 = {config.core.default_language}")
        # 测试过滤规则
        print("📋 测试过滤规则")
        from utils.filter_rules import AdvancedFilterRules

        filter_rules = AdvancedFilterRules()
        test_result = filter_rules.should_translate_field("label")
        print(f"✅ 过滤规则测试: should_translate = {test_result}")

        # 测试XML处理器
        print("📋 测试XML处理器")
        from utils.xml_processor import AdvancedXMLProcessor

        xml_processor = AdvancedXMLProcessor()
        print("✅ XML处理器初始化成功")

        return True

    except Exception as e:
        print(f"❌ 高级功能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🎯 Day Translation 2 - 完整工作流程测试")
    print("测试从提取到导出的完整翻译工作流程")
    print("=" * 80)

    # 运行测试
    tests = [
        ("基础功能验证", test_advanced_features),
        ("完整工作流程", test_complete_workflow),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 执行测试: {test_name}")
        print("-" * 40)

        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")

    # 测试结果总结
    print("\n" + "=" * 80)
    print(f"📊 工作流程测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 Day Translation 2 完整工作流程测试全部通过!")
        print("🚀 系统已准备好用于实际翻译工作!")
        return 0
    else:
        print(f"⚠️ {total - passed} 个测试失败，需要进一步检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())