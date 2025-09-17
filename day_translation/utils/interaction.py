"""
通用交互工具模块
提供所有功能模块共用的交互函数
"""

import os
from pathlib import Path
from typing import Optional, List
from colorama import Fore, Style
from .path_manager import PathManager

# 全局路径管理器实例
path_manager = PathManager()


def show_main_menu() -> str:
    """显示主菜单并返回用户选择"""
    print(
        f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗"
    )
    print(f"║                    Day Translation 主菜单                    ║")
    print(
        f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}"
    )

    print(f"\n{Fore.GREEN}🔧 核心功能：{Style.RESET_ALL}")
    print(f"  1. 🔄 完整流程  ── 提取→Java机翻→导入 一键完成")
    print(f"  2. 📤 提取模板  ── 提取翻译模板并生成 CSV 文件")
    print(f"  3. 🚀 Java机翻  ── 使用Java工具进行高性能翻译")
    print(f"  4. 📥 导入模板  ── 将翻译后的 CSV 导入翻译模板")

    print(f"\n{Fore.YELLOW}🛠️ 高级功能：{Style.RESET_ALL}")
    print(f"  5. 🤖 Python机翻 ── 使用Python阿里云翻译 CSV 文件")
    print(f"  6. 📦 批量处理  ── 处理多个模组")
    print(f"  7. ⚙️ 配置管理  ── 管理翻译配置")
    print(f"  8. 📚 语料生成  ── 生成英-中平行语料")

    print(f"\n{Fore.RED}❌ 退出程序：{Style.RESET_ALL}")
    print(f"  q. 🚪 退出     ── 退出程序")

    print(
        f"\n{Fore.CYAN}────────────────────────────────────────────────────────────────{Style.RESET_ALL}"
    )

    return input(f"{Fore.GREEN}请选择模式 (1-8, q): {Style.RESET_ALL}").strip()


def select_output_directory(mod_dir: str) -> Optional[str]:
    """
    选择输出目录，支持默认目录、历史记录和直接输入

    Args:
        mod_dir (str): 模组目录路径

    Returns:
        Optional[str]: 选择的输出目录路径，如果取消则返回None
    """
    default_dir = str(Path(mod_dir) / "Languages" / "ChineseSimplified")
    history = path_manager.get_history_list("output_dir")

    print(f"{Fore.BLUE}📁 请选择输出目录：{Style.RESET_ALL}")
    print(f"{Fore.GREEN}1. 使用默认目录：{default_dir}{Style.RESET_ALL}")

    # 展示所有历史记录
    if history:
        print(f"{Fore.YELLOW}历史记录：{Style.RESET_ALL}")
        for i, hist_path in enumerate(history, 2):
            print(f"   {i}. {hist_path}")
    else:
        print(f"{Fore.YELLOW}暂无历史记录{Style.RESET_ALL}")

    max_choice = len(history) + 1

    while True:
        choice = input(
            f"\n{Fore.CYAN}请选择 (1-{max_choice}) 或直接输入路径: {Style.RESET_ALL}"
        ).strip()

        if choice.lower() == "q":
            return None

        if choice == "1":
            print(f"   {Fore.GREEN}✅ 选择：{default_dir}{Style.RESET_ALL}")
            path_manager.remember_path("output_dir", default_dir)
            return default_dir
        elif choice.isdigit() and 2 <= int(choice) <= max_choice:
            selected_path = history[int(choice) - 2]
            print(f"   {Fore.GREEN}✅ 选择：{selected_path}{Style.RESET_ALL}")
            path_manager.remember_path("output_dir", selected_path)
            return selected_path
        elif choice:  # 非空输入，当作路径使用
            # 验证路径
            if os.path.isdir(choice) or not os.path.exists(choice):
                print(f"   {Fore.GREEN}✅ 选择：{choice}{Style.RESET_ALL}")
                path_manager.remember_path("output_dir", choice)
                return choice
            else:
                print(f"   {Fore.RED}❌ 路径无效：{choice}{Style.RESET_ALL}")
                continue
        else:
            print(f"   {Fore.RED}❌ 请输入选择或路径{Style.RESET_ALL}")


def select_csv_path_with_history() -> Optional[str]:
    """选择CSV文件路径，支持历史记录"""
    print(f"\n{Fore.CYAN}请输入要翻译的 CSV 文件路径:{Style.RESET_ALL}")

    # 显示CSV文件历史记录
    csv_history = path_manager.get_history_list("import_csv")
    if csv_history:
        print(f"{Fore.BLUE}CSV文件历史记录：{Style.RESET_ALL}")
        for i, path in enumerate(csv_history, 1):
            print(f"{i}. {path}")
        print(f"0. 输入新路径（或直接粘贴完整CSV路径）")

    csv_path: Optional[str] = None
    while True:
        prompt_text = (
            f"{Fore.CYAN}请选择 (0-{len(csv_history)}) 或直接输入CSV路径 (q退出): {Style.RESET_ALL}"
            if csv_history
            else f"{Fore.CYAN}请输入CSV文件路径 (q退出): {Style.RESET_ALL}"
        )
        choice = input(prompt_text).strip()

        if choice.lower() == "q":
            return None

        if csv_history and choice == "0":
            csv_path = input(f"{Fore.CYAN}请输入CSV文件路径: {Style.RESET_ALL}").strip()
        elif csv_history and choice.isdigit() and 1 <= int(choice) <= len(csv_history):
            csv_path = csv_history[int(choice) - 1]

        elif choice:  # 非空输入，当作路径使用
            csv_path = choice
        else:
            print(f"   {Fore.RED}❌ 请输入选择或路径{Style.RESET_ALL}")

        if not csv_path:
            print(f"{Fore.RED}❌ 路径不能为空{Style.RESET_ALL}")
            continue

        # 验证CSV文件
        if not os.path.exists(csv_path):
            print(f"{Fore.RED}❌ 文件不存在: {csv_path}{Style.RESET_ALL}")
            continue

        if not csv_path.lower().endswith(".csv"):
            print(f"{Fore.RED}❌ 文件必须是CSV格式{Style.RESET_ALL}")
            continue

        # 记住路径
        path_manager.remember_path("import_csv", csv_path)
        print(f"   {Fore.GREEN}✅ 选择：{csv_path}{Style.RESET_ALL}")
        return csv_path


def select_mod_path_with_version_detection() -> Optional[str]:
    """选择模组目录，支持版本检测"""
    return path_manager.get_mod_path_with_version_detection(
        path_type="mod_dir",
        prompt="请输入编号或模组目录路径（支持历史编号或直接输入路径）: ",
    )


def confirm_action(message: str) -> bool:
    """确认操作"""
    return input(f"{Fore.YELLOW}{message} [y/n]:{Style.RESET_ALL} ").lower() == "y"


def auto_generate_output_path(input_path: str) -> str:
    """自动生成输出CSV文件路径"""
    input_path_obj = Path(input_path)
    return str(input_path_obj.parent / f"{input_path_obj.stem}_zh.csv")


def show_success(message: str):
    """显示成功信息"""
    print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")


def show_error(message: str):
    """显示错误信息"""
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")


def show_warning(message: str):
    """显示警告信息"""
    print(f"{Fore.YELLOW}⚠️ {message}{Style.RESET_ALL}")


def show_info(message: str):
    """显示信息"""
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
