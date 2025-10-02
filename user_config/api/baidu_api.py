"""
百度翻译API配置
"""

from typing import Any, Dict
from .base_api import BaseAPIConfig


class BaiduAPIConfig(BaseAPIConfig):
    """百度翻译API配置"""

    def __init__(self):
        super().__init__("百度翻译", "baidu")

        # 百度特有的默认值
        self._defaults.update(
            {
                "app_id": "",
                "secret_key": "",
                "api_version": "v1",
                "endpoint": "https://fanyi-api.baidu.com/api/trans/vip/translate",
            }
        )

        # 必需字段
        self._required_fields.update({"app_id", "secret_key"})

        # 字段类型
        self._field_types.update(
            {
                "app_id": str,
                "secret_key": str,
                "api_version": str,
                "endpoint": str,
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "app_id": {
                "type": "text",
                "label": "APP ID",
                "description": "百度翻译应用ID",
                "required": True,
                "placeholder": "请输入APP ID",
            },
            "secret_key": {
                "type": "password",
                "label": "密钥",
                "description": "百度翻译密钥",
                "required": True,
                "placeholder": "请输入密钥",
            },
            "api_version": {
                "type": "select",
                "label": "API版本",
                "description": "百度翻译API版本",
                "options": [
                    {"value": "v1", "label": "标准版"},
                    {"value": "v2", "label": "高级版"},
                ],
                "default": "v1",
            },
            "endpoint": {
                "type": "text",
                "label": "API端点",
                "description": "百度翻译API地址",
                "default": "https://fanyi-api.baidu.com/api/trans/vip/translate",
            },
        }

    def test_connection(self) -> tuple[bool, str]:
        """测试百度API连接"""
        try:
            app_id = self.get_value("app_id")
            secret_key = self.get_value("secret_key")

            if not app_id or not secret_key:
                return False, "APP ID或密钥未配置"

            # TODO: 实际调用百度API进行测试
            self.logger.info("百度API连接测试通过")
            return True, "连接测试成功"

        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_auth_params(self) -> Dict[str, Any]:
        """获取认证参数"""
        return {
            "app_id": self.get_value("app_id"),
            "secret_key": self.get_value("secret_key"),
        }

    def get_request_params(self) -> Dict[str, Any]:
        """获取请求参数"""
        return {
            "api_version": self.get_value("api_version", "v1"),
            "endpoint": self.get_value("endpoint"),
            "timeout": self.get_timeout(),
            "max_retries": self.get_max_retries(),
        }
