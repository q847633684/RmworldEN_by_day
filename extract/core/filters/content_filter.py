"""
内容过滤器

提供智能的内容过滤功能，确保只提取真正需要翻译的内容
"""

import re
from utils.logging_config import get_logger
from user_config import UserConfigManager
from .text_validator import is_non_text


class ContentFilter:
    """
    翻译内容过滤器

    用于过滤可翻译的内容，支持：
    - 非文本内容过滤
    - 忽略字段过滤
    - 默认字段检查（DefInjected 上下文）
    - 非文本模式匹配
    """

    def __init__(self, config=None):
        """
        初始化内容过滤器

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        self.logger = get_logger(f"{__name__}.ContentFilter")
        if config is None:
            config = UserConfigManager()
        self.config = config
        # 直接使用新配置系统
        self.default_fields = config.system_config.get_translation_fields()
        self.ignore_fields = config.system_config.get_ignore_fields()
        self.non_text_patterns = config.system_config.get_non_text_patterns()

    def filter_content(self, key: str, text: str, context: str = "") -> bool:
        """
        过滤可翻译内容

        Args:
            key (str): 翻译键名
            text (str): 翻译文本内容
            context (str): 上下文类型，如 "DefInjected" 或 "Keyed"

        Returns:
            bool: True 表示内容需要翻译，False 表示应该过滤掉
        """
        if not text or not isinstance(text, str):
            self.logger.debug("过滤掉（%s）: 文本为空或非字符串", key)
            return False

        if is_non_text(text):
            self.logger.debug("过滤掉（%s）: 文本（%s）为非文本内容", key, text)
            return False

        # 智能提取字段名：从后往前找到第一个非数字的部分
        tag = self._extract_field_name(key)

        # 检查忽略字段
        if self._check_ignore_fields(tag):
            self.logger.debug("过滤掉（%s）: 标签（%s）在忽略字段中", key, tag)
            return False

        # 对于 Keyed 翻译，不限制 default_fields，因为 Keyed 使用自定义标签名
        # 对于 DefInjected 翻译，才检查 default_fields
        if context == "DefInjected":
            if not self._check_default_fields(tag):
                self.logger.debug(
                    "过滤掉（%s）: DefInjected 中字段 %s 未在默认字段中", key, tag
                )
                return False

        # 检查非文本模式
        if self._check_non_text_patterns(text):
            self.logger.debug("过滤掉（%s）: 文本（%s）匹配非文本模式", key, text)
            return False

        return True

    def _extract_field_name(self, key: str) -> str:
        """
        从key中提取字段名

        Args:
            key: 翻译键名

        Returns:
            str: 提取的字段名
        """
        parts = key.split(".")

        # 从后往前遍历，找到第一个非数字的部分
        for i in range(len(parts) - 1, -1, -1):
            if not parts[i].isdigit():
                return parts[i]

        return key  # 默认值

    def _check_ignore_fields(self, tag: str) -> bool:
        """
        检查字段是否在忽略列表中

        Args:
            tag: 字段标签

        Returns:
            bool: 如果在忽略列表中返回True
        """
        try:
            if (
                hasattr(self.ignore_fields, "__contains__")
                and tag in self.ignore_fields
            ):
                return True
        except (AttributeError, TypeError) as e:
            self.logger.warning("检查忽略字段时出错: %s", e)
        return False

    def _check_default_fields(self, tag: str) -> bool:
        """
        检查字段是否在默认字段列表中

        Args:
            tag: 字段标签

        Returns:
            bool: 如果在默认字段列表中返回True
        """
        try:
            if (
                self.default_fields
                and hasattr(self.default_fields, "__contains__")
                and tag in self.default_fields
            ):
                return True
        except (AttributeError, TypeError) as e:
            self.logger.warning("检查默认字段时出错: %s", e)
        return False

    def _check_non_text_patterns(self, text: str) -> bool:
        """
        检查文本是否匹配非文本模式

        Args:
            text: 要检查的文本

        Returns:
            bool: 如果匹配非文本模式返回True
        """
        try:
            if hasattr(self.non_text_patterns, "__iter__"):
                for pattern in self.non_text_patterns:
                    if isinstance(pattern, str) and re.match(pattern, text):
                        return True
        except (re.error, AttributeError, TypeError) as e:
            self.logger.warning("检查非文本模式时出错: %s", e)
        return False
