"""
工作流程模块

提供翻译提取的完整工作流程管理：
- manager: 模板管理器
- interaction: 交互管理器
- handler: 主处理器
"""

from .manager import TemplateManager
from .interaction import InteractionManager
from .handler import handle_extract

__all__ = [
    "TemplateManager",
    "InteractionManager",
    "handle_extract",
]
