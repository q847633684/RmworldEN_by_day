#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进合并逻辑测试脚本

测试新的智能合并 vs 传统合并 vs 完全替换三种模式
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from day_translation.utils.utils import handle_existing_translations_choice, smart_merge_xml_translations

def create_existing_xml(file_path: str):
    """创建现有的XML翻译文件"""
    xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
  <!--EN: weapon-->
  <Pistol.label>weapon</Pistol.label>
  <!--EN: A simple weapon-->
  <Pistol.description>A simple weapon</Pistol.description>
  <!--EN: rifle-->
  <Rifle.label>步枪</Rifle.label>
  <!--EN: manually translated description-->
  <Rifle.description>精心翻译的步枪描述</Rifle.description>
  <!--EN: old item that should be kept-->
  <OldItem.label>应该保留的旧项目</OldItem.label>
</LanguageData>'''
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    print(f"✅ 创建现有XML文件: {file_path}")

def demo_merge_modes():
    """演示三种合并模式的区别"""
    print(f"\n{'='*80}")
    print("🔄 合并模式对比演示")
    print(f"{'='*80}")
    
    # 准备新的翻译数据
    new_translations = {
        "Pistol.label": "手枪",                    # 更新：weapon -> 手枪
        "Pistol.description": "一把简单的手枪",     # 更新：A simple weapon -> 一把简单的手枪
        "Rifle.label": "步枪",                     # 相同：步枪 (保持不变)
        "Rifle.description": "机器翻译的步枪描述",  # 更新：精心翻译的步枪描述 -> 机器翻译版本
        "Sword.label": "剑",                       # 新增项目
        "Sword.description": "一把锋利的剑",        # 新增项目
    }
    
    # 测试1：智能合并模式
    print(f"\n{'-'*60}")
    print("🧠 测试1：智能合并模式")
    print(f"{'-'*60}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        xml_file = os.path.join(temp_dir, "smart_merge_test.xml")
        create_existing_xml(xml_file)
        
        print(f"\n📄 原始XML内容:")
        with open(xml_file, 'r', encoding='utf-8') as f:
            print(f.read())
        
        print(f"\n🧠 执行智能合并...")
        success = smart_merge_xml_translations(xml_file, new_translations, preserve_manual_edits=True)
        
        if success:
            print(f"\n✅ 智能合并结果:")
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
                
            # 分析结果
            print(f"\n📊 智能合并分析:")
            if "精心翻译的步枪描述" in content:
                print(f"✅ 保留了手动翻译: Rifle.description = '精心翻译的步枪描述'")
            else:
                print(f"❌ 手动翻译被覆盖了")
                
            if "剑" in content:
                print(f"✅ 添加了新项目: Sword.label, Sword.description")
            else:
                print(f"❌ 新项目未添加")
    
    # 测试2：传统合并模式
    print(f"\n{'-'*60}")
    print("🔀 测试2：传统合并模式")
    print(f"{'-'*60}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        xml_file = os.path.join(temp_dir, "traditional_merge_test.xml")
        create_existing_xml(xml_file)
        
        print(f"\n📄 原始XML内容:")
        with open(xml_file, 'r', encoding='utf-8') as f:
            print(f.read())
        
        print(f"\n🔀 执行传统合并...")
        # 模拟传统合并逻辑
        from day_translation.utils.utils import XMLProcessor
        processor = XMLProcessor()
        tree = processor.parse_xml(xml_file)
        if tree:
            processor.update_translations(tree, new_translations, merge=True)
            processor.save_xml(tree, xml_file)
            
        print(f"\n✅ 传统合并结果:")
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
            
        # 分析结果
        print(f"\n📊 传统合并分析:")
        if "精心翻译的步枪描述" in content:
            print(f"✅ 保留了手动翻译: Rifle.description = '精心翻译的步枪描述'")
        else:
            print(f"❌ 手动翻译被覆盖: Rifle.description = '机器翻译的步枪描述'")
            
        if "剑" in content:
            print(f"❌ 意外添加了新项目（传统合并不应该添加新项目）")
        else:
            print(f"✅ 正确：没有添加新项目（传统合并只更新现有元素）")
    
    # 测试3：完全替换模式
    print(f"\n{'-'*60}")
    print("🔄 测试3：完全替换模式")
    print(f"{'-'*60}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        xml_file = os.path.join(temp_dir, "replace_test.xml")
        create_existing_xml(xml_file)
        
        print(f"\n📄 原始XML内容:")
        with open(xml_file, 'r', encoding='utf-8') as f:
            print(f.read())
        
        print(f"\n🔄 执行完全替换...")
        # 模拟完全替换：删除文件并重新创建
        os.remove(xml_file)
        from day_translation.utils.utils import _create_new_xml_file
        _create_new_xml_file(xml_file, new_translations)
            
        print(f"\n✅ 完全替换结果:")
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
            
        # 分析结果
        print(f"\n📊 完全替换分析:")
        if "精心翻译的步枪描述" in content:
            print(f"❌ 意外保留了旧内容")
        else:
            print(f"❌ 手动翻译丢失: Rifle.description = '机器翻译的步枪描述'")
            
        if "剑" in content:
            print(f"✅ 添加了所有新项目")
        else:
            print(f"❌ 新项目未添加")
            
        if "应该保留的旧项目" in content:
            print(f"❌ 意外保留了不在新翻译中的旧项目")
        else:
            print(f"✅ 正确：清理了不在新翻译中的旧项目")

def demo_comparison_table():
    """显示对比表格"""
    print(f"\n{'='*80}")
    print("📊 三种合并模式对比总结")
    print(f"{'='*80}")
    
    print(f"""
┌─────────────────────────────┬─────────────┬─────────────┬─────────────┐
│            特性             │  智能合并   │  传统合并   │  完全替换   │
├─────────────────────────────┼─────────────┼─────────────┼─────────────┤
│ 保留相同翻译                │     ✅      │     ✅      │     ✅      │
│ 更新英文原文                │     ✅      │     ✅      │     ✅      │
│ 保留手动编辑                │     ✅      │     ❌      │     ❌      │
│ 添加新翻译项                │     ✅      │     ❌      │     ✅      │
│ 清理过时项目                │     ❌      │     ❌      │     ✅      │
│ 保留XML结构和注释           │     ✅      │    部分     │     ❌      │
│ 智能判断手动编辑            │     ✅      │     ❌      │     ❌      │
│ 处理复杂度                  │     高      │     低      │     低      │
│ 推荐场景                    │ 增量更新    │ 简单更新    │ 完全重建    │
└─────────────────────────────┴─────────────┴─────────────┴─────────────┘

💡 使用建议：
🧠 智能合并：适合有手动翻译维护的项目，希望在更新时保留已有工作成果
🔀 传统合并：适合只需更新现有翻译，不添加新内容的场景
🔄 完全替换：适合需要彻底重建翻译文件或清理过时内容的场景

🎯 最佳实践：
- 首次生成翻译模板：使用完全替换
- 增量更新翻译：使用智能合并
- 批量修正翻译：根据需要选择智能合并或传统合并
- 清理过时翻译：使用完全替换
""")

def main():
    """主函数"""
    print("🎯 RimWorld模组翻译工具 - 改进合并逻辑测试")
    print(f"测试智能合并、传统合并、完全替换三种模式的区别\n")
    
    try:
        # 演示三种合并模式
        demo_merge_modes()
        
        # 显示对比表格
        demo_comparison_table()
        
        print(f"\n🎉 测试完成！现在用户可以根据具体需求选择最合适的合并策略。")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
