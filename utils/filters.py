import re
import logging
from .config import get_config


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
        logging.warning("检查非文本模式时出错: %s", e)
    return False


class ContentFilter:
    def __init__(self, config=None):
        if config is None:
            config = get_config()
        self.config = config  # 调用属性方法获取实际值，而不是方法对象
        self.default_fields = config.default_fields  # 这会调用 @property 方法
        self.ignore_fields = config.ignore_fields  # 这会调用 @property 方法
        self.non_text_patterns = config.non_text_patterns  # 这会调用 @property 方法

    def filter_content(self, key: str, text: str, context: str = "") -> bool:
        """过滤可翻译内容"""
        if not text or not isinstance(text, str):
            logging.debug("过滤掉（%s）: 文本为空或非字符串", key)
            return False
        if is_non_text(text):
            logging.debug("过滤掉（%s）: 文本（%s）为非文本内容", key, text)
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
                logging.debug("过滤掉（%s）: 标签（%s）在忽略字段中", key, tag)
                return False
        except (AttributeError, TypeError) as e:
            logging.warning("检查忽略字段时出错: %s", e)

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
                    logging.debug(
                        "过滤掉（%s）: DefInjected 中字段 %s 未在默认字段中", key, tag
                    )
                    return False
            except (AttributeError, TypeError) as e:
                logging.warning("检查默认字段时出错: %s", e)

        # 安全检查非文本模式
        try:
            patterns = self.non_text_patterns
            if hasattr(patterns, "__iter__"):
                for pattern in patterns:
                    if isinstance(pattern, str) and re.match(pattern, text):
                        logging.debug(
                            "过滤掉（%s）: 文本（%s）匹配非文本模式", key, text
                        )
                        return False
        except (re.error, AttributeError, TypeError) as e:
            logging.warning("检查非文本模式时出错: %s", e)

        return True
