"""
Day Translation 2 - 配置管理模块

提供统一的配置管理功能，包括：
- 核心配置管理
- 用户偏好设置
- 路径验证和管理
- 配置持久化

新架构（纯架构）：
- data_models.py - 纯数据模型
- config_manager.py - 配置CRUD操作
- 所有业务逻辑已迁移到 services/ 下专属模块
"""

# 纯数据模型
from .data_models import (
    GeneralConfig,
    ExtractionConfig,
    APIConfig,
    ProcessingConfig,
    FilterConfig,
    PathValidationResult,
)

# 配置管理器
from .config_manager import ConfigManager

# 版本信息
CONFIG_VERSION = "2.0.0"

# 向后兼容类型别名
CoreConfig = GeneralConfig
UserConfig = dict
UnifiedConfig = dict

__all__ = [
    # 版本
    "CONFIG_VERSION",
    # 新架构数据模型
    "GeneralConfig",
    "ExtractionConfig",
    "APIConfig",
    "ProcessingConfig",
    "FilterConfig",
    "PathValidationResult",
    # 配置管理器
    "ConfigManager",
    # 向后兼容类型别名
    "CoreConfig",
    "UserConfig",
    "UnifiedConfig",
]
