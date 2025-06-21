"""
Day Translation 2 - 配置管理器

只负责配置的CRUD操作，不包含业务逻辑。
遵循"配置只做配置"的架构原则。
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from models.exceptions import ConfigError
from .data_models import UnifiedConfig, CONFIG_VERSION


class ConfigManager:
    """配置管理器 - 只负责配置的CRUD操作"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置目录，默认为用户主目录下的 .day_translation
        """
        if config_dir is None:
            config_dir = os.path.join(Path.home(), ".day_translation")

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")

    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return self.config_file

    def load_config(self) -> UnifiedConfig:
        """
        加载配置文件

        Returns:
            配置实例

        Raises:
            ConfigError: 配置加载失败时
        """
        if not os.path.exists(self.config_file):
            # 配置文件不存在，返回默认配置
            config = UnifiedConfig()
            self.save_config(config)  # 保存默认配置
            logging.info("已创建默认配置文件")
            return config

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            config = UnifiedConfig.from_dict(config_data)
            logging.info(f"已加载配置文件: {self.config_file}")
            return config

        except json.JSONDecodeError as e:
            error_msg = f"配置文件格式错误: {e}"
            logging.error(error_msg)
            raise ConfigError(error_msg, config_path=self.config_file)
        except Exception as e:
            error_msg = f"配置文件加载失败: {e}"
            logging.error(error_msg)
            raise ConfigError(error_msg, config_path=self.config_file)

    def save_config(self, config: UnifiedConfig) -> None:
        """
        保存配置到文件

        Args:
            config: 要保存的配置实例

        Raises:
            ConfigError: 配置保存失败时
        """
        try:
            # 确保配置目录存在
            os.makedirs(self.config_dir, exist_ok=True)

            config_data = config.to_dict()

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logging.info(f"配置已保存到: {self.config_file}")

        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            logging.error(error_msg)
            raise ConfigError(error_msg, config_path=self.config_file)

    def reset_config(self) -> UnifiedConfig:
        """
        重置为默认配置

        Returns:
            重置后的配置实例
        """
        config = UnifiedConfig()
        self.save_config(config)
        logging.info("配置已重置为默认值")
        return config

    def validate_config(self, config: UnifiedConfig) -> bool:
        """
        验证配置完整性

        Args:
            config: 要验证的配置实例

        Returns:
            是否有效
        """
        try:
            # 检查必要字段
            assert config.version is not None, "缺少版本信息"
            assert config.core is not None, "缺少核心配置"
            assert config.user is not None, "缺少用户配置"

            # 检查版本兼容性
            if config.version != CONFIG_VERSION:
                logging.warning(f"配置版本不匹配: {config.version} != {CONFIG_VERSION}")

            return True

        except AssertionError as e:
            logging.error(f"配置验证失败: {e}")
            return False
        except Exception as e:
            logging.error(f"配置验证过程出错: {e}")
            return False

    def backup_config(self, backup_suffix: str = ".backup") -> bool:
        """
        备份当前配置文件

        Args:
            backup_suffix: 备份文件后缀

        Returns:
            是否备份成功
        """
        if not os.path.exists(self.config_file):
            return False

        try:
            backup_file = self.config_file + backup_suffix
            import shutil

            shutil.copy2(self.config_file, backup_file)
            logging.info(f"配置已备份到: {backup_file}")
            return True
        except Exception as e:
            logging.error(f"配置备份失败: {e}")
            return False

    def config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return os.path.exists(self.config_file)

    def get_config_info(self) -> dict:
        """获取配置文件信息"""
        if not self.config_exists():
            return {"exists": False}

        try:
            stat = os.stat(self.config_file)
            return {
                "exists": True,
                "path": self.config_file,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            }
        except Exception as e:
            logging.error(f"获取配置文件信息失败: {e}")
            return {"exists": True, "error": str(e)}
