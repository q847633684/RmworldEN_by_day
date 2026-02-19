"""
API配置界面

提供API配置的用户界面
"""

from typing import Dict, Any
from utils.logging_config import get_logger
from utils.ui_style import ui
from utils.interaction import confirm_action
from ..api.base_api import BaseAPIConfig


class APIConfigUI:
    """API配置界面"""

    def __init__(self, config_manager):
        """
        初始化API配置界面

        Args:
            config_manager: 用户配置管理器
        """
        self.logger = get_logger(f"{__name__}.APIConfigUI")
        self.config_manager = config_manager
        self.api_manager = config_manager.api_manager

    def _auto_save_and_test(self, api_config: BaseAPIConfig) -> None:
        """
        自动保存配置并测试连接

        Args:
            api_config: API配置对象
        """
        try:
            # 自动保存配置 - 使用同一个配置管理器实例
            if self.config_manager.save_config():
                ui.print_success("✅ 配置已自动保存")
            else:
                ui.print_warning("⚠️ 配置保存失败")

            # 自动测试连接（如果配置完整且有效）
            if api_config.is_complete() and api_config.validate():
                ui.print_info("🔄 正在自动测试连接...")
                test_success, test_message = api_config.test_connection()
                if test_success:
                    ui.print_success(f"✅ 连接测试成功: {test_message}")
                else:
                    ui.print_error(f"❌ 连接测试失败: {test_message}")
            else:
                ui.print_info("ℹ️ 配置不完整，跳过连接测试")

        except Exception as e:
            self.logger.error(f"自动保存和测试失败: {e}")
            ui.print_error(f"❌ 自动操作失败: {e}")

    def show_api_menu(self) -> None:
        """显示API配置主菜单"""
        while True:
            ui.print_header("API配置管理", ui.Icons.API)

            # 显示API配置和操作选项
            ui.print_section_header("API配置", ui.Icons.INFO)

            # 获取API状态
            _ = self.api_manager.get_api_status()
            apis = self.api_manager.get_supported_apis()

            # 配置项列表
            config_items = []

            # 显示配置项
            for key, label, value, icon, description in config_items:
                ui.print_menu_item(
                    key, f"{label}: {value}", description, icon, compact=True
                )

            # API提供商列表
            ui.print_section_header("API提供商", ui.Icons.API)
            for i, (api_type, api_config) in enumerate(apis.items(), 4):
                # 状态图标
                enabled_icon = "🟢" if api_config.is_enabled() else "🔴"
                config_icon = "🟢" if api_config.is_complete() else "🟡"
                valid_icon = "🟢" if api_config.validate() else "🔴"

                # 连接测试状态
                test_success, test_message = api_config.test_connection()
                connection_icon = "🟢" if test_success else "🔴"

                # 状态说明
                enabled_text = "启用" if api_config.is_enabled() else "禁用"
                config_text = "完整" if api_config.is_complete() else "不完整"
                valid_text = "有效" if api_config.validate() else "无效"
                connection_text = "连通" if test_success else "失败"

                status_text = f"{enabled_icon}{enabled_text} {config_icon}{config_text} {valid_icon}{valid_text} {connection_icon}{connection_text}"

                ui.print_menu_item(
                    str(i),
                    f"{api_config.name}: {status_text}",
                    f"配置{api_config.name}",
                    ui.Icons.API,
                    compact=True,
                )

                # 显示详细状态信息
                if not test_success and api_config.is_enabled():
                    ui.print_warning(f"   └── 连接问题: {test_message}")

            # 额外操作
            ui.print_menu_item(
                "b", "返回上级", "返回上级菜单", ui.Icons.BACK, compact=True
            )

            ui.print_separator()

            choice = input(ui.get_input_prompt("请选择API", options="1-4, b")).strip()

            # 处理API选择
            try:
                api_index = int(choice)
                if 1 <= api_index <= len(apis):
                    api_type = list(apis.keys())[api_index - 1]
                    self._show_api_config(api_type)
                    continue
            except ValueError:
                pass

            # 处理管理选项
            if choice.lower() == "b":
                break
            else:
                ui.print_warning("无效选择，请重新输入")

    def _show_api_summary(self) -> None:
        """显示API状态摘要"""
        ui.print_section_header("API状态", ui.Icons.INFO)

        status = self.api_manager.get_api_status()

        # 统计信息（只统计支持的API）
        supported_apis = status.get("supported_apis", [])
        supported_api_info = {
            api_type: api_info
            for api_type, api_info in status["apis"].items()
            if api_type in supported_apis
        }

        enabled_count = sum(
            1 for api_info in supported_api_info.values() if api_info["enabled"]
        )
        valid_count = sum(
            1 for api_info in supported_api_info.values() if api_info["valid"]
        )
        total_count = len(supported_api_info)

        ui.print_key_value(
            "API统计",
            f"启用:{enabled_count} 有效:{valid_count} 总计:{total_count}",
            ui.Icons.STATS,
        )

        # 显示支持信息
        ui.print_key_value(
            "翻译工具支持",
            f"已实现:{len(supported_apis)} 个API",
            ui.Icons.TOOLS,
        )

    def _show_api_config(self, api_type: str) -> None:
        """显示特定API的配置"""
        api_config = self.api_manager.get_api(api_type)
        if not api_config:
            ui.print_error(f"未找到API: {api_type}")
            return

        while True:
            ui.print_header(f"{api_config.name}配置", ui.Icons.API)

            # 显示API信息
            self._show_api_info(api_config)

            # 显示配置字段
            self._show_api_fields(api_config)

            # 显示操作菜单
            ui.print_section_header("操作选项", ui.Icons.TOOLS)
            ui.print_menu_item("1", "修改配置", "修改API配置参数", ui.Icons.EDIT)
            ui.print_menu_item("2", "启用/禁用", "切换API启用状态", ui.Icons.TOGGLE)
            ui.print_menu_item("4", "重置配置", "重置为默认配置", ui.Icons.RESET)
            ui.print_menu_item("b", "返回上级", "返回API列表", ui.Icons.BACK)

            # 显示自动化功能提示
            ui.print_info("ℹ️ 配置修改后将自动保存并测试连接")

            ui.print_separator()

            choice = input(ui.get_input_prompt("请选择操作", options="1-4, b")).strip()

            if choice == "1":
                self._edit_api_config(api_config)
            elif choice == "2":
                self._toggle_api_enabled(api_config)
            elif choice == "4":
                self._reset_api_config(api_config)
            elif choice.lower() == "b":
                break
            else:
                ui.print_warning("无效选择，请重新输入")

    def _show_api_info(self, api_config: BaseAPIConfig) -> None:
        """显示API基本信息"""
        ui.print_section_header("基本信息", ui.Icons.INFO)

        display_info = api_config.get_display_info()

        ui.print_key_value("API名称", display_info["name"], ui.Icons.API)
        ui.print_key_value("API类型", display_info["type"], ui.Icons.TYPE)
        ui.print_key_value(
            "启用状态", "启用" if display_info["enabled"] else "禁用", ui.Icons.STATUS
        )
        ui.print_key_value("配置状态", display_info["status"], ui.Icons.CONFIG)
        ui.print_key_value(
            "验证状态", "通过" if display_info["valid"] else "失败", ui.Icons.VALID
        )

    def _show_api_fields(self, api_config: BaseAPIConfig) -> None:
        """显示API配置字段"""
        ui.print_section_header("配置参数", ui.Icons.SETTINGS)

        schema = api_config.get_schema()

        for field_name, field_info in schema.items():
            value = api_config.get_value(field_name)

            # 处理敏感信息显示
            if field_info.get("type") == "password" and value:
                if len(str(value)) > 8:
                    display_value = f"{str(value)[:4]}****{str(value)[-4:]}"
                else:
                    display_value = "****"
            else:
                display_value = value if value is not None else "未设置"

            label = field_info.get("label", field_name)
            ui.print_key_value(label, str(display_value), ui.Icons.FIELD)

    def _edit_api_config(self, api_config: BaseAPIConfig) -> None:
        """编辑API配置"""
        schema = api_config.get_schema()

        ui.print_header(f"编辑{api_config.name}配置", ui.Icons.EDIT)

        # 显示可编辑字段
        fields = list(schema.keys())

        ui.print_section_header("可编辑字段", ui.Icons.FIELD)

        for i, field_name in enumerate(fields, 1):
            field_info = schema[field_name]
            label = field_info.get("label", field_name)
            description = field_info.get("description", "")
            required = " (必需)" if field_info.get("required", False) else ""

            ui.print_menu_item(
                str(i), label, f"{description}{required}", ui.Icons.FIELD
            )

        ui.print_menu_item(
            "a", "编辑所有字段", "逐一编辑所有配置字段", ui.Icons.EDIT_ALL
        )
        ui.print_menu_item("b", "返回", "返回API配置", ui.Icons.BACK)

        ui.print_separator()

        choice = input(
            ui.get_input_prompt("请选择要编辑的字段", options=f"1-{len(fields)}, a, b")
        ).strip()

        if choice.lower() == "a":
            # 编辑所有字段
            for field_name in fields:
                self._edit_field(api_config, field_name, schema[field_name])
        elif choice.lower() == "b":
            return
        else:
            try:
                field_index = int(choice)
                if 1 <= field_index <= len(fields):
                    field_name = fields[field_index - 1]
                    self._edit_field(api_config, field_name, schema[field_name])
                else:
                    ui.print_error("无效选择")
            except ValueError:
                ui.print_error("请输入有效的数字")

    def _edit_field(
        self, api_config: BaseAPIConfig, field_name: str, field_info: Dict[str, Any]
    ) -> None:
        """编辑单个字段"""
        field_type = field_info.get("type", "text")
        label = field_info.get("label", field_name)
        description = field_info.get("description", "")
        current_value = api_config.get_value(field_name)

        print(f"\n编辑字段: {label}")
        if description:
            print(f"说明: {description}")

        # 显示当前值
        if field_type == "password" and current_value:
            print("当前值: ****")
        else:
            print(f"当前值: {current_value if current_value is not None else '未设置'}")

        # 根据字段类型处理输入
        if field_type == "select":
            self._edit_select_field(api_config, field_name, field_info)
        elif field_type == "boolean":
            self._edit_boolean_field(api_config, field_name, field_info)
        elif field_type == "number":
            self._edit_number_field(api_config, field_name, field_info)
        else:
            self._edit_text_field(api_config, field_name, field_info)

    def _edit_text_field(
        self, api_config: BaseAPIConfig, field_name: str, field_info: Dict[str, Any]
    ) -> None:
        """编辑文本字段"""
        placeholder = field_info.get("placeholder", "")
        prompt = f"请输入{field_info.get('label', field_name)}"
        if placeholder:
            prompt += f" ({placeholder})"
        prompt += " (留空保持当前值): "

        new_value = input(prompt).strip()
        if new_value:
            api_config.set_value(field_name, new_value)
            ui.print_success(f"{field_info.get('label', field_name)}已更新")
            # 自动保存和测试
            self._auto_save_and_test(api_config)
        else:
            ui.print_info("保持当前值不变")

    def _edit_select_field(
        self, api_config: BaseAPIConfig, field_name: str, field_info: Dict[str, Any]
    ) -> None:
        """编辑选择字段"""
        options = field_info.get("options", [])
        if not options:
            ui.print_error("没有可选选项")
            return

        print("可选值:")
        for i, option in enumerate(options, 1):
            if isinstance(option, dict):
                value = option.get("value")
                label = option.get("label", value)
                print(f"  {i}. {label} ({value})")
            else:
                print(f"  {i}. {option}")

        try:
            choice = input(f"请选择 (1-{len(options)}, 留空保持当前值): ").strip()
            if choice:
                choice = int(choice)
                if 1 <= choice <= len(options):
                    option = options[choice - 1]
                    if isinstance(option, dict):
                        new_value = option.get("value")
                    else:
                        new_value = option

                    api_config.set_value(field_name, new_value)
                    ui.print_success(
                        f"{field_info.get('label', field_name)}已更新为: {new_value}"
                    )
                    # 自动保存和测试
                    self._auto_save_and_test(api_config)
                else:
                    ui.print_error("无效选择")
            else:
                ui.print_info("保持当前值不变")
        except ValueError:
            ui.print_error("请输入有效的数字")

    def _edit_boolean_field(
        self, api_config: BaseAPIConfig, field_name: str, field_info: Dict[str, Any]
    ) -> None:
        """编辑布尔字段"""
        current_value = api_config.get_value(field_name, False)

        choice = (
            input(f"请选择 (y/n, 留空保持当前值 {'是' if current_value else '否'}): ")
            .strip()
            .lower()
        )
        if choice in ["y", "yes", "true", "1", "是"]:
            api_config.set_value(field_name, True)
            ui.print_success(f"{field_info.get('label', field_name)}已设置为: 是")
            # 自动保存和测试
            self._auto_save_and_test(api_config)
        elif choice in ["n", "no", "false", "0", "否"]:
            api_config.set_value(field_name, False)
            ui.print_success(f"{field_info.get('label', field_name)}已设置为: 否")
            # 自动保存和测试
            self._auto_save_and_test(api_config)
        elif choice == "":
            ui.print_info("保持当前值不变")
        else:
            ui.print_error("无效输入，请输入 y/n")

    def _edit_number_field(
        self, api_config: BaseAPIConfig, field_name: str, field_info: Dict[str, Any]
    ) -> None:
        """编辑数字字段"""
        min_val = field_info.get("min")
        max_val = field_info.get("max")

        range_text = ""
        if min_val is not None and max_val is not None:
            range_text = f" (范围: {min_val}-{max_val})"
        elif min_val is not None:
            range_text = f" (最小值: {min_val})"
        elif max_val is not None:
            range_text = f" (最大值: {max_val})"

        try:
            new_value = input(
                f"请输入{field_info.get('label', field_name)}{range_text} (留空保持当前值): "
            ).strip()
            if new_value:
                if field_info.get("integer", False):
                    new_value = int(new_value)
                else:
                    new_value = float(new_value)

                # 验证范围
                if min_val is not None and new_value < min_val:
                    ui.print_error(f"值不能小于 {min_val}")
                    return
                if max_val is not None and new_value > max_val:
                    ui.print_error(f"值不能大于 {max_val}")
                    return

                api_config.set_value(field_name, new_value)
                ui.print_success(
                    f"{field_info.get('label', field_name)}已更新为: {new_value}"
                )
                # 自动保存和测试
                self._auto_save_and_test(api_config)
            else:
                ui.print_info("保持当前值不变")
        except ValueError:
            ui.print_error("请输入有效的数字")

    def _test_api_connection(self, api_type: str) -> None:
        """测试API连接"""
        ui.print_header(f"测试{api_type}连接", ui.Icons.TEST)

        ui.print_info("正在测试API连接...")

        success, message = self.api_manager.test_api(api_type)

        if success:
            ui.print_success(f"连接测试成功: {message}")
        else:
            ui.print_error(f"连接测试失败: {message}")

        input("\n按回车键继续...")

    def _toggle_api_enabled(self, api_config: BaseAPIConfig) -> None:
        """切换API启用状态"""
        current_status = api_config.is_enabled()
        new_status = not current_status

        api_config.set_enabled(new_status)

        status_text = "启用" if new_status else "禁用"
        ui.print_success(f"{api_config.name}已{status_text}")

    def _reset_api_config(self, api_config: BaseAPIConfig) -> None:
        """重置API配置"""
        ui.print_warning("⚠️ 重置操作将会:")
        ui.print_warning("   • 清空所有AccessKey信息")
        ui.print_warning("   • 禁用API")
        ui.print_warning("   • 恢复所有设置为默认值")
        ui.print_warning("   • 此操作不可撤销!")

        print()
        if confirm_action(f"确定要重置{api_config.name}的所有配置吗？"):
            api_config.reset_to_defaults()
            ui.print_success(f"{api_config.name}配置已重置为默认值")
            # 自动保存重置后的配置
            self._auto_save_and_test(api_config)
        else:
            ui.print_info("取消重置操作")
