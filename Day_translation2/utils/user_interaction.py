"""
Day Translation 2 - 用户交互管理器

从day_translation迁移并增强的用户交互功能。
支持自动模式、预览模式、文件分析等高级交互特性。
"""

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from colorama import Fore, Style

    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

    # 定义无色彩的替代
    class _NoColor:
        def __getattr__(self, name):
            return ""

    Fore = Style = _NoColor()

try:
    from ..models.exceptions import ValidationError
    from .export_manager import ExportMode
except ImportError:
    # 如果无法导入，定义临时异常类用于独立运行
    class ValidationError(Exception):
        pass

    from export_manager import ExportMode


@dataclass
class FileAnalysisResult:
    """文件分析结果"""

    total_files: int = 0
    will_be_affected: int = 0
    files_list: List[str] = None
    estimated_size: int = 0
    changed_files: List[str] = None

    def __post_init__(self):
        if self.files_list is None:
            self.files_list = []
        if self.changed_files is None:
            self.changed_files = []


class UserInteractionManager:
    """用户交互管理器 - 处理用户选择和文件操作确认"""

    def __init__(self, enable_colors: bool = True):
        """初始化用户交互管理器"""
        self.enable_colors = enable_colors and COLORAMA_AVAILABLE

    def handle_existing_translations_choice(
        self,
        output_dir_path: str,
        file_pattern: str = "*.xml",
        backup_enabled: bool = True,
        auto_mode: Optional[str] = None,
        enable_advanced_options: bool = False,
    ) -> ExportMode:
        """
        处理现有翻译文件的用户选择

        Args:
            output_dir_path: 输出目录路径
            file_pattern: 文件匹配模式，默认为 "*.xml"
            backup_enabled: 是否启用备份选项
            auto_mode: 自动模式 ("replace", "merge", "smart-merge", "backup", "skip", etc.)
            enable_advanced_options: 是否启用高级选项

        Returns:
            ExportMode: 用户选择的处理模式
        """
        try:
            # 检查是否存在现有翻译文件
            existing_files = list(Path(output_dir_path).rglob(file_pattern))

            if not existing_files:
                # 没有现有文件，直接返回替换模式
                return ExportMode.REPLACE

            # 自动模式处理
            if auto_mode:
                return self._handle_auto_mode(auto_mode, existing_files, output_dir_path)

            # 交互模式
            return self._handle_interactive_mode(
                existing_files, output_dir_path, backup_enabled, enable_advanced_options
            )

        except Exception as e:
            logging.error(f"处理用户选择时出错: {e}")
            return ExportMode.REPLACE  # 默认返回替换模式

    def _handle_auto_mode(
        self, auto_mode: str, existing_files: List[Path], output_dir_path: str
    ) -> ExportMode:
        """处理自动模式"""
        mode_map = {
            "replace": ExportMode.REPLACE,
            "merge": ExportMode.MERGE,
            "smart-merge": ExportMode.SMART_MERGE,
            "backup": ExportMode.BACKUP,
            "skip": ExportMode.SKIP,
            "incremental": ExportMode.INCREMENTAL,
            "preview": ExportMode.PREVIEW,
        }

        mode = mode_map.get(auto_mode.lower())
        if mode:
            logging.info(f"自动模式: {auto_mode}")
            return self._execute_choice(mode, existing_files, output_dir_path)
        else:
            logging.warning(f"无效的自动模式: {auto_mode}，转为交互模式")
            return self._handle_interactive_mode(existing_files, output_dir_path, True, False)

    def _handle_interactive_mode(
        self,
        existing_files: List[Path],
        output_dir_path: str,
        backup_enabled: bool = True,
        enable_advanced_options: bool = False,
    ) -> ExportMode:
        """处理交互模式"""

        # 显示现有文件信息
        self._display_existing_files_info(existing_files, output_dir_path)

        # 显示处理选项
        choice_map = self._display_processing_options(backup_enabled, enable_advanced_options)

        # 获取用户选择
        choice = self._get_user_choice(choice_map, "2")  # 默认选择合并模式

        mode = choice_map[choice]
        return self._execute_choice(mode, existing_files, output_dir_path)

    def _display_existing_files_info(self, existing_files: List[Path], output_dir_path: str):
        """显示现有文件信息"""
        if not self.enable_colors:
            print(f"\n检测到输出目录中已存在 {len(existing_files)} 个翻译文件")
        else:
            print(
                f"\n{Fore.YELLOW}检测到输出目录中已存在 {len(existing_files)} 个翻译文件{Style.RESET_ALL}"
            )

        # 显示文件列表（如果文件不多）
        if len(existing_files) <= 10:
            if self.enable_colors:
                print(f"{Fore.CYAN}现有文件：{Style.RESET_ALL}")
            else:
                print("现有文件：")

            for i, file_path in enumerate(existing_files[:10], 1):
                rel_path = Path(file_path).relative_to(Path(output_dir_path))
                print(f"  {i}. {rel_path}")

        elif len(existing_files) > 10:
            if self.enable_colors:
                print(f"{Fore.CYAN}现有文件（显示前5个）：{Style.RESET_ALL}")
            else:
                print("现有文件（显示前5个）：")

            for i, file_path in enumerate(existing_files[:5], 1):
                rel_path = Path(file_path).relative_to(Path(output_dir_path))
                print(f"  {i}. {rel_path}")
            print(f"  ... 还有 {len(existing_files) - 5} 个文件")

    def _display_processing_options(
        self, backup_enabled: bool = True, enable_advanced_options: bool = False
    ) -> Dict[str, ExportMode]:
        """显示处理选项"""
        if self.enable_colors:
            print(f"\n{Fore.CYAN}请选择处理方式：{Style.RESET_ALL}")
            print(f"1. {Fore.GREEN}替换{Style.RESET_ALL}（删除现有文件，重新生成）")
            print(f"2. {Fore.GREEN}合并{Style.RESET_ALL}（保留现有翻译，仅更新新内容）")
            print(
                f"3. {Fore.MAGENTA}智能合并{Style.RESET_ALL}（扫描XML内容，替换已有key，添加缺失key）"
            )
        else:
            print("\n请选择处理方式：")
            print("1. 替换（删除现有文件，重新生成）")
            print("2. 合并（保留现有翻译，仅更新新内容）")
            print("3. 智能合并（扫描XML内容，替换已有key，添加缺失key）")

        option_count = 4
        choice_map = {"1": ExportMode.REPLACE, "2": ExportMode.MERGE, "3": ExportMode.SMART_MERGE}

        if backup_enabled:
            if self.enable_colors:
                print(f"4. {Fore.BLUE}备份并替换{Style.RESET_ALL}（备份现有文件，然后重新生成）")
            else:
                print("4. 备份并替换（备份现有文件，然后重新生成）")
            choice_map["4"] = ExportMode.BACKUP
            option_count += 1

        if enable_advanced_options:
            if self.enable_colors:
                print(
                    f"{option_count}. {Fore.MAGENTA}增量更新{Style.RESET_ALL}（只更新有变化的文件）"
                )
            else:
                print(f"{option_count}. 增量更新（只更新有变化的文件）")
            choice_map[str(option_count)] = ExportMode.INCREMENTAL
            option_count += 1

            if self.enable_colors:
                print(
                    f"{option_count}. {Fore.CYAN}预览模式{Style.RESET_ALL}（先预览变化，再确认执行）"
                )
            else:
                print(f"{option_count}. 预览模式（先预览变化，再确认执行）")
            choice_map[str(option_count)] = ExportMode.PREVIEW
            option_count += 1

        if self.enable_colors:
            print(f"{option_count}. {Fore.YELLOW}跳过{Style.RESET_ALL}（不生成新文件，保持现状）")
        else:
            print(f"{option_count}. 跳过（不生成新文件，保持现状）")
        choice_map[str(option_count)] = ExportMode.SKIP

        return choice_map

    def _get_user_choice(self, choice_map: Dict[str, ExportMode], default_choice: str = "2") -> str:
        """获取用户选择"""
        valid_choices = list(choice_map.keys())

        if self.enable_colors:
            prompt = f"{Fore.CYAN}请输入选项编号（回车默认{default_choice}）：{Style.RESET_ALL}"
        else:
            prompt = f"请输入选项编号（回车默认{default_choice}）："

        choice = input(prompt).strip()

        if not choice:
            choice = default_choice

        if choice not in valid_choices:
            if self.enable_colors:
                print(f"{Fore.RED}无效选择，使用默认选项：合并模式{Style.RESET_ALL}")
            else:
                print("无效选择，使用默认选项：合并模式")
            choice = default_choice

        return choice

    def _execute_choice(
        self, mode: ExportMode, existing_files: List[Path], output_dir_path: str
    ) -> ExportMode:
        """执行用户选择的操作"""

        if mode == ExportMode.REPLACE:
            self._execute_replace_mode(existing_files)

        elif mode == ExportMode.MERGE:
            self._execute_merge_mode()

        elif mode == ExportMode.BACKUP:
            success = self._execute_backup_mode(existing_files, output_dir_path)
            if not success:
                if self.enable_colors:
                    print(f"{Fore.RED}❌ 备份失败，切换到合并模式{Style.RESET_ALL}")
                else:
                    print("❌ 备份失败，切换到合并模式")
                return ExportMode.MERGE

        elif mode == ExportMode.SKIP:
            self._execute_skip_mode()

        elif mode == ExportMode.INCREMENTAL:
            changed_files = self._execute_incremental_mode(existing_files, output_dir_path)
            if not changed_files:
                return ExportMode.SKIP

        elif mode == ExportMode.PREVIEW:
            return self._execute_preview_mode(existing_files, output_dir_path)

        elif mode == ExportMode.SMART_MERGE:
            self._execute_smart_merge_mode()

        return mode

    def _execute_replace_mode(self, existing_files: List[Path]):
        """执行替换模式"""
        logging.info("选择替换模式，删除现有翻译文件")
        if self.enable_colors:
            print(f"{Fore.GREEN}✅ 将删除现有文件并重新生成{Style.RESET_ALL}")
        else:
            print("✅ 将删除现有文件并重新生成")

        deleted_count = 0
        for xml_file in existing_files:
            try:
                os.remove(xml_file)
                logging.info(f"删除文件：{xml_file}")
                deleted_count += 1
            except OSError as e:
                logging.error(f"无法删除 {xml_file}: {e}")

        if self.enable_colors:
            print(f"{Fore.GREEN}✅ 已删除 {deleted_count} 个文件{Style.RESET_ALL}")
        else:
            print(f"✅ 已删除 {deleted_count} 个文件")

    def _execute_merge_mode(self):
        """执行合并模式"""
        logging.info("选择合并模式，保留现有翻译文件")
        if self.enable_colors:
            print(f"{Fore.GREEN}✅ 将保留现有翻译，仅更新新内容{Style.RESET_ALL}")
        else:
            print("✅ 将保留现有翻译，仅更新新内容")

    def _execute_smart_merge_mode(self):
        """执行智能合并模式"""
        logging.info("选择智能合并模式")
        if self.enable_colors:
            print(f"{Fore.MAGENTA}🧠 将使用智能合并模式处理翻译文件{Style.RESET_ALL}")
        else:
            print("🧠 将使用智能合并模式处理翻译文件")

    def _execute_backup_mode(self, existing_files: List[Path], output_dir_path: str) -> bool:
        """执行备份模式"""
        logging.info("选择备份并替换模式")
        if self.enable_colors:
            print(f"{Fore.BLUE}🔄 正在备份现有文件...{Style.RESET_ALL}")
        else:
            print("🔄 正在备份现有文件...")

        backup_success = self._backup_existing_files(existing_files, output_dir_path)
        if backup_success:
            if self.enable_colors:
                print(f"{Fore.GREEN}✅ 备份完成，将重新生成翻译文件{Style.RESET_ALL}")
            else:
                print("✅ 备份完成，将重新生成翻译文件")

            # 备份成功后删除原文件
            for xml_file in existing_files:
                try:
                    os.remove(xml_file)
                    logging.info(f"删除文件：{xml_file}")
                except OSError as e:
                    logging.error(f"无法删除 {xml_file}: {e}")

        return backup_success

    def _execute_skip_mode(self):
        """执行跳过模式"""
        logging.info("选择跳过模式，保持现状")
        if self.enable_colors:
            print(f"{Fore.YELLOW}⏭️ 已跳过，保持现有文件不变{Style.RESET_ALL}")
        else:
            print("⏭️ 已跳过，保持现有文件不变")

    def _execute_incremental_mode(
        self, existing_files: List[Path], output_dir_path: str
    ) -> List[Path]:
        """执行增量更新模式"""
        logging.info("选择增量更新模式")
        if self.enable_colors:
            print(f"{Fore.MAGENTA}🔄 正在分析文件变化...{Style.RESET_ALL}")
        else:
            print("🔄 正在分析文件变化...")

        changed_files = self._analyze_file_changes(existing_files)
        if changed_files:
            if self.enable_colors:
                print(
                    f"{Fore.MAGENTA}📊 检测到 {len(changed_files)} 个文件需要更新{Style.RESET_ALL}"
                )
            else:
                print(f"📊 检测到 {len(changed_files)} 个文件需要更新")

            for file_path in changed_files[:5]:  # 显示前5个
                rel_path = Path(file_path).relative_to(Path(output_dir_path))
                print(f"  - {rel_path}")
            if len(changed_files) > 5:
                print(f"  ... 还有 {len(changed_files) - 5} 个文件")
        else:
            if self.enable_colors:
                print(f"{Fore.GREEN}✅ 所有文件都是最新的，无需更新{Style.RESET_ALL}")
            else:
                print("✅ 所有文件都是最新的，无需更新")

        return changed_files

    def _execute_preview_mode(self, existing_files: List[Path], output_dir_path: str) -> ExportMode:
        """执行预览模式"""
        logging.info("选择预览模式")
        if self.enable_colors:
            print(f"{Fore.CYAN}👁️ 预览将要发生的变化...{Style.RESET_ALL}")
        else:
            print("👁️ 预览将要发生的变化...")

        preview_info = self._generate_preview(existing_files, output_dir_path)
        self._display_preview(preview_info)

        # 询问用户是否确认执行
        if self.enable_colors:
            confirm_prompt = f"\n{Fore.CYAN}确认执行这些变化吗？(y/N): {Style.RESET_ALL}"
        else:
            confirm_prompt = "\n确认执行这些变化吗？(y/N): "

        confirm = input(confirm_prompt).strip().lower()
        if confirm in ["y", "yes", "是"]:
            # 让用户选择具体执行什么操作
            if self.enable_colors:
                print(f"\n{Fore.CYAN}请选择执行方式：{Style.RESET_ALL}")
                print(f"1. {Fore.GREEN}替换{Style.RESET_ALL}（执行替换操作）")
                print(f"2. {Fore.GREEN}合并{Style.RESET_ALL}（执行合并操作）")
                print(f"3. {Fore.BLUE}备份并替换{Style.RESET_ALL}（执行备份并替换）")
            else:
                print("\n请选择执行方式：")
                print("1. 替换（执行替换操作）")
                print("2. 合并（执行合并操作）")
                print("3. 备份并替换（执行备份并替换）")

            if self.enable_colors:
                exec_prompt = f"{Fore.CYAN}请选择（默认合并）：{Style.RESET_ALL}"
            else:
                exec_prompt = "请选择（默认合并）："

            exec_choice = input(exec_prompt).strip()
            exec_map = {"1": ExportMode.REPLACE, "2": ExportMode.MERGE, "3": ExportMode.BACKUP}
            actual_mode = exec_map.get(exec_choice, ExportMode.MERGE)

            # 递归调用执行实际操作
            return self._execute_choice(actual_mode, existing_files, output_dir_path)
        else:
            if self.enable_colors:
                print(f"{Fore.YELLOW}⏭️ 用户取消操作{Style.RESET_ALL}")
            else:
                print("⏭️ 用户取消操作")
            return ExportMode.SKIP

    def _backup_existing_files(self, existing_files: List[Path], output_dir_path: str) -> bool:
        """备份现有文件"""
        try:
            import shutil
            from datetime import datetime

            # 创建备份目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(output_dir_path) / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            backup_count = 0
            for file_path in existing_files:
                # 计算相对路径
                rel_path = Path(file_path).relative_to(Path(output_dir_path))
                backup_file = backup_dir / rel_path

                # 确保备份目录存在
                backup_file.parent.mkdir(parents=True, exist_ok=True)

                # 复制文件
                shutil.copy2(file_path, backup_file)
                logging.info(f"备份文件：{file_path} -> {backup_file}")
                backup_count += 1

            if self.enable_colors:
                print(
                    f"{Fore.GREEN}✅ 已备份 {backup_count} 个文件到：{backup_dir}{Style.RESET_ALL}"
                )
            else:
                print(f"✅ 已备份 {backup_count} 个文件到：{backup_dir}")
            return True

        except Exception as e:
            logging.error(f"备份文件失败：{e}")
            if self.enable_colors:
                print(f"{Fore.RED}❌ 备份失败：{e}{Style.RESET_ALL}")
            else:
                print(f"❌ 备份失败：{e}")
            return False

    def _analyze_file_changes(self, existing_files: List[Path]) -> List[Path]:
        """分析文件变化"""
        changed_files = []

        try:
            current_time = time.time()

            for file_path in existing_files:
                try:
                    # 获取文件修改时间
                    file_mtime = os.path.getmtime(file_path)

                    # 如果文件修改时间超过1小时，认为可能需要更新
                    # 这是一个简化的判断逻辑，实际可以更复杂
                    if current_time - file_mtime > 3600:  # 1小时
                        changed_files.append(file_path)

                except OSError as e:
                    logging.warning(f"无法获取文件信息 {file_path}: {e}")
                    # 如果无法获取文件信息，保守起见认为需要更新
                    changed_files.append(file_path)

        except Exception as e:
            logging.error(f"分析文件变化时出错: {e}")
            # 出错时返回所有文件
            return existing_files

        return changed_files

    def _generate_preview(
        self, existing_files: List[Path], output_dir_path: str
    ) -> FileAnalysisResult:
        """生成预览信息"""
        preview_info = FileAnalysisResult()
        preview_info.total_files = len(existing_files)
        preview_info.will_be_affected = len(existing_files)

        try:
            # 计算总文件大小
            total_size = 0
            for file_path in existing_files:
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size

                    # 添加到文件列表
                    rel_path = str(Path(file_path).relative_to(Path(output_dir_path)))
                    preview_info.files_list.append(rel_path)

                except OSError as e:
                    logging.warning(f"无法获取文件大小 {file_path}: {e}")

            preview_info.estimated_size = total_size

        except Exception as e:
            logging.error(f"生成预览信息时出错: {e}")

        return preview_info

    def _display_preview(self, preview_info: FileAnalysisResult):
        """显示预览信息"""
        if self.enable_colors:
            print(f"\n{Fore.CYAN}📊 预览信息：{Style.RESET_ALL}")
        else:
            print("\n📊 预览信息：")

        print(f"  总文件数：{preview_info.total_files}")
        print(f"  将受影响的文件：{preview_info.will_be_affected}")

        # 格式化文件大小
        size_mb = preview_info.estimated_size / (1024 * 1024)
        if size_mb >= 1:
            size_str = f"{size_mb:.2f} MB"
        else:
            size_kb = preview_info.estimated_size / 1024
            size_str = f"{size_kb:.2f} KB"

        print(f"  估计文件大小：{size_str}")

        # 显示文件列表（限制显示数量）
        if preview_info.files_list:
            print(f"  文件列表（显示前5个）：")
            for file_name in preview_info.files_list[:5]:
                print(f"    - {file_name}")
            if len(preview_info.files_list) > 5:
                print(f"    ... 还有 {len(preview_info.files_list) - 5} 个文件")

        if self.enable_colors:
            print(f"\n{Fore.YELLOW}⚠️ 注意：{Style.RESET_ALL}")
        else:
            print("\n⚠️ 注意：")
        print("  - 替换操作将删除现有文件并重新生成")
        print("  - 合并操作将保留现有翻译内容")
        print("  - 备份操作将先备份现有文件")


# 兼容性函数，支持旧代码调用
def handle_existing_translations_choice(
    output_dir_path: str,
    file_pattern: str = "*.xml",
    backup_enabled: bool = True,
    auto_mode: Optional[str] = None,
    enable_advanced_options: bool = False,
) -> str:
    """
    兼容性函数：处理现有翻译文件的用户选择

    Returns:
        str: 处理模式字符串（为了兼容性）
    """
    manager = UserInteractionManager()
    mode = manager.handle_existing_translations_choice(
        output_dir_path, file_pattern, backup_enabled, auto_mode, enable_advanced_options
    )

    # 转换回字符串格式
    mode_map = {
        ExportMode.REPLACE: "replace",
        ExportMode.MERGE: "merge",
        ExportMode.SMART_MERGE: "smart-merge",
        ExportMode.BACKUP: "backup",
        ExportMode.SKIP: "skip",
        ExportMode.INCREMENTAL: "incremental",
        ExportMode.PREVIEW: "preview",
    }

    return mode_map.get(mode, "replace")


# 导出主要接口
__all__ = [
    "UserInteractionManager",
    "FileAnalysisResult",
    "handle_existing_translations_choice",  # 兼容性函数
]
