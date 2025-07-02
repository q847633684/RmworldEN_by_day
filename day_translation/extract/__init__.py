"""
提取模板模块
提取翻译模板并生成CSV文件
"""

from .handler import handle_extract
from .extractors import extract_keyed_translations, scan_defs_sync, extract_definjected_translations
from .exporters import export_definjected_with_original_structure, export_definjected_with_defs_structure, export_definjected_with_file_structure, export_keyed_template
from .template_manager import TemplateManager
from .interaction_manager import InteractionManager

__all__ = [
    'handle_extract',
    'extract_keyed_translations', 
    'scan_defs_sync', 
    'extract_definjected_translations',
    'export_definjected_with_original_structure',
    'export_definjected_with_defs_structure',
    'export_definjected_with_file_structure',
    'export_keyed_template',
    'TemplateManager',
    'InteractionManager'
] 