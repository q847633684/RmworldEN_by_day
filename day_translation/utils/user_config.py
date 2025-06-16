import json
import os
from pathlib import Path
from typing import Dict

def get_config_path() -> str:
    """获取配置文件路径"""
    return os.path.join(Path.home(), ".day_translation", "config.json")

def load_user_config() -> Dict:
    """加载用户配置"""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    return {}

def save_user_config(config: Dict) -> None:
    """保存用户配置"""
    config_path = get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"保存配置文件失败: {e}")