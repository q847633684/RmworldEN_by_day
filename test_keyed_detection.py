#!/usr/bin/env python3
"""
测试修改后的英文Keyed目录自动检测逻辑
"""

import os
import tempfile
from pathlib import Path
from colorama import init, Fore, Style
from day_translation.utils.config import get_config
from day_translation.utils.path_manager import PathManager
from day_translation.core.main import TranslationFacade

# 初始化colorama
init()

def test_keyed_detection():
    """测试英文Keyed目录检测逻辑"""
    print("=== 测试修改后的英文Keyed目录检测逻辑 ===\n")
    
    # 使用测试模组
    mod_dir = r"c:\Users\q8476\Documents\我的工作\Day_汉化\test_mod"
    CONFIG = get_config()
    
    print(f"测试模组目录: {mod_dir}")
    
    # 模拟主菜单模式1的逻辑
    print("\n--- 模拟模式1的英文Keyed检测流程 ---")
    
    # 步骤1：输出目录（模拟）
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "test_output")
        os.makedirs(output_dir, exist_ok=True)
        print(f"输出目录: {output_dir}")
        
        # 步骤2：英文Keyed目录检测
        en_keyed_dir = None
        
        # 步骤2a：自动检测英文Keyed目录
        auto_en_keyed_dir = os.path.join(mod_dir, "Languages", "English", CONFIG.keyed_dir)
        print(f"自动构建的英文Keyed路径: {auto_en_keyed_dir}")
        print(f"目录是否存在: {os.path.exists(auto_en_keyed_dir)}")
        
        if os.path.exists(auto_en_keyed_dir):
            # 自动使用检测到的英文Keyed目录
            en_keyed_dir = auto_en_keyed_dir
            print(f"{Fore.GREEN}✅ 已自动检测并使用英文 Keyed 目录: {auto_en_keyed_dir}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}未检测到英文 Keyed 目录{Style.RESET_ALL}")
        
        # 步骤3：验证结果
        print(f"\n最终使用的英文Keyed目录: {en_keyed_dir}")
        
        if en_keyed_dir:
            files = os.listdir(en_keyed_dir)
            print(f"英文Keyed目录中的文件: {files}")
            
            # 测试提取
            print("\n--- 执行提取测试 ---")
            try:
                facade = TranslationFacade(mod_dir, language="ChineseSimplified")
                translations = facade.extract_templates_and_generate_csv(
                    output_dir=output_dir,
                    en_keyed_dir=en_keyed_dir,
                    auto_choose_definjected=True
                )
                print(f"提取成功！共 {len(translations)} 条翻译")
                
                # 检查是否使用了英文Keyed
                keyed_translations = [t for t in translations if '/' not in t[0]]
                print(f"其中Keyed翻译: {len(keyed_translations)} 条")
                
            except Exception as e:
                print(f"提取失败: {e}")
        
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_keyed_detection()
