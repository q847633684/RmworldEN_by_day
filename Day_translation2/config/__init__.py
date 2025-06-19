"""
Day Translation 2 - 配置管理模块

提供统一的配置管理功能，包括：
- 核心配置管理
- 用户偏好设置
- 路径验证和管理
- 配置持久化
"""

from .unified_models import (CONFIG_VERSION, UnifiedConfig, CoreConfig, UserConfig,
                            FilterConfig, ProcessingConfig, PathValidationResult,
                            get_config, save_config, reset_config, get_config_path)

__all__ = [
    "UnifiedConfig",
    "CoreConfig", 
    "UserConfig",
    "FilterConfig",
    "ProcessingConfig",
    "PathValidationResult",
    "get_config",
    "save_config",
    "reset_config",
    "get_config_path",
    "CONFIG_VERSION",
]
