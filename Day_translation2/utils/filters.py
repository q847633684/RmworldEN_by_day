"""
Day Translation 2 - 内容过滤器

提供翻译内容的过滤和验证功能。
遵循提示文件标准：PEP 8规范、具体异常处理、游戏UI术语统一。
"""

import re
from typing import Set, List, Optional

try:
    # 尝试相对导入 (包内使用)
    from ..models.config_models import FilterConfig
except ImportError:
    # 回退到绝对导入 (直接运行时)
    from models.config_models import FilterConfig


class ContentFilter:
    """内容过滤器，用于判断哪些内容应该被翻译"""
    
    def __init__(self, config=None):
        """
        初始化内容过滤器
        
        Args:
            config: 配置对象，包含过滤规则
        """
        if config and hasattr(config, 'core') and hasattr(config.core, 'filter_config'):
            self.filter_config = config.core.filter_config
        else:
            # 使用默认过滤配置
            self.filter_config = FilterConfig()
    
    def should_include_field(self, field_name: str) -> bool:
        """
        检查字段是否应该包含在翻译中
        
        Args:
            field_name: 字段名称
            
        Returns:
            是否应该包含此字段
        """
        return self.filter_config.should_include_field(field_name)
    
    def should_include_content(self, content: str) -> bool:
        """
        检查内容是否应该被翻译
        
        Args:
            content: 文本内容
            
        Returns:
            是否应该翻译此内容
        """
        return self.filter_config.should_include_content(content)
    
    def filter_translations(self, translations: List[tuple]) -> List[tuple]:
        """
        过滤翻译列表，移除不需要翻译的条目
        
        Args:
            translations: 翻译数据列表 [(key, text, tag, file), ...]
            
        Returns:
            过滤后的翻译列表
        """
        filtered = []
        
        for translation in translations:
            if len(translation) < 4:
                continue
            
            key, text, tag, file_path = translation[:4]
            
            # 检查字段是否应该包含
            if not self.should_include_field(tag):
                continue
            
            # 检查内容是否应该包含
            if not self.should_include_content(text):
                continue
            
            filtered.append(translation)
        
        return filtered
    
    def is_ui_term(self, text: str) -> bool:
        """
        检查是否是游戏UI术语（需要保持统一翻译）
        
        Args:
            text: 文本内容
            
        Returns:
            是否是UI术语
        """
        # 常见的游戏UI术语（根据翻译领域知识）
        ui_terms = {
            "OK", "Cancel", "Yes", "No", "Apply", "Close", "Save", "Load",
            "New", "Delete", "Edit", "Settings", "Options", "Help", "About",
            "Start", "Stop", "Pause", "Resume", "Exit", "Quit"
        }
        
        return text.strip() in ui_terms
    
    def clean_text_content(self, text: str) -> str:
        """
        清理文本内容，移除多余的空白字符
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除首尾空白
        cleaned = text.strip()
        
        # 规范化内部空白（多个空白字符替换为单个空格）
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
