#!/usr/bin/env python3
"""
测试智能输出目录选择功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from day_translation.utils.unified_interaction_manager import UnifiedInteractionManager
from day_translation.utils.unified_config import get_config
from colorama import Fore, Style

def test_smart_output_directory():
    """测试智能输出目录选择功能"""
    print(f"{Fore.BLUE}=== 测试智能输出目录选择功能 ==={Style.RESET_ALL}")
    
    # 初始化
    interaction_manager = UnifiedInteractionManager()
    config = get_config()
    
    print(f"{Fore.GREEN}✅ 统一配置系统初始化成功{Style.RESET_ALL}")
    print(f"配置版本: {config.version}")
    
    # 测试智能输出目录选择
    print(f"\n{Fore.YELLOW}开始测试智能输出目录选择...{Style.RESET_ALL}")
    
    result = interaction_manager._get_smart_output_directory("测试输出目录", "test_output")
    
    if result:
        output_dir, processing_mode = result
        print(f"{Fore.GREEN}✅ 目录选择成功:{Style.RESET_ALL}")
        print(f"   输出目录: {output_dir}")
        print(f"   处理模式: {processing_mode}")
    else:
        print(f"{Fore.RED}❌ 用户取消或选择失败{Style.RESET_ALL}")

def test_extraction_preferences():
    """测试提取偏好配置"""
    print(f"\n{Fore.BLUE}=== 测试提取偏好配置 ==={Style.RESET_ALL}")
    
    interaction_manager = UnifiedInteractionManager()
    
    # 模拟模组目录
    test_mod_dir = r"C:\Users\q8476\Documents\我的工作\Day_汉化\mod"
    
    print(f"测试模组目录: {test_mod_dir}")
    
    if os.path.exists(test_mod_dir):
        print(f"{Fore.GREEN}✅ 测试模组目录存在{Style.RESET_ALL}")
        
        cancelled, config = interaction_manager._configure_extraction_preferences(test_mod_dir)
        
        if not cancelled:
            print(f"{Fore.GREEN}✅ 提取偏好配置成功:{Style.RESET_ALL}")
            for key, value in config.items():
                print(f"   {key}: {value}")
        else:
            print(f"{Fore.YELLOW}⚠️ 用户取消配置{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️ 测试模组目录不存在，跳过测试{Style.RESET_ALL}")

def main():
    """主测试函数"""
    print(f"{Fore.MAGENTA}=== Day Translation 智能输出目录功能测试 ==={Style.RESET_ALL}")
    
    try:
        # 测试智能输出目录选择
        test_smart_output_directory()
        
        # 测试提取偏好配置
        test_extraction_preferences()
        
        print(f"\n{Fore.GREEN}✅ 所有测试完成{Style.RESET_ALL}")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ 用户中断测试{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ 测试出现异常: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
