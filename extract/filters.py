"""
RimWorld 翻译内容过滤器

提供智能的内容过滤功能，确保只提取真正需要翻译的内容：

主要组件：
- ContentFilter 类：核心过滤器，支持多种过滤规则
- is_non_text() 函数：检查文本是否为非文本内容

过滤规则：
1. 非文本内容过滤
   - 纯数字、纯符号、空白字符
   - 基于正则表达式的模式匹配

2. 字段过滤
   - 忽略字段列表：排除不需要翻译的字段
   - 默认字段检查：DefInjected 上下文中只处理指定字段

3. 上下文相关过滤
   - DefInjected 模式：严格按默认字段过滤
   - Keyed 模式：宽松过滤，支持自定义标签

主要功能：
- filter_content(): 核心过滤方法
- 支持多种过滤策略的组合使用
- 提供详细的过滤日志和调试信息
- 与配置系统集成，支持动态规则调整
"""

import re
from utils.logging_config import get_logger
from utils.config import get_config


def is_non_text(text: str) -> bool:
    """检查文本是否为非文本内容"""
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
        config = get_config()
        patterns = config.non_text_patterns
        if patterns and hasattr(patterns, "__iter__"):
            for pattern in patterns:
                if isinstance(pattern, str) and re.match(pattern, text):
                    return True
    except (re.error, TypeError, AttributeError) as e:
        # 使用 get_logger 获取 logger 实例
        logger = get_logger(__name__)
        logger.warning("检查非文本模式时出错: %s", e)
    return False


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
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        if config is None:
            config = get_config()
        self.config = config  # 调用属性方法获取实际值，而不是方法对象
        self.default_fields = config.default_fields  # 这会调用 @property 方法
        self.ignore_fields = config.ignore_fields  # 这会调用 @property 方法
        self.non_text_patterns = config.non_text_patterns  # 这会调用 @property 方法

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
        parts = key.split(".")
        tag = key  # 默认值

        # 从后往前遍历，找到第一个非数字的部分
        for i in range(len(parts) - 1, -1, -1):
            if not parts[i].isdigit():
                tag = parts[i]
                break

        # 安全检查 ignore_fields
        try:
            ignore_fields = self.ignore_fields
            if hasattr(ignore_fields, "__contains__") and tag in ignore_fields:
                self.logger.debug("过滤掉（%s）: 标签（%s）在忽略字段中", key, tag)
                return False
        except (AttributeError, TypeError) as e:
            self.logger.warning("检查忽略字段时出错: %s", e)

        # 对于 Keyed 翻译，不限制 default_fields，因为 Keyed 使用自定义标签名
        # 对于 DefInjected 翻译，才检查 default_fields
        if context == "DefInjected":
            try:
                default_fields = self.default_fields
                if (
                    default_fields
                    and hasattr(default_fields, "__contains__")
                    and tag not in default_fields
                ):
                    self.logger.debug(
                        "过滤掉（%s）: DefInjected 中字段 %s 未在默认字段中", key, tag
                    )
                    return False
            except (AttributeError, TypeError) as e:
                self.logger.warning("检查默认字段时出错: %s", e)

        # 安全检查非文本模式
        try:
            patterns = self.non_text_patterns
            if hasattr(patterns, "__iter__"):
                for pattern in patterns:
                    if isinstance(pattern, str) and re.match(pattern, text):
                        self.logger.debug(
                            "过滤掉（%s）: 文本（%s）匹配非文本模式", key, text
                        )
                        return False
        except (re.error, AttributeError, TypeError) as e:
            self.logger.warning("检查非文本模式时出错: %s", e)

        return True
