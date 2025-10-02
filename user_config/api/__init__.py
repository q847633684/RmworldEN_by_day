"""
API配置模块

支持多种翻译API的配置管理
"""

from .base_api import BaseAPIConfig
from .aliyun_api import AliyunAPIConfig
from .baidu_api import BaiduAPIConfig
from .tencent_api import TencentAPIConfig
from .google_api import GoogleAPIConfig
from .custom_api import CustomAPIConfig
from .api_manager import APIManager

__all__ = [
    "BaseAPIConfig",
    "AliyunAPIConfig",
    "BaiduAPIConfig",
    "TencentAPIConfig",
    "GoogleAPIConfig",
    "CustomAPIConfig",
    "APIManager",
]
