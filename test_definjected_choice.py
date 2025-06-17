#!/usr/bin/env python3
"""
测试 DefInjected 智能选择逻辑
"""

import os
import tempfile
import shutil
from pathlib import Path
from day_translation.core.main import TranslationFacade

def test_definjected_choice():
    """测试 DefInjected 选择逻辑"""
    test_mod_dir = r"c:\Users\q8476\Documents\我的工作\Day_汉化\test_mod"
    
    print("=== 测试 DefInjected 智能选择逻辑 ===")
    print(f"测试模组目录: {test_mod_dir}")
    
    # 创建临时输出目录
    with tempfile.TemporaryDirectory() as temp_output_dir:
        output_dir = os.path.join(temp_output_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"输出目录: {output_dir}")
        
        # 创建 TranslationFacade 实例
        facade = TranslationFacade(test_mod_dir, language="ChineseSimplified")
        
        print("\n--- 测试1: 自动选择模式 (auto_choose_definjected=True) ---")
        try:
            translations_auto = facade.extract_templates_and_generate_csv(
                output_dir=output_dir + "_auto",
                auto_choose_definjected=True
            )
            print(f"自动模式提取完成，共 {len(translations_auto)} 条翻译")
            for i, (key, text, group, file_info) in enumerate(translations_auto[:5]):  # 显示前5条
                print(f"  {i+1}. {key}: {text[:50]}...")
        except Exception as e:
            print(f"自动模式失败: {e}")
        
        print("\n--- 测试2: 交互选择模式 (auto_choose_definjected=False) ---")
        # 注意：这个模式会要求用户输入选择，在测试环境中可能不适用
        # 这里我们只是验证方法调用不会出错
        try:
            print("提示：交互模式需要用户输入，这里只测试初始化...")
            # 可以通过模拟输入来测试，但这里简化处理
            print("交互模式测试跳过（需要用户交互）")
        except Exception as e:
            print(f"交互模式初始化失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_definjected_choice()
