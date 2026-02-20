"""
路径与键名规范化工具

- 统一反斜杠转正斜杠、相对路径字符串
- 供 extract、import_template、batch 等模块复用
"""

from pathlib import Path
from typing import List, Union

PathLike = Union[str, Path]


def normalize_slashes(s: str) -> str:
    """将路径字符串中的反斜杠统一为正斜杠并 strip。"""
    return (s or "").strip().replace("\\", "/")


def resolve_path(p: PathLike) -> Path:
    """解析为绝对路径。"""
    return Path(p).resolve()


def rel_path_str(base: PathLike, path: PathLike) -> str:
    """
    计算 path 相对于 base 的路径字符串（正斜杠）。
    若 path 与 base 相同则返回 "/"；若 path 不在 base 下则返回 path 的目录名或 "?"。
    """
    base_p = Path(base).resolve()
    path_p = Path(path).resolve()
    if path_p == base_p:
        return "/"
    try:
        return str(path_p.relative_to(base_p)).replace("\\", "/")
    except ValueError:
        return Path(path).name if Path(path).name else "?"


def key_to_dot_notation(key: str) -> str:
    """将 DefInjected 风格的 key（路径含 / 或 \\）转为点号形式。"""
    if not key:
        return key
    if "/" in key or "\\" in key:
        return normalize_slashes(key).replace("/", ".")
    return key


def compute_scan_labels_for_roots(roots: List[str], scan_base: str) -> List[str]:
    """
    为多个内容根计算显示标签（用于「扫描"xxx"下」）。
    根目录为 "/"，其它为相对 scan_base 的正斜杠路径。
    """
    return [rel_path_str(scan_base, r) for r in roots]
