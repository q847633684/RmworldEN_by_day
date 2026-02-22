"""
翻译 API 配置工具
供 handler 和各类翻译器统一获取、校验主 API。
"""

from typing import Optional, Tuple


def get_primary_api():
    """从配置获取主翻译 API，不可用则返回 None。"""
    from user_config import UserConfigManager

    config = UserConfigManager.get_instance()
    return config.api_manager.get_primary_api()


def get_validated_primary_api() -> Tuple[Optional[object], Optional[str]]:
    """
    获取并校验主翻译 API。
    Returns: (primary_api, None) 若可用；否则 (None, error_message)。
    """
    api = get_primary_api()
    if not api or not api.is_enabled():
        return None, "未找到启用的翻译API配置"
    if not api.validate():
        return None, f"{api.name}配置不完整或无效"
    return api, None
