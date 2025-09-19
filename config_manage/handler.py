"""
配置管理处理器
处理配置管理相关交互流程
"""

import logging
from utils.logging_config import get_logger, log_error_with_context
from colorama import Fore, Style
from utils.ui_style import ui

from utils.interaction import (
    show_success,
    show_error,
    show_info,
    show_warning,
)
from utils.path_manager import PathManager
from utils.config import (
    get_config,
    get_user_config,
    save_user_config_to_file,
    get_config_path,
    ConfigError,
)

path_manager = PathManager()
CONFIG = get_config()


def handle_config_manage():
    logger = get_logger(f"{__name__}.handle_config_manage")

    """处理配置管理功能"""
    try:
        ui.print_header("配置管理", ui.Icons.SETTINGS)

        # 获取用户配置
        user_config = get_user_config()
        config_path = get_config_path()

        ui.print_section_header("当前配置", ui.Icons.SETTINGS)
        ui.print_key_value("配置文件路径", config_path, ui.Icons.FILE)
        ui.print_key_value(
            "阿里云AccessKeyId",
            "已设置" if user_config.get("aliyun_access_key_id") else "未设置",
            ui.Icons.SETTINGS,
        )
        ui.print_key_value(
            "阿里云AccessKeySecret",
            "已设置" if user_config.get("aliyun_access_key_secret") else "未设置",
            ui.Icons.SETTINGS,
        )
        ui.print_key_value(
            "默认导入路径",
            user_config.get("default_import_csv", "未设置"),
            ui.Icons.IMPORT,
        )
        ui.print_key_value(
            "默认导出路径",
            user_config.get("default_export_csv", "未设置"),
            ui.Icons.EXPORT,
        )

        ui.print_section_header("配置选项", ui.Icons.SETTINGS)
        ui.print_menu_item(
            "1",
            "设置阿里云AccessKeyId",
            "配置阿里云翻译服务的访问密钥ID",
            ui.Icons.SETTINGS,
        )
        ui.print_menu_item(
            "2",
            "设置阿里云AccessKeySecret",
            "配置阿里云翻译服务的访问密钥Secret",
            ui.Icons.SETTINGS,
        )
        ui.print_menu_item(
            "3", "设置默认导入/导出路径", "配置默认的CSV文件路径", ui.Icons.FOLDER
        )
        ui.print_menu_item("4", "清空历史记录", "清除所有历史记录", ui.Icons.SETTINGS)
        ui.print_menu_item("b", "返回主菜单", "返回主菜单", ui.Icons.BACK)

        ui.print_separator()

        while True:
            choice = input(
                ui.get_input_prompt("请选择配置项", options="1-4, b")
            ).strip()
            if choice == "1":
                current_ak = user_config.get("aliyun_access_key_id", "")
                if current_ak:
                    print(f"   当前值: {current_ak[:8]}****")
                ak = input(ui.get_input_prompt("请输入阿里云AccessKeyId")).strip()
                if ak:
                    user_config["aliyun_access_key_id"] = ak
                    save_user_config_to_file(user_config)
                    show_success("AccessKeyId已设置")
                else:
                    show_warning("输入为空，未做更改")
            elif choice == "2":
                current_sk = user_config.get("aliyun_access_key_secret", "")
                if current_sk:
                    print(f"   当前值: {current_sk[:8]}****")
                sk = input(ui.get_input_prompt("请输入阿里云AccessKeySecret")).strip()
                if sk:
                    user_config["aliyun_access_key_secret"] = sk
                    save_user_config_to_file(user_config)
                    show_success("AccessKeySecret已设置")
                else:
                    show_warning("输入为空，未做更改")
            elif choice == "3":
                print(
                    f"   当前导入路径: {user_config.get('default_import_csv', '未设置')}"
                )
                print(
                    f"   当前导出路径: {user_config.get('default_export_csv', '未设置')}"
                )
                imp = input(ui.get_input_prompt("请输入默认导入路径")).strip()
                exp = input(ui.get_input_prompt("请输入默认导出路径")).strip()
                if imp:
                    user_config["default_import_csv"] = imp
                if exp:
                    user_config["default_export_csv"] = exp
                if imp or exp:
                    save_user_config_to_file(user_config)
                    show_success("默认路径已设置")
                else:
                    show_warning("输入为空，未做更改")
            elif choice == "4":
                confirm = (
                    input(ui.get_input_prompt("确认清空所有历史记录", options="y/n"))
                    .strip()
                    .lower()
                )
                if confirm == "y":
                    path_manager._history_cache.clear()
                    show_success("历史记录已清空")
                else:
                    show_info("取消清空操作")
            elif choice == "b":
                break
            else:
                show_warning("无效选项，请重新输入")

    except ConfigError as e:
        show_error(str(e))
    except Exception as e:
        show_error(f"配置管理失败: {str(e)}")
        logger.error("配置管理失败: %s", str(e), exc_info=True)
