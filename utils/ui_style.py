"""
统一UI样式模块
提供一致的界面风格和交互体验
"""

import os
import shutil
from functools import wraps
from typing import Optional, List, Dict, Any
from colorama import Fore, Style, init  # type: ignore

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

        # 配置系统图标
        API = "🌐"  # API
        MODULE = "📦"  # 模块
        TOOLS = "🛠️"  # 工具
        DEFAULT = "⭐"  # 默认
        BALANCE = "⚖️"  # 负载均衡
        TEST = "🧪"  # 测试
        PRIORITY = "🔢"  # 优先级
        FAILOVER = "🛡️"  # 故障切换
        STATS = "📊"  # 统计
        EDIT = "✏️"  # 编辑
        TOGGLE = "🔄"  # 切换
        RESET = "🔄"  # 重置
        SAVE = "💾"  # 保存
        TYPE = "🏷️"  # 类型
        STATUS = "📊"  # 状态
        CONFIG = "⚙️"  # 配置
        VALID = "✅"  # 验证
        FIELD = "📝"  # 字段
        DEBUG = "🐛"  # 调试
        RULES = "📋"  # 规则
        PATTERN = "🔍"  # 模式
        MENU = "📋"  # 菜单
        EDIT_ALL = "📝"  # 编辑全部
        RESULT = "📋"  # 结果
        LANGUAGE = "🌐"  # 语言
        LOG = "📝"  # 日志
        UI = "🖥️"  # 界面
        CHECK = "✅"  # 检查
        BACKUP = "💾"  # 备份
        RESTORE = "🔄"  # 恢复
        CONSOLE = "💻"  # 控制台
        SIZE = "📏"  # 大小
        THEME = "🎨"  # 主题
        PROGRESS = "📊"  # 进度
        CLEAR = "🧹"  # 清理
        NEW = "🆕"  # 新的
        OLD = "📜"  # 旧的
        VERSION = "🔖"  # 版本
        RECOMMEND = "💡"  # 推荐
        TIME = "🕐"  # 时间

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
            except (OSError, AttributeError):
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

    # ==================== 统一进度条工具 ====================

    class ProgressBar:
        """进度条上下文管理器"""

        def __init__(self, total: int, prefix: str = "进度", description: str = ""):
            """
            初始化进度条

            Args:
                total: 总数量
                prefix: 进度条前缀
                description: 描述信息
            """
            self.total = total
            self.prefix = prefix
            self.description = description
            self.current = 0

        def __enter__(self):
            """进入上下文"""
            if self.total > 0:
                ui.print_info(f"{self.description}...")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """退出上下文"""
            if self.total > 0:
                ui.print_info("")  # 换行
            return False  # 不抑制异常

        def update(self, increment: int = 1):
            """更新进度"""
            self.current += increment
            if self.total > 0:
                ui.print_progress_bar(self.current, self.total, prefix=self.prefix)

    @classmethod
    def progress_bar(cls, total: int, prefix: str = "进度", description: str = ""):
        """
        进度条装饰器

        Args:
            total: 总数量
            prefix: 进度条前缀
            description: 描述信息

        Returns:
            装饰器函数
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with cls.ProgressBar(total, prefix, description) as progress:
                    # 将progress对象传递给原函数
                    return func(*args, progress=progress, **kwargs)

            return wrapper

        return decorator

    @classmethod
    def iter_with_progress(
        cls, items: list, prefix: str = "处理", description: str = ""
    ):
        """
        带进度条的迭代器

        Args:
            items: 要迭代的项目列表
            prefix: 进度条前缀
            description: 描述信息

        Yields:
            项目及其索引
        """
        total = len(items)
        if total == 0:
            return

        with cls.ProgressBar(total, prefix, description) as progress:
            for i, item in enumerate(items, 1):
                yield i, item
                progress.update()

    @classmethod
    def file_processing_progress(
        cls, files: list, prefix: str = "处理文件", description: str = ""
    ):
        """
        文件处理进度条装饰器

        Args:
            files: 文件列表
            prefix: 进度条前缀
            description: 描述信息

        Returns:
            装饰器函数
        """
        return cls.progress_bar(len(files), prefix, description)

    @classmethod
    def data_processing_progress(
        cls, data: list, prefix: str = "处理数据", description: str = ""
    ):
        """
        数据处理进度条装饰器

        Args:
            data: 数据列表
            prefix: 进度条前缀
            description: 描述信息

        Returns:
            装饰器函数
        """
        return cls.progress_bar(len(data), prefix, description)

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


def _get_terminal_width() -> int:
    """获取终端宽度"""
    try:
        return shutil.get_terminal_size().columns
    except (OSError, AttributeError):
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
        except (ET.ParseError, FileNotFoundError, PermissionError, AttributeError):
            pass

    # 如果无法读取XML，使用目录名
    return os.path.basename(mod_path)


def display_mods_with_adaptive_width(
    all_mods: List[str], items_per_page: int = 20
) -> Optional[str]:
    """使用自适应列宽显示模组列表，支持多页显示"""
    if not all_mods:
        ui.print_warning("📦 未找到任何模组")
        return

    mod_names = [_get_mod_display_name(mod_path) for mod_path in all_mods]
    mods_per_line, item_width = _calculate_adaptive_layout(mod_names)

    # 计算每页显示的项目数（按行计算）
    items_per_line = mods_per_line
    lines_per_page = max(1, items_per_page // items_per_line)
    items_per_page = lines_per_page * items_per_line

    # 计算总页数
    total_pages = (len(all_mods) + items_per_page - 1) // items_per_page

    current_page = 1

    while True:
        # 清屏并显示当前页
        os.system("cls" if os.name == "nt" else "clear")

        # 计算当前页的起始和结束索引
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(all_mods))
        current_page_mods = all_mods[start_idx:end_idx]
        current_page_names = mod_names[start_idx:end_idx]

        # 显示标题和分页信息
        ui.print_header(f"📦 模组列表 (第 {current_page}/{total_pages} 页)")
        ui.print_info(f"显示 {len(current_page_mods)} 个模组 (共 {len(all_mods)} 个)")

        # 显示当前页的模组
        _display_mods_page(
            current_page_mods, current_page_names, mods_per_line, item_width, start_idx
        )

        # 显示分页导航
        _display_pagination_navigation(current_page, total_pages, len(all_mods))

        # 获取用户输入
        choice = (
            input(
                ui.get_input_prompt(
                    "请选择操作", options="n下一页, p上一页, 数字选择模组, q退出"
                )
            )
            .strip()
            .lower()
        )

        if choice == "q":
            break
        elif choice == "n" and current_page < total_pages:
            current_page += 1
        elif choice == "p" and current_page > 1:
            current_page -= 1
        elif choice.isdigit():
            global_mod_number = int(choice)
            # 计算当前页面显示的模组编号范围
            page_start_number = start_idx + 1
            page_end_number = end_idx

            if page_start_number <= global_mod_number <= page_end_number:
                # 计算在当前页面中的相对索引
                relative_index = global_mod_number - page_start_number
                # 返回选中的模组路径
                return current_page_mods[relative_index]
            else:
                ui.print_warning(
                    f"无效选择，请输入 {page_start_number}-{page_end_number} 之间的数字"
                )
        else:
            ui.print_warning("无效选择，请重新输入")

    return None


def _display_mods_page(
    mods: List[str],
    mod_names: List[str],
    mods_per_line: int,
    item_width: int,
    start_index: int,
) -> None:
    """显示单页模组列表"""
    if not mods:
        return

    # 计算需要的行数
    total_lines = (len(mods) + mods_per_line - 1) // mods_per_line

    # 计算每列的实际宽度（减少间距）
    column_width = item_width + 2  # 编号(2) + ". " + 模组名 + 1个空格
    total_width = mods_per_line * column_width

    # 顶部边框
    top_line = "═" * total_width
    print(f"   ┌{top_line}┐")

    for line in range(total_lines):
        start_idx = line * mods_per_line
        end_idx = min(start_idx + mods_per_line, len(mods))

        # 构建当前行的显示内容
        line_content = "   │"
        for i in range(start_idx, end_idx):
            global_index = start_index + i
            mod_name = mod_names[i]

            # 计算可用的模组名长度
            available_width = item_width - 3  # 预留3个字符给编号和点
            display_name = (
                mod_name[: available_width - 3] + "..."
                if len(mod_name) > available_width
                else mod_name
            )

            # 格式化每个项目
            item_text = f"{global_index+1:2d}. {display_name}"
            # 使用固定宽度格式化
            line_content += f"{item_text:<{column_width}}"

        # 填充剩余空间
        remaining_slots = mods_per_line - (end_idx - start_idx)
        if remaining_slots > 0:
            line_content += " " * (remaining_slots * column_width)

        line_content += "│"
        print(line_content)

    # 底部边框
    bottom_line = "─" * total_width
    print(f"   └{bottom_line}┘")


def _display_pagination_navigation(
    current_page: int, total_pages: int, total_items: int
) -> None:
    """显示分页导航"""
    ui.print_separator("-", 40)

    # 分页信息
    ui.print_info(f"📄 第 {current_page} 页，共 {total_pages} 页")

    # 导航选项
    nav_options = []
    if current_page > 1:
        nav_options.append("p - 上一页")
    if current_page < total_pages:
        nav_options.append("n - 下一页")
    nav_options.append("q - 退出")

    if nav_options:
        ui.print_info("导航: " + " | ".join(nav_options))

    ui.print_info(f"💡 直接输入数字选择模组 (1-{total_items})")


def confirm_action(message: str) -> bool:
    """确认操作"""
    return input(
        f"{UIStyle.Colors.WARNING}{message} [y/n]: {UIStyle.Colors.RESET}"
    ).lower() in [
        "y",
        "yes",
        "是",
        "确认",
    ]
