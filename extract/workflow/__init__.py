"""
工作流程模块

提供翻译提取的完整工作流程管理：
- manager: 模板管理器
- interaction: 提取专用交互管理器（与 utils.interaction 主菜单区分）
- handler: 主处理器
- rel_path_converter: Def rel_path 转换（def 路径 <-> def_type/def_type.xml）
"""

from .manager import TemplateManager
from .interaction import InteractionManager
from .handler import handle_extract

__all__ = [
    "TemplateManager",
    "InteractionManager",
    "handle_extract",
]
