import json
import os
from pathlib import Path
from typing import Dict
import logging

def get_config_path() -> str:
    """获取用户配置文件路径"""
    config_path = os.path.join(Path.home(), ".day_translation", "config.json")
    logging.debug(f"获取配置文件路径: {config_path}")
    return config_path

def load_user_config() -> Dict:
    """
    加载用户配置

    Returns:
        Dict: 配置字典，包含 API 密钥和历史记录
    """
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logging.debug(f"加载配置: {config}")
                return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            logging.error(f"加载配置文件失败: {e}")
    return {}

def save_user_config(config: Dict) -> None:
    """
    保存用户配置

    Args:
        config (Dict): 配置字典
    """
    config_path = get_config_path()
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logging.debug(f"配置文件保存成功: {config_path}")
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        logging.error(f"保存配置文件失败: {e}")