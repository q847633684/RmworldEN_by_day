"""
提取专用交互管理器（extract.workflow.interaction）

与 utils.interaction（主菜单、通用交互）区分。实现提取流程的四步智能工作流，
自动检测模组状态、提供智能决策建议。
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Union
from utils.constants import (
    PATH_HISTORY_OUTPUT_DIR,
    SUBDIR_TYPE_DEFINJECTED,
    SUBDIR_TYPE_KEYED,
)
from utils.ui_style import ui
from utils.logging_config import get_logger, log_user_action
from user_config import UserConfigManager


class InteractionManager:
    """
    智能交互管理器

    实现用户友好的四步智能工作流程，自动检测和分析模组状态，提供智能化的决策建议
    """

    def __init__(self):
        """初始化交互管理器"""
        self.config = UserConfigManager.get_instance()
        self.path_manager = self.config.path_manager
        self.logger = get_logger(f"{__name__}.InteractionManager")
        self.logger.debug("初始化InteractionManager")

    def _print_separator(self, title: str = "", char: str = "=", length: int = 60):
        """
        打印分隔线

        Args:
            title: 分隔线标题
            char: 分隔线字符
            length: 分隔线长度
        """
        if title:
            ui.print_section_header(title)
        else:
            ui.print_separator(char, length)

    def _print_step_header(self, step_num: int, total_steps: int, title: str):
        """
        打印步骤标题

        Args:
            step_num: 当前步骤号
            total_steps: 总步骤数
            title: 步骤标题
        """
        ui.print_step_header(step_num, total_steps, title)

    def handle_smart_extraction_workflow(
        self,
        mod_dir: str,
        skip_output_selection: bool = False,
        fixed_output_dir: Optional[str] = None,
        batch_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        执行用户设计的四步智能流程

        Args:
            mod_dir: 当前内容根路径（如 1.6 或 1.6/rimvore-2/Common），Keyed/Defs 同逻辑：从该目录提取即该目录下 Languages
            skip_output_selection: 是否跳过输出目录选择，直接使用默认目录
            fixed_output_dir: 若指定，则强制使用该目录为输出目录（用于批量提取）
            batch_mode: 批量模式，使用默认数据来源与冲突处理，不交互、不确认

        Returns:
            Dict[str, Any]: 智能流程决策结果
        """
        if not batch_mode:
            self._print_separator("智能提取", "=", 40)

        # 获取配置中的语言设置
        en_language = self.config.language_config.get_value("en_language", "English")
        cn_language = self.config.language_config.get_default_cn_language()

        # 第一步：检测当前内容根下的英文目录状态（Keyed/DefInjected 与 Defs 同逻辑）
        if not batch_mode:
            self._print_step_header(1, 4, "检测英文目录")
        import_status = self._detect_language_directories(
            mod_dir, language=en_language
        )

        # 第二步：检测输出目录状态
        if not batch_mode:
            self._print_step_header(2, 4, "选择输出目录")
        output_dir, output_language = self._get_output_directory(
            mod_dir,
            language=cn_language,
            skip_user_selection=skip_output_selection or fixed_output_dir is not None,
            fixed_output_dir=fixed_output_dir,
        )
        output_status = self._detect_language_directories(
            output_dir, language=output_language, for_output=True
        )

        # 第三步：选择数据来源
        if not batch_mode:
            self._print_step_header(3, 4, "数据来源")
        if batch_mode:
            data_source_choice = self._get_data_source_default(import_status)
        else:
            data_source_choice = self._choose_data_source(import_status)

        # 第四步：处理输出冲突
        if not batch_mode:
            self._print_step_header(4, 4, "冲突处理")
        if batch_mode:
            conflict_resolution = self._get_conflict_resolution_default(output_status)
        else:
            conflict_resolution = self._handle_output_conflicts(output_status)

        # 模板结构：由数据来源直接决定，Defs 固定按 Def 类型分组，DefInjected 保持原结构
        if conflict_resolution in ["merge", "incremental"]:
            template_structure = "merge_logic"
        elif data_source_choice == "definjected_only":
            template_structure = "original_structure"
        else:
            template_structure = "defs_by_type"

        # 构建智能配置
        smart_config = {
            "data_sources": {
                "choice": data_source_choice,  # 数据来源
                "import_status": import_status,  # 英语状态
            },
            "output_config": {
                "conflict_resolution": conflict_resolution,  # 冲突解决
                "output_dir": output_dir,  # 输出目录
                "output_language": output_language,  # 输出语言
                "output_status": output_status,  # 输出目录状态
            },
            "template_structure": template_structure,  # 模板结构
        }

        if batch_mode:
            log_user_action(
                "智能提取配置完成(批量)",
                mod_dir=mod_dir,
                data_source=data_source_choice,
                conflict_resolution=conflict_resolution,
                template_structure=template_structure,
            )
            return smart_config

        # 配置确认和验证
        if self._confirm_configuration(smart_config):
            self._print_separator("✅ 配置完成", "=", 40)

            # 记录用户操作
            log_user_action(
                "智能提取配置完成",
                mod_dir=mod_dir,
                data_source=data_source_choice,
                conflict_resolution=conflict_resolution,
                template_structure=template_structure,
            )

            return smart_config
        else:
            ui.print_info("重新开始配置流程...")
            return self.handle_smart_extraction_workflow(mod_dir)

    def _confirm_configuration(self, config: Dict[str, Any]) -> bool:
        """
        确认配置信息

        Args:
            config: 智能配置

        Returns:
            bool: 用户是否确认配置
        """
        ui.print_section_header("配置确认", ui.Icons.SETTINGS)
        data_desc = self._format_choice_description(config['data_sources']['choice'])
        conflict_desc = self._format_conflict_description(config['output_config']['conflict_resolution'])
        struct_desc = self._format_structure_description(config['template_structure'])
        ui.print_info(f"  数据: {data_desc}  冲突: {conflict_desc}  结构: {struct_desc}")
        ui.print_info(f"  输出: {config['output_config']['output_dir']}")
        ui.print_tip("  y=确认  n=取消  r=重配")

        while True:
            choice = (
                input(ui.get_input_prompt("确认", options="y/n/r"))
                .strip()
                .lower()
            )
            if choice in ["y", "yes", ""]:
                return True
            elif choice in ["n", "no"]:
                return False
            elif choice in ["r", "restart"]:
                return False
            else:
                ui.print_error("请输入 y(确认)/n(取消)/r(重新配置)")

    def _format_choice_description(self, choice: str) -> str:
        """格式化数据来源描述"""
        descriptions = {
            "definjected_only": "使用英文DefInjected",
            "defs_only": "扫描Defs文件",
        }
        return descriptions.get(choice, choice)

    def _format_conflict_description(self, resolution: str) -> str:
        """格式化冲突处理描述"""
        descriptions = {
            "merge": "合并现有文件",
            "incremental": "新增缺少的key",
            "rebuild": "重建所有文件",
            "new": "新建目录",
        }
        return descriptions.get(resolution, resolution)

    def _format_structure_description(self, structure: str) -> str:
        """格式化文件结构描述"""
        descriptions = {
            "original_structure": "保持原英文结构",
            "defs_by_type": "按 Def 类型分组",
            "merge_logic": "智能合并/新增逻辑",
        }
        return descriptions.get(structure, structure)

    def _detect_language_directories(
        self, mod_dir: str, language: str, for_output: bool = False
    ) -> Dict[str, Union[bool, str]]:
        """
        检测当前内容根下指定语言目录状态（DefInjected/Keyed）。
        与 Defs 同逻辑：从该目录提取的 Keyed/DefInjected 即该目录下的 Languages。

        Args:
            mod_dir: 当前内容根路径（如 1.6 或 1.6/rimvore-2/Common）
            language: 语言目录名（如 'English', 'ChineseSimplified'）
            for_output: 若为 True 表示在检测「输出目录」状态（仅影响调用方语义，本函数只认当前路径）

        Returns:
            Dict[str, Union[bool, str]]: 目录状态
        """
        self.config.language_config.get_language_dir(mod_dir, language)

        def_dir = self.config.language_config.get_language_subdir(
            mod_dir, language, SUBDIR_TYPE_DEFINJECTED
        )
        keyed_dir = self.config.language_config.get_language_subdir(
            mod_dir, language, SUBDIR_TYPE_KEYED
        )
        has_definjected = def_dir.exists() and any(def_dir.rglob("*.xml"))
        # 目录存在即视为有 Keyed，不强制要求 *.xml（避免漏检如 rjw-brothel-colony）
        has_keyed = keyed_dir.exists()

        k = "✓" if has_keyed else "✗"
        d = "✓" if has_definjected else "✗"
        ui.print_info(f"  Keyed {k}  DefInjected {d}  ({language})")

        return {
            "has_definjected": has_definjected,
            "has_keyed": has_keyed,
            "definjected_path": str(def_dir) if has_definjected else "",
            "keyed_path": str(keyed_dir) if has_keyed else "",
            "mod_dir": str(mod_dir),
            "language": str(language),
        }

    def _get_output_directory(
        self,
        mod_dir: str,
        language: str,
        skip_user_selection: bool = False,
        fixed_output_dir: Optional[str] = None,
    ) -> tuple:
        """
        获取用户指定的输出目录（支持多语言）

        Args:
            mod_dir: 模组目录路径
            language: 目标语言目录名
            skip_user_selection: 是否跳过用户选择，直接使用默认目录
            fixed_output_dir: 若指定则强制使用该路径（批量提取用），忽略 skip_user_selection 的默认目录

        Returns:
            (str, str): 输出目录路径和语言名（自定义目录时 language 为空字符串）
        """
        path_manager = self.path_manager
        default_dir = str(Path(mod_dir))
        history = path_manager.get_history_list(PATH_HISTORY_OUTPUT_DIR)

        # 批量提取时使用指定输出目录
        if fixed_output_dir is not None:
            path_manager.remember_path(PATH_HISTORY_OUTPUT_DIR, str(fixed_output_dir))
            return str(fixed_output_dir), language

        # 如果跳过用户选择，直接使用模组根目录
        if skip_user_selection:
            ui.print_info(f"✓ 输出: {default_dir}")
            path_manager.remember_path(PATH_HISTORY_OUTPUT_DIR, str(default_dir))
            return str(default_dir), language

        # 输出目录选择（步骤 2 已打印步骤头，此处仅选项）
        ui.print_section_header("推荐", ui.Icons.SETTINGS)
        ui.print_menu_item(
            "1", "默认目录", str(default_dir), ui.Icons.FOLDER, is_recommended=True
        )

        if history:
            ui.print_section_header("历史", ui.Icons.HISTORY)
            for i, hist_path in enumerate(history, 2):
                ui.print_menu_item(
                    str(i), os.path.basename(hist_path), hist_path, ui.Icons.FOLDER
                )
        else:
            ui.print_section_header("历史", ui.Icons.HISTORY)
            ui.print_info("暂无")

        max_choice = len(history) + 1
        while True:
            choice = input(
                ui.get_input_prompt(
                    "请选择",
                    options=f"1-{max_choice}",
                    default="1",
                    icon="或直接输入路径",
                )
            ).strip()

            # 处理回车默认选择
            if not choice:
                choice = "1"

            if choice == "1":
                ui.print_success(f"✓ 输出: {default_dir}")
                path_manager.remember_path(PATH_HISTORY_OUTPUT_DIR, str(default_dir))
                return str(default_dir), language
            elif choice.isdigit() and 2 <= int(choice) <= max_choice:
                selected_path = history[int(choice) - 2]
                ui.print_success(f"✓ 输出: {selected_path}")
                path_manager.remember_path(PATH_HISTORY_OUTPUT_DIR, selected_path)
                return selected_path, language
            elif choice:
                if os.path.isdir(choice) or not os.path.exists(choice):
                    ui.print_success(f"✓ 输出: {choice}")
                    path_manager.remember_path(PATH_HISTORY_OUTPUT_DIR, choice)
                    # 用户自定义目录，language 置空
                    return choice, language
                else:
                    ui.print_error(f"路径无效：{choice}")
                    ui.print_tip("请检查路径是否正确，或选择历史记录中的路径")
                    continue
            else:
                ui.print_error("请输入选择或路径")
                ui.print_tip("直接回车选择默认目录")

    def _get_data_source_default(
        self, import_status: Dict[str, Union[bool, str]]
    ) -> str:
        """批量模式：根据 import_status 返回默认数据来源，不交互。"""
        has_definjected = import_status.get("has_definjected", False)
        if not has_definjected:
            return "defs_only"
        definjected_path = import_status.get("definjected_path")
        if not definjected_path:
            return "defs_only"
        recommendation = self._analyze_definjected_quality(str(definjected_path))
        return recommendation.get("recommended", "definjected_only")

    def _get_conflict_resolution_default(
        self, output_status: Dict[str, Union[bool, str]]
    ) -> str:
        """批量模式：根据 output_status 返回默认冲突处理，不交互。"""
        has_output_files = output_status.get("has_definjected") or output_status.get(
            "has_keyed"
        )
        return "merge" if has_output_files else "new"

    def _choose_data_source(self, import_status: Dict[str, Union[bool, str]]) -> str:
        """
        选择数据来源

        Args:
            import_status: 英文目录状态

        Returns:
            str: 数据来源选择
        """
        has_definjected = import_status["has_definjected"]
        if has_definjected:
            # 智能分析英文DefInjected的内容质量
            definjected_path = import_status.get("definjected_path")
            if definjected_path is None:
                return "defs_only"

            recommendation = self._analyze_definjected_quality(str(definjected_path))
            ui.print_info("DefInjected ✓")

            # 显示智能推荐
            if recommendation["recommended"] == "definjected_only":
                ui.print_tip(
                    f"智能推荐：使用DefInjected目录提取 (理由: {recommendation['reason']})"
                )
            else:
                ui.print_tip(
                    f"智能推荐：扫描Defs文件重新提取 (理由: {recommendation['reason']})"
                )

            ui.print_section_header("请选择数据来源", ui.Icons.DATA)
            ui.print_menu_item(
                "1", "使用DefInjected目录提取翻译", "更快", ui.Icons.SCAN
            )
            ui.print_menu_item("2", "扫描Defs文件重新提取", "完整扫描", ui.Icons.SCAN)
            ui.print_menu_item(
                "3", "采用智能推荐", "自动选择最佳方案", ui.Icons.SETTINGS
            )

            while True:
                choice = input(
                    ui.get_input_prompt("请选择", options="1/2/3", default="采用推荐")
                ).strip()
                if choice == "1":
                    ui.print_success("选择：使用DefInjected目录提取翻译")
                    return "definjected_only"
                elif choice == "2":
                    ui.print_success("选择：扫描Defs文件重新提取")
                    return "defs_only"
                elif choice == "3" or choice == "":
                    ui.print_success(f"采用智能推荐：{recommendation['recommended']}")
                    return recommendation["recommended"]
                else:
                    ui.print_error("请输入 1、2、3 或直接回车")
        else:
            ui.print_success("DefInjected 无，自动：扫描Defs")
            return "defs_only"

    def _analyze_definjected_quality(self, definjected_path: str) -> Dict[str, str]:
        """
        分析英文DefInjected目录的内容质量

        Args:
            definjected_path: DefInjected目录路径

        Returns:
            Dict[str, str]: 包含推荐选择和理由
        """
        try:
            definjected_dir = Path(definjected_path)
            xml_files = list(definjected_dir.rglob("*.xml"))

            if len(xml_files) == 0:
                return {"recommended": "defs_only", "reason": "DefInjected目录为空"}
            elif len(xml_files) < 5:
                return {
                    "recommended": "defs_only",
                    "reason": f"DefInjected文件较少({len(xml_files)}个)，可能不完整",
                }
            else:
                # 检查文件的修改时间，判断是否是最新的
                recent_files = 0
                for xml_file in xml_files:
                    mtime = datetime.fromtimestamp(os.path.getmtime(xml_file))
                    if datetime.now() - mtime < timedelta(days=90):  # 90天内修改过
                        recent_files += 1

                if recent_files / len(xml_files) > 0.3:  # 30%以上的文件是最近修改的
                    return {
                        "recommended": "definjected_only",
                        "reason": f"DefInjected内容较新，包含{len(xml_files)}个文件",
                    }
                else:
                    return {
                        "recommended": "defs_only",
                        "reason": "DefInjected文件可能过时，建议重新扫描",
                    }
        except (OSError, ValueError) as e:
            self.logger.warning("分析DefInjected质量时出错: %s", e)
            return {
                "recommended": "definjected_only",
                "reason": "无法分析，使用默认推荐",
            }

    def _handle_output_conflicts(
        self, output_status: Dict[str, Union[bool, str]]
    ) -> str:
        """
        处理输出冲突

        Args:
            output_status: 输出目录状态

        Returns:
            str: 冲突处理方式
        """
        has_output_files = output_status.get("has_definjected") or output_status.get(
            "has_keyed"
        )

        if has_output_files:
            # 分析现有文件状态
            analysis = self._analyze_existing_files(output_status)
            ui.print_warning("检测到输出目录中已有翻译文件")
            ui.print_info(f"分析结果：{analysis['summary']}")

            # 智能推荐
            if analysis["recommended"]:
                ui.print_tip(
                    f"智能推荐：{analysis['recommended']} (理由: {analysis['reason']})"
                )

            ui.print_section_header("请选择处理方式", ui.Icons.SETTINGS)
            ui.print_menu_item(
                "1", "合并", "保留现有翻译文件，仅添加新内容", ui.Icons.SETTINGS
            )
            ui.print_menu_item(
                "2", "新增", "扫描对比现有内容，只新增缺少的key", ui.Icons.SETTINGS
            )
            ui.print_menu_item(
                "3", "重建", "清空整个输出目录，所有内容全部重建", ui.Icons.SETTINGS
            )

            if analysis["recommended"]:
                ui.print_info("💡 直接按回车键使用智能推荐")
                ui.print_info(f"   📊 {analysis['summary']}")
                ui.print_info(
                    f"   🎯 推荐：{analysis['recommended']} - {analysis['reason']}"
                )

            while True:
                prompt_options = "1-3"
                if analysis["recommended"]:
                    prompt_options += " 或直接回车使用智能推荐"

                choice = input(
                    ui.get_input_prompt("请选择", options=prompt_options)
                ).strip()

                if choice == "1":
                    ui.print_success("选择：合并")
                    return "merge"
                elif choice == "2":
                    ui.print_success("选择：新增")
                    return "incremental"
                elif choice == "3":
                    ui.print_success("选择：重建")
                    return "rebuild"
                elif (
                    choice == ""
                    and analysis["recommended"]
                    and analysis["recommended_value"]
                ):
                    ui.print_success(f"采用智能推荐：{analysis['recommended']}")
                    return analysis["recommended_value"]
                else:
                    ui.print_error("请输入 1、2 或 3，或直接按回车使用智能推荐")
        else:
            ui.print_success("无现有文件，自动：新建")
            return "new"

    def _analyze_existing_files(
        self, output_status: Dict[str, Union[bool, Optional[str]]]
    ) -> Dict[str, Optional[str]]:
        """
        分析现有输出文件的状态

        Args:
            output_status: 输出目录状态

        Returns:
            Dict[str, Optional[str]]: 分析结果和推荐
        """
        try:
            file_count = 0
            total_size = 0
            recent_files = 0

            # 统计DefInjected文件
            if output_status["has_definjected"] and output_status["definjected_path"]:
                definjected_path = Path(str(output_status["definjected_path"]))
                for xml_file in definjected_path.rglob("*.xml"):
                    file_count += 1
                    total_size += xml_file.stat().st_size
                    mtime = datetime.fromtimestamp(os.path.getmtime(xml_file))
                    if datetime.now() - mtime < timedelta(days=7):
                        recent_files += 1

            # 统计Keyed文件
            if output_status["has_keyed"] and output_status["keyed_path"]:
                keyed_path = Path(str(output_status["keyed_path"]))
                for xml_file in keyed_path.rglob("*.xml"):
                    file_count += 1
                    total_size += xml_file.stat().st_size
                    mtime = datetime.fromtimestamp(os.path.getmtime(xml_file))
                    if datetime.now() - mtime < timedelta(days=7):
                        recent_files += 1

            # 生成摘要
            size_mb = total_size / (1024 * 1024)
            summary = f"共{file_count}个文件, {size_mb:.1f}MB, {recent_files}个最近修改"

            # 智能推荐 - 简化为合并或重建
            if recent_files > file_count * 0.5:  # 超过50%是最近修改的
                return {
                    "summary": summary,
                    "recommended": "合并",
                    "reason": "多数文件是最近修改的，建议保留",
                    "recommended_value": "merge",
                }
            else:  # 文件较旧或较少
                return {
                    "summary": summary,
                    "recommended": "重建",
                    "reason": "文件较旧或较少，建议重新开始",
                    "recommended_value": "rebuild",
                }

        except (OSError, ValueError) as e:
            self.logger.warning("分析现有文件时出错: %s", e)
            return {
                "summary": "无法分析文件状态",
                "recommended": None,
                "reason": "分析失败",
                "recommended_value": None,
            }
