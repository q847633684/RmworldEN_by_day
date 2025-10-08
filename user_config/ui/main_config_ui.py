"""
主配置界面

提供用户友好的配置管理界面
"""

from typing import Optional
from utils.logging_config import get_logger
from utils.ui_style import ui, confirm_action
from ..core.user_config import UserConfigManager
from ..core.config_validator import ConfigValidator
from .api_config_ui import APIConfigUI


class MainConfigUI:
    """主配置界面"""

    def __init__(self, config_manager: Optional[UserConfigManager] = None):
        """
        初始化主配置界面

        Args:
            config_manager: 用户配置管理器
        """
        self.logger = get_logger(f"{__name__}.MainConfigUI")
        self.config_manager = config_manager or UserConfigManager()
        self.validator = ConfigValidator()
        self.api_ui = APIConfigUI(self.config_manager)

    def show_main_menu(self) -> None:
        """显示主菜单"""
        while True:
            ui.print_header("用户配置管理", ui.Icons.SETTINGS)

            # 显示配置摘要
            self._show_config_summary()

            # 显示菜单选项
            ui.print_section_header("配置模块", ui.Icons.SETTINGS)
            ui.print_menu_item("1", "API配置", "管理翻译API配置", ui.Icons.API)
            ui.print_menu_item("2", "系统配置", "管理系统核心设置", ui.Icons.SETTINGS)
            ui.print_menu_item("3", "路径配置", "管理默认路径设置", ui.Icons.FOLDER)
            ui.print_menu_item("4", "语言配置", "管理语言目录设置", ui.Icons.LANGUAGE)
            ui.print_menu_item("5", "日志配置", "管理日志记录设置", ui.Icons.LOG)
            ui.print_menu_item("6", "界面配置", "管理界面显示设置", ui.Icons.UI)

            ui.print_section_header("配置管理", ui.Icons.TOOLS)
            ui.print_menu_item("7", "备份配置", "备份当前配置", ui.Icons.BACKUP)
            ui.print_menu_item("8", "恢复配置", "从备份恢复配置", ui.Icons.RESTORE)
            ui.print_menu_item("0", "重置配置", "重置为默认配置", ui.Icons.RESET)
            ui.print_menu_item("b", "返回主菜单", "返回主菜单", ui.Icons.BACK)

            ui.print_separator()

            choice = input(
                ui.get_input_prompt("请选择配置模块", options="1-8, 0, b")
            ).strip()

            if choice == "1":
                self.api_ui.show_api_menu()
            elif choice == "2":
                self._show_system_config()
            elif choice == "3":
                self._show_path_config()
            elif choice == "4":
                self._show_language_config()
            elif choice == "5":
                self._show_log_config()
            elif choice == "6":
                self._show_ui_config()
            elif choice == "7":
                self._backup_config()
            elif choice == "8":
                self._restore_config()
            elif choice == "0":
                self._reset_config()
            elif choice.lower() == "b":
                break
            else:
                ui.print_warning("无效选择，请重新输入")

    def _show_config_summary(self) -> None:
        """显示配置摘要"""
        ui.print_section_header("配置状态", ui.Icons.INFO)

        summary = self.config_manager.get_config_summary()

        # 显示配置文件信息
        config_exists = "✓" if summary["config_exists"] else "✗"
        ui.print_key_value(
            "配置文件", f"{summary['config_file']} {config_exists}", ui.Icons.FILE
        )

        # 显示各模块状态
        for module_name, module_info in summary["modules"].items():
            status_icon = "✓" if module_info["valid"] else "✗"
            complete_icon = "✓" if module_info["complete"] else "○"
            status_text = f"有效:{status_icon} 完整:{complete_icon}"
            ui.print_key_value(f"{module_name}配置", status_text, ui.Icons.MODULE)

        # 显示API状态
        api_status = summary["api_status"]
        enabled_count = sum(
            1 for api_info in api_status["apis"].values() if api_info["enabled"]
        )
        total_count = len(api_status["apis"])
        ui.print_key_value(
            "API状态", f"{enabled_count}/{total_count} 已启用", ui.Icons.API
        )

    def _show_system_config(self) -> None:
        """显示和编辑系统配置"""
        while True:
            ui.print_header("系统配置", ui.Icons.SETTINGS)

            system_config = self.config_manager.system_config

            # 显示系统配置和操作选项
            ui.print_section_header("系统配置", ui.Icons.INFO)

            # 获取翻译规则统计
            translation_fields = system_config.get_translation_fields()
            ignore_fields = system_config.get_ignore_fields()
            non_text_patterns = system_config.get_non_text_patterns()

            # 配置项列表
            config_items = [
                (
                    "1",
                    "配置版本",
                    system_config.get_value("version"),
                    ui.Icons.VERSION,
                    "查看配置版本信息",
                ),
                (
                    "2",
                    "日志格式",
                    system_config.get_value("log_format"),
                    ui.Icons.LOG,
                    "修改日志格式字符串",
                ),
                (
                    "3",
                    "调试模式",
                    "开启" if system_config.get_value("debug_mode") else "关闭",
                    ui.Icons.DEBUG,
                    "开启/关闭调试模式",
                ),
                (
                    "4",
                    "预览字段数",
                    str(system_config.get_value("preview_translatable_fields", 0)),
                    ui.Icons.FIELD,
                    "设置预览可翻译字段数量",
                ),
                (
                    "5",
                    "翻译字段",
                    f"{len(translation_fields)} 个",
                    ui.Icons.FIELD,
                    "查看翻译字段规则",
                ),
                (
                    "6",
                    "忽略字段",
                    f"{len(ignore_fields)} 个",
                    ui.Icons.FIELD,
                    "查看忽略字段规则",
                ),
                (
                    "7",
                    "非文本模式",
                    f"{len(non_text_patterns)} 个",
                    ui.Icons.PATTERN,
                    "查看非文本模式规则",
                ),
            ]

            # 显示配置项
            for key, label, value, icon, description in config_items:
                ui.print_menu_item(
                    key, f"{label}: {value}", description, icon, compact=True
                )

            # 返回选项
            ui.print_menu_item(
                "b", "返回上级", "返回主配置菜单", ui.Icons.BACK, compact=True
            )

            ui.print_separator()

            choice = input(ui.get_input_prompt("请选择操作", options="1-7, b")).strip()

            if choice == "1":
                ui.print_info(f"配置版本: {system_config.get_value('version')}")
                input("\n按回车键继续...")
            elif choice == "2":
                self._edit_system_field("log_format", "日志格式")
            elif choice == "3":
                current = system_config.get_value("debug_mode", True)
                system_config.set_value("debug_mode", not current)
                ui.print_success(f"调试模式已{'关闭' if current else '开启'}")
            elif choice == "4":
                self._edit_system_field(
                    "preview_translatable_fields", "预览字段数", field_type="int"
                )
            elif choice == "5":
                ui.print_info(f"翻译字段规则: {len(translation_fields)} 个")
                if translation_fields:
                    ui.print_info(
                        "字段列表: " + ", ".join(list(translation_fields)[:10])
                    )
                    if len(translation_fields) > 10:
                        ui.print_info(f"... 还有 {len(translation_fields) - 10} 个字段")
                input("\n按回车键继续...")
            elif choice == "6":
                ui.print_info(f"忽略字段规则: {len(ignore_fields)} 个")
                if ignore_fields:
                    ui.print_info("字段列表: " + ", ".join(list(ignore_fields)[:10]))
                    if len(ignore_fields) > 10:
                        ui.print_info(f"... 还有 {len(ignore_fields) - 10} 个字段")
                input("\n按回车键继续...")
            elif choice == "7":
                ui.print_info(f"非文本模式规则: {len(non_text_patterns)} 个")
                if non_text_patterns:
                    ui.print_info("模式列表: " + ", ".join(non_text_patterns[:10]))
                    if len(non_text_patterns) > 10:
                        ui.print_info(f"... 还有 {len(non_text_patterns) - 10} 个模式")
                input("\n按回车键继续...")
            elif choice.lower() == "b":
                break
            else:
                ui.print_warning("无效选择，请重新输入")

    def _edit_system_field(self, key: str, label: str, field_type: str = "str") -> None:
        """编辑系统配置字段"""
        current_value = self.config_manager.system_config.get_value(key, "")
        if current_value:
            print(f"   当前值: {current_value}")

        new_value = input(f"请输入新的{label}: ").strip()
        if new_value:
            try:
                if field_type == "int":
                    new_value = int(new_value)
                    if new_value < 0:
                        ui.print_warning("数值不能为负数")
                        return
                elif field_type == "bool":
                    new_value = new_value.lower() in ("true", "1", "yes", "on", "开启")

                self.config_manager.system_config.set_value(key, new_value)
                ui.print_success(f"{label}已更新")
            except ValueError:
                ui.print_warning("输入的数值格式不正确")
        else:
            ui.print_info("操作已取消")

    def _show_path_config(self) -> None:
        """显示路径配置"""
        while True:
            ui.print_header("路径配置", ui.Icons.FOLDER)

            path_config = self.config_manager.path_config

            # 显示路径配置和操作选项
            ui.print_section_header("路径配置", ui.Icons.INFO)

            # 配置项列表
            config_items = [
                (
                    "1",
                    "默认导出CSV",
                    path_config.get_value("default_export_csv", "未设置"),
                    ui.Icons.EXPORT,
                    "设置默认的CSV导出文件路径",
                ),
                (
                    "2",
                    "默认输出目录",
                    path_config.get_value("default_output_dir", "未设置"),
                    ui.Icons.FOLDER,
                    "设置默认的输出目录",
                ),
                (
                    "3",
                    "记住路径",
                    "是" if path_config.get_value("remember_paths", True) else "否",
                    ui.Icons.SETTINGS,
                    "开启/关闭路径记忆功能",
                ),
            ]

            # 显示配置项
            for key, label, value, icon, description in config_items:
                ui.print_menu_item(
                    key, f"{label}: {value}", description, icon, compact=True
                )

            # 返回选项
            ui.print_menu_item(
                "b", "返回上级", "返回上级菜单", ui.Icons.BACK, compact=True
            )

            ui.print_separator()

            choice = input(ui.get_input_prompt("请选择操作", options="1-3, b")).strip()

            if choice == "1":
                self._set_path_config(
                    "default_export_csv", "默认导出CSV路径", is_file=True
                )
            elif choice == "2":
                self._set_path_config(
                    "default_output_dir", "默认输出目录", is_directory=True
                )
            elif choice == "3":
                current = path_config.get_value("remember_paths", True)
                path_config.set_value("remember_paths", not current)
                ui.print_success(f"路径记忆功能已{'关闭' if current else '开启'}")
            elif choice.lower() == "b":
                break
            else:
                ui.print_warning("无效选择，请重新输入")

    def _set_path_config(
        self, key: str, label: str, is_file: bool = False, is_directory: bool = False
    ) -> None:
        """设置路径配置"""
        current_value = self.config_manager.path_config.get_value(key, "")
        if current_value:
            print(f"   当前值: {current_value}")

        new_value = input(f"请输入{label} (留空保持当前值): ").strip()
        if new_value:
            # 简单验证
            import os

            if is_file and new_value:
                if not new_value.endswith(".csv"):
                    new_value += ".csv"
                # 检查父目录
                parent_dir = os.path.dirname(new_value)
                if parent_dir and not os.path.exists(parent_dir):
                    ui.print_warning(f"父目录不存在: {parent_dir}")
            elif is_directory and new_value:
                if not os.path.exists(new_value):
                    ui.print_warning(f"目录不存在: {new_value}")

            self.config_manager.path_config.set_value(key, new_value)
            ui.print_success(f"{label}已更新")
        else:
            ui.print_info(f"{label}保持不变")

    def _show_language_config(self) -> None:
        """显示语言配置 - 界面语言和CSV格式"""
        while True:
            ui.print_header("语言配置", ui.Icons.LANGUAGE)

            lang_config = self.config_manager.language_config

            # 显示语言配置和操作选项
            ui.print_section_header("语言配置", ui.Icons.INFO)

            # 界面语言显示
            interface_lang = lang_config.get_value("interface_language")
            if interface_lang == "zh_CN":
                lang_display = "简体中文"
            elif interface_lang == "en_US":
                lang_display = "English"
            else:
                lang_display = interface_lang or "未设置"

            # 配置项列表
            config_items = [
                (
                    "1",
                    "中文语言目录",
                    lang_config.get_value("cn_language") or "未设置",
                    ui.Icons.LANGUAGE,
                    "设置中文语言目录",
                ),
                (
                    "2",
                    "英文语言目录",
                    lang_config.get_value("en_language") or "未设置",
                    ui.Icons.LANGUAGE,
                    "设置英文语言目录",
                ),
                (
                    "3",
                    "DefInjected目录",
                    lang_config.get_value("definjected_dir") or "未设置",
                    ui.Icons.FOLDER,
                    "设置DefInjected目录",
                ),
                (
                    "4",
                    "Keyed目录",
                    lang_config.get_value("keyed_dir") or "未设置",
                    ui.Icons.FOLDER,
                    "设置Keyed目录",
                ),
                (
                    "5",
                    "默认输出CSV",
                    lang_config.get_value("output_csv") or "未设置",
                    ui.Icons.FILE,
                    "设置默认输出CSV文件",
                ),
                ("6", "界面语言", lang_display, ui.Icons.LANGUAGE, "设置界面显示语言"),
                (
                    "7",
                    "CSV编码",
                    lang_config.get_value("csv_encoding") or "未设置",
                    ui.Icons.FILE,
                    "设置CSV文件编码",
                ),
                (
                    "8",
                    "CSV分隔符",
                    lang_config.get_value("csv_delimiter") or "未设置",
                    ui.Icons.FILE,
                    "设置CSV分隔符",
                ),
                (
                    "9",
                    "日期格式",
                    lang_config.get_value("date_format") or "未设置",
                    ui.Icons.TIME,
                    "设置日期显示格式",
                ),
                (
                    "0",
                    "数字格式",
                    lang_config.get_value("number_format") or "未设置",
                    ui.Icons.FIELD,
                    "设置数字显示格式",
                ),
            ]

            # 显示配置项
            for key, label, value, icon, description in config_items:
                ui.print_menu_item(
                    key, f"{label}: {value}", description, icon, compact=True
                )

            # 显示菜单
            ui.print_section_header("配置选项", ui.Icons.SETTINGS)
            ui.print_menu_item(
                "1", "设置中文语言目录", "设置中文语言目录名称", ui.Icons.LANGUAGE
            )
            ui.print_menu_item(
                "2", "设置英文语言目录", "设置英文语言目录名称", ui.Icons.LANGUAGE
            )
            ui.print_menu_item(
                "3", "设置DefInjected目录", "设置DefInjected子目录名称", ui.Icons.FOLDER
            )
            ui.print_menu_item(
                "4", "设置Keyed目录", "设置Keyed子目录名称", ui.Icons.FOLDER
            )
            ui.print_menu_item(
                "5", "设置默认CSV文件名", "设置默认输出CSV文件名", ui.Icons.FILE
            )
            ui.print_menu_item("b", "返回上级", "返回上级菜单", ui.Icons.BACK)

            ui.print_separator()

            choice = input(ui.get_input_prompt("请选择操作", options="1-5, b")).strip()

            if choice == "1":
                self._set_string_config(
                    lang_config, "cn_language", "中文语言目录名称", "ChineseSimplified"
                )
            elif choice == "2":
                self._set_string_config(
                    lang_config, "en_language", "英文语言目录名称", "English"
                )
            elif choice == "3":
                self._set_string_config(
                    lang_config, "definjected_dir", "DefInjected目录名称", "DefInjected"
                )
            elif choice == "4":
                self._set_string_config(
                    lang_config, "keyed_dir", "Keyed目录名称", "Keyed"
                )
            elif choice == "5":
                self._set_string_config(
                    lang_config,
                    "output_csv",
                    "默认CSV文件名",
                    "extracted_translations.csv",
                )
            elif choice.lower() == "b":
                break
            else:
                ui.print_warning("无效选择，请重新输入")

    def _show_log_config(self) -> None:
        """显示日志配置"""
        while True:
            ui.print_header("日志配置", ui.Icons.LOG)

            log_config = self.config_manager.log_config

            # 显示配置和操作选项
            ui.print_section_header("日志配置", ui.Icons.INFO)

            # 配置项列表
            config_items = [
                (
                    "1",
                    "日志级别",
                    log_config.get_value("log_level", "INFO"),
                    ui.Icons.LOG,
                    "设置日志记录级别",
                ),
                (
                    "2",
                    "记录到文件",
                    "是" if log_config.get_value("log_to_file", True) else "否",
                    ui.Icons.FILE,
                    "开启/关闭文件记录",
                ),
                (
                    "3",
                    "输出到控制台",
                    "是" if log_config.get_value("log_to_console", False) else "否",
                    ui.Icons.CONSOLE,
                    "开启/关闭控制台输出",
                ),
                (
                    "4",
                    "文件大小限制",
                    f"{log_config.get_value('log_file_size', 10)}MB",
                    ui.Icons.SIZE,
                    "设置日志文件大小限制",
                ),
                (
                    "5",
                    "备份文件数量",
                    f"{log_config.get_value('log_backup_count', 5)}个",
                    ui.Icons.BACKUP,
                    "设置备份文件数量",
                ),
                (
                    "6",
                    "启动时自动清理",
                    "是" if log_config.get_value("auto_cleanup_logs", True) else "否",
                    ui.Icons.CLEANUP,
                    "开启/关闭启动时自动清理日志",
                ),
                (
                    "7",
                    "启动时清理所有日志",
                    (
                        "是"
                        if log_config.get_value("cleanup_all_logs_on_startup", False)
                        else "否"
                    ),
                    ui.Icons.DELETE,
                    "开启：清理所有日志；关闭：清理指定天数",
                ),
                (
                    "8",
                    "日志保留天数",
                    f"{log_config.get_value('log_retention_days', 7)}天",
                    ui.Icons.TIME,
                    "设置日志保留天数",
                ),
            ]

            # 显示配置项
            for key, label, value, icon, description in config_items:
                ui.print_menu_item(
                    key, f"{label}: {value}", description, icon, compact=True
                )

            # 额外操作
            ui.print_menu_item(
                "9",
                "手动清理日志",
                "立即清理指定天数前的日志文件",
                ui.Icons.CLEANUP,
                compact=True,
            )
            ui.print_menu_item(
                "0",
                "清理所有日志",
                "立即清理所有日志文件（谨慎使用）",
                ui.Icons.DELETE,
                compact=True,
            )
            ui.print_menu_item(
                "b", "返回上级", "返回上级菜单", ui.Icons.BACK, compact=True
            )

            ui.print_separator()

            choice = input(
                ui.get_input_prompt("请选择操作", options="1-9, 0, b")
            ).strip()

            if choice == "1":
                self._set_log_level(log_config)
            elif choice == "2":
                current = log_config.get_value("log_to_file", True)
                log_config.set_value("log_to_file", not current)
                ui.print_success(f"文件记录已{'关闭' if current else '开启'}")
            elif choice == "3":
                current = log_config.get_value("log_to_console", False)
                log_config.set_value("log_to_console", not current)
                ui.print_success(f"控制台输出已{'关闭' if current else '开启'}")
            elif choice == "4":
                self._set_number_config(
                    log_config, "log_file_size", "日志文件大小(MB)", 1, 100, 10
                )
            elif choice == "5":
                self._set_number_config(
                    log_config, "log_backup_count", "备份文件数量", 1, 20, 5
                )
            elif choice == "6":
                current = log_config.get_value("auto_cleanup_logs", True)
                log_config.set_value("auto_cleanup_logs", not current)
                ui.print_success(f"启动时自动清理日志已{'关闭' if current else '开启'}")
            elif choice == "7":
                current = log_config.get_value("cleanup_all_logs_on_startup", False)
                log_config.set_value("cleanup_all_logs_on_startup", not current)
                mode = "清理所有日志" if not current else "清理指定天数"
                ui.print_success(f"启动时清理模式已切换为：{mode}")
            elif choice == "8":
                self._set_number_config(
                    log_config, "log_retention_days", "日志保留天数", 1, 30, 7
                )
            elif choice == "9":
                self._cleanup_old_logs_ui()
            elif choice == "0":
                self._cleanup_all_logs_ui()
            elif choice.lower() == "b":
                break
            else:
                ui.print_warning("无效选择，请重新输入")

    def _show_ui_config(self) -> None:
        """显示界面配置"""
        while True:
            ui.print_header("界面配置", ui.Icons.UI)

            ui_config = self.config_manager.ui_config

            # 显示配置和操作选项
            ui.print_section_header("界面配置", ui.Icons.INFO)

            # 配置项列表
            config_items = [
                (
                    "1",
                    "界面主题",
                    ui_config.get_value("theme", "default"),
                    ui.Icons.THEME,
                    "选择界面主题",
                ),
                (
                    "2",
                    "界面语言",
                    ui_config.get_value("language", "zh_CN"),
                    ui.Icons.LANGUAGE,
                    "选择界面显示语言",
                ),
                (
                    "3",
                    "显示进度条",
                    "是" if ui_config.get_value("show_progress", True) else "否",
                    ui.Icons.PROGRESS,
                    "开启/关闭进度条显示",
                ),
                (
                    "4",
                    "确认操作",
                    "是" if ui_config.get_value("confirm_actions", True) else "否",
                    ui.Icons.CONFIRM,
                    "开启/关闭操作确认",
                ),
                (
                    "5",
                    "自动保存",
                    "是" if ui_config.get_value("auto_save", True) else "否",
                    ui.Icons.SAVE,
                    "开启/关闭自动保存",
                ),
            ]

            # 显示配置项
            for key, label, value, icon, description in config_items:
                ui.print_menu_item(
                    key, f"{label}: {value}", description, icon, compact=True
                )

            # 额外操作
            ui.print_menu_item(
                "b", "返回上级", "返回上级菜单", ui.Icons.BACK, compact=True
            )

            ui.print_separator()

            choice = input(ui.get_input_prompt("请选择操作", options="1-5, b")).strip()

            if choice == "1":
                self._set_theme_config(ui_config)
            elif choice == "2":
                self._set_language_config(ui_config)
            elif choice == "3":
                current = ui_config.get_value("show_progress", True)
                ui_config.set_value("show_progress", not current)
                ui.print_success(f"进度条显示已{'关闭' if current else '开启'}")
            elif choice == "4":
                current = ui_config.get_value("confirm_actions", True)
                ui_config.set_value("confirm_actions", not current)
                ui.print_success(f"操作确认已{'关闭' if current else '开启'}")
            elif choice == "5":
                current = ui_config.get_value("auto_save", True)
                ui_config.set_value("auto_save", not current)
                ui.print_success(f"自动保存已{'关闭' if current else '开启'}")
            elif choice.lower() == "b":
                break
            else:
                ui.print_warning("无效选择，请重新输入")

    def _set_string_config(
        self, config_obj, key: str, label: str, default: str
    ) -> None:
        """设置字符串配置"""
        current_value = config_obj.get_value(key, default)
        print(f"   当前值: {current_value}")

        new_value = input(f"请输入{label} (留空保持当前值): ").strip()
        if new_value:
            config_obj.set_value(key, new_value)
            ui.print_success(f"{label}已更新为: {new_value}")
        else:
            ui.print_info(f"{label}保持不变")

    def _set_number_config(
        self, config_obj, key: str, label: str, min_val: int, max_val: int, default: int
    ) -> None:
        """设置数字配置"""
        current_value = config_obj.get_value(key, default)
        print(f"   当前值: {current_value}")
        print(f"   有效范围: {min_val}-{max_val}")

        try:
            new_value = input(f"请输入{label} (留空保持当前值): ").strip()
            if new_value:
                new_value = int(new_value)
                if min_val <= new_value <= max_val:
                    config_obj.set_value(key, new_value)
                    ui.print_success(f"{label}已更新为: {new_value}")
                else:
                    ui.print_error(f"值必须在 {min_val}-{max_val} 范围内")
            else:
                ui.print_info(f"{label}保持不变")
        except ValueError:
            ui.print_error("请输入有效的数字")

    def _set_log_level(self, log_config) -> None:
        """设置日志级别"""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        current = log_config.get_value("log_level", "INFO")

        print(f"   当前级别: {current}")
        print("   可选级别:")
        for i, level in enumerate(levels, 1):
            print(f"     {i}. {level}")

        try:
            choice = input("请选择日志级别 (1-4, 留空保持当前值): ").strip()
            if choice:
                choice = int(choice)
                if 1 <= choice <= len(levels):
                    new_level = levels[choice - 1]
                    log_config.set_value("log_level", new_level)
                    ui.print_success(f"日志级别已更新为: {new_level}")
                else:
                    ui.print_error("无效选择")
            else:
                ui.print_info("日志级别保持不变")
        except ValueError:
            ui.print_error("请输入有效的数字")

    def _set_theme_config(self, ui_config) -> None:
        """设置主题配置"""
        themes = ["default", "dark", "light"]
        current = ui_config.get_value("theme", "default")

        print(f"   当前主题: {current}")
        print("   可选主题:")
        for i, theme in enumerate(themes, 1):
            print(f"     {i}. {theme}")

        try:
            choice = input("请选择界面主题 (1-3, 留空保持当前值): ").strip()
            if choice:
                choice = int(choice)
                if 1 <= choice <= len(themes):
                    new_theme = themes[choice - 1]
                    ui_config.set_value("theme", new_theme)
                    ui.print_success(f"界面主题已更新为: {new_theme}")
                else:
                    ui.print_error("无效选择")
            else:
                ui.print_info("界面主题保持不变")
        except ValueError:
            ui.print_error("请输入有效的数字")

    def _set_language_config(self, ui_config) -> None:
        """设置语言配置"""
        languages = [("zh_CN", "简体中文"), ("en_US", "English")]
        current = ui_config.get_value("language", "zh_CN")

        print(f"   当前语言: {current}")
        print("   可选语言:")
        for i, (code, name) in enumerate(languages, 1):
            print(f"     {i}. {name} ({code})")

        try:
            choice = input("请选择界面语言 (1-2, 留空保持当前值): ").strip()
            if choice:
                choice = int(choice)
                if 1 <= choice <= len(languages):
                    new_lang = languages[choice - 1][0]
                    ui_config.set_value("language", new_lang)
                    ui.print_success(f"界面语言已更新为: {languages[choice - 1][1]}")
                else:
                    ui.print_error("无效选择")
            else:
                ui.print_info("界面语言保持不变")
        except ValueError:
            ui.print_error("请输入有效的数字")

    def _validate_all_configs(self) -> None:
        """验证所有配置"""
        ui.print_header("配置验证", ui.Icons.CHECK)

        ui.print_info("正在验证所有配置...")

        results = self.validator.validate_all_configs(self.config_manager)

        ui.print_section_header("验证结果", ui.Icons.RESULT)

        all_valid = True
        for config_name, result in results.items():
            status_icon = "✓" if result.is_valid else "✗"
            error_count = len(result.errors)
            warning_count = len(result.warnings)

            status_text = f"{status_icon} 错误:{error_count} 警告:{warning_count}"
            ui.print_key_value(f"{config_name}配置", status_text, ui.Icons.MODULE)

            if not result.is_valid:
                all_valid = False
                for error in result.errors:
                    ui.print_error(f"  - {error}")

            for warning in result.warnings:
                ui.print_warning(f"  - {warning}")

        if all_valid:
            ui.print_success("所有配置验证通过！")
        else:
            ui.print_error("部分配置存在问题，请检查并修正")

        input("\n按回车键继续...")

    def _backup_config(self) -> None:
        """备份配置"""
        ui.print_header("备份配置", ui.Icons.BACKUP)

        if self.config_manager.backup_config():
            ui.print_success("配置备份成功")
        else:
            ui.print_error("配置备份失败")

        input("\n按回车键继续...")

    def _cleanup_old_logs_ui(self) -> None:
        """清理旧日志文件 - UI包装"""
        from utils.logging_config import LoggingConfig

        ui.print_header("清理旧日志", ui.Icons.CLEANUP)

        try:
            # 显示当前日志信息
            log_info = LoggingConfig.get_log_info()
            if "error" in log_info:
                ui.print_error(f"获取日志信息失败: {log_info['error']}")
                input("\n按回车键继续...")
                return

            if "message" in log_info:
                ui.print_info(log_info["message"])
                input("\n按回车键继续...")
                return

            ui.print_info(f"当前日志文件: {log_info['total_files']} 个")
            ui.print_info(f"总大小: {log_info['total_size_mb']:.2f} MB")

            # 获取用户输入的天数
            days_input = input("\n请输入要保留的天数 (默认7天): ").strip()
            try:
                days = int(days_input) if days_input else 7
                if days < 0:
                    ui.print_error("天数不能为负数")
                    input("\n按回车键继续...")
                    return
            except ValueError:
                ui.print_error("请输入有效的数字")
                input("\n按回车键继续...")
                return

            # 确认清理
            if confirm_action(f"确定要清理 {days} 天前的日志文件吗？"):
                LoggingConfig.cleanup_old_logs(days)
            else:
                ui.print_info("取消清理操作")

        except Exception as e:
            ui.print_error(f"清理日志时发生错误: {str(e)}")

        input("\n按回车键继续...")

    def _cleanup_all_logs_ui(self) -> None:
        """清理所有日志文件 - UI包装"""
        from utils.logging_config import LoggingConfig

        ui.print_header("清理所有日志", ui.Icons.DELETE)

        try:
            # 显示当前日志信息
            log_info = LoggingConfig.get_log_info()
            if "error" in log_info:
                ui.print_error(f"获取日志信息失败: {log_info['error']}")
                input("\n按回车键继续...")
                return

            if "message" in log_info:
                ui.print_info(log_info["message"])
                input("\n按回车键继续...")
                return

            ui.print_warning(
                f"⚠️ 当前有 {log_info['total_files']} 个日志文件，总大小 {log_info['total_size_mb']:.2f} MB"
            )
            ui.print_warning("⚠️ 此操作将删除所有日志文件，无法恢复！")

            # 双重确认
            if confirm_action("确定要删除所有日志文件吗？"):
                if confirm_action("请再次确认：删除所有日志文件？"):
                    LoggingConfig.cleanup_all_logs()
                else:
                    ui.print_info("取消清理操作")
            else:
                ui.print_info("取消清理操作")

        except Exception as e:
            ui.print_error(f"清理所有日志时发生错误: {str(e)}")

        input("\n按回车键继续...")

    def _restore_config(self) -> None:
        """恢复配置"""
        ui.print_header("恢复配置", ui.Icons.RESTORE)

        backup_path = input("请输入备份文件路径: ").strip()
        if backup_path:
            if self.config_manager.restore_config(backup_path):
                ui.print_success("配置恢复成功")
            else:
                ui.print_error("配置恢复失败")
        else:
            ui.print_info("取消恢复操作")

        input("\n按回车键继续...")

    def _reset_config(self) -> None:
        """重置配置"""
        ui.print_header("重置配置", ui.Icons.RESET)

        if ui.confirm("确定要重置所有配置为默认值吗？此操作不可撤销！"):
            self.config_manager.reset_to_defaults()
            if self.config_manager.save_config():
                ui.print_success("配置已重置为默认值")
            else:
                ui.print_error("保存重置后的配置失败")
        else:
            ui.print_info("取消重置操作")

        input("\n按回车键继续...")
