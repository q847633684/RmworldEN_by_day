"""
Day Translation 2 - 配置操作服务

负责配置的高级操作，如导入导出、合并等业务逻辑。
将配置业务逻辑从配置层分离出来。
"""

import json
import logging
from datetime import datetime
from typing import Optional

from colorama import Fore, Style

from models.exceptions import ConfigError
from config.data_models import UnifiedConfig
from config.config_manager import ConfigManager


class ConfigService:
    """配置操作服务 - 专门处理配置相关的业务逻辑"""

    def __init__(self, manager: Optional[ConfigManager] = None):
        """
        初始化配置操作服务

        Args:
            manager: 配置管理器实例，如果为None则创建默认实例
        """
        self.manager = manager or ConfigManager()
        self.logger = logging.getLogger(__name__)

    def export_config(self, config: UnifiedConfig, export_path: str) -> bool:
        """
        导出配置到文件

        Args:
            config: 要导出的配置实例
            export_path: 导出文件路径

        Returns:
            是否成功
        """
        try:
            # 准备导出数据
            config_data = {
                "version": config.version,
                "core": config.core.to_dict(),
                "user": config.user.to_dict(),
                "exported_at": datetime.now().isoformat(),
                "exported_by": "Day Translation 2 Config Service",
            }

            # 确保导出目录存在
            import os

            export_dir = os.path.dirname(export_path)
            if export_dir and not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)

            # 写入文件
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"配置已导出到: {export_path}")
            print(f"{Fore.GREEN}✅ 配置已导出到: {export_path}{Style.RESET_ALL}")
            return True

        except Exception as e:
            error_msg = f"配置导出失败: {e}"
            self.logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            return False

    def import_config(self, import_path: str) -> Optional[UnifiedConfig]:
        """
        从文件导入配置

        Args:
            import_path: 导入文件路径

        Returns:
            导入的配置实例，失败时返回None
        """
        try:
            # 读取配置文件
            with open(import_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # 验证配置版本
            if "version" not in config_data:
                print(f"{Fore.YELLOW}⚠️ 配置文件缺少版本信息，可能不兼容{Style.RESET_ALL}")

            # 检查导出时间
            if "exported_at" in config_data:
                exported_at = config_data["exported_at"]
                print(f"{Fore.BLUE}📅 配置导出时间: {exported_at}{Style.RESET_ALL}")

            # 创建配置实例
            config = UnifiedConfig.from_dict(config_data)

            self.logger.info(f"配置已从文件导入: {import_path}")
            print(f"{Fore.GREEN}✅ 配置已从文件导入: {import_path}{Style.RESET_ALL}")
            return config

        except json.JSONDecodeError as e:
            error_msg = f"配置文件格式错误: {e}"
            self.logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            return None
        except Exception as e:
            error_msg = f"配置导入失败: {e}"
            self.logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            return None

    def merge_configs(self, base: UnifiedConfig, override: UnifiedConfig) -> UnifiedConfig:
        """
        合并配置

        Args:
            base: 基础配置
            override: 要合并的配置

        Returns:
            合并后的配置
        """
        try:
            # 创建新配置实例
            merged_config = UnifiedConfig()

            # 合并核心配置
            merged_config.core = self._merge_core_config(base.core, override.core)

            # 合并用户配置
            merged_config.user = self._merge_user_config(base.user, override.user)

            # 使用最新版本
            merged_config.version = max(base.version, override.version)

            self.logger.info("配置合并完成")
            return merged_config

        except Exception as e:
            self.logger.error(f"配置合并失败: {e}")
            raise ConfigError(f"配置合并失败: {e}")

    def _merge_core_config(self, base, override):
        """合并核心配置"""
        from config.data_models import CoreConfig

        # 使用override的非空值，否则使用base的值
        return CoreConfig(
            version=override.version or base.version,
            default_language=override.default_language or base.default_language,
            source_language=override.source_language or base.source_language,
            debug_mode=override.debug_mode if override.debug_mode is not None else base.debug_mode,
            encoding=override.encoding or base.encoding,
            backup_enabled=(
                override.backup_enabled
                if override.backup_enabled is not None
                else base.backup_enabled
            ),
        )

    def _merge_user_config(self, base, override):
        """合并用户配置"""
        from config.data_models import UserConfig

        # 深度合并用户配置
        merged_config = UserConfig()

        # 合并记住的路径
        merged_config.remembered_paths = {**base.remembered_paths, **override.remembered_paths}

        # 合并路径历史
        merged_config.path_history = self._merge_path_history(
            base.path_history, override.path_history
        )

        # 合并其他配置（使用override优先）
        merged_config.general = (
            override.general if hasattr(override, "general") and override.general else base.general
        )
        merged_config.extraction = (
            override.extraction
            if hasattr(override, "extraction") and override.extraction
            else base.extraction
        )
        merged_config.api = override.api if hasattr(override, "api") and override.api else base.api
        merged_config.processing = (
            override.processing
            if hasattr(override, "processing") and override.processing
            else base.processing
        )
        merged_config.filter = (
            override.filter if hasattr(override, "filter") and override.filter else base.filter
        )

        return merged_config

    def _merge_path_history(self, base_history, override_history):
        """合并路径历史"""
        merged_history = {}

        # 合并所有路径类型的历史
        all_path_types = set(base_history.keys()) | set(override_history.keys())

        for path_type in all_path_types:
            base_data = base_history.get(path_type, {})
            override_data = override_history.get(path_type, {})

            # 合并路径列表
            base_paths = base_data.get("paths", []) if isinstance(base_data, dict) else []
            override_paths = (
                override_data.get("paths", []) if isinstance(override_data, dict) else []
            )

            # 去重并保持顺序
            all_paths = list(dict.fromkeys(base_paths + override_paths))

            # 使用最新的最后使用路径
            last_used = override_data.get("last_used") if isinstance(override_data, dict) else None
            if not last_used and isinstance(base_data, dict):
                last_used = base_data.get("last_used")

            merged_history[path_type] = {
                "paths": all_paths[-10:],  # 只保留最近10个
                "last_used": last_used,
            }

        return merged_history

    def backup_config(self, config: UnifiedConfig, backup_suffix: Optional[str] = None) -> bool:
        """
        备份配置

        Args:
            config: 要备份的配置
            backup_suffix: 备份文件后缀

        Returns:
            是否备份成功
        """
        try:
            if backup_suffix is None:
                backup_suffix = f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            config_path = self.manager.get_config_path()
            backup_path = config_path + backup_suffix

            # 导出配置到备份文件
            success = self.export_config(config, backup_path)
            if success:
                self.logger.info(f"配置已备份到: {backup_path}")
                print(f"{Fore.GREEN}✅ 配置已备份到: {backup_path}{Style.RESET_ALL}")

            return success

        except Exception as e:
            error_msg = f"配置备份失败: {e}"
            self.logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            return False

    def restore_config(self, backup_path: str) -> Optional[UnifiedConfig]:
        """
        从备份恢复配置

        Args:
            backup_path: 备份文件路径

        Returns:
            恢复的配置实例，失败时返回None
        """
        try:
            # 导入备份配置
            restored_config = self.import_config(backup_path)
            if restored_config:
                # 保存恢复的配置
                self.manager.save_config(restored_config)
                self.logger.info(f"配置已从备份恢复: {backup_path}")
                print(f"{Fore.GREEN}✅ 配置已从备份恢复: {backup_path}{Style.RESET_ALL}")

            return restored_config

        except Exception as e:
            error_msg = f"配置恢复失败: {e}"
            self.logger.error(error_msg)
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            return None

    def validate_config_compatibility(self, config_data: dict) -> bool:
        """
        验证配置兼容性

        Args:
            config_data: 配置数据字典

        Returns:
            是否兼容
        """
        try:
            # 检查必要字段
            required_fields = ["version", "core", "user"]
            for field in required_fields:
                if field not in config_data:
                    self.logger.warning(f"配置缺少必要字段: {field}")
                    return False

            # 检查版本兼容性
            config_version = config_data.get("version", "1.0.0")
            from config.data_models import CONFIG_VERSION

            if config_version != CONFIG_VERSION:
                self.logger.warning(f"配置版本不匹配: {config_version} != {CONFIG_VERSION}")
                # 可以考虑版本迁移逻辑
                return True  # 暂时允许版本不匹配

            return True

        except Exception as e:
            self.logger.error(f"配置兼容性验证失败: {e}")
            return False

    def get_config_summary(self, config: UnifiedConfig) -> dict:
        """
        获取配置摘要信息

        Args:
            config: 配置实例

        Returns:
            配置摘要
        """
        try:
            summary = {
                "version": config.version,
                "language": config.core.default_language,
                "debug_mode": config.core.debug_mode,
                "auto_mode": config.user.general.auto_mode,
                "remembered_paths_count": len(config.user.remembered_paths),
                "path_history_types": len(config.user.path_history),
                "api_configured": bool(config.user.api.aliyun_access_key_id),
            }
            return summary

        except Exception as e:
            self.logger.error(f"获取配置摘要失败: {e}")
            return {"error": str(e)}

    def get_unified_config(self) -> UnifiedConfig:
        """
        获取统一配置

        Returns:
            UnifiedConfig: 当前统一配置

        Raises:
            ConfigError: 配置获取失败时抛出
        """
        try:
            return self.manager.load_config()
        except Exception as e:
            self.logger.error(f"获取统一配置失败: {e}")
            raise ConfigError(f"配置获取失败: {e}")

    def save_unified_config(self, config: UnifiedConfig) -> bool:
        """
        保存统一配置

        Args:
            config: 要保存的配置

        Returns:
            bool: 保存是否成功

        Raises:
            ConfigError: 配置保存失败时抛出
        """
        try:
            self.manager.save_config(config)
            return True
        except Exception as e:
            self.logger.error(f"保存统一配置失败: {e}")
            raise ConfigError(f"配置保存失败: {e}")

    def reset_to_defaults(self) -> UnifiedConfig:
        """
        重置配置为默认值

        Returns:
            UnifiedConfig: 重置后的默认配置

        Raises:
            ConfigError: 配置重置失败时抛出
        """
        try:
            # 创建新的默认配置实例
            default_config = UnifiedConfig()
            self.manager.save_config(default_config)
            return default_config
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            raise ConfigError(f"配置重置失败: {e}")

    def get_config_file_path(self) -> str:
        """
        获取配置文件路径

        Returns:
            str: 配置文件的绝对路径
        """
        return str(self.manager.config_file)


# 全局配置服务实例（单例）
config_service = ConfigService()

__all__ = ["ConfigService", "config_service"]
