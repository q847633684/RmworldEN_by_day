"""
文本验证器模块

提供各种文本验证和规范化功能
"""

import re
from utils.logging_config import get_logger
from user_config import UserConfigManager


def is_non_text(text: str) -> bool:
    """
    检查文本是否为非文本内容

    Args:
        text: 要检查的文本

    Returns:
        bool: 如果是非文本内容返回True
    """
    if not text or not isinstance(text, str):
        return True
    if text.isspace():
        return True
    if re.match(r"^\d+$", text):
        return True
    if re.match(r"^[0-9\.\-\+]+$", text):
        return True

    # 从配置中获取非文本模式进行检查 - 添加安全检查
    try:
        config_manager = UserConfigManager()
        patterns = config_manager.system_config.get_non_text_patterns()
        if patterns and hasattr(patterns, "__iter__"):
            for pattern in patterns:
                if isinstance(pattern, str) and re.match(pattern, text):
                    return True
    except (re.error, TypeError, AttributeError) as e:
        # 使用 get_logger 获取 logger 实例
        logger = get_logger(__name__)
        logger.warning("检查非文本模式时出错: %s", e)
    return False


def is_valid_translation_text(text: str) -> bool:
    """
    检查文本是否为有效的翻译文本

    Args:
        text: 要检查的文本

    Returns:
        bool: 如果是有效的翻译文本返回True
    """
    if not text or not isinstance(text, str):
        return False

    # 检查是否为空或只包含空白字符
    if not text.strip():
        return False

    # 检查是否为非文本内容
    if is_non_text(text):
        return False

    # 检查长度是否合理（太短或太长都不适合翻译）
    if len(text.strip()) < 2 or len(text.strip()) > 1000:
        return False

    return True


def normalize_text(text: str) -> str:
    """
    规范化文本内容

    Args:
        text: 要规范化的文本

    Returns:
        str: 规范化后的文本
    """
    if not text or not isinstance(text, str):
        return ""

    # 去除首尾空白字符
    normalized = text.strip()

    # 规范化空白字符（多个连续空白字符替换为单个空格）
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized
