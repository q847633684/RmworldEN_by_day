"""
配置基类

提供所有配置类的基础功能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from utils.logging_config import get_logger


class BaseConfig(ABC):
    """配置基类"""

    def __init__(self, name: str):
        """
        初始化配置

        Args:
            name: 配置名称
        """
        self.name = name
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._data: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {}
        self._loading = False  # 加载状态标志，防止递归保存
        self._required_fields: set = set()
        self._field_types: Dict[str, type] = {}

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        获取配置模式定义

        Returns:
            配置模式字典
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """
        验证配置是否有效

        Returns:
            是否有效
        """
        pass

    def set_value(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        # 类型检查
        if key in self._field_types:
            expected_type = self._field_types[key]
            if not isinstance(value, expected_type):
                try:
                    value = expected_type(value)
                except (ValueError, TypeError) as e:
                    self.logger.error(
                        f"配置值类型转换失败: {key}={value}, 期望类型: {expected_type}"
                    )
                    raise ValueError(f"配置值类型错误: {key}") from e

        # 检查值是否发生变化
        old_value = self._data.get(key)
        self._data[key] = value
        self.logger.debug(f"设置配置: {self.name}.{key} = {value}")

        # 如果值发生变化且不在加载状态，自动保存
        if old_value != value and not self._loading:
            self._auto_save()

    def _auto_save(self) -> None:
        """自动保存配置"""
        try:
            # 延迟导入避免循环依赖
            from user_config import UserConfigManager

            config_manager = UserConfigManager()
            config_manager.save_config()

            # 特殊处理：日志配置需要重新应用
            if self.name == "日志配置":
                try:
                    from utils.logging_config import LoggingConfig

                    LoggingConfig.reload_from_user_config()
                except Exception as e:
                    self.logger.warning(f"应用日志配置失败: {e}")

        except Exception as e:
            # 静默失败，避免影响用户操作
            self.logger.error(f"自动保存配置失败: {e}")

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._data.get(key, self._defaults.get(key, default))

    def has_value(self, key: str) -> bool:
        """
        检查是否有指定配置

        Args:
            key: 配置键

        Returns:
            是否存在
        """
        return key in self._data

    def remove_value(self, key: str) -> None:
        """
        删除配置值

        Args:
            key: 配置键
        """
        if key in self._data:
            del self._data[key]
            self.logger.debug(f"删除配置: {self.name}.{key}")

    def clear(self) -> None:
        """清空所有配置"""
        self._data.clear()
        self.logger.debug(f"清空配置: {self.name}")

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典，包含默认值和用户设置的值

        Returns:
            配置字典
        """
        # 合并默认值和用户设置的值
        result = self._defaults.copy()
        result.update(self._data)
        return result

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        从字典加载配置

        Args:
            data: 配置字典
        """
        self._loading = True  # 设置加载状态，防止自动保存
        try:
            for key, value in data.items():
                self.set_value(key, value)
            self.logger.debug(f"从字典加载配置: {self.name}")
        finally:
            self._loading = False  # 确保加载状态被重置

    def get_missing_required_fields(self) -> set:
        """
        获取缺失的必需字段

        Returns:
            缺失字段集合
        """
        return self._required_fields - set(self._data.keys())

    def is_complete(self) -> bool:
        """
        检查配置是否完整（所有必需字段都已设置）

        Returns:
            是否完整
        """
        return len(self.get_missing_required_fields()) == 0

    def reset_to_defaults(self) -> None:
        """重置为默认值"""
        self._data = self._defaults.copy()
        self.logger.debug(f"重置配置为默认值: {self.name}")

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(name='{self.name}', fields={len(self._data)})"
        )

    def __repr__(self) -> str:
        return self.__str__()
