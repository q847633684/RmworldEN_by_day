"""
智能交互管理器

实现用户友好的四步智能工作流程，自动检测和分析模组状态，提供智能化的决策建议
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Union
from utils.ui_style import ui
from utils.logging_config import get_logger, log_user_action
from user_config.path_manager import PathManager
from user_config import UserConfigManager


class InteractionManager:
    """
    智能交互管理器

    实现用户友好的四步智能工作流程，自动检测和分析模组状态，提供智能化的决策建议
    """

    def __init__(self):
        """初始化交互管理器"""
        self.path_manager = PathManager()
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
        self, mod_dir: str, skip_output_selection: bool = False
    ) -> Dict[str, Any]:
        """
        执行用户设计的四步智能流程

        Args:
            mod_dir: 模组目录路径
            skip_output_selection: 是否跳过输出目录选择，直接使用默认目录

        Returns:
            Dict[str, Any]: 智能流程决策结果
        """
        self._print_separator("智能提取翻译模板工作流", "=", 60)

        # 获取配置中的语言设置
        config = UserConfigManager()
        en_language = config.language_config.get_value("en_language", "English")
        cn_language = config.language_config.get_value(
            "cn_language", "ChineseSimplified"
        )

        # 第一步：检测英文目录状态
        self._print_step_header(1, 5, "检测mod英文目录状态")
        import_status = self._detect_language_directories(mod_dir, language=en_language)

        # 第二步：检测输出目录状态
        self._print_step_header(2, 5, "检测输出目录状态")
        output_dir, output_language = self._get_output_directory(
            mod_dir,
            language=cn_language,
            skip_user_selection=skip_output_selection,
        )
        output_status = self._detect_language_directories(
            output_dir, language=output_language
        )

        # 第三步：选择数据来源
        self._print_step_header(3, 5, "选择数据来源")
        data_source_choice = self._choose_data_source(import_status)

        # 第四步：处理输出冲突
        self._print_step_header(4, 5, "处理输出冲突")
        conflict_resolution = self._handle_output_conflicts(output_status)

        # 第五步：选择模板结构（根据决策树逻辑）
        self._print_step_header(5, 5, "选择模板结构")
        # 根据你的决策树，如果选择了merge，则使用5.1合并逻辑，不需要选择模板结构
        if conflict_resolution == "merge":
            ui.print_info("检测到选择合并模式")
            ui.print_success("将使用5.1智能合并逻辑，无需选择模板结构")
            template_structure = "merge_logic"  # 特殊标识
        else:
            template_structure = self._choose_template_structure(
                data_source_choice, conflict_resolution
            )

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

        # 配置确认和验证
        if self._confirm_configuration(smart_config):
            self._print_separator("✅ 智能流程决策完成", "=", 60)

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
        ui.print_section_header("配置摘要确认", ui.Icons.SETTINGS)
        ui.print_key_value("y", "确认，继续执行", ui.Icons.CONFIRM)
        ui.print_key_value("n", "取消，退出流程", ui.Icons.CANCEL)
        ui.print_key_value("r", "重新配置，回到第一步", ui.Icons.BACK)
        ui.print_key_value(
            "数据来源",
            self._format_choice_description(config["data_sources"]["choice"]),
            ui.Icons.DATA,
        )
        ui.print_key_value(
            "输出目录", config["output_config"]["output_dir"], ui.Icons.FOLDER
        )
        ui.print_key_value(
            "冲突处理",
            self._format_conflict_description(
                config["output_config"]["conflict_resolution"]
            ),
            ui.Icons.SETTINGS,
        )
        ui.print_key_value(
            "文件结构",
            self._format_structure_description(config["template_structure"]),
            ui.Icons.FOLDER,
        )

        while True:
            choice = (
                input(ui.get_input_prompt("确认以上配置", options="y/n/r"))
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
            "rebuild": "重建所有文件",
            "new": "新建目录",
        }
        return descriptions.get(resolution, resolution)

    def _format_structure_description(self, structure: str) -> str:
        """格式化文件结构描述"""
        descriptions = {
            "original_structure": "保持原英文结构",
            "defs_by_type": "按定义类型分组",
            "defs_by_file_structure": "按Defs文件结构",
            "merge_logic": "5.1智能合并逻辑",
        }
        return descriptions.get(structure, structure)

    def _detect_language_directories(
        self, mod_dir: str, language: str
    ) -> Dict[str, Union[bool, str]]:
        """
        检测指定语言目录状态（DefInjected/Keyed）

        Args:
            mod_dir: 模组目录路径
            language: 语言目录名（如 'English', 'ChineseSimplified'）

        Returns:
            Dict[str, Union[bool, str]]: 目录状态
        """
        config = UserConfigManager()
        language_dir = config.language_config.get_language_dir(mod_dir, language)
        ui.print_info(f"🔍 正在检测目录:{mod_dir} 语言:{language}...")
        ui.print_info(f"🔍 正在检测 {language_dir} 目录状态...")

        def_dir = config.language_config.get_language_subdir(
            mod_dir, language, "definjected"
        )
        keyed_dir = config.language_config.get_language_subdir(
            mod_dir, language, "keyed"
        )

        has_definjected = def_dir.exists() and any(def_dir.rglob("*.xml"))
        has_keyed = keyed_dir.exists() and any(keyed_dir.rglob("*.xml"))

        if has_definjected:
            ui.print_success(f"   检测到{def_dir}目录: ✅ 有")
        else:
            ui.print_warning(f"   检测到{def_dir}目录: ❌ 否")

        if has_keyed:
            ui.print_success(f"   检测到{keyed_dir}目录: ✅ 有")
        else:
            ui.print_warning(f"   检测到{keyed_dir}目录: ❌ 否")

        return {
            "has_definjected": has_definjected,
            "has_keyed": has_keyed,
            "definjected_path": str(def_dir) if has_definjected else "",
            "keyed_path": str(keyed_dir) if has_keyed else "",
            "mod_dir": str(mod_dir),
            "language": str(language),
        }

    def _get_output_directory(
        self, mod_dir: str, language: str, skip_user_selection: bool = False
    ) -> tuple:
        """
        获取用户指定的输出目录（支持多语言）

        Args:
            mod_dir: 模组目录路径
            language: 目标语言目录名
            skip_user_selection: 是否跳过用户选择，直接使用默认目录

        Returns:
            (str, str): 输出目录路径和语言名（自定义目录时 language 为空字符串）
        """
        path_manager = PathManager()
        default_dir = str(Path(mod_dir))
        config = UserConfigManager()
        default_dirs = config.language_config.get_language_dir(mod_dir, language)
        history = path_manager.get_history_list("output_dir")

        # 如果跳过用户选择，直接使用模组根目录
        if skip_user_selection:
            ui.print_info("📁 使用默认输出目录")
            ui.print_info(f"📁 输出目录: {default_dir}")
            path_manager.remember_path("output_dir", str(default_dir))
            return str(default_dir), language

        # 美化输出目录选择界面
        ui.print_header("📁 选择输出目录")

        ui.print_section_header("推荐选择", ui.Icons.SETTINGS)
        ui.print_menu_item(
            "1", "使用默认目录", str(default_dir), ui.Icons.FOLDER, is_recommended=True
        )

        if history:
            ui.print_section_header("历史记录", ui.Icons.HISTORY)
            for i, hist_path in enumerate(history, 2):
                ui.print_menu_item(
                    str(i), os.path.basename(hist_path), hist_path, ui.Icons.FOLDER
                )
        else:
            ui.print_section_header("历史记录", ui.Icons.HISTORY)
            ui.print_info("暂无历史记录")

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
                ui.print_success("输出目录选择成功")
                ui.print_info(f"📁 选择目录: {default_dir}")
                path_manager.remember_path("output_dir", str(default_dir))
                return str(default_dir), language
            elif choice.isdigit() and 2 <= int(choice) <= max_choice:
                selected_path = history[int(choice) - 2]
                ui.print_success("输出目录选择成功")
                ui.print_info(f"📁 选择目录: {selected_path}")
                path_manager.remember_path("output_dir", selected_path)
                # 判断是否为标准多语言目录
                return selected_path, language
            elif choice:
                if os.path.isdir(choice) or not os.path.exists(choice):
                    ui.print_success("输出目录选择成功")
                    ui.print_info(f"📁 选择目录: {choice}")
                    path_manager.remember_path("output_dir", choice)
                    # 用户自定义目录，language 置空
                    return choice, language
                else:
                    ui.print_error(f"路径无效：{choice}")
                    ui.print_tip("请检查路径是否正确，或选择历史记录中的路径")
                    continue
            else:
                ui.print_error("请输入选择或路径")
                ui.print_tip("直接回车选择默认目录")

    def _analyze_keyed_quality(self, keyed_dir: str) -> dict:
        """
        分析 Keyed 目录质量，统计文件数、最近30天修改数，给出智能建议
        """
        dir_path = Path(keyed_dir)
        xml_files = list(dir_path.rglob("*.xml"))
        file_count = len(xml_files)
        recent_files = 0

        for xml_file in xml_files:
            mtime = datetime.fromtimestamp(os.path.getmtime(xml_file))
            if (datetime.now() - mtime).days < 30:
                recent_files += 1

        suggestion = "合并" if recent_files > file_count * 0.5 else "覆盖"
        reason = (
            "大部分文件近期有更新"
            if recent_files > file_count * 0.5
            else "文件较旧或较少，建议覆盖"
        )

        return {
            "file_count": file_count,
            "recent_files": recent_files,
            "suggestion": suggestion,
            "reason": reason,
        }

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
            ui.print_success("检测DefInjected目录：有")

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
            ui.print_warning("检测DefInjected目录：没有")
            ui.print_success("自动选择：扫描Defs文件重新提取")
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
                "2", "重建", "清空整个输出目录，所有内容全部重建", ui.Icons.SETTINGS
            )

            if analysis["recommended"]:
                ui.print_info("💡 直接按回车键使用智能推荐")
                ui.print_info(f"   📊 {analysis['summary']}")
                ui.print_info(
                    f"   🎯 推荐：{analysis['recommended']} - {analysis['reason']}"
                )

            while True:
                prompt_options = "1-2"
                if analysis["recommended"]:
                    prompt_options += " 或直接回车使用智能推荐"

                choice = input(
                    ui.get_input_prompt("请选择", options=prompt_options)
                ).strip()

                if choice == "1":
                    ui.print_success("选择：合并")
                    return "merge"
                elif choice == "2":
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
                    ui.print_error("请输入 1 或 2，或直接按回车使用智能推荐")
        else:
            ui.print_info("输出目录中没有现有翻译文件")
            ui.print_success("自动选择：新建")
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

    def get_english_keyed_directory(self, mod_dir: str) -> Optional[str]:
        """
        获取英文 Keyed 目录路径

        Args:
            mod_dir: 模组目录路径

        Returns:
            Optional[str]: Keyed 目录路径，如果不存在则返回 None
        """
        config = UserConfigManager()
        en_language = config.language_config.get_value("en_language", "English")
        en_keyed_dir = config.language_config.get_language_subdir(
            mod_dir, en_language, "keyed"
        )
        if en_keyed_dir.exists() and any(en_keyed_dir.rglob("*.xml")):
            return str(en_keyed_dir)
        return None

    def _choose_template_structure(
        self, data_source_choice: str, conflict_resolution: str
    ) -> str:
        """
        根据数据来源和冲突处理方式选择模板结构（实现你的决策树逻辑）

        Args:
            data_source_choice: 数据来源选择
            conflict_resolution: 冲突处理方式

        Returns:
            str: 模板结构选择
        """
        # 根据你的决策树逻辑：
        # 1. 如果选择了merge(3.2)，使用5.1合并逻辑，不需要选择结构
        if conflict_resolution == "merge":
            return "merge_logic"  # 这应该在上层已经处理了

        # 2. 如果选择definjected_only且非merge，使用4.1(original_structure)
        if data_source_choice == "definjected_only":
            ui.print_info("检测到使用DefInjected目录提取翻译")
            ui.print_success("自动选择：保持原英文DefInjected结构")
            return "original_structure"

        # 3. 如果选择defs_only且非merge，询问用户选择4.2或4.3
        elif data_source_choice == "defs_only":
            ui.print_info("检测到使用Defs文件扫描提取翻译")
            ui.print_section_header("请选择DefInjected文件组织方式", ui.Icons.FOLDER)
            ui.print_menu_item(
                "1",
                "按原始Defs文件结构组织",
                "保持与Defs目录相同的文件夹和文件结构，便于对照原始定义文件",
                ui.Icons.FOLDER,
                is_recommended=True,
            )
            ui.print_menu_item(
                "2",
                "按定义类型分组",
                "ThingDefs.xml、PawnKindDefs.xml 等，便于翻译工作分类管理",
                ui.Icons.FOLDER,
            )

            while True:
                choice = input(
                    ui.get_input_prompt("请选择", options="1/2", default="1")
                ).strip()
                if choice == "1" or choice == "":
                    ui.print_success("选择：按原始Defs文件结构组织")
                    return "defs_by_file_structure"
                elif choice == "2":
                    ui.print_success("选择：按定义类型分组")
                    return "defs_by_type"
                else:
                    ui.print_error("请输入 1 或 2")

        # 默认选择
        return "defs_by_type"
