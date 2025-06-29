"""
配置管理处理器
处理配置管理相关交互流程
"""

import logging
from colorama import Fore, Style

from day_translation.utils.interaction import (
    show_success,
    show_error,
    show_info,
    show_warning
)
from day_translation.utils.path_manager import PathManager
from day_translation.utils.config import get_config, ConfigError

path_manager = PathManager()
CONFIG = get_config()

def handle_config_manage():
    """处理配置管理功能"""
    try:
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║                     ⚙️ 配置管理 ⚙️                     ║")
        print(f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}📋 当前配置：{Style.RESET_ALL}")
        print(f"   配置文件路径: {CONFIG.user_config}")
        
        print(f"\n{Fore.YELLOW}🔧 配置选项：{Style.RESET_ALL}")
        print(f"   1. 🔑 设置阿里云AccessKeyId")
        print(f"   2. 🔐 设置阿里云AccessKeySecret")
        print(f"   3. 📁 设置默认导入/导出路径")
        print(f"   4. 🗑️ 清空历史记录")
        print(f"   b. 🔙 返回主菜单")
        
        print(f"\n{Fore.CYAN}────────────────────────────────────────────────────────────────{Style.RESET_ALL}")
        
        while True:
            choice = input(f"{Fore.GREEN}请选择配置项 (1-4, b): {Style.RESET_ALL}").strip()
            if choice == '1':
                ak = input(f"{Fore.CYAN}请输入阿里云AccessKeyId: {Style.RESET_ALL}").strip()
                CONFIG.user_config['aliyun_access_key_id'] = ak
                show_success("AccessKeyId已设置")
            elif choice == '2':
                sk = input(f"{Fore.CYAN}请输入阿里云AccessKeySecret: {Style.RESET_ALL}").strip()
                CONFIG.user_config['aliyun_access_key_secret'] = sk
                show_success("AccessKeySecret已设置")
            elif choice == '3':
                imp = input(f"{Fore.CYAN}请输入默认导入路径: {Style.RESET_ALL}").strip()
                exp = input(f"{Fore.CYAN}请输入默认导出路径: {Style.RESET_ALL}").strip()
                CONFIG.user_config['default_import_csv'] = imp
                CONFIG.user_config['default_export_csv'] = exp
                show_success("默认路径已设置")
            elif choice == '4':
                confirm = input(f"{Fore.YELLOW}确认清空所有历史记录？[y/n]: {Style.RESET_ALL}").strip().lower()
                if confirm == 'y':
                    path_manager._history_cache.clear()
                    show_success("历史记录已清空")
                else:
                    show_info("取消清空操作")
            elif choice == 'b':
                break
            else:
                show_warning("无效选项，请重新输入")
        CONFIG.save_user_config()
    except ConfigError as e:
        show_error(str(e))
    except Exception as e:
        show_error(f"配置管理失败: {str(e)}")
        logging.error("配置管理失败: %s", str(e), exc_info=True) 