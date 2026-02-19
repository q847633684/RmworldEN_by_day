"""
项目常量 - 集中管理硬编码路径等

支持通过环境变量覆盖默认值：
- RIMWORLD_MODS_PATH: 模组根目录，多个用 ; 分隔
- RIMWORLD_WORKSHOP_PATH: Workshop 目录，多个用 ; 分隔
"""

import os
from typing import List

# 常见 RimWorld 模组根目录（Steam 安装路径）
COMMON_MOD_PATHS: List[str] = [
    r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods",
    r"C:\Program Files\Steam\steamapps\common\RimWorld\Mods",
    r"D:\Steam\steamapps\common\RimWorld\Mods",
    r"D:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods",
    r"D:\Program Files\Steam\steamapps\common\RimWorld\Mods",
]

# Steam Workshop 模组路径（RimWorld AppID 294100）
STEAM_WORKSHOP_PATHS: List[str] = [
    r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100",
    r"C:\Program Files\Steam\steamapps\workshop\content\294100",
    r"D:\Steam\steamapps\workshop\content\294100",
    r"E:\Steam\steamapps\workshop\content\294100",
]


def get_common_mod_paths() -> List[str]:
    """获取模组根目录列表，支持环境变量 RIMWORLD_MODS_PATH 覆盖（多个用 ; 分隔）"""
    env = os.environ.get("RIMWORLD_MODS_PATH", "").strip()
    if env:
        return [p.strip() for p in env.split(";") if p.strip()]
    return COMMON_MOD_PATHS.copy()


def get_steam_workshop_paths() -> List[str]:
    """获取 Workshop 目录列表，支持环境变量 RIMWORLD_WORKSHOP_PATH 覆盖（多个用 ; 分隔）"""
    env = os.environ.get("RIMWORLD_WORKSHOP_PATH", "").strip()
    if env:
        return [p.strip() for p in env.split(";") if p.strip()]
    return STEAM_WORKSHOP_PATHS.copy()
