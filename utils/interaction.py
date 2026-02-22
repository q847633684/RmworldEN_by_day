"""
通用交互工具模块
提供所有功能模块共用的交互函数
"""

import os
from typing import Optional, List
from user_config import UserConfigManager
from .constants import (
    PATH_HISTORY_IMPORT_CSV,
    PATH_HISTORY_MOD_DIR,
    get_common_mod_paths,
    get_steam_workshop_paths,
)
from .ui_style import (
    ui,
    display_mods_with_adaptive_width,
    _get_mod_display_name,
    UIStyle,
)

def _get_path_manager():
    """获取 PathManager，统一从 UserConfigManager 获取"""
    return UserConfigManager.get_instance().path_manager


def prompt_choose_from_list(
    options: List[str], title: str, default: str = "1"
) -> Optional[str]:
    """
    让用户从列表中选一项，返回选中的项或 None（取消）。
    供提取、批量等流程复用「请选择版本」类交互。
    """
    if not options:
        return None
    ui.print_info(title)
    for i, v in enumerate(options, 1):
        ui.print_info(f"  {i}. {v}")
    opts = "/".join(str(i) for i in range(1, len(options) + 1))
    choice = safe_input(ui.get_input_prompt("请选择版本", options=opts, default=default))
    if choice is None:
        return None
    idx = int(choice) if choice.isdigit() else 0
    return options[min(max(idx - 1, 0), len(options) - 1)]


def safe_input(prompt: str, default: str = None) -> Optional[str]:
    """
    安全的输入函数，处理EOFError和KeyboardInterrupt

    Args:
        prompt: 输入提示
        default: 默认返回值（当发生异常时）

    Returns:
        用户输入或默认值
    """
    try:
        return input(prompt).strip()
    except EOFError:
        ui.print_error("输入流异常")
        return default
    except KeyboardInterrupt:
        ui.print_info("\n用户中断")
        return default


def show_main_menu() -> str:
    """显示主菜单并返回用户选择"""
    ui.print_header("Day Translation 主菜单")

    ui.print_section_header("主菜单", ui.Icons.CORE)
    ui.print_menu_item(
        "1",
        "完整流程",
        "单次或批量：提取→翻译→导入 一键完成",
        ui.Icons.RUNNING,
        is_recommended=True,
        compact=True,
    )
    ui.print_menu_item(
        "2", "提取模板", "单次或批量提取翻译模板", ui.Icons.TEMPLATE, compact=True
    )
    ui.print_menu_item(
        "3", "智能翻译", "自动选择最佳翻译器（Java/Python）", ui.Icons.TRANSLATE, compact=True
    )
    ui.print_menu_item(
        "4", "导入模板", "将翻译后的 CSV 导入模板（自动识别批量/单次）", ui.Icons.IMPORT, compact=True
    )
    ui.print_menu_item(
        "5", "工具", "迁移、恢复占位符、修补、清理、语料、批量操作", ui.Icons.TOOLS, compact=True
    )
    ui.print_menu_item("6", "配置管理", "管理翻译配置", ui.Icons.SETTINGS, compact=True)

    ui.print_section_header("退出", ui.Icons.EXIT)
    ui.print_menu_item("q", "退出", "退出程序", ui.Icons.EXIT, compact=True)

    ui.print_separator()

    result = safe_input(ui.get_input_prompt("请选择", options="1-6, q"), "q")
    return result if result is not None else "q"


def show_full_pipeline_submenu() -> Optional[str]:
    """完整流程子菜单，返回 1.1 / 1.2 / b"""
    ui.print_header("完整流程")
    ui.print_menu_item(
        "1", "单次提取完整流程", "提取→翻译→导入 一键完成", ui.Icons.RUNNING, compact=True
    )
    ui.print_menu_item(
        "2",
        "批量提取完整流程",
        "Vanilla 前缀模组：批量提取+翻译+导入+汇总到根目录（根目录现有语言文件将被删除）",
        ui.Icons.BATCH,
        compact=True,
    )
    ui.print_menu_item("b", "返回主菜单", "", ui.Icons.BACK, compact=True)
    ui.print_separator()
    result = safe_input(ui.get_input_prompt("请选择", options="1 / 2 / b"), "b")
    return (result or "b").strip().lower()


def show_extract_submenu() -> Optional[str]:
    """提取模板子菜单，返回 1 / 2 / b"""
    ui.print_header("提取模板")
    ui.print_menu_item("1", "单次提取", "单个模组提取翻译模板并生成 CSV", ui.Icons.TEMPLATE, compact=True)
    ui.print_menu_item("2", "批量提取", "批量提取 Vanilla 前缀模组", ui.Icons.BATCH, compact=True)
    ui.print_menu_item("b", "返回主菜单", "", ui.Icons.BACK, compact=True)
    ui.print_separator()
    result = safe_input(ui.get_input_prompt("请选择", options="1 / 2 / b"), "b")
    return (result or "b").strip().lower()


def show_tools_submenu() -> Optional[str]:
    """工具子菜单，返回 1-6 / b"""
    ui.print_header("工具")
    ui.print_menu_item("1", "迁移旧翻译到新翻译", "将旧翻译目录填到新目录（可仅填充空项）", ui.Icons.IMPORT, compact=True)
    ui.print_menu_item("2", "恢复占位符", "恢复 CSV 中 (PH_1) 等占位符为原始文本", ui.Icons.TRANSLATE, compact=True)
    ui.print_menu_item("3", "修补翻译", "修复 Google 错误（如 Error 500）并重新翻译", ui.Icons.TRANSLATE, compact=True)
    ui.print_menu_item("4", "清理过时/重复 key", "删除带「过时key」或「重复key」标记的条目", ui.Icons.SETTINGS, compact=True)
    ui.print_menu_item("5", "语料生成", "生成英-中平行语料", ui.Icons.CORPUS, compact=True)
    ui.print_menu_item("6", "批量操作", "批量导入、汇总到根目录", ui.Icons.BATCH, compact=True)
    ui.print_menu_item("b", "返回主菜单", "", ui.Icons.BACK, compact=True)
    ui.print_separator()
    result = safe_input(ui.get_input_prompt("请选择", options="1-6 / b"), "b")
    return (result or "b").strip().lower()


def select_csv_path_with_history() -> Optional[str]:
    """选择CSV文件路径，支持历史记录"""
    ui.print_info("请输入要翻译的 CSV 文件路径:")

    # 显示CSV文件历史记录
    csv_history = _get_path_manager().get_history_list(PATH_HISTORY_IMPORT_CSV)
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
        choice = safe_input(prompt_text)
        if choice is None:
            return None

        if choice.lower() == "q":
            return None

        if csv_history and choice == "0":
            csv_path = safe_input(ui.get_input_prompt("请输入CSV文件路径"))
            if csv_path is None:
                return None
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
        _get_path_manager().remember_path(PATH_HISTORY_IMPORT_CSV, csv_path)
        ui.print_success(f"选择：{csv_path}")
        return csv_path


def select_mod_path_with_version_detection(
    allow_multidlc: bool = False,
) -> Optional[str]:
    """选择模组目录，支持版本检测和自动扫描"""
    ui.print_header("模组目录选择", ui.Icons.FOLDER)

    common_mod_paths = get_common_mod_paths()
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
    history = _get_path_manager().get_history_list(PATH_HISTORY_MOD_DIR)
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
        choice = safe_input(
            ui.get_input_prompt(
                "请选择", options=f"1-{max_choice}, b", icon="或直接输入路径"
            )
        )
        if choice is None:
            return None

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
                return _get_path_manager().detect_version_and_choose(
                    selected_path, allow_multidlc
                )
        elif choice:
            # 直接输入路径 - 用户已经输入了路径，直接使用
            if os.path.exists(choice):
                # 对直接输入的路径进行版本检测
                return _get_path_manager().detect_version_and_choose(choice, allow_multidlc)
            else:
                ui.print_error(f"路径不存在: {choice}")
                ui.print_info("请重新选择或输入正确的路径")
                continue
        else:
            ui.print_error("请输入选择或路径")


def _collect_mods_from_dirs(base_dirs: List[str]) -> List[str]:
    """从多个基目录收集含 About 的模组路径"""
    found = []
    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            continue
        try:
            for name in os.listdir(base_dir):
                path = os.path.join(base_dir, name)
                if os.path.isdir(path) and os.path.exists(os.path.join(path, "About")):
                    found.append(path)
        except (OSError, PermissionError):
            continue
    return found


def _select_mod_from_list(
    mods: List[str], empty_msg: str, success_label: str
) -> Optional[str]:
    """显示模组列表并处理选择，成功则记住路径并返回版本检测结果"""
    if not mods:
        ui.print_warning(empty_msg)
        return None
    selected = display_mods_with_adaptive_width(mods)
    if selected:
        ui.print_success(success_label)
        ui.print_info(f"📁 路径：{selected}")
        ui.print_info(f"📦 模组名称：{_get_mod_display_name(selected)}")
        _get_path_manager().remember_path(PATH_HISTORY_MOD_DIR, selected)
        return _get_path_manager().detect_version_and_choose(selected)
    return None


def _scan_game_mods() -> Optional[str]:
    """扫描 Steam Workshop 模组"""
    ui.print_header("扫描Steam Workshop模组", ui.Icons.SCAN)
    ui.print_info("正在扫描Steam Workshop目录...")
    mods = _collect_mods_from_dirs(get_steam_workshop_paths())
    if not mods:
        ui.print_info("请确保RimWorld已通过Steam安装")
    return _select_mod_from_list(
        mods, "未找到Steam Workshop模组", "🎮 选择Steam Workshop模组"
    )


def _scan_third_party_mods(available_mod_dirs: List[str]) -> Optional[str]:
    """扫描第三方模组目录"""
    ui.print_info("📦 正在扫描第三方模组...")
    mods = _collect_mods_from_dirs(available_mod_dirs)
    return _select_mod_from_list(
        mods, "⚠️ 未找到任何第三方模组", "📦 选择第三方模组"
    )


def confirm_action(message: str) -> bool:
    """确认操作"""
    result = safe_input(f"{ui.Colors.WARNING}{message} [y/n]: {ui.Colors.RESET}", "n")
    return result and result.lower() in ["y", "yes", "是", "确认"]


def wait_for_user_input(prompt: str = "按回车继续..."):
    """等待用户输入"""
    safe_input(f"{UIStyle.Colors.INFO}{prompt}{UIStyle.Colors.RESET}")
