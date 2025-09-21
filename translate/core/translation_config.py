"""
翻译配置类
管理翻译相关的配置参数
"""

from typing import Optional
from utils.logging_config import get_logger
from utils.config import get_user_config


class TranslationConfig:
    """翻译配置类"""

    def __init__(self, config_dict: Optional[dict] = None):
        """
        初始化翻译配置

        Args:
            config_dict: 配置字典，如果为None则从用户配置中加载
        """
        self.logger = get_logger(f"{__name__}.TranslationConfig")

        if config_dict:
            self._load_from_dict(config_dict)
        else:
            self._load_from_user_config()

    def _load_from_dict(self, config_dict: dict):
        """从字典加载配置"""
        self.access_key_id = config_dict.get("access_key_id", "")
        self.access_key_secret = config_dict.get("access_key_secret", "")
        self.region_id = config_dict.get("region_id", "cn-hangzhou")
        self.model_id = config_dict.get("model_id", 27345)
        self.sleep_sec = config_dict.get("sleep_sec", 0.5)
        self.enable_interrupt = config_dict.get("enable_interrupt", True)
        self.default_translator = config_dict.get("default_translator", "auto")

    def _load_from_user_config(self):
        """从用户配置加载"""
        try:
            user_config = get_user_config() or {}

            self.access_key_id = user_config.get("aliyun_access_key_id", "")
            self.access_key_secret = user_config.get("aliyun_access_key_secret", "")
            self.region_id = user_config.get("aliyun_region_id", "cn-hangzhou")
            self.model_id = user_config.get("model_id", 27345)
            self.sleep_sec = user_config.get("sleep_sec", 0.5)
            self.enable_interrupt = user_config.get("enable_interrupt", True)
            self.default_translator = user_config.get("default_translator", "auto")

            self.logger.debug("从用户配置加载翻译配置")

        except Exception as e:
            self.logger.warning("加载用户配置失败，使用默认配置: %s", e)
            self._load_defaults()

    def _load_defaults(self):
        """加载默认配置"""
        self.access_key_id = ""
        self.access_key_secret = ""
        self.region_id = "cn-hangzhou"
        self.model_id = 27345
        self.sleep_sec = 0.5
        self.enable_interrupt = True
        self.default_translator = "auto"

    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return bool(self.access_key_id and self.access_key_secret)

    def get_api_params(self) -> dict:
        """获取API参数"""
        return {
            "access_key_id": self.access_key_id,
            "access_key_secret": self.access_key_secret,
            "region_id": self.region_id,
            "model_id": self.model_id,
            "sleep_sec": self.sleep_sec,
        }

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "access_key_id": self.access_key_id,
            "access_key_secret": self.access_key_secret,
            "region_id": self.region_id,
            "model_id": self.model_id,
            "sleep_sec": self.sleep_sec,
            "enable_interrupt": self.enable_interrupt,
            "default_translator": self.default_translator,
        }
