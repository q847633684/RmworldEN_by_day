import re
from typing import Optional
import logging
from .config import get_config
from colorama import Fore, Style

def is_non_text(text: str) -> bool:
    """检查文本是否为非文本内容"""
    if not text or not isinstance(text, str):
        return True
    if text.isspace():
        return True
    if re.match(r'^\d+$', text):
        return True
    if re.match(r'^[0-9\.\-\+]+$', text):
        return True
    
    # 从配置中获取非文本模式进行检查 - 添加安全检查
    try:
        config = get_config()
        patterns = config.non_text_patterns
        if patterns and hasattr(patterns, '__iter__'):
            for pattern in patterns:
                if isinstance(pattern, str) and re.match(pattern, text):
                    return True
    except Exception as e:
        logging.warning(f"检查非文本模式时出错: {e}")
    return False

class ContentFilter:
    def __init__(self, config=None):
        if config is None:
            config = get_config()
        self.config = config        # 调用属性方法获取实际值，而不是方法对象
        self.default_fields = config.default_fields  # 这会调用 @property 方法
        self.ignore_fields = config.ignore_fields    # 这会调用 @property 方法
        self.non_text_patterns = config.non_text_patterns  # 这会调用 @property 方法
    
    def filter_content(self, key: str, text: str, context: str = "") -> bool:
        """过滤可翻译内容"""
        if not text or not isinstance(text, str):
            logging.debug(f"过滤掉（{key}）: 文本为空或非字符串")
            return False
        if is_non_text(text):
            logging.debug(f"过滤掉（{key}）: 文本（{text}）为非文本内容")
            return False        # 改进字段名提取逻辑，支持嵌套字段
        key_parts = key.split('.')
        # 获取最后一个非数字的部分作为字段名，或者倒数第二个部分
        tag = key_parts[-1]
        if tag.isdigit() and len(key_parts) > 1:
            tag = key_parts[-2]  # 如果最后一个是数字索引，使用倒数第二个
          # 如果是嵌套字段，也检查上级字段名
        parent_tags = []
        if len(key_parts) > 2:
            # 获取所有可能的父级字段名（不包含已选中的tag）
            for i in range(1, len(key_parts) - 1):  # 排除defName(第0个)和最后一个
                part = key_parts[i]
                if not part.isdigit() and part != tag:  # 排除数字索引和重复的tag
                    parent_tags.append(part)
        
        # 安全检查 ignore_fields
        try:
            ignore_fields = self.ignore_fields
            if hasattr(ignore_fields, '__contains__') and tag in ignore_fields:
                logging.debug(f"过滤掉（{key}）: 标签（{tag}）在忽略字段中")
                return False
        except Exception as e:
            logging.warning(f"检查忽略字段时出错: {e}")
          # 对于 Keyed 翻译，不限制 default_fields，因为 Keyed 使用自定义标签名
        # 对于 DefInjected 翻译，才检查 default_fields
        if context == "DefInjected":
            try:
                default_fields = self.default_fields
                if default_fields and hasattr(default_fields, '__contains__'):
                    # 检查主字段名或任何父级字段是否在默认字段中
                    field_found = tag in default_fields
                    if not field_found and parent_tags:
                        field_found = any(parent_tag in default_fields for parent_tag in parent_tags)
                    
                    if not field_found:
                        logging.debug(f"过滤掉（{key}）: DefInjected 中字段 {tag} 及父级字段 {parent_tags} 均未在默认字段中")
                        return False
            except Exception as e:
                logging.warning(f"检查默认字段时出错: {e}")
        
        # 安全检查非文本模式
        try:
            patterns = self.non_text_patterns
            if hasattr(patterns, '__iter__'):
                for pattern in patterns:
                    if isinstance(pattern, str) and re.match(pattern, text):
                        logging.debug(f"过滤掉（{key}）: 文本（{text}）匹配非文本模式")
                        return False
        except Exception as e:
            logging.warning(f"检查非文本模式时出错: {e}")
            
        return True