"""
用户配置系统

提供完整的用户配置管理功能，包括：
- API配置管理（支持多种翻译服务）
- 路径配置管理
- 日志配置管理
- 界面配置管理
- 配置的导入导出、备份恢复等功能
"""

from .core.user_config import UserConfigManager
from .api.api_manager import APIManager

__version__ = "2.0.0"
__all__ = ["UserConfigManager", "APIManager"]
