"""
版本号解析与判断，供 path_manager、extract、batch 等复用。
"""
import re


def is_version_number(name: str) -> bool:
    """
    判断字符串是否为版本号格式（如 1.5、1.6、v1.5、1.5.0）。

    Args:
        name: 目录名或标签

    Returns:
        是否为版本号格式
    """
    if not name or not name.strip():
        return False
    pattern = r"^v?(\d+\.)+\d+$"
    return bool(re.match(pattern, name.strip()))


def parse_version_number(version_str: str) -> tuple:
    """
    解析版本号字符串为可比较的元组，用于排序。

    Args:
        version_str: 如 "1.6"、"v1.5"

    Returns:
        如 (1, 6)、(1, 5)；解析失败返回 (0,)。
    """
    try:
        clean = version_str.strip().lower()
        if clean.startswith("v"):
            clean = clean[1:]
        parts = [int(p) for p in clean.split(".")]
        return tuple(parts)
    except (ValueError, TypeError):
        return (0,)
