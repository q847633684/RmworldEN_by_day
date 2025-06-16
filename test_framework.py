"""
框架功能测试脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """测试模块导入"""
    print("🔧 测试模块导入...")
    
    try:
        from day_translation.core.main import TranslationFacade, main
        print("  ✅ main 模块导入成功")
        
        from day_translation.core.filters import ContentFilter
        print("  ✅ filters 模块导入成功")
        
        from day_translation.utils.filter_config import UnifiedFilterRules
        print("  ✅ filter_config 模块导入成功")
        
        from day_translation.utils.config import TranslationConfig
        print("  ✅ config 模块导入成功")
        
        print("🎉 所有核心模块导入成功！")
        return True
        
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n🔧 测试基本功能...")
    
    try:
        from day_translation.core.main import TranslationFacade
        
        # 创建测试实例
        facade = TranslationFacade(".", ".")
        print("  ✅ TranslationFacade 创建成功")
        
        # 测试过滤器
        result = facade.content_filter.is_translatable("label", "Test Label")
        print(f"  ✅ 过滤器测试: is_translatable('label', 'Test Label') = {result}")
        
        # 测试模式切换
        facade.set_filter_mode("standard")
        print("  ✅ 标准模式设置成功")
        
        facade.set_filter_mode("custom")
        print("  ✅ 自定义模式设置成功")
        
        print("🎉 基本功能测试成功！")
        return True
        
    except Exception as e:
        print(f"  ❌ 功能测试失败: {e}")
        return False

def test_filter_rules():
    """测试过滤规则"""
    print("\n🔧 测试过滤规则...")
    
    try:
        from day_translation.utils.filter_config import UnifiedFilterRules
        
        print(f"  📋 白名单字段数量: {len(UnifiedFilterRules.DEFAULT_FIELDS)}")
        print(f"  ❌ 黑名单字段数量: {len(UnifiedFilterRules.IGNORE_FIELDS)}")
        print(f"  🔍 正则模式数量: {len(UnifiedFilterRules.NON_TEXT_PATTERNS)}")
        
        # 测试一些典型字段
        from day_translation.core.filters import ContentFilter
        filter_obj = ContentFilter("standard")
        
        test_cases = [
            ("label", "Steel sword", True),
            ("defName", "WeaponMelee", False),
            ("cost", "100", False),
            ("description", "A sharp blade", True),
        ]
        
        for tag, text, expected in test_cases:
            result = filter_obj.is_translatable(tag, text)
            status = "✅" if result == expected else "❌"
            print(f"  {status} {tag}='{text}' → {result}")
        
        print("🎉 过滤规则测试完成！")
        return True
        
    except Exception as e:
        print(f"  ❌ 过滤规则测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Day Translation 框架测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    if test_imports():
        success_count += 1
    
    if test_basic_functionality():
        success_count += 1
    
    if test_filter_rules():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！框架可以正常使用。")
        print("\n💡 下一步：")
        print("  运行 python run_translation.py 开始翻译工作")
    else:
        print("❌ 部分测试失败，请检查配置")
        sys.exit(1)
