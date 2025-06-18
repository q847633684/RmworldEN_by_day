#!/usr/bin/env python3
"""
Day Translation 2 - 独立测试脚本

直接测试核心类而不依赖复杂的导入链
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

def test_xml_processor():
    """测试XML处理器"""
    try:
        # 创建一个简单的XML内容进行测试
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item>
        <label>Test Label</label>
        <description>Test Description</description>
    </item>
</root>"""
        
        # 写入临时文件
        test_file = "temp_test.xml"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # 导入XML处理器
        from utils.xml_processor import XMLProcessor
        
        processor = XMLProcessor()
        tree = processor.parse_xml(test_file)
        
        if tree is not None:
            print("✅ XML处理器测试成功")
            
            # 清理临时文件
            os.remove(test_file)
            return True
        else:
            print("❌ XML处理器返回None")
            return False
            
    except Exception as e:
        print(f"❌ XML处理器测试失败: {e}")
        # 清理临时文件
        if os.path.exists("temp_test.xml"):
            os.remove("temp_test.xml")
        return False


def test_translation_entry():
    """测试翻译条目模型"""
    try:
        from models.translation_data import TranslationEntry, TranslationType
        
        # 创建翻译条目
        entry = TranslationEntry(
            key="test.key",
            source_text="Hello World",
            translation_type=TranslationType.KEYED,
            xml_tag="label",
            file_path="test.xml"
        )
        
        # 测试基本属性
        assert entry.key == "test.key"
        assert entry.source_text == "Hello World"
        assert entry.translation_type == TranslationType.KEYED
        
        print("✅ 翻译条目模型测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 翻译条目模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_content_filter():
    """测试内容过滤器"""
    try:
        from utils.filters import ContentFilter
        
        filter_obj = ContentFilter()
        
        # 测试基本过滤功能
        should_include = filter_obj.should_include_content("Hello World")
        print(f"✅ 内容过滤器测试成功: should_include={should_include}")
        return True
        
    except Exception as e:
        print(f"❌ 内容过滤器测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 Day Translation 2 - 独立组件测试")
    print("=" * 50)
    
    tests = [
        ("XML处理器", test_xml_processor),
        ("翻译条目模型", test_translation_entry),  
        ("内容过滤器", test_content_filter),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 测试 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} 测试失败")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
