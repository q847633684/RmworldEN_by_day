#!/usr/bin/env python3
"""
测试智能输出目录功能的简单演示
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from day_translation.utils.unified_interaction_manager import UnifiedInteractionManager
from colorama import Fore, Style

def demo_smart_output_selection():
    """演示智能输出目录选择功能"""
    print(f"{Fore.BLUE}=== 智能输出目录选择演示 ==={Style.RESET_ALL}")
    print(f"这个功能会:")
    print(f"1. 检查目录是否存在")
    print(f"2. 如果目录有内容，显示内容信息")
    print(f"3. 提供合适的处理选项（合并、覆盖、备份等）")
    print(f"\n现在我们创建了一个测试目录 'test_output' 包含一个 CSV 文件")
    
    interaction_manager = UnifiedInteractionManager()
    
    # 测试1: 选择已存在且有内容的目录
    print(f"\n{Fore.YELLOW}测试场景1: 选择有内容的目录{Style.RESET_ALL}")
    print(f"请在提示时输入: test_output")
    
    try:
        # 这会触发智能目录选择
        result = interaction_manager._get_smart_output_directory("输出目录", "test_output")
        
        if result:
            output_dir, processing_mode = result
            print(f"\n{Fore.GREEN}✅ 智能选择结果:{Style.RESET_ALL}")
            print(f"   输出目录: {output_dir}")
            print(f"   处理模式: {processing_mode}")
            
            mode_desc = {
                'create': '创建新目录',
                'merge': '合并模式 - 保留现有文件',
                'overwrite': '覆盖模式 - 覆盖同名文件',
                'backup_overwrite': '备份覆盖 - 先备份再覆盖'
            }
            print(f"   模式说明: {mode_desc.get(processing_mode, '未知模式')}")
        else:
            print(f"{Fore.YELLOW}⚠️ 用户取消了选择{Style.RESET_ALL}")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ 用户中断操作{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ 测试出现异常: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    demo_smart_output_selection()
