"""
Day Translation 2 - 交互管理模块

提供统一的用户交互功能，包括：
- 菜单显示和用户输入
- 配置操作引导
- 操作结果显示
- 设置管理界面
"""

import sys
from pathlib import Path

try:
    # 尝试相对导入（包内使用）
    from .interaction_manager import UnifiedInteractionManager
except ImportError:
    # 备用绝对导入（独立运行时）
    # 添加interaction目录到sys.path
    interaction_dir = Path(__file__).parent
    if str(interaction_dir) not in sys.path:
        sys.path.insert(0, str(interaction_dir))

    from interaction_manager import UnifiedInteractionManager

__all__ = ["UnifiedInteractionManager"]
