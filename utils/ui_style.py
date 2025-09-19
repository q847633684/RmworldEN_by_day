"""
统一UI样式模块
提供一致的界面风格和交互体验
"""

import shutil
import sys
from typing import Optional, List, Dict, Any
from colorama import Fore, Style, init

# 初始化colorama，确保输出到控制台
init(autoreset=True, strip=False)


class UIStyle:
    """统一UI样式类"""

    # 颜色主题
    class Colors:
        PRIMARY = Fore.CYAN  # 主色调 - 青色
        SUCCESS = Fore.GREEN  # 成功 - 绿色
        WARNING = Fore.YELLOW  # 警告 - 黄色
        ERROR = Fore.RED  # 错误 - 红色
        INFO = Fore.BLUE  # 信息 - 蓝色
        HIGHLIGHT = Fore.MAGENTA  # 高亮 - 紫色
        MUTED = Fore.BLACK  # 次要信息 - 黑色
        RESET = Style.RESET_ALL  # 重置样式

    # 图标主题
    class Icons:
        # 功能图标
        CORE = "🔧"  # 核心功能
        ADVANCED = "🛠️"  # 高级功能
        EXIT = "🚪"  # 退出
        SUCCESS = "✅"  # 成功
        ERROR = "❌"  # 错误
        WARNING = "⚠️"  # 警告
        INFO = "ℹ️"  # 信息
        LOADING = "⏳"  # 加载中

        # 操作图标
        SCAN = "🔍"  # 扫描
        FOLDER = "📁"  # 文件夹
        FILE = "📄"  # 文件
        SETTINGS = "⚙️"  # 设置
        HISTORY = "📋"  # 历史记录
        BACK = "🔙"  # 返回
        NEXT = "➡️"  # 下一步
        CONFIRM = "✓"  # 确认
        CANCEL = "✗"  # 取消

        # 状态图标
        RUNNING = "🔄"  # 运行中
        COMPLETED = "🎉"  # 完成
        PAUSED = "⏸️"  # 暂停
        PROCESSING = "⚡"  # 处理中

        # 数据图标
        DATA = "📊"  # 数据
        TEMPLATE = "📤"  # 模板
        IMPORT = "📥"  # 导入
        EXPORT = "📤"  # 导出
        TRANSLATE = "🚀"  # 翻译
        BATCH = "📦"  # 批量
        CORPUS = "📚"  # 语料

    # 布局常量
    class Layout:
        TERMINAL_WIDTH = 80
        BOX_WIDTH = 60
        SEPARATOR_LENGTH = 60
        INDENT_SIZE = 2

        @classmethod
        def get_terminal_width(cls) -> int:
            """获取终端宽度"""
            try:
                return shutil.get_terminal_size().columns
            except:
                return cls.TERMINAL_WIDTH

    @classmethod
    def print_header(cls, title: str, icon: str = "", width: int = None) -> None:
        """打印标题头部"""
        if width is None:
            width = cls.Layout.get_terminal_width()

        # 构建标题
        if icon:
            title = f"{icon} {title}"

        # 计算填充
        padding = (width - len(title) - 4) // 2
        if padding < 0:
            padding = 0

        print(f"\n{cls.Colors.PRIMARY}╔{'═' * (width - 2)}╗{cls.Colors.RESET}")
        print(
            f"{cls.Colors.PRIMARY}║{cls.Colors.RESET}{' ' * padding}{cls.Colors.HIGHLIGHT}{title}{cls.Colors.RESET}{' ' * (width - len(title) - padding - 2)}{cls.Colors.PRIMARY}║{cls.Colors.RESET}"
        )
        print(f"{cls.Colors.PRIMARY}╚{'═' * (width - 2)}╝{cls.Colors.RESET}")

    @classmethod
    def print_section_header(cls, title: str, icon: str = "", step: str = "") -> None:
        """打印章节标题"""
        if step:
            title = f"{step} {title}"
        if icon:
            title = f"{icon} {title}"

        print(
            f"\n{cls.Colors.PRIMARY}{'─' * cls.Layout.SEPARATOR_LENGTH}{cls.Colors.RESET}"
        )
        print(f"{cls.Colors.HIGHLIGHT}{title}{cls.Colors.RESET}")
        print(
            f"{cls.Colors.PRIMARY}{'─' * cls.Layout.SEPARATOR_LENGTH}{cls.Colors.RESET}"
        )

    @classmethod
    def print_step_header(
        cls, step_num: int, total_steps: int, title: str, icon: str = ""
    ) -> None:
        """打印步骤标题"""
        if icon:
            title = f"{icon} {title}"

        step_text = f"【步骤 {step_num}/{total_steps}】{title}"
        print(f"\n{cls.Colors.WARNING}{step_text}{cls.Colors.RESET}")
        print(f"{cls.Colors.WARNING}{'─' * 50}{cls.Colors.RESET}")

    @classmethod
    def print_menu_item(
        cls,
        number: str,
        title: str,
        description: str = "",
        icon: str = "",
        is_recommended: bool = False,
        is_default: bool = False,
        compact: bool = False,
    ) -> None:
        """打印菜单项"""
        # 构建前缀
        prefix = f"{cls.Colors.PRIMARY}{number:>2}.{cls.Colors.RESET}"

        # 构建标题
        title_parts = []
        if icon:
            title_parts.append(icon)
        title_parts.append(title)

        if is_recommended:
            title_parts.append(f"{cls.Colors.SUCCESS}(推荐){cls.Colors.RESET}")
        if is_default:
            title_parts.append(f"{cls.Colors.INFO}(默认){cls.Colors.RESET}")

        title_text = " ".join(title_parts)

        if compact:
            # 紧凑模式：标题和描述在同一行
            if description:
                print(
                    f"  {prefix} {title_text} ── {cls.Colors.MUTED}{description}{cls.Colors.RESET}"
                )
            else:
                print(f"  {prefix} {title_text}")
        else:
            # 标准模式：描述在下一行
            print(f"  {prefix} {title_text}")
            if description:
                print(f"      {cls.Colors.MUTED}└── {description}{cls.Colors.RESET}")

    @classmethod
    def print_status(
        cls, message: str, status_type: str = "info", icon: str = ""
    ) -> None:
        """打印状态信息"""
        color_map = {
            "success": cls.Colors.SUCCESS,
            "error": cls.Colors.ERROR,
            "warning": cls.Colors.WARNING,
            "info": cls.Colors.INFO,
            "highlight": cls.Colors.HIGHLIGHT,
        }

        color = color_map.get(status_type, cls.Colors.INFO)

        if icon:
            message = f"{icon} {message}"

        print(f"{color}{message}{cls.Colors.RESET}")

    @classmethod
    def print_success(cls, message: str) -> None:
        """打印成功信息"""
        cls.print_status(message, "success", cls.Icons.SUCCESS)

    @classmethod
    def print_error(cls, message: str) -> None:
        """打印错误信息"""
        cls.print_status(message, "error", cls.Icons.ERROR)

    @classmethod
    def print_warning(cls, message: str) -> None:
        """打印警告信息"""
        cls.print_status(message, "warning", cls.Icons.WARNING)

    @classmethod
    def print_info(cls, message: str) -> None:
        """打印信息"""
        cls.print_status(message, "info", cls.Icons.INFO)

    @classmethod
    def print_highlight(cls, message: str) -> None:
        """打印高亮信息"""
        cls.print_status(message, "highlight")

    @classmethod
    def print_separator(cls, char: str = "─", length: int = None) -> None:
        """打印分隔线"""
        if length is None:
            length = cls.Layout.SEPARATOR_LENGTH
        print(f"\n{cls.Colors.PRIMARY}{char * length}{cls.Colors.RESET}")

    @classmethod
    def print_progress_bar(
        cls,
        current: int,
        total: int,
        width: int = 40,
        prefix: str = "进度",
        suffix: str = "",
    ) -> None:
        """打印进度条"""
        if total == 0:
            percent = 0
        else:
            percent = current / total

        filled_length = int(width * percent)
        bar = "█" * filled_length + "░" * (width - filled_length)

        print(
            f"\r{cls.Colors.PRIMARY}{prefix}: {cls.Colors.SUCCESS}[{bar}]{cls.Colors.RESET} {percent:.1%} ({current}/{total}) {suffix}",
            end="",
            flush=True,
        )

    @classmethod
    def print_table(
        cls,
        headers: List[str],
        rows: List[List[str]],
        title: str = "",
        max_width: int = None,
    ) -> None:
        """打印表格"""
        if max_width is None:
            max_width = cls.Layout.get_terminal_width() - 4

        if title:
            cls.print_header(title)

        if not headers or not rows:
            return

        # 计算列宽
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # 调整列宽以适应终端
        total_width = sum(col_widths) + len(headers) * 3 + 1
        if total_width > max_width:
            # 按比例缩小
            scale = max_width / total_width
            col_widths = [int(w * scale) for w in col_widths]

        # 打印表头
        header_line = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        print(f"{cls.Colors.PRIMARY}{header_line}{cls.Colors.RESET}")

        header_row = (
            "│"
            + "│".join(
                f" {cls.Colors.HIGHLIGHT}{h:<{w}}{cls.Colors.RESET} "
                for h, w in zip(headers, col_widths)
            )
            + "│"
        )
        print(f"{cls.Colors.PRIMARY}{header_row}{cls.Colors.RESET}")

        separator_line = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        print(f"{cls.Colors.PRIMARY}{separator_line}{cls.Colors.RESET}")

        # 打印数据行
        for row in rows:
            data_row = (
                "│"
                + "│".join(f" {str(cell):<{w}} " for cell, w in zip(row, col_widths))
                + "│"
            )
            print(f"{cls.Colors.PRIMARY}{data_row}{cls.Colors.RESET}")

        footer_line = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
        print(f"{cls.Colors.PRIMARY}{footer_line}{cls.Colors.RESET}")

    @classmethod
    def print_list(
        cls,
        items: List[str],
        title: str = "",
        icon: str = "",
        numbered: bool = False,
        start_index: int = 1,
    ) -> None:
        """打印列表"""
        if title:
            if icon:
                title = f"{icon} {title}"
            cls.print_section_header(title)

        for i, item in enumerate(items, start_index):
            if numbered:
                print(f"  {cls.Colors.PRIMARY}{i:2d}.{cls.Colors.RESET} {item}")
            else:
                print(f"  {cls.Colors.PRIMARY}•{cls.Colors.RESET} {item}")

    @classmethod
    def print_menu_items_compact(
        cls,
        items: List[Dict[str, str]],
        columns: int = 2,
        title: str = "",
        icon: str = "",
    ) -> None:
        """紧凑多列显示菜单项"""
        if title:
            if icon:
                title = f"{icon} {title}"
            cls.print_section_header(title)

        if not items:
            return

        # 计算每列的最大宽度
        max_width = cls.Layout.get_terminal_width() // columns - 4
        col_widths = [0] * columns

        # 计算每列的最大宽度
        for i, item in enumerate(items):
            col_idx = i % columns
            item_width = (
                len(item.get("title", "")) + len(item.get("description", "")) + 10
            )
            col_widths[col_idx] = max(col_widths[col_idx], min(item_width, max_width))

        # 打印菜单项
        for i in range(0, len(items), columns):
            row_items = items[i : i + columns]
            row_parts = []

            for j, item in enumerate(row_items):
                number = item.get("number", "")
                title = item.get("title", "")
                description = item.get("description", "")
                item_icon = item.get("icon", "")
                is_recommended = item.get("is_recommended", False)

                # 构建项目文本
                parts = []
                if item_icon:
                    parts.append(item_icon)
                parts.append(title)
                if is_recommended:
                    parts.append(f"{cls.Colors.SUCCESS}(推荐){cls.Colors.RESET}")

                item_text = " ".join(parts)
                if description:
                    item_text += (
                        f" ── {cls.Colors.MUTED}{description}{cls.Colors.RESET}"
                    )

                # 格式化并添加到行
                formatted_item = (
                    f"{cls.Colors.PRIMARY}{number:>2}.{cls.Colors.RESET} {item_text}"
                )
                row_parts.append(formatted_item.ljust(col_widths[j]))

            # 补齐空列
            while len(row_parts) < columns:
                row_parts.append("")

            print(f"  {'  '.join(row_parts)}")

    @classmethod
    def print_key_value(cls, key: str, value: str, icon: str = "") -> None:
        """打印键值对"""
        if icon:
            key = f"{icon} {key}"
        print(f"  {cls.Colors.HIGHLIGHT}{key}:{cls.Colors.RESET} {value}")

    @classmethod
    def print_config_summary(
        cls, config: Dict[str, Any], title: str = "配置摘要"
    ) -> None:
        """打印配置摘要"""
        cls.print_header(title, cls.Icons.SETTINGS)

        for key, value in config.items():
            cls.print_key_value(key, str(value))

    @classmethod
    def get_input_prompt(
        cls, message: str, default: str = "", options: str = "", icon: str = ""
    ) -> str:
        """获取输入提示"""
        prompt_parts = []

        if icon:
            prompt_parts.append(icon)

        prompt_parts.append(message)

        if options:
            prompt_parts.append(f"({options})")

        if default:
            prompt_parts.append(f"[默认: {default}]")

        prompt = " ".join(prompt_parts)
        return f"{cls.Colors.PRIMARY}{prompt}: {cls.Colors.RESET}"

    @classmethod
    def print_tip(cls, message: str, icon: str = "💡") -> None:
        """打印提示信息"""
        print(f"\n{cls.Colors.INFO}{icon} {message}{cls.Colors.RESET}")

    @classmethod
    def print_quick_actions(cls, actions: Dict[str, str]) -> None:
        """打印快速操作"""
        cls.print_section_header("快速操作", cls.Icons.SETTINGS)

        for key, description in actions.items():
            cls.print_key_value(key, description)

    @classmethod
    def print_workflow_complete(cls, title: str = "流程完成", icon: str = None) -> None:
        """打印工作流完成"""
        if icon is None:
            icon = cls.Icons.COMPLETED

        cls.print_separator("=", cls.Layout.SEPARATOR_LENGTH)
        cls.print_status(f"{icon} {title}", "success")
        cls.print_separator("=", cls.Layout.SEPARATOR_LENGTH)


# 创建全局实例
ui = UIStyle()
