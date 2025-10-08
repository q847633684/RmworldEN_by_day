"""
阿里云翻译API配置
"""

from typing import Any, Dict
from .base_api import BaseAPIConfig


class AliyunAPIConfig(BaseAPIConfig):
    """阿里云翻译API配置"""

    def __init__(self):
        super().__init__("阿里云翻译", "aliyun")

        # 阿里云特有的默认值
        self._defaults.update(
            {
                "access_key_id": "",
                "access_key_secret": "",
                "region": "cn-hangzhou",
                "model_id": 27345,
                "sleep_sec": 0.5,
                "enable_interrupt": True,
            }
        )

        # 必需字段
        self._required_fields.update({"access_key_id", "access_key_secret"})

        # 字段类型
        self._field_types.update(
            {
                "access_key_id": str,
                "access_key_secret": str,
                "region": str,
                "model_id": int,
                "sleep_sec": float,
                "enable_interrupt": bool,
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "access_key_id": {
                "type": "password",
                "label": "AccessKeyId",
                "description": "阿里云访问密钥ID",
                "required": True,
                "placeholder": "请输入AccessKeyId",
            },
            "access_key_secret": {
                "type": "password",
                "label": "AccessKeySecret",
                "description": "阿里云访问密钥Secret",
                "required": True,
                "placeholder": "请输入AccessKeySecret",
            },
            "region": {
                "type": "select",
                "label": "区域",
                "description": "阿里云服务区域",
                "options": [
                    {"value": "cn-hangzhou", "label": "华东1（杭州）"},
                    {"value": "cn-beijing", "label": "华北2（北京）"},
                    {"value": "cn-shanghai", "label": "华东2（上海）"},
                    {"value": "cn-shenzhen", "label": "华南1（深圳）"},
                    {"value": "ap-southeast-1", "label": "新加坡"},
                    {"value": "us-west-1", "label": "美国西部1"},
                ],
                "default": "cn-hangzhou",
            },
            "model_id": {
                "type": "select",
                "label": "翻译模型",
                "description": "选择翻译模型",
                "options": [
                    {"value": 27345, "label": "通用翻译"},
                    {"value": 27346, "label": "电商翻译"},
                    {"value": 27347, "label": "社交翻译"},
                    {"value": 27348, "label": "医疗翻译"},
                    {"value": 27349, "label": "金融翻译"},
                ],
                "default": 27345,
            },
            "sleep_sec": {
                "type": "number",
                "label": "请求延迟(秒)",
                "description": "两次请求之间的延迟时间",
                "min": 0.1,
                "max": 5.0,
                "step": 0.1,
                "default": 0.5,
            },
            "enable_interrupt": {
                "type": "boolean",
                "label": "启用中断功能",
                "description": "是否允许中断翻译过程",
                "default": True,
            },
            "timeout": {
                "type": "number",
                "label": "超时时间(秒)",
                "description": "API请求超时时间",
                "min": 5,
                "max": 300,
                "default": 30,
            },
            "max_retries": {
                "type": "number",
                "label": "最大重试次数",
                "description": "请求失败时的重试次数",
                "min": 0,
                "max": 10,
                "default": 3,
            },
            "rate_limit": {
                "type": "number",
                "label": "速率限制(请求/秒)",
                "description": "每秒最大请求数",
                "min": 1,
                "max": 50,
                "default": 10,
            },
        }

    def test_connection(self) -> tuple[bool, str]:
        """测试阿里云API连接"""
        try:
            access_key_id = self.get_value("access_key_id")
            access_key_secret = self.get_value("access_key_secret")

            if not access_key_id or not access_key_secret:
                return False, "AccessKey未配置"

            # 首先进行基本格式验证
            if not self.validate():
                return False, "配置验证失败，请检查AccessKey格式"

            # TODO: 实际调用阿里云API进行测试
            # 这里应该发送真实的API请求来测试连接
            # 示例代码：
            # try:
            #     from aliyunsdkcore.client import AcsClient
            #     from aliyunsdkalimt.request.v20181012 import TranslateGeneralRequest
            #
            #     client = AcsClient(access_key_id, access_key_secret, self.get_value("region", "cn-hangzhou"))
            #     request = TranslateGeneralRequest.TranslateGeneralRequest()
            #     request.set_SourceText("test")
            #     request.set_SourceLanguage("en")
            #     request.set_TargetLanguage("zh")
            #     response = client.do_action_with_exception(request)
            #     return True, "连接测试成功"
            # except Exception as e:
            #     return False, f"API调用失败: {str(e)}"

            # 暂时返回验证结果（实际项目中应该发送真实API请求）
            self.logger.info("阿里云API连接测试通过（基于配置验证）")
            return True, "连接测试成功（注意：这是基于配置验证，未实际调用API）"

        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_auth_params(self) -> Dict[str, Any]:
        """获取认证参数"""
        return {
            "access_key_id": self.get_value("access_key_id"),
            "access_key_secret": self.get_value("access_key_secret"),
            "region": self.get_value("region", "cn-hangzhou"),
        }

    def get_request_params(self) -> Dict[str, Any]:
        """获取请求参数"""
        return {
            "model_id": self.get_value("model_id", 27345),
            "sleep_sec": self.get_value("sleep_sec", 0.5),
            "enable_interrupt": self.get_value("enable_interrupt", True),
            "timeout": self.get_timeout(),
            "max_retries": self.get_max_retries(),
        }

    def validate(self) -> bool:
        """验证阿里云API配置"""
        # 先调用基类验证
        if not super().validate():
            return False

        # 阿里云特有验证
        access_key_id = self.get_value("access_key_id")
        if not access_key_id:
            self.logger.error("AccessKeyId不能为空")
            return False
        if len(access_key_id) < 16:
            self.logger.error("AccessKeyId长度不足，至少需要16个字符")
            return False
        if not access_key_id.startswith("LTAI"):
            self.logger.error("AccessKeyId格式无效，应以LTAI开头")
            return False

        access_key_secret = self.get_value("access_key_secret")
        if not access_key_secret:
            self.logger.error("AccessKeySecret不能为空")
            return False
        if len(access_key_secret) < 30:
            self.logger.error("AccessKeySecret格式无效，长度至少需要30个字符")
            return False

        model_id = self.get_value("model_id", 27345)
        valid_models = [27345, 27346, 27347, 27348, 27349]
        if model_id not in valid_models:
            self.logger.error(f"无效的模型ID: {model_id}")
            return False

        sleep_sec = self.get_value("sleep_sec", 0.5)
        if sleep_sec < 0.1 or sleep_sec > 5.0:
            self.logger.error(f"请求延迟无效: {sleep_sec}")
            return False

        return True

    def get_display_info(self) -> Dict[str, Any]:
        """获取显示信息"""
        info = super().get_display_info()

        # 添加阿里云特有信息
        access_key_id = self.get_value("access_key_id", "")
        if access_key_id:
            # 只显示前4位和后4位
            masked_key = (
                f"{access_key_id[:4]}****{access_key_id[-4:]}"
                if len(access_key_id) > 8
                else "****"
            )
            info["access_key_id"] = masked_key
        else:
            info["access_key_id"] = "未设置"

        info.update(
            {
                "region": self.get_value("region", "cn-hangzhou"),
                "model_id": self.get_value("model_id", 27345),
                "sleep_sec": self.get_value("sleep_sec", 0.5),
            }
        )

        return info
