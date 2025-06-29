#!/usr/bin/env python3
"""
测试优化后的用户界面效果
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from day_translation.utils.interaction import show_welcome, show_main_menu

def demo_ui():
    """演示用户界面效果"""
    print("🎮 Day Translation 用户界面演示")
    print("=" * 50)
    
    # 演示欢迎界面
    print("\n📋 1. 欢迎界面演示：")
    show_welcome()
    
    # 演示主菜单
    print("\n📋 2. 主菜单演示：")
    show_main_menu()
    
    print("\n✅ 界面演示完成！")

if __name__ == "__main__":
    demo_ui() 