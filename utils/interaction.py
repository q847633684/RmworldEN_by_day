"""
通用交互工具模块
提供所有功能模块共用的交互函数
"""

import os
from pathlib import Path
from typing import Optional, List
from .path_manager import PathManager
from .ui_style import ui, display_mods_with_adaptive_width, _get_mod_display_name

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
        "3",
        "智能翻译",
        "自动选择最佳翻译器（Java/Python）",
        ui.Icons.TRANSLATE,
        compact=True,
    )
    ui.print_menu_item(
        "4", "导入模板", "将翻译后的 CSV 导入翻译模板", ui.Icons.IMPORT, compact=True
    )

    # 高级功能 - 使用紧凑模式
    ui.print_section_header("高级功能", ui.Icons.ADVANCED)
    ui.print_menu_item("5", "批量处理", "处理多个模组", ui.Icons.BATCH, compact=True)
    ui.print_menu_item("6", "配置管理", "管理翻译配置", ui.Icons.SETTINGS, compact=True)
    ui.print_menu_item(
        "7", "语料生成", "生成英-中平行语料", ui.Icons.CORPUS, compact=True
    )

    # 退出选项
    ui.print_section_header("退出程序", ui.Icons.EXIT)
    ui.print_menu_item("q", "退出", "退出程序", ui.Icons.EXIT, compact=True)

    ui.print_separator()

    return input(ui.get_input_prompt("请选择模式", options="1-7, q")).strip()


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

                ui.print_success("🎮 选择Steam Workshop模组")
                ui.print_info(f"📁 路径：{selected_mod}")
                ui.print_info(f"📦 模组名称：{mod_display_name}")
                ui.print_info(f"🆔 模组ID：{mod_id}")
                path_manager.remember_path("mod_dir", selected_mod)
                # 对选择的模组进行版本检测
                return path_manager.detect_version_and_choose(selected_mod)
            else:
                ui.print_error(f"无效选择，请输入 1-{len(found_mods)} 或 b")
        except ValueError:
            ui.print_error("无效输入，请输入数字或 b")


def _scan_third_party_mods(available_mod_dirs: List[str]) -> Optional[str]:
    """扫描第三方模组"""
    ui.print_info("📦 正在扫描第三方模组...")

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
        ui.print_warning("⚠️ 未找到任何第三方模组")
        return None

    # 使用自适应列宽显示模组列表
    display_mods_with_adaptive_width(all_mods)

    ui.print_menu_item("b", "🔙 返回")

    while True:
        choice = input(f"\n请选择模组 (1-{len(all_mods)}, b) 或直接输入路径: ").strip()

        if choice.lower() == "b":
            # 返回上级菜单
            ui.print_info("🔙 返回")
            return None
        elif choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(all_mods):
                selected_path = all_mods[choice_num - 1]
                mod_display_name = _get_mod_display_name(selected_path)

                ui.print_success("📦 选择第三方模组")
                ui.print_info(f"📁 路径：{selected_path}")
                ui.print_info(f"📦 模组名称：{mod_display_name}")
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
    return input(f"{message} [y/n]: ").lower() == "y"


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
