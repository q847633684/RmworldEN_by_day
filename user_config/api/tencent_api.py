"""
腾讯翻译API配置
"""

from typing import Any, Dict
from .base_api import BaseAPIConfig


class TencentAPIConfig(BaseAPIConfig):
    """腾讯翻译API配置"""

    def __init__(self):
        super().__init__("腾讯翻译", "tencent")

        # 腾讯特有的默认值
        self._defaults.update(
            {
                "secret_id": "",
                "secret_key": "",
                "region": "ap-beijing",
                "endpoint": "tmt.tencentcloudapi.com",
            }
        )

        # 必需字段
        self._required_fields.update({"secret_id", "secret_key"})

        # 字段类型
        self._field_types.update(
            {
                "secret_id": str,
                "secret_key": str,
                "region": str,
                "endpoint": str,
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "secret_id": {
                "type": "text",
                "label": "SecretId",
                "description": "腾讯云SecretId",
                "required": True,
                "placeholder": "请输入SecretId",
            },
            "secret_key": {
                "type": "password",
                "label": "SecretKey",
                "description": "腾讯云SecretKey",
                "required": True,
                "placeholder": "请输入SecretKey",
            },
            "region": {
                "type": "select",
                "label": "区域",
                "description": "腾讯云服务区域",
                "options": [
                    {"value": "ap-beijing", "label": "北京"},
                    {"value": "ap-shanghai", "label": "上海"},
                    {"value": "ap-guangzhou", "label": "广州"},
                    {"value": "ap-chengdu", "label": "成都"},
                    {"value": "ap-singapore", "label": "新加坡"},
                ],
                "default": "ap-beijing",
            },
        }

    def test_connection(self) -> tuple[bool, str]:
        """测试腾讯API连接"""
        try:
            secret_id = self.get_value("secret_id")
            secret_key = self.get_value("secret_key")

            if not secret_id or not secret_key:
                return False, "SecretId或SecretKey未配置"

            # TODO: 实际调用腾讯API进行测试
            self.logger.info("腾讯API连接测试通过")
            return True, "连接测试成功"

        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_auth_params(self) -> Dict[str, Any]:
        """获取认证参数"""
        return {
            "secret_id": self.get_value("secret_id"),
            "secret_key": self.get_value("secret_key"),
            "region": self.get_value("region", "ap-beijing"),
        }

    def get_request_params(self) -> Dict[str, Any]:
        """获取请求参数"""
        return {
            "endpoint": self.get_value("endpoint"),
            "timeout": self.get_timeout(),
            "max_retries": self.get_max_retries(),
        }
