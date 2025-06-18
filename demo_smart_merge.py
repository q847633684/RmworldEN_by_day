#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能合并方案演示脚本

演示智能合并和完全替换两种方案的区别
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from day_translation.utils.utils import smart_merge_xml_translations, handle_existing_translations_choice

def create_sample_xml(file_path: str):
    """创建示例XML文件"""
    xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
  <!--EN: insertable-->
  <AnalInsertableBondage.label>insertable</AnalInsertableBondage.label>
  <!--EN: outer-->
  <ArmsOuterBondage.label>outer</ArmsOuterBondage.label>
  <!--EN: Over skin-->
  <BeltsOnSkinBondage.label>Over skin</BeltsOnSkinBondage.label>
  <!--EN: headgear-->
  <GagOuterBondage.label>headgear</GagOuterBondage.label>
  <!--EN: outer-->
  <LegsOuterBondage.label>outer</LegsOuterBondage.label>
  <!--EN: insertable-->
  <VaginalInsertableBondage.label>insertable</VaginalInsertableBondage.label>
  <!--EN: manually edited translation-->
  <ManualEdit.label>手动编辑的翻译</ManualEdit.label>
</LanguageData>'''
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    print(f"✅ 创建示例XML文件: {file_path}")

def demo_smart_merge():
    """演示智能合并方案"""
    print(f"\n{'='*60}")
    print("🧠 方案1演示：智能合并（扫描XML内容，替换已有key，添加缺失key）")
    print(f"{'='*60}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        xml_file = os.path.join(temp_dir, "test.xml")
        
        # 1. 创建现有XML文件
        create_sample_xml(xml_file)
        
        print("\n📄 现有XML内容:")
        with open(xml_file, 'r', encoding='utf-8') as f:
            print(f.read())
        
        # 2. 准备新的翻译数据
        new_translations = {
            # 更新现有的翻译
            "AnalInsertableBondage.label": "可插入的",
            "ArmsOuterBondage.label": "外层的",
            "BeltsOnSkinBondage.label": "贴肤的",
            "GagOuterBondage.label": "头部装备",
            "LegsOuterBondage.label": "腿部外层",
            "VaginalInsertableBondage.label": "阴道可插入的",
            # 手动编辑的翻译（应该保留）
            "ManualEdit.label": "新的机器翻译",  # 这个应该被保留为手动编辑
            # 添加新的翻译
            "NewItem1.label": "新项目1",
            "NewItem2.label": "新项目2",
            "AnotherCategory.description": "另一个类别的描述"
        }
        
        print(f"\n🔄 准备更新的翻译数据（{len(new_translations)} 个条目）:")
        for key, value in list(new_translations.items())[:5]:  # 显示前5个
            print(f"  {key} = '{value}'")
        print(f"  ... 还有 {len(new_translations) - 5} 个")
        
        # 3. 执行智能合并
        print(f"\n🧠 执行智能合并...")
        success = smart_merge_xml_translations(xml_file, new_translations, preserve_manual_edits=True)
        
        if success:
            print(f"\n✅ 智能合并完成！合并后的XML内容:")
            with open(xml_file, 'r', encoding='utf-8') as f:
                print(f.read())
        else:
            print(f"\n❌ 智能合并失败！")

def demo_full_replace():
    """演示完全替换方案"""
    print(f"\n{'='*60}")
    print("🔄 方案2演示：完全替换（删除现有文件，重新生成）")
    print(f"{'='*60}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        xml_file = os.path.join(temp_dir, "test.xml")
        
        # 1. 创建现有XML文件
        create_sample_xml(xml_file)
        
        print("\n📄 现有XML内容:")
        with open(xml_file, 'r', encoding='utf-8') as f:
            print(f.read())
        
        # 2. 准备新的翻译数据（同智能合并）
        new_translations = {
            "AnalInsertableBondage.label": "可插入的",
            "ArmsOuterBondage.label": "外层的", 
            "BeltsOnSkinBondage.label": "贴肤的",
            "GagOuterBondage.label": "头部装备",
            "LegsOuterBondage.label": "腿部外层",
            "VaginalInsertableBondage.label": "阴道可插入的",
            "ManualEdit.label": "新的机器翻译",  # 在完全替换模式下，手动编辑会丢失
            "NewItem1.label": "新项目1",
            "NewItem2.label": "新项目2",
            "AnotherCategory.description": "另一个类别的描述"
        }
        
        print(f"\n🔄 删除现有文件并重新生成...")
        
        # 3. 删除现有文件
        os.remove(xml_file)
        print("❌ 删除现有XML文件")
        
        # 4. 重新创建文件
        from day_translation.utils.utils import _create_new_xml_file
        success = _create_new_xml_file(xml_file, new_translations)
        
        if success:
            print(f"\n✅ 完全替换完成！新生成的XML内容:")
            with open(xml_file, 'r', encoding='utf-8') as f:
                print(f.read())
        else:
            print(f"\n❌ 完全替换失败！")

def demo_comparison():
    """对比两种方案"""
    print(f"\n{'='*60}")
    print("📊 方案对比总结")
    print(f"{'='*60}")
    
    print(f"""
🧠 方案1：智能合并
✅ 优点：
   - 保留手动编辑的翻译（如 'ManualEdit.label' 保持为 '手动编辑的翻译'）
   - 只更新有变化的内容，效率高
   - 保留XML结构和注释
   - 增量更新，适合大型项目
   
❌ 缺点：
   - 实现复杂，需要解析和对比XML
   - 可能出现格式不一致
   - 需要判断哪些是手动编辑的翻译

🔄 方案2：完全替换  
✅ 优点：
   - 实现简单，逻辑清晰
   - 格式统一，所有内容都是新生成的
   - 避免遗留的错误或过时内容
   
❌ 缺点：
   - 丢失手动编辑的翻译（如 'ManualEdit.label' 被覆盖为 '新的机器翻译'）
   - 效率低，需要重新处理所有内容
   - 风险高，可能丢失重要的自定义内容

💡 建议的使用场景：
   - 智能合并：适合有手动翻译维护的项目，需要保留已有工作成果
   - 完全替换：适合全自动化流程，或者需要彻底清理格式的情况
   
🎯 实际项目中的最佳实践：
   - 提供用户选择，默认使用智能合并
   - 在完全替换前进行备份
   - 提供预览功能，让用户了解会发生什么变化
""")

def main():
    """主函数"""
    print("🎯 RimWorld模组翻译工具 - 智能合并方案演示")
    print(f"演示智能合并 vs 完全替换两种处理方案的区别\n")
    
    try:
        # 演示智能合并
        demo_smart_merge()
        
        # 演示完全替换
        demo_full_replace()
        
        # 对比总结
        demo_comparison()
        
        print(f"\n🎉 演示完成！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
