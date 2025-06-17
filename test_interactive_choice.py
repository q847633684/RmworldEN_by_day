#!/usr/bin/env python3
"""
测试 DefInjected 智能选择逻辑 - 交互版本
"""

import os
import tempfile
from day_translation.core.main import TranslationFacade

def test_interactive_choice():
    """测试交互式 DefInjected 选择"""
    test_mod_dir = r"c:\Users\q8476\Documents\我的工作\Day_汉化\test_mod"
    
    print("=== 测试交互式 DefInjected 选择逻辑 ===")
    print(f"测试模组目录: {test_mod_dir}")
    print("注意：该测试有英文 DefInjected 目录，将提供选择选项")
    print()
    
    # 创建临时输出目录
    with tempfile.TemporaryDirectory() as temp_output_dir:
        output_dir = os.path.join(temp_output_dir, "interactive_output")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"输出目录: {output_dir}")
        
        # 创建 TranslationFacade 实例
        facade = TranslationFacade(test_mod_dir, language="ChineseSimplified")
        
        print("\n--- 测试交互式选择 ---")
        print("当询问DefInjected处理方式时：")
        print("选择 1 = 使用英文 DefInjected 为基础")
        print("选择 2 = 从 Defs 目录重新提取")
        print("让我们开始测试...")
        
        try:
            translations = facade.extract_templates_and_generate_csv(
                output_dir=output_dir,
                auto_choose_definjected=False  # 启用交互选择
            )
            print(f"\n交互模式提取完成，共 {len(translations)} 条翻译")
            
            # 显示提取结果的分类
            keyed_count = len([t for t in translations if '/' not in t[0]])
            definjected_count = len([t for t in translations if '/' in t[0]])
            print(f"- Keyed 翻译: {keyed_count} 条")
            print(f"- DefInjected 翻译: {definjected_count} 条")
            
        except Exception as e:
            print(f"交互模式失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_interactive_choice()
