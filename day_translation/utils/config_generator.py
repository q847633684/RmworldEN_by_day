import logging
import os
from typing import Optional
from .config import TranslationConfig
from .utils import save_json

CONFIG = TranslationConfig()

def generate_default_config(config_file: str) -> None:
    """生成默认配置文件模板"""
    logging.info(f"生成默认配置文件: {config_file}")
    template = {
        "default_fields": list(CONFIG.default_fields),
        "ignore_fields": list(CONFIG.ignore_fields),
        "non_text_patterns": CONFIG.non_text_patterns
    }
    save_json(template, config_file)

def generate_config_for_mod(mod_dir: str, config_file: str, custom_fields: Optional[set] = None) -> None:
    """为特定模组生成配置文件"""
    logging.info(f"生成模组配置文件: {mod_dir} -> {config_file}")
    custom_fields = custom_fields or set()
    template = {
        "default_fields": list(CONFIG.default_fields | custom_fields),
        "ignore_fields": list(CONFIG.ignore_fields),
        "non_text_patterns": CONFIG.non_text_patterns
    }
    save_json(template, config_file)