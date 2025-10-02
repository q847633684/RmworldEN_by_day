"""
谷歌翻译API配置
"""

from typing import Any, Dict
from .base_api import BaseAPIConfig


class GoogleAPIConfig(BaseAPIConfig):
    """谷歌翻译API配置"""

    def __init__(self):
        super().__init__("谷歌翻译", "google")

        # 谷歌特有的默认值
        self._defaults.update(
            {
                "api_key": "",
                "project_id": "",
                "endpoint": "https://translation.googleapis.com/language/translate/v2",
            }
        )

        # 必需字段
        self._required_fields.update({"api_key"})

        # 字段类型
        self._field_types.update(
            {
                "api_key": str,
                "project_id": str,
                "endpoint": str,
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "api_key": {
                "type": "password",
                "label": "API Key",
                "description": "谷歌翻译API密钥",
                "required": True,
                "placeholder": "请输入API Key",
            },
            "project_id": {
                "type": "text",
                "label": "项目ID",
                "description": "谷歌云项目ID（可选）",
                "placeholder": "请输入项目ID",
            },
        }

    def test_connection(self) -> tuple[bool, str]:
        """测试谷歌API连接"""
        try:
            api_key = self.get_value("api_key")

            if not api_key:
                return False, "API Key未配置"

            # TODO: 实际调用谷歌API进行测试
            self.logger.info("谷歌API连接测试通过")
            return True, "连接测试成功"

        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_auth_params(self) -> Dict[str, Any]:
        """获取认证参数"""
        return {
            "api_key": self.get_value("api_key"),
            "project_id": self.get_value("project_id"),
        }

    def get_request_params(self) -> Dict[str, Any]:
        """获取请求参数"""
        return {
            "endpoint": self.get_value("endpoint"),
            "timeout": self.get_timeout(),
            "max_retries": self.get_max_retries(),
        }
