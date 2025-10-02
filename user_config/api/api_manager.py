"""
API管理器

管理所有翻译API的配置和使用
"""

from typing import Dict, List, Optional, Any
from utils.logging_config import get_logger
from .aliyun_api import AliyunAPIConfig
from .baidu_api import BaiduAPIConfig
from .tencent_api import TencentAPIConfig
from .google_api import GoogleAPIConfig
from .custom_api import CustomAPIConfig
from .base_api import BaseAPIConfig


class APIManager:
    """API管理器"""

    def __init__(self):
        """初始化API管理器"""
        self.logger = get_logger(f"{__name__}.APIManager")

        # 初始化所有支持的API
        self.apis: Dict[str, BaseAPIConfig] = {
            "aliyun": AliyunAPIConfig(),
            "baidu": BaiduAPIConfig(),
            "tencent": TencentAPIConfig(),
            "google": GoogleAPIConfig(),
            "custom": CustomAPIConfig(),
        }

        # 管理设置
        self.default_api = "aliyun"
        self.failover_enabled = True
        # 注意：由于目前只有阿里云有翻译工具实现，负载均衡实际上是故障转移
        self.load_balancing = "priority"  # priority(推荐), round_robin, random
        self.current_api_index = 0  # 用于轮询

        # 定义有翻译工具支持的API类型
        self.supported_apis = {"aliyun"}  # 目前只有阿里云有翻译工具实现
        # TODO: 当实现其他API的翻译工具时，添加到此集合中

        self.logger.info("API管理器初始化完成")

    def get_api(self, api_type: str) -> Optional[BaseAPIConfig]:
        """
        获取指定类型的API配置

        Args:
            api_type: API类型

        Returns:
            API配置对象
        """
        return self.apis.get(api_type)

    def get_all_apis(self) -> Dict[str, BaseAPIConfig]:
        """
        获取所有API配置

        Returns:
            所有API配置字典
        """
        return self.apis.copy()

    def get_supported_apis(self) -> Dict[str, BaseAPIConfig]:
        """
        获取有翻译工具支持的API配置

        Returns:
            支持的API配置字典
        """
        return {
            api_type: api_config
            for api_type, api_config in self.apis.items()
            if api_type in self.supported_apis
        }

    def is_api_supported(self, api_type: str) -> bool:
        """
        检查API是否有翻译工具支持

        Args:
            api_type: API类型

        Returns:
            是否支持
        """
        return api_type in self.supported_apis

    def get_enabled_apis(self) -> List[BaseAPIConfig]:
        """
        获取已启用且有翻译工具支持的API列表

        Returns:
            已启用且支持的API列表，按优先级排序
        """
        enabled = [
            api
            for api_type, api in self.apis.items()
            if api.is_enabled() and api_type in self.supported_apis
        ]
        # 按优先级排序（数字越小优先级越高）
        enabled.sort(key=lambda x: x.get_priority())
        return enabled

    def get_primary_api(self) -> Optional[BaseAPIConfig]:
        """
        获取主要API（只返回有翻译工具支持的API）

        Returns:
            主要API配置对象
        """
        # 首先尝试获取默认API（必须是支持的API）
        default_api = self.apis.get(self.default_api)
        if (
            default_api
            and default_api.is_enabled()
            and default_api.validate()
            and self.is_api_supported(self.default_api)
        ):
            return default_api

        # 如果默认API不可用，获取第一个可用且支持的API
        enabled_apis = self.get_enabled_apis()  # 已经过滤了支持的API
        for api in enabled_apis:
            if api.validate():
                return api

        return None

    def get_next_api(self) -> Optional[BaseAPIConfig]:
        """
        根据负载均衡策略获取下一个API

        注意：由于目前只有阿里云有翻译工具支持，此方法实际上等同于get_primary_api()

        Returns:
            下一个API配置对象
        """
        enabled_apis = self.get_enabled_apis()
        if not enabled_apis:
            return None

        if self.load_balancing == "priority":
            # 优先级模式：总是返回优先级最高的可用API
            for api in enabled_apis:
                if api.validate():
                    return api

        elif self.load_balancing == "round_robin":
            # 轮询模式：依次使用每个API
            if enabled_apis:
                api = enabled_apis[self.current_api_index % len(enabled_apis)]
                self.current_api_index += 1
                return api

        elif self.load_balancing == "random":
            # 随机模式：随机选择一个API
            import random

            return random.choice(enabled_apis)

        return None

    def test_api(self, api_type: str) -> tuple[bool, str]:
        """
        测试指定API的连接

        Args:
            api_type: API类型

        Returns:
            (是否成功, 结果信息)
        """
        api = self.get_api(api_type)
        if not api:
            return False, f"未找到API类型: {api_type}"

        if not api.is_enabled():
            return False, f"API未启用: {api_type}"

        return api.test_connection()

    def test_all_apis(self) -> Dict[str, tuple[bool, str]]:
        """
        测试所有已启用API的连接

        Returns:
            测试结果字典
        """
        results = {}
        for api_type, api in self.apis.items():
            if api.is_enabled():
                results[api_type] = api.test_connection()
            else:
                results[api_type] = (False, "API未启用")

        return results

    def set_default_api(self, api_type: str) -> bool:
        """
        设置默认API

        Args:c
            api_type: API类型

        Returns:
            是否设置成功
        """
        if api_type not in self.apis:
            self.logger.error(f"无效的API类型: {api_type}")
            return False

        self.default_api = api_type
        self.logger.info(f"设置默认API: {api_type}")
        return True

    def enable_api(self, api_type: str) -> bool:
        """
        启用API

        Args:
            api_type: API类型

        Returns:
            是否启用成功
        """
        api = self.get_api(api_type)
        if not api:
            return False

        api.set_enabled(True)
        self.logger.info(f"启用API: {api_type}")
        return True

    def disable_api(self, api_type: str) -> bool:
        """
        禁用API

        Args:
            api_type: API类型

        Returns:
            是否禁用成功
        """
        api = self.get_api(api_type)
        if not api:
            return False

        api.set_enabled(False)
        self.logger.info(f"禁用API: {api_type}")
        return True

    def set_api_priority(self, api_type: str, priority: int) -> bool:
        """
        设置API优先级

        Args:
            api_type: API类型
            priority: 优先级（数字越小优先级越高）

        Returns:
            是否设置成功
        """
        api = self.get_api(api_type)
        if not api:
            return False

        api.set_priority(priority)
        self.logger.info(f"设置API优先级: {api_type} = {priority}")
        return True

    def get_api_status(self) -> Dict[str, Any]:
        """
        获取所有API的状态信息

        Returns:
            API状态信息字典
        """
        status = {
            "default_api": self.default_api,
            "failover_enabled": self.failover_enabled,
            "load_balancing": self.load_balancing,
            "supported_apis": list(self.supported_apis),
            "apis": {},
        }

        for api_type, api in self.apis.items():
            api_info = api.get_display_info()
            api_info["translator_supported"] = self.is_api_supported(api_type)
            status["apis"][api_type] = api_info

        return status

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            配置字典
        """
        return {
            "default_api": self.default_api,
            "failover_enabled": self.failover_enabled,
            "load_balancing": self.load_balancing,
            "apis": {api_type: api.to_dict() for api_type, api in self.apis.items()},
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        从字典加载配置

        Args:
            data: 配置字典
        """
        self.default_api = data.get("default_api", "aliyun")
        self.failover_enabled = data.get("failover_enabled", True)
        self.load_balancing = data.get("load_balancing", "priority")

        apis_data = data.get("apis", {})
        for api_type, api_data in apis_data.items():
            if api_type in self.apis:
                self.apis[api_type].from_dict(api_data)

        self.logger.info("从字典加载API配置完成")
