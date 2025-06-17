import logging
import os
from typing import Optional, Set
from .config import get_config
from .utils import save_json

CONFIG = get_config()

def generate_default_config(config_file: str) -> None:
    """生成默认配置文件模板"""
    logging.info(f"生成默认配置文件: {config_file}")
    template = {
        "default_fields": list(CONFIG.default_fields),
        "ignore_fields": list(CONFIG.ignore_fields),
        "non_text_patterns": CONFIG.non_text_patterns
    }
    save_json(template, config_file)

def generate_config_for_mod(mod_dir: str, config_file: str, custom_fields: Optional[Set[str]] = None) -> None:
    """为特定模组生成配置文件"""
    logging.info(f"生成模组配置文件: {mod_dir} -> {config_file}")
    custom_fields = custom_fields or set()
    
    # 安全获取默认字段
    try:
        default_fields = CONFIG.default_fields or set()
        ignore_fields = CONFIG.ignore_fields or set()
        non_text_patterns = CONFIG.non_text_patterns or []
    except Exception as e:
        logging.warning(f"获取配置字段失败: {e}")
        default_fields = set()
        ignore_fields = set()  
        non_text_patterns = []
    
    template = {
        "default_fields": list(default_fields | custom_fields),
        "ignore_fields": list(ignore_fields),
        "non_text_patterns": non_text_patterns
    }
    save_json(template, config_file)