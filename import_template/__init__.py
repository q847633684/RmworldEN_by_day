"""
导入模板模块
将翻译后的CSV导入翻译模板
"""

from .handler import handle_import_template
from .importers import update_translations

__all__ = [
    "handle_import_template",
    "update_translations",
]
