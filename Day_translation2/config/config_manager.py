"""
Day Translation 2 - 配置管理器

只负责配置的CRUD操作，不包含业务逻辑。
遵循"配置只做配置"的架构原则。
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

from models.exceptions import ConfigError

from .data_models import CONFIG_VERSION, UnifiedConfig


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

    def create_default_config(self) -> UnifiedConfig:
        """
        创建默认配置实例

        Returns:
            默认配置实例
        """
        return UnifiedConfig()

    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return self.config_file

    def load_config(
        self, config_path: Optional[str] = None, error_recovery: bool = False
    ) -> UnifiedConfig:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
            error_recovery: 是否启用错误恢复（在错误时返回默认配置而不是抛出异常）

        Returns:
            配置实例

        Raises:
            ConfigError: 配置加载失败时（仅在error_recovery=False时）
        """
        target_path = config_path or self.config_file

        if not os.path.exists(target_path):
            # 配置文件不存在，返回默认配置
            config = UnifiedConfig()
            # 如果是默认路径，自动保存默认配置
            if config_path is None:
                self.save_config(config)
            return config

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # 验证基本结构
            if not isinstance(config_data, dict):
                raise ValueError("配置文件格式无效：根元素必须是对象")

            # 确保版本号存在
            if "version" not in config_data:
                config_data["version"] = CONFIG_VERSION

            # 从字典创建配置实例
            config = UnifiedConfig.from_dict(config_data)

            logging.debug(f"配置加载成功: {target_path}")
            return config

        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"配置文件格式错误: {str(e)}"
            logging.error(error_msg)

            if error_recovery:
                # 错误恢复模式：返回默认配置
                logging.warning("启用错误恢复，返回默认配置")
                return UnifiedConfig()
            else:
                # 正常模式：抛出异常
                raise ConfigError(error_msg, config_path=target_path)

        except Exception as e:
            error_msg = f"配置文件加载失败: {str(e)}"
            logging.error(error_msg)

            if error_recovery:
                # 错误恢复模式：返回默认配置
                logging.warning("启用错误恢复，返回默认配置")
                return UnifiedConfig()
            else:
                # 正常模式：抛出异常
                raise ConfigError(error_msg, config_path=target_path)

    def save_config(
        self, config: UnifiedConfig, config_path: Optional[str] = None
    ) -> None:
        """
        保存配置到文件

        Args:
            config: 要保存的配置实例
            config_path: 配置文件路径，如果为None则使用默认路径

        Raises:
            ConfigError: 配置保存失败时
        """
        target_path = config_path or self.config_file
        target_dir = os.path.dirname(target_path)

        try:
            # 确保配置目录存在
            os.makedirs(target_dir, exist_ok=True)

            config_data = config.to_dict()

            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logging.debug(f"配置保存成功: {target_path}")

        except Exception as e:
            error_msg = f"配置保存失败: {str(e)}"
            logging.error(error_msg)
            raise ConfigError(error_msg, config_path=target_path)

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

    def validate_config(self, config: UnifiedConfig) -> Tuple[bool, List[str]]:
        """
        验证配置完整性

        Args:
            config: 要验证的配置实例

        Returns:
            (是否有效, 错误列表)
        """
        errors: List[str] = []

        try:
            # 检查必要字段
            if config.version is None:
                errors.append("缺少版本信息")
            if config.core is None:
                errors.append("缺少核心配置")
            if config.user is None:
                errors.append("缺少用户配置")

            # 检查版本兼容性
            if config.version != CONFIG_VERSION:
                logging.warning(f"配置版本不匹配: {config.version} != {CONFIG_VERSION}")

            return len(errors) == 0, errors

        except Exception as e:
            error_msg = f"配置验证过程出错: {e}"
            logging.error(error_msg)
            return False, [error_msg]

    def backup_config(
        self, config_path: Optional[str] = None, backup_suffix: str = ".backup"
    ) -> Optional[str]:
        """
        备份配置文件

        Args:
            config_path: 要备份的配置文件路径，如果为None则使用默认路径
            backup_suffix: 备份文件后缀

        Returns:
            备份文件路径，失败时返回None
        """
        source_file = config_path or self.config_file

        if not os.path.exists(source_file):
            return None

        try:
            backup_file = source_file + backup_suffix
            import shutil

            shutil.copy2(source_file, backup_file)
            logging.info(f"配置已备份到: {backup_file}")
            return backup_file
        except Exception as e:
            logging.error(f"配置备份失败: {e}")
            return None

    def restore_config(
        self, backup_path: str, target_path: Optional[str] = None
    ) -> bool:
        """
        从备份恢复配置文件

        Args:
            backup_path: 备份文件路径
            target_path: 目标文件路径，如果为None则使用默认路径

        Returns:
            是否恢复成功
        """
        target_file = target_path or self.config_file

        if not os.path.exists(backup_path):
            logging.error(f"备份文件不存在: {backup_path}")
            return False

        try:
            import shutil

            shutil.copy2(backup_path, target_file)
            logging.info(f"配置已从备份恢复: {backup_path} -> {target_file}")
            return True
        except Exception as e:
            logging.error(f"配置恢复失败: {e}")
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
