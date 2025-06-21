"""
历史记录服务模块

提供路径历史记录的管理功能，包括：
- 路径历史记录的添加、获取
- 最后使用路径的管理
- 记住路径的功能

Author: Day汉化项目
Created: 2024-12-19
"""

from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

from config.data_models import UnifiedConfig

logger = logging.getLogger(__name__)


class HistoryService:
    """历史记录服务

    管理路径历史记录、最后使用路径和记住路径的功能
    """

    def __init__(self, default_max_history: int = 10):
        """初始化历史记录服务

        Args:
            default_max_history: 默认最大历史记录长度
        """
        self.default_max_history = default_max_history

    def add_to_history(self, path_type: str, path: str, config: UnifiedConfig) -> None:
        """添加路径到历史记录

        Args:
            path_type: 路径类型（如 'mod_folder', 'source_file' 等）
            path: 要添加的路径
            config: 统一配置对象
        """
        try:
            # 确保路径类型存在
            if path_type not in config.user.path_history:
                config.user.path_history[path_type] = {
                    "paths": [],
                    "max_length": self.default_max_history,
                    "last_used": None,
                }

            history = config.user.path_history[path_type]

            # 如果路径已存在，先移除
            if path in history["paths"]:
                history["paths"].remove(path)

            # 添加到开头
            history["paths"].insert(0, path)

            # 限制历史记录长度
            max_length = history.get("max_length", self.default_max_history)
            if len(history["paths"]) > max_length:
                history["paths"] = history["paths"][:max_length]

            # 更新最后使用的路径
            history["last_used"] = path

            logger.debug(f"添加路径到历史记录: {path_type} -> {path}")

        except Exception as e:
            logger.error(f"添加历史记录失败: {path_type} -> {path}, 错误: {e}")
            raise

    def get_history(self, path_type: str, config: UnifiedConfig) -> List[str]:
        """获取路径历史记录

        Args:
            path_type: 路径类型
            config: 统一配置对象

        Returns:
            历史路径列表，按时间倒序排列
        """
        try:
            history_data = config.user.path_history.get(path_type, {})

            if isinstance(history_data, dict) and "paths" in history_data:
                paths = history_data["paths"]
                if isinstance(paths, list):
                    # 确保返回的是字符串列表，过滤掉None值
                    return [str(path) for path in paths if path is not None]

            return []

        except Exception as e:
            logger.error(f"获取历史记录失败: {path_type}, 错误: {e}")
            return []

    def get_last_used_path(self, path_type: str, config: UnifiedConfig) -> Optional[str]:
        """获取最后使用的路径

        Args:
            path_type: 路径类型
            config: 统一配置对象

        Returns:
            最后使用的路径，如果没有则返回None
        """
        try:
            history_data = config.user.path_history.get(path_type, {})

            if isinstance(history_data, dict) and "last_used" in history_data:
                last_used = history_data["last_used"]
                return str(last_used) if last_used is not None else None

            return None

        except Exception as e:
            logger.error(f"获取最后使用路径失败: {path_type}, 错误: {e}")
            return None

    def remember_path(self, path_type: str, path: str, config: UnifiedConfig) -> None:
        """记住路径

        将路径保存到记住路径列表中，用于快速访问

        Args:
            path_type: 路径类型
            path: 要记住的路径
            config: 统一配置对象
        """
        try:
            config.user.remembered_paths[path_type] = path
            logger.debug(f"记住路径: {path_type} -> {path}")

        except Exception as e:
            logger.error(f"记住路径失败: {path_type} -> {path}, 错误: {e}")
            raise

    def get_remembered_path(self, path_type: str, config: UnifiedConfig) -> Optional[str]:
        """获取记住的路径

        Args:
            path_type: 路径类型
            config: 统一配置对象

        Returns:
            记住的路径，如果没有则返回None
        """
        try:
            return config.user.remembered_paths.get(path_type)

        except Exception as e:
            logger.error(f"获取记住路径失败: {path_type}, 错误: {e}")
            return None

    def clear_history(self, path_type: str, config: UnifiedConfig) -> None:
        """清空指定类型的历史记录

        Args:
            path_type: 路径类型
            config: 统一配置对象
        """
        try:
            if path_type in config.user.path_history:
                config.user.path_history[path_type] = {
                    "paths": [],
                    "max_length": self.default_max_history,
                    "last_used": None,
                }
                logger.debug(f"清空历史记录: {path_type}")

        except Exception as e:
            logger.error(f"清空历史记录失败: {path_type}, 错误: {e}")
            raise

    def clear_all_history(self, config: UnifiedConfig) -> None:
        """清空所有历史记录

        Args:
            config: 统一配置对象
        """
        try:
            config.user.path_history.clear()
            logger.debug("清空所有历史记录")

        except Exception as e:
            logger.error(f"清空所有历史记录失败: {e}")
            raise

    def get_history_types(self, config: UnifiedConfig) -> List[str]:
        """获取所有历史记录类型

        Args:
            config: 统一配置对象

        Returns:
            历史记录类型列表
        """
        try:
            return list(config.user.path_history.keys())

        except Exception as e:
            logger.error(f"获取历史记录类型失败: {e}")
            return []

    def get_history_stats(self, config: UnifiedConfig) -> Dict[str, Any]:
        """获取历史记录统计信息

        Args:
            config: 统一配置对象

        Returns:
            历史记录统计信息
        """
        try:
            stats = {}

            for path_type, history_data in config.user.path_history.items():
                if isinstance(history_data, dict):
                    paths = history_data.get("paths", [])
                    stats[path_type] = {
                        "count": len(paths) if isinstance(paths, list) else 0,
                        "max_length": history_data.get("max_length", self.default_max_history),
                        "has_last_used": history_data.get("last_used") is not None,
                    }

            return stats

        except Exception as e:
            logger.error(f"获取历史记录统计失败: {e}")
            return {}

    def validate_and_clean_history(self, config: UnifiedConfig) -> None:
        """验证并清理历史记录

        移除无效的路径，整理历史记录结构

        Args:
            config: 统一配置对象
        """
        try:
            cleaned_count = 0

            for path_type, history_data in list(config.user.path_history.items()):
                if not isinstance(history_data, dict):
                    # 修复无效的历史记录结构
                    config.user.path_history[path_type] = {
                        "paths": [],
                        "max_length": self.default_max_history,
                        "last_used": None,
                    }
                    cleaned_count += 1
                    continue

                paths = history_data.get("paths", [])
                if isinstance(paths, list):
                    # 过滤掉无效路径
                    valid_paths = []
                    for path in paths:
                        if path and isinstance(path, str):
                            path_obj = Path(path)
                            if path_obj.exists():
                                valid_paths.append(path)
                            else:
                                cleaned_count += 1

                    history_data["paths"] = valid_paths

                    # 检查last_used是否还有效
                    last_used = history_data.get("last_used")
                    if last_used and last_used not in valid_paths:
                        history_data["last_used"] = valid_paths[0] if valid_paths else None
                        cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个无效的历史记录项")

        except Exception as e:
            logger.error(f"验证和清理历史记录失败: {e}")
            raise


# 单例实例
history_service = HistoryService()
