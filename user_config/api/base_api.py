"""
API配置基类

所有翻译API配置的基础类
"""

from abc import abstractmethod
from typing import Any, Dict, Optional
from ..core.base_config import BaseConfig


class BaseAPIConfig(BaseConfig):
    """API配置基类"""

    def __init__(self, name: str, api_type: str):
        """
        初始化API配置

        Args:
            name: API名称
            api_type: API类型标识
        """
        super().__init__(name)
        self.api_type = api_type
        self.enabled = False

        # 通用API配置
        self._defaults.update(
            {
                "enabled": False,
                "timeout": 30,
                "max_retries": 3,
                "retry_delay": 1.0,
                "rate_limit": 10,  # 每秒请求数限制
            }
        )

        # 通用字段类型
        self._field_types.update(
            {
                "enabled": bool,
                "timeout": int,
                "max_retries": int,
                "retry_delay": float,
                "rate_limit": int,
            }
        )

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """
        测试API连接

        Returns:
            (是否成功, 错误信息)
        """
        pass

    @abstractmethod
    def get_auth_params(self) -> Dict[str, Any]:
        """
        获取认证参数

        Returns:
            认证参数字典
        """
        pass

    @abstractmethod
    def get_request_params(self) -> Dict[str, Any]:
        """
        获取请求参数

        Returns:
            请求参数字典
        """
        pass

    def is_enabled(self) -> bool:
        """
        检查API是否启用

        Returns:
            是否启用
        """
        return self.get_value("enabled", False)

    def set_enabled(self, enabled: bool) -> None:
        """
        设置API启用状态

        Args:
            enabled: 是否启用
        """
        self.set_value("enabled", enabled)

    def get_timeout(self) -> int:
        """
        获取超时时间

        Returns:
            超时时间（秒）
        """
        return self.get_value("timeout", 30)

    def get_max_retries(self) -> int:
        """
        获取最大重试次数

        Returns:
            最大重试次数
        """
        return self.get_value("max_retries", 3)

    def get_rate_limit(self) -> int:
        """
        获取速率限制

        Returns:
            每秒最大请求数
        """
        return self.get_value("rate_limit", 10)

    def validate(self) -> bool:
        """
        验证API配置

        Returns:
            是否有效
        """
        # 检查必需字段
        if not self.is_complete():
            missing = self.get_missing_required_fields()
            self.logger.error(f"API配置不完整，缺少字段: {missing}")
            return False

        # 检查数值范围
        timeout = self.get_timeout()
        if timeout < 1 or timeout > 300:
            self.logger.error(f"超时时间无效: {timeout}，应在1-300秒之间")
            return False

        max_retries = self.get_max_retries()
        if max_retries < 0 or max_retries > 10:
            self.logger.error(f"重试次数无效: {max_retries}，应在0-10之间")
            return False

        rate_limit = self.get_rate_limit()
        if rate_limit < 1 or rate_limit > 100:
            self.logger.error(f"速率限制无效: {rate_limit}，应在1-100之间")
            return False

        return True

    def get_display_info(self) -> Dict[str, Any]:
        """
        获取显示信息

        Returns:
            显示信息字典
        """
        return {
            "name": self.name,
            "type": self.api_type,
            "enabled": self.is_enabled(),
            "status": "已配置" if self.is_complete() else "未配置",
            "valid": self.validate(),
        }
