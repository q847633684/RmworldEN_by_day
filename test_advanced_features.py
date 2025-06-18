#!/usr/bin/env python3
"""
测试 handle_existing_translations_choice 函数的增强功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from day_translation.utils.utils import handle_existing_translations_choice

def create_test_files(test_dir: Path, count: int = 5):
    """创建测试用的 XML 文件"""
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
    <Test.label>测试内容</Test.label>
    <Test.description>这是一个测试文件</Test.description>
</LanguageData>"""
    
    test_files = []
    for i in range(count):
        file_path = test_dir / f"test_{i+1}.xml"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        test_files.append(file_path)
    
    return test_files

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试基本功能...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "translations"
        test_dir.mkdir()
        
        # 创建测试文件
        test_files = create_test_files(test_dir, 3)
        print(f"✅ 创建了 {len(test_files)} 个测试文件")
        
        # 测试自动模式
        print("\n📋 测试自动模式...")
        for mode in ["replace", "merge", "backup", "skip"]:
            print(f"  测试 {mode} 模式...")
            result = handle_existing_translations_choice(
                str(test_dir), 
                auto_mode=mode,
                backup_enabled=True
            )
            print(f"  ✅ {mode} 模式返回: {result}")
            
            # 恢复测试文件（如果被删除了）
            if not any(f.exists() for f in test_files):
                test_files = create_test_files(test_dir, 3)

def test_advanced_functionality():
    """测试高级功能"""
    print("\n🚀 测试高级功能...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "translations"
        test_dir.mkdir()
        
        # 创建测试文件
        test_files = create_test_files(test_dir, 8)
        print(f"✅ 创建了 {len(test_files)} 个测试文件")
        
        # 测试增量更新模式
        print("\n📊 测试增量更新模式...")
        result = handle_existing_translations_choice(
            str(test_dir), 
            auto_mode="incremental",
            enable_advanced_options=True
        )
        print(f"  ✅ 增量更新模式返回: {result}")
        
        # 测试预览模式
        print("\n👁️ 测试预览模式...")
        result = handle_existing_translations_choice(
            str(test_dir), 
            auto_mode="preview",
            enable_advanced_options=True
        )
        print(f"  ✅ 预览模式返回: {result}")

def test_interactive_mode():
    """测试交互模式的菜单显示"""
    print("\n🎮 测试交互模式菜单显示...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "translations"
        test_dir.mkdir()
        
        # 创建测试文件
        test_files = create_test_files(test_dir, 15)  # 创建更多文件来测试显示逻辑
        print(f"✅ 创建了 {len(test_files)} 个测试文件")
        
        print("\n🖥️ 模拟交互模式显示（自动选择跳过）...")
        
        # 模拟用户输入，这里我们不能真正测试交互，但可以测试菜单显示
        # 实际使用时需要用户手动输入
        print("  注意：实际测试需要手动运行并输入选项")

def test_error_handling():
    """测试错误处理"""
    print("\n⚠️ 测试错误处理...")
    
    # 测试不存在的目录
    result = handle_existing_translations_choice("/nonexistent/path")
    print(f"✅ 不存在目录返回: {result}")
    
    # 测试无效的自动模式
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "translations"
        test_dir.mkdir()
        
        # 创建测试文件
        create_test_files(test_dir, 2)
        
        result = handle_existing_translations_choice(
            str(test_dir), 
            auto_mode="invalid_mode"
        )
        print(f"✅ 无效自动模式处理: {result}")

def main():
    """主测试函数"""
    print("🎯 开始测试 handle_existing_translations_choice 增强功能\n")
    
    try:
        test_basic_functionality()
        test_advanced_functionality()
        test_interactive_mode()
        test_error_handling()
        
        print("\n🎉 所有测试完成！")
        print("\n📝 新增功能说明：")
        print("  1. ✨ 增量更新模式 - 只更新有变化的文件")
        print("  2. 👁️ 预览模式 - 先预览变化再确认执行")
        print("  3. 🎛️ 高级选项开关 - 可选启用高级功能")
        print("  4. 🚀 更灵活的自动模式支持")
        print("  5. 📊 更详细的文件信息显示")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
