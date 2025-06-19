#!/usr/bin/env python3
"""
Day Translation 2 - 高级集成测试

测试新迁移的高级XML处理器和过滤器的实际功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def test_advanced_xml_processor():
    """测试高级XML处理器的实际功能"""
    print("🧪 测试高级XML处理器实际功能...")
    
    try:
        from utils.xml_processor import AdvancedXMLProcessor

        # 创建处理器实例
        processor = AdvancedXMLProcessor()

        # 创建测试XML内容
        test_xml = """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
    <Confirm>确认</Confirm>
    <Cancel>取消</Cancel>
    <TestKey>This is a test translation</TestKey>
    <EmptyKey></EmptyKey>
    <NumberKey>123</NumberKey>
</LanguageData>"""

        # 创建临时XML文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(test_xml)
            temp_file = f.name
        try:
            # 测试XML解析
            tree = processor.parse_xml(temp_file)
            if tree is not None:
                print("✅ XML文件解析成功")

                # 测试可翻译内容提取
                translations = processor.extract_translations(tree, context="Keyed")
                print(f"✅ 提取到 {len(translations)} 个可翻译项目")

                # 显示提取的内容
                for key, text, tag in translations:
                    print(f"   - {key}: {text}")

                return True
            else:
                print("❌ XML解析失败")
                return False

        finally:
            # 清理临时文件
            os.unlink(temp_file)

    except Exception as e:
        print(f"❌ 高级XML处理器测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_advanced_filters_integration():
    """测试高级过滤器与XML处理器的集成"""
    print("🧪 测试高级过滤器与XML处理器集成...")
    
    try:
        from utils.filter_rules import AdvancedFilterRules
        from utils.xml_processor import AdvancedXMLProcessor

        # 创建实例
        processor = AdvancedXMLProcessor()
        filter_rules = AdvancedFilterRules()

        # 创建测试XML内容
        test_xml = """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
    <UI_Confirm>确认</UI_Confirm>
    <TestKey>Test translation</TestKey>
    <NumericValue>12345</NumericValue>
    <EmptyValue></EmptyValue>
    <ShortCode>OK</ShortCode>
    <ValidText>This is a valid translation text</ValidText>
</LanguageData>"""

        # 创建临时XML文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(test_xml)
            temp_file = f.name
        try:
            # 解析XML
            tree = processor.parse_xml(temp_file)
            if tree is None:
                print("❌ XML解析失败")
                return False

            # 提取内容并应用过滤器
            translations = processor.extract_translations(tree, context="Keyed")
            filtered_count = 0
            print("📋 过滤结果:")
            for key, text, tag in translations:
                # 应用过滤规则 - 使用通用方法
                should_translate = filter_rules.should_translate_field(key, text)
                status = "✅ 需要翻译" if should_translate else "❌ 过滤掉"

                print(f"   - {key}: '{text}' -> {status}")

                if should_translate:
                    filtered_count += 1

            print(f"✅ 过滤完成: {filtered_count}/{len(translations)} 项目需要翻译")

            # 测试统计信息
            stats = filter_rules.get_filter_statistics()
            print(f"✅ 过滤器统计: {stats}")

            return True

        finally:
            # 清理临时文件
            os.unlink(temp_file)

    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_xml_smart_merge():
    """测试XML智能合并功能"""
    print("🧪 测试XML智能合并功能...")
    
    try:
        from utils.xml_processor import AdvancedXMLProcessor

        processor = AdvancedXMLProcessor()

        # 创建原始XML
        original_xml = """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
    <Confirm>Confirm</Confirm>
    <Cancel>Cancel</Cancel>
    <NewKey>New content</NewKey>
</LanguageData>"""

        # 创建翻译XML
        translation_xml = """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
    <Confirm>确认</Confirm>
    <Cancel>取消</Cancel>
    <OldKey>旧内容</OldKey>
</LanguageData>"""

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(original_xml)
            original_file = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(translation_xml)
            translation_file = f.name
        try:
            # 首先解析翻译文件，提取翻译内容
            translation_tree = processor.parse_xml(translation_file)
            if not translation_tree:
                print("❌ 翻译文件解析失败")
                return False

            # 提取翻译内容为字典格式
            translations = processor.extract_translations(translation_tree, context="Translation")
            translation_dict = {key: text for key, text, tag in translations}

            print(f"📝 提取到 {len(translation_dict)} 个翻译项目")

            # 执行智能合并
            result = processor.smart_merge_xml_translations(original_file, translation_dict)

            if result:
                print("✅ XML智能合并成功")

                # 读取结果验证
                with open(original_file, "r", encoding="utf-8") as f:
                    merged_content = f.read()

                print("📄 合并后的内容:")
                print(merged_content)

                # 验证合并结果包含新旧内容
                if (
                    "确认" in merged_content
                    and "取消" in merged_content
                    and "New content" in merged_content
                ):
                    print("✅ 合并结果验证通过")
                    return True
                else:
                    print("❌ 合并结果验证失败")
                    return False
            else:
                print("❌ XML智能合并失败")
                return False

        finally:
            # 清理临时文件
            os.unlink(original_file)
            os.unlink(translation_file)

    except Exception as e:
        print(f"❌ XML智能合并测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有高级集成测试"""
    print("🚀 Day Translation 2 - 高级集成测试")
    print("=" * 50)

    tests = [
        ("高级XML处理器", test_advanced_xml_processor),
        ("高级过滤器集成", test_advanced_filters_integration),
        ("XML智能合并", test_xml_smart_merge),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 运行测试: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name} 测试通过")
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")

    print(f"\n📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有高级集成测试通过！")
        return 0
    else:
        print("⚠️  部分高级测试失败，需要进一步调试")
        return 1


if __name__ == "__main__":
    sys.exit(main())
