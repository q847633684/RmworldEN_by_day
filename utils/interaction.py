"""
通用交互工具模块
提供所有功能模块共用的交互函数
"""

import os
from pathlib import Path
from typing import Optional, List
from colorama import Fore, Style
from .path_manager import PathManager
from .ui_style import ui

# 全局路径管理器实例
path_manager = PathManager()


def show_main_menu() -> str:
    """显示主菜单并返回用户选择"""
    ui.print_header("Day Translation 主菜单")

    # 核心功能 - 使用紧凑模式
    ui.print_section_header("核心功能", ui.Icons.CORE)
    ui.print_menu_item(
        "1",
        "完整流程",
        "提取→Java机翻→导入 一键完成",
        ui.Icons.RUNNING,
        is_recommended=True,
        compact=True,
    )
    ui.print_menu_item(
        "2", "提取模板", "提取翻译模板并生成 CSV 文件", ui.Icons.TEMPLATE, compact=True
    )
    ui.print_menu_item(
        "3", "Java机翻", "使用Java工具进行高性能翻译", ui.Icons.TRANSLATE, compact=True
    )
    ui.print_menu_item(
        "4", "导入模板", "将翻译后的 CSV 导入翻译模板", ui.Icons.IMPORT, compact=True
    )

    # 高级功能 - 使用紧凑模式
    ui.print_section_header("高级功能", ui.Icons.ADVANCED)
    ui.print_menu_item(
        "5",
        "Python机翻",
        "使用Python阿里云翻译 CSV 文件",
        ui.Icons.TRANSLATE,
        compact=True,
    )
    ui.print_menu_item("6", "批量处理", "处理多个模组", ui.Icons.BATCH, compact=True)
    ui.print_menu_item("7", "配置管理", "管理翻译配置", ui.Icons.SETTINGS, compact=True)
    ui.print_menu_item(
        "8", "语料生成", "生成英-中平行语料", ui.Icons.CORPUS, compact=True
    )

    # 退出选项
    ui.print_section_header("退出程序", ui.Icons.EXIT)
    ui.print_menu_item("q", "退出", "退出程序", ui.Icons.EXIT, compact=True)

    ui.print_separator()

    return input(ui.get_input_prompt("请选择模式", options="1-8, q")).strip()


def select_csv_path_with_history() -> Optional[str]:
    """选择CSV文件路径，支持历史记录"""
    ui.print_info("请输入要翻译的 CSV 文件路径:")

    # 显示CSV文件历史记录
    csv_history = path_manager.get_history_list("import_csv")
    if csv_history:
        ui.print_section_header("CSV文件历史记录", ui.Icons.HISTORY)
        for i, path in enumerate(csv_history, 1):
            ui.print_menu_item(str(i), os.path.basename(path), path, ui.Icons.FILE)
        ui.print_menu_item("0", "输入新路径", "或直接粘贴完整CSV路径", ui.Icons.FILE)

    csv_path: Optional[str] = None
    while True:
        prompt_text = (
            ui.get_input_prompt(
                "请选择",
                options=f"0-{len(csv_history)}",
                icon="或直接输入CSV路径 (q退出)",
            )
            if csv_history
            else ui.get_input_prompt("请输入CSV文件路径", options="q退出")
        )
        choice = input(prompt_text).strip()

        if choice.lower() == "q":
            return None

        if csv_history and choice == "0":
            csv_path = input(ui.get_input_prompt("请输入CSV文件路径")).strip()
        elif csv_history and choice.isdigit() and 1 <= int(choice) <= len(csv_history):
            csv_path = csv_history[int(choice) - 1]

        elif choice:  # 非空输入，当作路径使用
            csv_path = choice
        else:
            ui.print_error("请输入选择或路径")

        if not csv_path:
            ui.print_error("路径不能为空")
            continue

        # 验证CSV文件
        if not os.path.exists(csv_path):
            ui.print_error(f"文件不存在: {csv_path}")
            continue

        if not csv_path.lower().endswith(".csv"):
            ui.print_error("文件必须是CSV格式")
            continue

        # 记住路径
        path_manager.remember_path("import_csv", csv_path)
        ui.print_success(f"选择：{csv_path}")
        return csv_path


def select_mod_path_with_version_detection() -> Optional[str]:
    """选择模组目录，支持版本检测和自动扫描"""
    ui.print_header("模组目录选择", ui.Icons.FOLDER)

    # 扫描常见的RimWorld模组目录
    common_mod_paths = [
        r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods",
        r"C:\Program Files\Steam\steamapps\common\RimWorld\Mods",
        r"D:\Steam\steamapps\common\RimWorld\Mods",
        r"D:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods",
        r"D:\Program Files\Steam\steamapps\common\RimWorld\Mods",
    ]

    available_mod_dirs = []
    for mod_path in common_mod_paths:
        if os.path.exists(mod_path):
            available_mod_dirs.append(mod_path)

    # 显示选项
    ui.print_section_header("自动扫描选项", ui.Icons.SETTINGS)
    ui.print_menu_item(
        "1", "扫描Steam Workshop模组", "自动扫描Steam Workshop模组目录", ui.Icons.SCAN
    )
    if available_mod_dirs:
        ui.print_menu_item(
            "2", "扫描第三方模组目录", "扫描本地第三方模组目录", ui.Icons.SCAN
        )

    # 显示历史记录
    history = path_manager.get_history_list("mod_dir")
    if history:
        ui.print_section_header("历史记录", ui.Icons.HISTORY)
        start_idx = 3 if available_mod_dirs else 2
        for i, hist_path in enumerate(history, start_idx):
            mod_name = os.path.basename(hist_path)
            ui.print_menu_item(str(i), mod_name, hist_path, ui.Icons.FOLDER)
    else:
        ui.print_section_header("历史记录", ui.Icons.HISTORY)
        ui.print_info("暂无历史记录")

    # 添加返回选项
    ui.print_section_header("其他选项", ui.Icons.EXIT)
    ui.print_menu_item("b", "返回主菜单", "返回主菜单", ui.Icons.BACK)

    max_choice = (2 if available_mod_dirs else 1) + len(history)

    while True:
        choice = input(
            ui.get_input_prompt(
                "请选择", options=f"1-{max_choice}, b", icon="或直接输入路径"
            )
        ).strip()

        if choice.lower() == "b":
            # 返回主菜单
            ui.print_info("返回主菜单")
            return None
        elif choice == "1":
            # 扫描Steam Workshop模组
            return _scan_game_mods()
        elif choice == "2" and available_mod_dirs:
            # 扫描第三方模组目录
            return _scan_third_party_mods(available_mod_dirs)
        elif choice.isdigit():
            choice_num = int(choice)
            start_idx = 3 if available_mod_dirs else 2
            if start_idx <= choice_num <= max_choice:
                selected_path = history[choice_num - start_idx]
                ui.print_success(f"选择：{selected_path}")
                # 对历史记录路径也进行版本检测
                return path_manager.detect_version_and_choose(selected_path)
        elif choice:
            # 直接输入路径 - 先获取路径，然后进行版本检测
            selected_path = path_manager.get_path(
                path_type="mod_dir",
                prompt="请输入编号或模组目录路径（支持历史编号或直接输入路径）: ",
                validator_type="mod",
                required=True,
            )
            if selected_path:
                return path_manager.detect_version_and_choose(selected_path)
            return None
        else:
            ui.print_error("请输入选择或路径")


def _scan_game_mods() -> Optional[str]:
    """扫描游戏内置模组"""
    ui.print_header("扫描Steam Workshop模组", ui.Icons.SCAN)

    # Steam Workshop模组路径
    steam_workshop_paths = [
        r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100",
        r"C:\Program Files\Steam\steamapps\workshop\content\294100",
        r"D:\Steam\steamapps\workshop\content\294100",
        r"E:\Steam\steamapps\workshop\content\294100",
    ]

    ui.print_info("正在扫描Steam Workshop目录...")

    found_mods = []
    for workshop_path in steam_workshop_paths:
        if os.path.exists(workshop_path):
            try:
                mods = [
                    d
                    for d in os.listdir(workshop_path)
                    if os.path.isdir(os.path.join(workshop_path, d))
                ]
                for mod_id in mods:
                    mod_path = os.path.join(workshop_path, mod_id)
                    # 检查是否有About目录（RimWorld模组的标准特征）
                    if os.path.exists(os.path.join(mod_path, "About")):
                        found_mods.append(mod_path)
            except (OSError, PermissionError):
                continue

    if not found_mods:
        ui.print_warning("未找到Steam Workshop模组")
        ui.print_info("请确保RimWorld已通过Steam安装")
        return None

    # 使用自适应列宽显示Steam Workshop模组列表
    _display_mods_with_adaptive_width(found_mods)

    ui.print_menu_item("b", "返回", "返回主菜单", ui.Icons.BACK)

    while True:
        choice = input(
            ui.get_input_prompt("请选择模组编号", options=f"1-{len(found_mods)}, b返回")
        ).strip()

        if choice.lower() == "b":
            return None

        try:
            mod_index = int(choice) - 1
            if 0 <= mod_index < len(found_mods):
                selected_mod = found_mods[mod_index]
                mod_display_name = _get_mod_display_name(selected_mod)
                mod_id = os.path.basename(selected_mod)

                print(
                    f"\n   {Fore.CYAN}╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}"
                )
                print(
                    f"   {Fore.CYAN}║{Style.RESET_ALL}  {Fore.GREEN}🎮 选择Steam Workshop模组{Style.RESET_ALL}  {Fore.CYAN}║{Style.RESET_ALL}"
                )
                print(
                    f"   {Fore.CYAN}╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}"
                )
                print(
                    f"   {Fore.CYAN}📁 路径：{Style.RESET_ALL}{Fore.WHITE}{selected_mod}{Style.RESET_ALL}"
                )
                print(
                    f"   {Fore.CYAN}📦 模组名称：{Style.RESET_ALL}{Fore.WHITE}{mod_display_name}{Style.RESET_ALL}"
                )
                print(
                    f"   {Fore.CYAN}🆔 模组ID：{Style.RESET_ALL}{Fore.WHITE}{mod_id}{Style.RESET_ALL}"
                )
                path_manager.remember_path("mod_dir", selected_mod)
                # 对选择的模组进行版本检测
                return path_manager.detect_version_and_choose(selected_mod)
            else:
                print(
                    f"   {Fore.RED}❌ 无效选择，请输入 1-{len(found_mods)} 或 b{Style.RESET_ALL}"
                )
        except ValueError:
            print(f"   {Fore.RED}❌ 无效输入，请输入数字或 b{Style.RESET_ALL}")


def _scan_third_party_mods(available_mod_dirs: List[str]) -> Optional[str]:
    """扫描第三方模组"""
    print(f"\n{Fore.BLUE}📦 正在扫描第三方模组...{Style.RESET_ALL}")

    all_mods = []
    for mod_dir in available_mod_dirs:
        try:
            mods = [
                d
                for d in os.listdir(mod_dir)
                if os.path.isdir(os.path.join(mod_dir, d))
            ]
            for mod in mods:
                mod_path = os.path.join(mod_dir, mod)
                # 检查是否有About目录（RimWorld模组的标准特征）
                if os.path.exists(os.path.join(mod_path, "About")):
                    all_mods.append(mod_path)
        except (OSError, PermissionError):
            continue

    if not all_mods:
        print(f"   {Fore.YELLOW}⚠️ 未找到任何第三方模组{Style.RESET_ALL}")
        return None

    # 使用自适应列宽显示模组列表
    _display_mods_with_adaptive_width(all_mods)

    print(f"{Fore.RED}b. 🔙 返回{Style.RESET_ALL}")

    while True:
        choice = input(
            f"\n{Fore.CYAN}请选择模组 (1-{len(all_mods)}, b) 或直接输入路径: {Style.RESET_ALL}"
        ).strip()

        if choice.lower() == "b":
            # 返回上级菜单
            print(f"   {Fore.YELLOW}🔙 返回{Style.RESET_ALL}")
            return None
        elif choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(all_mods):
                selected_path = all_mods[choice_num - 1]
                mod_display_name = _get_mod_display_name(selected_path)

                print(
                    f"\n   {Fore.CYAN}╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}"
                )
                print(
                    f"   {Fore.CYAN}║{Style.RESET_ALL}  {Fore.GREEN}📦 选择第三方模组{Style.RESET_ALL}  {Fore.CYAN}║{Style.RESET_ALL}"
                )
                print(
                    f"   {Fore.CYAN}╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}"
                )
                print(
                    f"   {Fore.CYAN}📁 路径：{Style.RESET_ALL}{Fore.WHITE}{selected_path}{Style.RESET_ALL}"
                )
                print(
                    f"   {Fore.CYAN}📦 模组名称：{Style.RESET_ALL}{Fore.WHITE}{mod_display_name}{Style.RESET_ALL}"
                )
                path_manager.remember_path("mod_dir", selected_path)
                # 对选择的模组进行版本检测
                return path_manager.detect_version_and_choose(selected_path)
        elif choice:
            # 直接输入路径 - 先获取路径，然后进行版本检测
            selected_path = path_manager.get_path(
                path_type="mod_dir",
                prompt="请输入编号或模组目录路径（支持历史编号或直接输入路径）: ",
                validator_type="mod",
                required=True,
            )
            if selected_path:
                return path_manager.detect_version_and_choose(selected_path)
            return None
        else:
            ui.print_error("请输入选择或路径")


def confirm_action(message: str) -> bool:
    """确认操作"""
    return input(f"{Fore.YELLOW}{message} [y/n]:{Style.RESET_ALL} ").lower() == "y"


def auto_generate_output_path(input_path: str) -> str:
    """自动生成输出CSV文件路径"""
    input_path_obj = Path(input_path)
    return str(input_path_obj.parent / f"{input_path_obj.stem}_zh.csv")


def show_success(message: str):
    """显示成功信息"""
    ui.print_success(message)


def show_error(message: str):
    """显示错误信息"""
    ui.print_error(message)


def show_warning(message: str):
    """显示警告信息"""
    ui.print_warning(message)


def show_info(message: str):
    """显示信息"""
    ui.print_info(message)


def _get_terminal_width() -> int:
    """获取终端宽度"""
    try:
        import shutil

        return shutil.get_terminal_size().columns
    except:
        return 80  # 默认宽度


def _calculate_adaptive_layout(
    mod_names: List[str], terminal_width: int = None
) -> tuple:
    """计算自适应布局参数"""
    if terminal_width is None:
        terminal_width = _get_terminal_width()

    # 预留边框和边距空间
    available_width = terminal_width - 10  # 边框 + 边距

    # 计算每个模组名需要的最大宽度
    max_name_length = max(len(name) for name in mod_names) if mod_names else 10
    # 编号宽度 (如 "81.") + 模组名 + 间距
    item_width = len(str(len(mod_names))) + 1 + max_name_length + 3

    # 计算每行能放多少个模组
    mods_per_line = max(1, available_width // item_width)

    # 限制最大列数，避免过于拥挤
    mods_per_line = min(mods_per_line, 6)

    return mods_per_line, item_width


def _get_mod_display_name(mod_path: str) -> str:
    """获取模组的显示名称"""
    # 首先尝试从About/About.xml读取模组名称
    about_xml_path = os.path.join(mod_path, "About", "About.xml")
    if os.path.exists(about_xml_path):
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(about_xml_path)
            root = tree.getroot()
            # 查找name标签
            name_elem = root.find("name")
            if name_elem is not None and name_elem.text:
                return name_elem.text.strip()
        except:
            pass

    # 如果无法读取XML，使用目录名
    return os.path.basename(mod_path)


def _display_mods_with_adaptive_width(all_mods: List[str]) -> None:
    """使用自适应列宽显示模组列表"""
    mod_names = [_get_mod_display_name(mod_path) for mod_path in all_mods]
    mods_per_line, item_width = _calculate_adaptive_layout(mod_names)

    # 计算边框宽度
    border_width = mods_per_line * item_width + 4  # 4 = 左右边框 + 间距
    border_line = "═" * (border_width - 2)

    # 显示标题
    print(f"\n   {Fore.CYAN}╔{border_line}╗{Style.RESET_ALL}")
    title = f"📦 找到 {len(all_mods)} 个第三方模组"
    title_padding = (border_width - 2 - len(title)) // 2
    print(
        f"   {Fore.CYAN}║{Style.RESET_ALL}{' ' * title_padding}{Fore.GREEN}{title}{Style.RESET_ALL}{' ' * (border_width - 2 - len(title) - title_padding)}{Fore.CYAN}║{Style.RESET_ALL}"
    )
    print(f"   {Fore.CYAN}╚{border_line}╝{Style.RESET_ALL}")

    # 计算需要的行数
    total_lines = (len(all_mods) + mods_per_line - 1) // mods_per_line

    for line in range(total_lines):
        start_idx = line * mods_per_line
        end_idx = min(start_idx + mods_per_line, len(all_mods))

        # 构建当前行的显示内容
        line_content = f"   {Fore.YELLOW}│{Style.RESET_ALL} "
        for i in range(start_idx, end_idx):
            mod_name = mod_names[i]
            # 动态截断模组名
            max_name_len = item_width - len(str(i + 1)) - 4  # 预留编号和间距空间
            display_name = (
                mod_name[: max_name_len - 3] + "..."
                if len(mod_name) > max_name_len
                else mod_name
            )
            line_content += f"{Fore.CYAN}{i+1:2d}.{Style.RESET_ALL} {Fore.WHITE}{display_name:<{max_name_len}}{Style.RESET_ALL} "

        # 填充剩余空间
        remaining_slots = mods_per_line - (end_idx - start_idx)
        if remaining_slots > 0:
            line_content += " " * (remaining_slots * item_width)

        line_content += f"{Fore.YELLOW}│{Style.RESET_ALL}"
        print(line_content)

    # 底部边框
    bottom_line = "─" * (border_width - 2)
    print(f"   {Fore.YELLOW}└{bottom_line}┘{Style.RESET_ALL}")
