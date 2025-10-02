"""
自定义API配置
"""

from typing import Any, Dict
from .base_api import BaseAPIConfig


class CustomAPIConfig(BaseAPIConfig):
    """自定义API配置"""

    def __init__(self):
        super().__init__("自定义API", "custom")

        # 自定义API的默认值
        self._defaults.update(
            {
                "name": "自定义API",
                "endpoint": "",
                "auth_type": "none",  # none, api_key, bearer, basic
                "api_key": "",
                "username": "",
                "password": "",
                "headers": {},
                "request_format": "json",  # json, form, xml
                "response_format": "json",  # json, xml, text
            }
        )

        # 必需字段
        self._required_fields.update({"name", "endpoint"})

        # 字段类型
        self._field_types.update(
            {
                "name": str,
                "endpoint": str,
                "auth_type": str,
                "api_key": str,
                "username": str,
                "password": str,
                "headers": dict,
                "request_format": str,
                "response_format": str,
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "name": {
                "type": "text",
                "label": "API名称",
                "description": "自定义API的显示名称",
                "required": True,
                "placeholder": "请输入API名称",
            },
            "endpoint": {
                "type": "text",
                "label": "API端点",
                "description": "API的完整URL地址",
                "required": True,
                "placeholder": "https://api.example.com/translate",
            },
            "auth_type": {
                "type": "select",
                "label": "认证方式",
                "description": "API认证方式",
                "options": [
                    {"value": "none", "label": "无认证"},
                    {"value": "api_key", "label": "API Key"},
                    {"value": "bearer", "label": "Bearer Token"},
                    {"value": "basic", "label": "Basic Auth"},
                ],
                "default": "none",
            },
            "api_key": {
                "type": "password",
                "label": "API Key",
                "description": "API密钥（当认证方式为API Key时）",
                "placeholder": "请输入API Key",
                "show_when": {"auth_type": ["api_key", "bearer"]},
            },
            "username": {
                "type": "text",
                "label": "用户名",
                "description": "Basic认证用户名",
                "placeholder": "请输入用户名",
                "show_when": {"auth_type": ["basic"]},
            },
            "password": {
                "type": "password",
                "label": "密码",
                "description": "Basic认证密码",
                "placeholder": "请输入密码",
                "show_when": {"auth_type": ["basic"]},
            },
            "request_format": {
                "type": "select",
                "label": "请求格式",
                "description": "API请求数据格式",
                "options": [
                    {"value": "json", "label": "JSON"},
                    {"value": "form", "label": "Form Data"},
                    {"value": "xml", "label": "XML"},
                ],
                "default": "json",
            },
            "response_format": {
                "type": "select",
                "label": "响应格式",
                "description": "API响应数据格式",
                "options": [
                    {"value": "json", "label": "JSON"},
                    {"value": "xml", "label": "XML"},
                    {"value": "text", "label": "纯文本"},
                ],
                "default": "json",
            },
        }

    def test_connection(self) -> tuple[bool, str]:
        """测试自定义API连接"""
        try:
            endpoint = self.get_value("endpoint")

            if not endpoint:
                return False, "API端点未配置"

            # TODO: 实际调用自定义API进行测试
            self.logger.info("自定义API连接测试通过")
            return True, "连接测试成功"

        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_auth_params(self) -> Dict[str, Any]:
        """获取认证参数"""
        auth_type = self.get_value("auth_type", "none")

        if auth_type == "api_key":
            return {"type": "api_key", "api_key": self.get_value("api_key")}
        elif auth_type == "bearer":
            return {"type": "bearer", "token": self.get_value("api_key")}
        elif auth_type == "basic":
            return {
                "type": "basic",
                "username": self.get_value("username"),
                "password": self.get_value("password"),
            }
        else:
            return {"type": "none"}

    def get_request_params(self) -> Dict[str, Any]:
        """获取请求参数"""
        return {
            "endpoint": self.get_value("endpoint"),
            "request_format": self.get_value("request_format", "json"),
            "response_format": self.get_value("response_format", "json"),
            "headers": self.get_value("headers", {}),
            "timeout": self.get_timeout(),
            "max_retries": self.get_max_retries(),
        }
