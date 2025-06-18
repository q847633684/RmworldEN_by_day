#!/usr/bin/env python3
"""
测试新的用户交互和偏好管理系统
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from day_translation.utils.user_preferences import UserPreferencesManager, UserInteraction, ExtractionPreferences
from colorama import init, Fore, Style

init()

def test_preferences_system():
    """测试偏好系统"""
    print(f"{Fore.BLUE}=== 测试用户偏好系统 ==={Style.RESET_ALL}")
    
    # 初始化偏好管理器
    prefs_manager = UserPreferencesManager()
    
    # 获取当前偏好
    prefs = prefs_manager.get_preferences()
    print(f"自动模式: {prefs.general.auto_mode}")
    print(f"记住路径: {prefs.general.remember_paths}")
    print(f"输出位置: {prefs.extraction.output_location}")
    print(f"结构选择: {prefs.extraction.structure_choice}")
    print(f"合并模式: {prefs.extraction.merge_mode}")
    
    # 模拟设置一些偏好
    prefs.general.auto_mode = True # 自动模式
    prefs.extraction.output_location = "external" # 输出位置选择
    prefs.extraction.output_dir = "提取的翻译" # 假设这是外部目录
    prefs.extraction.structure_choice = "original"  # 结构选择
    prefs.extraction.merge_mode = "smart-merge" # 合并模式
    
    # 保存偏好
    prefs_manager.save_preferences()
    print(f"{Fore.GREEN}✅ 偏好设置已保存{Style.RESET_ALL}")
    
    # 测试记忆路径
    prefs_manager.remember_path("test_path", "C:\\test\\path")
    remembered = prefs_manager.get_remembered_path("test_path")
    print(f"记忆的路径: {remembered}")
    
    return prefs_manager

def test_interaction_system():
    """测试交互系统"""
    print(f"\n{Fore.BLUE}=== 测试用户交互系统 ==={Style.RESET_ALL}")
    
    prefs_manager = UserPreferencesManager()
    interaction = UserInteraction(prefs_manager)
    
    # 显示当前配置
    interaction.show_current_extraction_config()
    
    print(f"{Fore.GREEN}✅ 交互系统测试完成{Style.RESET_ALL}")

def main():
    """主测试函数"""
    print(f"{Fore.MAGENTA}=== Day Translation 偏好管理系统测试 ==={Style.RESET_ALL}")
    
    try:
        prefs_manager = test_preferences_system()
        test_interaction_system()
        
        print(f"\n{Fore.GREEN}✅ 所有测试通过！{Style.RESET_ALL}")
        
        # 显示配置文件位置
        print(f"\n{Fore.CYAN}配置文件位置:{Style.RESET_ALL}")
        print(f"偏好设置: {prefs_manager.preferences_file}")
        print(f"记忆路径: {prefs_manager.paths_file}")
        
    except Exception as e:
        print(f"{Fore.RED}❌ 测试失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
