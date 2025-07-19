"""
智能交互管理器 - 实现用户设计的四步智能流程
负责协调用户交互决策，复用现有功能完成实际工作
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Union
from colorama import Fore, Style  # type: ignore
from day_translation.utils.path_manager import PathManager
from day_translation.utils.config import (
    get_config,
    get_language_dir,
    get_language_subdir,
)

CONFIG = get_config()


class InteractionManager:
    """
    智能交互管理器 - 实现用户设计的四步智能流程
    1. 检测英文目录状态（DefInjected/Keyed）
    2. 检测输出目录状态（DefInjected/Keyed）
    3. 选择数据来源（DefInjected提取 vs Defs扫描）
    4. 处理输出冲突（合并/覆盖/重建）
    """

    def __init__(self):
        """初始化交互管理器"""
        self.path_manager = PathManager()
        self.logger = logging.getLogger(__name__)

    def _print_separator(self, title: str = "", char: str = "=", length: int = 60):
        """
        打印分隔线

        Args:
            title (str): 分隔线标题
            char (str): 分隔线字符
            length (int): 分隔线长度
        """
        if title:
            padding = (length - len(title) - 2) // 2
            print(
                f"\n{Fore.CYAN}{char * padding} {title} {char * padding}{Style.RESET_ALL}"
            )
        else:
            print(f"\n{Fore.CYAN}{char * length}{Style.RESET_ALL}")

    def _print_step_header(self, step_num: int, total_steps: int, title: str):
        """
        打印步骤标题

        Args:
            step_num (int): 当前步骤号
            total_steps (int): 总步骤数
            title (str): 步骤标题
        """
        print(
            f"\n{Fore.YELLOW}【步骤 {step_num}/{total_steps}】{title}{Style.RESET_ALL}"
        )
        print(f"{Fore.YELLOW}{'─' * 50}{Style.RESET_ALL}")

    def handle_smart_extraction_workflow(
        self,
        mod_dir: str,
    ) -> Dict[str, Any]:
        """
        执行用户设计的四步智能流程
        Args:
            mod_dir (str): 模组目录路径
        Returns:
            Dict[str, Any]: 智能流程决策结果
        """
        self._print_separator("智能提取翻译模板工作流", "=", 60)
        # 第一步：检测英文目录状态
        self._print_step_header(1, 5, "检测mod英文目录状态")
        import_status = self._detect_language_directories(mod_dir, language="English")
        # 第二步：检测输出目录状态
        self._print_step_header(2, 5, "检测输出目录状态")
        output_dir, output_language = self._get_output_directory(
            mod_dir, language="ChineseSimplified"
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
            print(f"{Fore.BLUE}检测到选择合并模式{Style.RESET_ALL}")
            print(
                f"   {Fore.GREEN}✅ 将使用5.1智能合并逻辑，无需选择模板结构{Style.RESET_ALL}"
            )
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
            return smart_config
        else:
            print(f"{Fore.YELLOW}🔄 重新开始配置流程...{Style.RESET_ALL}")
            return self.handle_smart_extraction_workflow(mod_dir)

    def _confirm_configuration(self, config: Dict[str, Any]) -> bool:
        """
        确认配置信息

        Args:
            config (Dict[str, Any]): 智能配置

        Returns:
            bool: 用户是否确认配置
        """
        print(f"\n{Fore.CYAN}📋 配置摘要确认：{Style.RESET_ALL}")
        print("   y = 确认，继续执行")
        print("   n = 取消，退出流程")
        print("   r = 重新配置，回到第一步")
        print(
            f"   📊 数据来源：{self._format_choice_description(config['data_sources']['choice'])}"
        )
        print(f"   📁 输出目录：{config['output_config']['output_dir']}")
        print(
            f"   ⚙️ 冲突处理：{self._format_conflict_description(config['output_config']['conflict_resolution'])}"
        )
        print(
            f"   🗂️ 文件结构：{self._format_structure_description(config['template_structure'])}"
        )

        while True:
            choice = (
                input(f"\n{Fore.CYAN}确认以上配置？(y/n/r): {Style.RESET_ALL}")
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
                print(
                    f"   {Fore.RED}❌ 请输入 y(确认)/n(取消)/r(重新配置){Style.RESET_ALL}"
                )

    def _format_choice_description(self, choice: str) -> str:
        """格式化数据来源描述"""
        descriptions = {
            "definjected_only": f"{Fore.GREEN}使用英文DefInjected{Style.RESET_ALL}",
            "defs_only": f"{Fore.CYAN}扫描Defs文件{Style.RESET_ALL}",
        }
        return descriptions.get(choice, choice)

    def _format_conflict_description(self, resolution: str) -> str:
        """格式化冲突处理描述"""
        descriptions = {
            "merge": f"{Fore.GREEN}合并现有文件{Style.RESET_ALL}",
            "overwrite": f"{Fore.YELLOW}覆盖相关文件{Style.RESET_ALL}",
            "rebuild": f"{Fore.RED}重建所有文件{Style.RESET_ALL}",
            "new": f"{Fore.BLUE}新建目录{Style.RESET_ALL}",
        }
        return descriptions.get(resolution, resolution)

    def _format_structure_description(self, structure: str) -> str:
        """格式化文件结构描述"""
        descriptions = {
            "original_structure": f"{Fore.GREEN}保持原英文结构{Style.RESET_ALL}",
            "defs_by_type": f"{Fore.CYAN}按定义类型分组{Style.RESET_ALL}",
            "defs_by_file_structure": f"{Fore.YELLOW}按Defs文件结构{Style.RESET_ALL}",
            "merge_logic": f"{Fore.BLUE}5.1智能合并逻辑{Style.RESET_ALL}",
        }
        return descriptions.get(structure, structure)

    def _detect_language_directories(
        self,
        mod_dir: str,
        language: str,  # 语言
    ) -> Dict[str, Union[bool, str]]:
        """
        检测指定语言目录状态（DefInjected/Keyed）
        Args:
            mod_dir (str): 模组目录路径
            language (str): 语言目录名（如 'English', 'ChineseSimplified'）
        Returns:
            Dict[str, Union[bool, str]]: 目录状态
        """
        language_dir = get_language_dir(mod_dir, language)
        print(
            f"{Fore.BLUE}🔍 正在检测目录:{mod_dir} 语言:{language}... {Style.RESET_ALL}"
            f"\n{Fore.BLUE}🔍 正在检测 {language_dir} 目录状态...{Style.RESET_ALL}"
        )
        def_dir = get_language_subdir(mod_dir, language, subdir_type="defInjected")
        keyed_dir = get_language_subdir(mod_dir, language, subdir_type="keyed")
        has_definjected = def_dir.exists() and any(def_dir.rglob("*.xml"))
        has_keyed = keyed_dir.exists() and any(keyed_dir.rglob("*.xml"))
        print(
            f"   {Fore.CYAN}检测到{def_dir}目录: {Fore.GREEN if has_definjected else Fore.RED}{'✅ 有' if has_definjected else '❌ 否'}{Style.RESET_ALL}"
        )
        print(
            f"   {Fore.CYAN}检测到{keyed_dir}目录: {Fore.GREEN if has_keyed else Fore.RED}{'✅ 有' if has_keyed else '❌ 否'}{Style.RESET_ALL}"
        )
        return {
            "has_definjected": has_definjected,
            "has_keyed": has_keyed,
            "definjected_path": str(def_dir) if has_definjected else "",
            "keyed_path": str(keyed_dir) if has_keyed else "",
            "mod_dir": str(mod_dir),
            "language": str(language),
        }

    def _get_output_directory(self, mod_dir: str, language: str) -> tuple:
        """
        获取用户指定的输出目录（支持多语言）
        Args:
            mod_dir (str): 模组目录路径
            language (str): 目标语言目录名
        Returns:
            (str, str): 输出目录路径和语言名（自定义目录时 language 为空字符串）
        """
        path_manager = PathManager()
        default_dir = str(Path(mod_dir))
        default_dirs = get_language_dir(mod_dir, language)
        history = path_manager.get_history_list("output_dir")
        print(f"{Fore.BLUE}📁 请选择输出目录：{Style.RESET_ALL}")
        print(f"{Fore.GREEN}1. 使用默认目录：{default_dirs}{Style.RESET_ALL}")
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
            if choice == "1":
                print(f"   {Fore.GREEN}✅ 选择：{default_dir}{Style.RESET_ALL}")
                path_manager.remember_path("output_dir", default_dir)
                return default_dir, language
            elif choice.isdigit() and 2 <= int(choice) <= max_choice:
                selected_path = history[int(choice) - 2]
                print(f"   {Fore.GREEN}✅ 选择：{selected_path}{Style.RESET_ALL}")
                path_manager.remember_path("output_dir", selected_path)
                # 判断是否为标准多语言目录
                return selected_path, language
            elif choice:
                if os.path.isdir(choice) or not os.path.exists(choice):
                    print(f"   {Fore.GREEN}✅ 选择：{choice}{Style.RESET_ALL}")
                    path_manager.remember_path("output_dir", choice)
                    # 用户自定义目录，language 置空
                    return choice, language
                else:
                    print(f"   {Fore.RED}❌ 路径无效：{choice}{Style.RESET_ALL}")
                    continue
            else:
                print(f"{Fore.RED}❌ 请输入选择或路径{Style.RESET_ALL}")

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
            import_status (Dict[str, Union[bool, str]]): 英文目录状态
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
            print(f"{Fore.BLUE}检测DefInjected目录：{Fore.GREEN}✅ 有{Style.RESET_ALL}")
            # 显示智能推荐
            if recommendation["recommended"] == "definjected_only":
                print(
                    f"{Fore.GREEN}🤖 智能推荐：使用DefInjected目录提取 (理由: {recommendation['reason']}){Style.RESET_ALL}"
                )
            else:
                print(
                    f"{Fore.YELLOW}🤖 智能推荐：扫描Defs文件重新提取 (理由: {recommendation['reason']}){Style.RESET_ALL}"
                )
            print(f"{Fore.YELLOW}请选择数据来源：{Style.RESET_ALL}")
            print(
                f"   {Fore.GREEN}1. 使用DefInjected目录提取翻译（更快）{Style.RESET_ALL}"
            )
            print(f"   {Fore.CYAN}2. 扫描Defs文件重新提取（完整扫描）{Style.RESET_ALL}")
            print(f"   {Fore.BLUE}3. 采用智能推荐{Style.RESET_ALL}")
            while True:
                choice = input(
                    f"\n{Fore.CYAN}请选择 (1/2/3，回车默认采用推荐): {Style.RESET_ALL}"
                ).strip()
                if choice == "1":
                    print(
                        f"   {Fore.GREEN}✅ 选择：使用DefInjected目录提取翻译{Style.RESET_ALL}"
                    )
                    return "definjected_only"
                elif choice == "2":
                    print(
                        f"   {Fore.GREEN}✅ 选择：扫描Defs文件重新提取{Style.RESET_ALL}"
                    )
                    return "defs_only"
                elif choice == "3" or choice == "":
                    print(
                        f"   {Fore.BLUE}✅ 采用智能推荐：{recommendation['recommended']}{Style.RESET_ALL}"
                    )
                    return recommendation["recommended"]
                else:
                    print(f"   {Fore.RED}❌ 请输入 1、2、3 或直接回车{Style.RESET_ALL}")
        else:
            print(f"{Fore.BLUE}检测DefInjected目录：{Fore.RED}❌ 没有{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✅ 自动选择：扫描Defs文件重新提取{Style.RESET_ALL}")
            return "defs_only"

    def _analyze_definjected_quality(self, definjected_path: str) -> Dict[str, str]:
        """
        分析英文DefInjected目录的内容质量

        Args:
            definjected_path (str): DefInjected目录路径

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
            logging.warning("分析DefInjected质量时出错: %s", e)
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
            output_status (Dict[str, Union[bool, str]]): 输出目录状态
        Returns:
            str: 冲突处理方式
        """
        has_output_files = output_status.get("has_definjected") or output_status.get(
            "has_keyed"
        )
        if has_output_files:
            # 分析现有文件状态
            analysis = self._analyze_existing_files(output_status)  # type: ignore
            print(f"{Fore.YELLOW}⚠️  检测到输出目录中已有翻译文件{Style.RESET_ALL}")
            print(f"   📊 分析结果：{analysis['summary']}")
            # 智能推荐
            if analysis["recommended"]:
                print(
                    f"{Fore.GREEN}🤖 智能推荐：{analysis['recommended']} (理由: {analysis['reason']}){Style.RESET_ALL}"
                )
            print(f"{Fore.YELLOW}请选择处理方式：{Style.RESET_ALL}")
            print(
                f"   {Fore.GREEN}1. 合并 - 保留现有翻译文件，仅添加新内容{Style.RESET_ALL}"
            )
            print(
                f"   {Fore.YELLOW}2. 覆盖 - 删除并重新生成本次要导出的翻译文件{Style.RESET_ALL}"
            )
            print(
                f"   {Fore.RED}3. 重建 - 清空整个输出目录，所有内容全部重建{Style.RESET_ALL}"
            )
            if analysis["recommended"]:
                print(f"   {Fore.BLUE}4. 采用智能推荐{Style.RESET_ALL}")
            while True:
                max_choice = 4 if analysis["recommended"] else 3
                choice = input(
                    f"\n{Fore.CYAN}请选择 (1-{max_choice}): {Style.RESET_ALL}"
                ).strip()
                if choice == "1":
                    print(f"   {Fore.GREEN}✅ 选择：合并{Style.RESET_ALL}")
                    return "merge"
                elif choice == "2":
                    print(f"   {Fore.YELLOW}✅ 选择：覆盖{Style.RESET_ALL}")
                    return "overwrite"
                elif choice == "3":
                    print(f"   {Fore.RED}✅ 选择：重建{Style.RESET_ALL}")
                    return "rebuild"
                elif (
                    choice == "4"
                    and analysis["recommended"]
                    and analysis["recommended_value"]
                ):
                    print(
                        f"   {Fore.BLUE}✅ 采用智能推荐：{analysis['recommended']}{Style.RESET_ALL}"
                    )
                    return analysis["recommended_value"]
                else:
                    print(f"   {Fore.RED}❌ 请输入 1-{max_choice}{Style.RESET_ALL}")
        else:
            print(f"{Fore.BLUE}输出目录中没有现有翻译文件{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✅ 自动选择：新建{Style.RESET_ALL}")
            return "new"

    def _analyze_existing_files(
        self, output_status: Dict[str, Union[bool, Optional[str]]]
    ) -> Dict[str, Optional[str]]:
        """
        分析现有输出文件的状态

        Args:
            output_status (Dict[str, Union[bool, Optional[str]]]): 输出目录状态

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

            # 智能推荐
            if recent_files > file_count * 0.5:  # 超过50%是最近修改的
                return {
                    "summary": summary,
                    "recommended": "合并",
                    "reason": "多数文件是最近修改的，建议保留",
                    "recommended_value": "merge",
                }
            elif file_count < 10:  # 文件较少
                return {
                    "summary": summary,
                    "recommended": "覆盖",
                    "reason": "文件较少，重新生成更干净",
                    "recommended_value": "overwrite",
                }
            elif recent_files == 0:  # 没有最近修改的文件
                return {
                    "summary": summary,
                    "recommended": "重建",
                    "reason": "文件较旧，建议重新开始",
                    "recommended_value": "rebuild",
                }
            else:
                return {
                    "summary": summary,
                    "recommended": "覆盖",
                    "reason": "平衡选择，更新相关文件",
                    "recommended_value": "overwrite",
                }

        except (OSError, ValueError) as e:
            logging.warning("分析现有文件时出错: %s", e)
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
            mod_dir (str): 模组目录路径

        Returns:
            Optional[str]: Keyed 目录路径，如果不存在则返回 None
        """
        en_keyed_dir = get_language_subdir(
            base_dir=mod_dir, language="English", subdir_type="keyed"
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
            data_source_choice (str): 数据来源选择
            conflict_resolution (str): 冲突处理方式

        Returns:
            str: 模板结构选择
        """
        # 根据你的决策树逻辑：
        # 1. 如果选择了merge(3.2)，使用5.1合并逻辑，不需要选择结构
        if conflict_resolution == "merge":
            return "merge_logic"  # 这应该在上层已经处理了

        # 2. 如果选择definjected_only且非merge，使用4.1(original_structure)
        if data_source_choice == "definjected_only":
            print(f"{Fore.BLUE}检测到使用DefInjected目录提取翻译{Style.RESET_ALL}")
            print(
                f"   {Fore.GREEN}✅ 自动选择：保持原英文DefInjected结构{Style.RESET_ALL}"
            )
            return "original_structure"

        # 3. 如果选择defs_only且非merge，询问用户选择4.2或4.3
        elif data_source_choice == "defs_only":
            print(f"{Fore.BLUE}检测到使用Defs文件扫描提取翻译{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}请选择DefInjected文件组织方式：{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}1. 按定义类型分组（推荐）{Style.RESET_ALL}")
            print("      └── ThingDefs.xml、PawnKindDefs.xml 等")
            print("      └── 便于翻译工作分类管理")
            print(f"   {Fore.CYAN}2. 按原始Defs文件结构组织{Style.RESET_ALL}")
            print("      └── 保持与Defs目录相同的文件夹和文件结构")
            print("      └── 便于对照原始定义文件")

            while True:
                choice = input(f"\n{Fore.CYAN}请选择 (1/2): {Style.RESET_ALL}").strip()
                if choice == "1":
                    print(f"   {Fore.GREEN}✅ 选择：按定义类型分组{Style.RESET_ALL}")
                    return "defs_by_type"
                elif choice == "2":
                    print(
                        f"   {Fore.CYAN}✅ 选择：按原始Defs文件结构组织{Style.RESET_ALL}"
                    )
                    return "defs_by_file_structure"
                else:
                    print(f"   {Fore.RED}❌ 请输入 1 或 2{Style.RESET_ALL}")

        # 默认选择
        return "defs_by_type"
