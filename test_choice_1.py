#!/usr/bin/env python3
"""
测试选择 1 - 使用英文 DefInjected 为基础
"""

import os
import tempfile
from day_translation.core.main import TranslationFacade

def test_choice_1():
    """测试选择1：使用英文DefInjected为基础"""
    test_mod_dir = r"c:\Users\q8476\Documents\我的工作\Day_汉化\test_mod"
    
    print("=== 测试选择1：使用英文DefInjected为基础 ===")
    
    # 创建临时输出目录
    with tempfile.TemporaryDirectory() as temp_output_dir:
        output_dir = os.path.join(temp_output_dir, "choice1_output")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"输出目录: {output_dir}")
        
        # 创建 TranslationFacade 实例
        facade = TranslationFacade(test_mod_dir, language="ChineseSimplified")
        
        print("\n--- 即将进行选择1测试，请输入'1'或直接回车 ---")
        
        try:
            translations = facade.extract_templates_and_generate_csv(
                output_dir=output_dir,
                auto_choose_definjected=False
            )
            print(f"\n选择1模式提取完成，共 {len(translations)} 条翻译")
            
            # 检查输出目录结构
            lang_dir = os.path.join(output_dir, "Languages", "ChineseSimplified")
            if os.path.exists(lang_dir):
                print(f"\n生成的文件结构:")
                for root, dirs, files in os.walk(lang_dir):
                    level = root.replace(lang_dir, '').count(os.sep)
                    indent = ' ' * 2 * level
                    print(f"{indent}{os.path.basename(root)}/")
                    subindent = ' ' * 2 * (level + 1)
                    for file in files:
                        print(f"{subindent}{file}")
                        
        except Exception as e:
            print(f"选择1模式失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_choice_1()
