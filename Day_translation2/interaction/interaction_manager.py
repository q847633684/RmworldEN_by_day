"""
Day Translation 2 - 统一交互管理器

使用统一配置系统的用户交互层，提供一致的用户体验。
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from colorama import Fore, Style

from ..config import UnifiedConfig, get_config
from ..models.result_models import OperationResult, OperationStatus


class UnifiedInteractionManager:
    """统一交互管理器，使用统一配置系统"""

    def __init__(self):
        self.config = get_config()

    def show_welcome(self):
        """显示程序欢迎界面"""
        has_api_key = bool(
            self.config.user.api.aliyun_access_key_id
            or os.getenv("ALIYUN_ACCESS_KEY_ID")
        )

        print(
            f"\n{Fore.MAGENTA}=== 欢迎使用 Day Translation v2.0.0 ==={Style.RESET_ALL}"
        )
        print("功能：模组文本提取、阿里云机器翻译、翻译导入、批量处理")
        print(
            f"阿里云密钥：{Fore.GREEN if has_api_key else Fore.RED}{'已配置' if has_api_key else '未配置'}{Style.RESET_ALL}"
        )

        # 显示当前配置状态
        auto_status = (
            f"{Fore.GREEN}开启{Style.RESET_ALL}"
            if self.config.user.general.auto_mode
            else f"{Fore.YELLOW}关闭{Style.RESET_ALL}"
        )
        print(f"自动模式：{auto_status}")

        print(
            f"输入 '{Fore.RED}q{Style.RESET_ALL}' 随时退出，'{Fore.YELLOW}b{Style.RESET_ALL}' 返回主菜单"
        )
        print(f"{Fore.MAGENTA}====================================={Style.RESET_ALL}\n")
        logging.debug("显示欢迎界面")

    def show_main_menu(self) -> str:
        """显示主菜单并获取用户选择"""
        print(f"\n{Fore.MAGENTA}=== Day Translation 主菜单 ==={Style.RESET_ALL}")
        print(f"\n{Fore.BLUE}可用模式：{Style.RESET_ALL}")
        print(f"1. {Fore.GREEN}提取模板{Style.RESET_ALL}：提取翻译模板并生成 CSV 文件")
        print(f"2. {Fore.GREEN}机翻{Style.RESET_ALL}：使用阿里云翻译 CSV 文件")
        print(f"3. {Fore.GREEN}导入模板{Style.RESET_ALL}：将翻译后的 CSV 导入翻译模板")
        print(f"4. {Fore.GREEN}语料{Style.RESET_ALL}：生成英-中平行语料")
        print(f"5. {Fore.GREEN}一键流程{Style.RESET_ALL}：自动化翻译流程")
        print(f"6. {Fore.GREEN}批量处理{Style.RESET_ALL}：处理多个模组")
        print(f"7. {Fore.GREEN}配置管理{Style.RESET_ALL}：管理翻译配置")
        print(f"8. {Fore.CYAN}设置中心{Style.RESET_ALL}：统一配置管理")
        print(f"q. {Fore.YELLOW}退出{Style.RESET_ALL}")

        return (
            input(f"\n{Fore.CYAN}选择模式 (1-8, q):{Style.RESET_ALL} ").strip().lower()
        )

    def get_mod_directory(self) -> Optional[str]:
        """获取模组目录"""
        return self.config.get_path_with_validation(
            path_type="mod_dir",
            prompt="请输入模组目录（例如：C:\\Mods\\MyMod）",
            validator_type="mod",
            default=self.config.get_remembered_path("mod_dir"),
        )

    def configure_extraction_operation(self, mod_dir: str) -> Optional[Dict[str, Any]]:
        """配置提取操作的所有参数"""
        try:
            # 询问是否使用上次配置
            if self._ask_use_previous_config("提取模板"):
                extraction = self.config.user.extraction
                return {
                    "structure_choice": extraction.structure_choice,
                    "merge_mode": extraction.merge_mode,
                    "output_location": extraction.output_location,
                    "output_dir": extraction.output_dir,
                    "en_keyed_dir": extraction.en_keyed_dir,
                    "auto_detect_en_keyed": extraction.auto_detect_en_keyed,
                    "auto_choose_definjected": extraction.auto_choose_definjected,
                }

            # 重新配置
            cancelled, extraction_config = self._configure_extraction_preferences(
                mod_dir
            )
            if cancelled:
                return None

            # 保存偏好设置
            if self._ask_save_current_config():
                for key, value in extraction_config.items():
                    if hasattr(self.config.user.extraction, key):
                        setattr(self.config.user.extraction, key, value)
                self.config.save_config()
                print(f"{Fore.GREEN}✅ 配置已保存{Style.RESET_ALL}")

            return extraction_config

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}操作已取消{Style.RESET_ALL}")
            return None
        except Exception as e:
            logging.error(f"配置提取操作失败: {e}")
            print(f"{Fore.RED}❌ 配置失败: {e}{Style.RESET_ALL}")
            return None

    def _ask_use_previous_config(self, operation_name: str) -> bool:
        """询问用户是否使用上次的配置"""
        if self.config.user.general.auto_mode:
            print(
                f"{Fore.GREEN}🔄 自动模式：使用上次配置进行{operation_name}{Style.RESET_ALL}"
            )
            return True

        print(f"\n{Fore.CYAN}=== {operation_name} 配置选择 ==={Style.RESET_ALL}")
        print(f"1. {Fore.GREEN}使用上次配置{Style.RESET_ALL}（快速开始）")
        print(f"2. {Fore.YELLOW}重新配置{Style.RESET_ALL}（自定义设置）")
        print(f"3. {Fore.BLUE}查看上次配置{Style.RESET_ALL}（查看后再决定）")

        while True:
            choice = input(f"{Fore.CYAN}请选择 (1-3): {Style.RESET_ALL}").strip()

            if choice == "1":
                return True
            elif choice == "2":
                return False
            elif choice == "3":
                self._show_current_extraction_config()
                continue
            else:
                print(f"{Fore.RED}❌ 请输入 1-3{Style.RESET_ALL}")

    def _show_current_extraction_config(self):
        """显示当前的提取配置"""
        extraction = self.config.user.extraction

        print(f"\n{Fore.BLUE}=== 当前提取配置 ==={Style.RESET_ALL}")
        print(f"输出位置: {Fore.GREEN}{extraction.output_location}{Style.RESET_ALL}")
        if extraction.output_dir:
            print(f"输出目录: {Fore.GREEN}{extraction.output_dir}{Style.RESET_ALL}")
        if extraction.en_keyed_dir:
            print(
                f"英文Keyed目录: {Fore.GREEN}{extraction.en_keyed_dir}{Style.RESET_ALL}"
            )
        print(f"结构选择: {Fore.GREEN}{extraction.structure_choice}{Style.RESET_ALL}")
        print(f"合并模式: {Fore.GREEN}{extraction.merge_mode}{Style.RESET_ALL}")
        print(
            f"自动检测英文Keyed: {Fore.GREEN}{'是' if extraction.auto_detect_en_keyed else '否'}{Style.RESET_ALL}"
        )
        print(
            f"自动选择DefInjected: {Fore.GREEN}{'是' if extraction.auto_choose_definjected else '否'}{Style.RESET_ALL}"
        )

    def _configure_extraction_preferences(
        self, mod_dir: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """配置提取偏好设置"""
        extraction_config = {}

        # 1. 选择输出位置
        print(f"\n{Fore.CYAN}1. 请选择模板输出位置：{Style.RESET_ALL}")
        print(
            f"   1. {Fore.GREEN}模组内部{Style.RESET_ALL}（直接集成到模组Languages目录）"
        )
        print(f"   2. {Fore.GREEN}外部目录{Style.RESET_ALL}（独立管理，推荐）")
        default_choice = (
            "2" if self.config.user.extraction.output_location == "external" else "1"
        )

        choice = (
            input(
                f"{Fore.CYAN}请选择 (1/2, 默认{default_choice}): {Style.RESET_ALL}"
            ).strip()
            or default_choice
        )

        if choice == "1":
            extraction_config["output_location"] = "internal"
            extraction_config["output_dir"] = None
        else:
            extraction_config["output_location"] = "external"
            # 获取输出目录
            default_dir = self.config.get_remembered_path("output_dir") or "提取的翻译"
            result = self._get_smart_output_directory("输出目录", default_dir)
            if not result:
                return True, {}  # 用户取消
            output_dir, processing_mode = result
            extraction_config["output_dir"] = output_dir
            extraction_config["processing_mode"] = processing_mode

        # 2. 英文Keyed目录配置
        auto_en_keyed_dir = os.path.join(mod_dir, "Languages", "English", "Keyed")

        if os.path.exists(auto_en_keyed_dir):
            print(
                f"\n{Fore.GREEN}✅ 检测到英文Keyed目录: {auto_en_keyed_dir}{Style.RESET_ALL}"
            )
            if input(
                f"{Fore.CYAN}是否使用检测到的目录？[Y/n]: {Style.RESET_ALL}"
            ).lower() not in [
                "n",
                "no",
            ]:
                extraction_config["en_keyed_dir"] = auto_en_keyed_dir
                extraction_config["auto_detect_en_keyed"] = True
            else:
                en_keyed_dir = self._get_directory_path(
                    "英文Keyed目录",
                    self.config.get_remembered_path("en_keyed_dir"),
                    required=False,
                )
                extraction_config["en_keyed_dir"] = en_keyed_dir
                extraction_config["auto_detect_en_keyed"] = False
        else:
            print(f"\n{Fore.YELLOW}⚠️ 未检测到标准英文Keyed目录{Style.RESET_ALL}")
            if input(
                f"{Fore.CYAN}是否手动指定英文Keyed目录？[y/N]: {Style.RESET_ALL}"
            ).lower() in [
                "y",
                "yes",
            ]:
                en_keyed_dir = self._get_directory_path(
                    "英文Keyed目录",
                    self.config.get_remembered_path("en_keyed_dir"),
                    required=False,
                )
                extraction_config["en_keyed_dir"] = en_keyed_dir
                extraction_config["auto_detect_en_keyed"] = False
            else:
                extraction_config["en_keyed_dir"] = None
                extraction_config["auto_detect_en_keyed"] = True

        # 3. 结构选择
        print(f"\n{Fore.CYAN}3. 选择输出结构：{Style.RESET_ALL}")
        print(f"   1. {Fore.GREEN}原始结构{Style.RESET_ALL}（保持原有目录结构，推荐）")
        print(f"   2. {Fore.GREEN}Defs结构{Style.RESET_ALL}（按Defs分类）")
        print(f"   3. {Fore.GREEN}结构化{Style.RESET_ALL}（高度组织化）")

        structure_map = {"1": "original", "2": "defs", "3": "structured"}
        reverse_map = {v: k for k, v in structure_map.items()}
        default_structure = reverse_map.get(
            self.config.user.extraction.structure_choice, "1"
        )

        choice = (
            input(
                f"{Fore.CYAN}请选择 (1-3, 默认{default_structure}): {Style.RESET_ALL}"
            ).strip()
            or default_structure
        )
        extraction_config["structure_choice"] = structure_map.get(choice, "original")

        # 4. 合并模式选择
        print(
            f"\n{Fore.CYAN}4. 选择合并模式（处理已有翻译文件的方式）：{Style.RESET_ALL}"
        )
        print(
            f"   1. {Fore.GREEN}智能合并{Style.RESET_ALL}（推荐：保留手动编辑，添加新条目）"
        )
        print(f"   2. {Fore.YELLOW}传统合并{Style.RESET_ALL}（只更新现有条目）")
        print(f"   3. {Fore.BLUE}备份替换{Style.RESET_ALL}（备份后完全替换）")
        print(f"   4. {Fore.RED}直接替换{Style.RESET_ALL}（完全替换，不备份）")
        print(f"   5. {Fore.MAGENTA}跳过处理{Style.RESET_ALL}（跳过已有文件）")

        merge_map = {
            "1": "smart-merge",
            "2": "merge",
            "3": "backup",
            "4": "replace",
            "5": "skip",
        }
        reverse_merge_map = {v: k for k, v in merge_map.items()}
        default_merge = reverse_merge_map.get(
            self.config.user.extraction.merge_mode, "1"
        )

        choice = (
            input(
                f"{Fore.CYAN}请选择 (1-5, 默认{default_merge}): {Style.RESET_ALL}"
            ).strip()
            or default_merge
        )
        extraction_config["merge_mode"] = merge_map.get(choice, "smart-merge")

        # 5. 其他选项
        print(f"\n{Fore.CYAN}5. 其他选项：{Style.RESET_ALL}")

        default_auto_def = (
            "y" if self.config.user.extraction.auto_choose_definjected else "n"
        )
        auto_def = (
            input(
                f"{Fore.CYAN}自动选择DefInjected提取方式？[y/N, 默认{default_auto_def}]: {Style.RESET_ALL}"
            ).lower()
            or default_auto_def
        )
        extraction_config["auto_choose_definjected"] = auto_def in ["y", "yes"]

        return False, extraction_config

    def _get_directory_path(
        self, name: str, default: str = None, required: bool = True
    ) -> Optional[str]:
        """获取目录路径输入"""
        return self.config.get_path_with_validation(
            path_type=name.replace(" ", "_").lower(),
            prompt=f"请输入{name}" + (f"（默认: {default}）" if default else ""),
            validator_type="dir",
            required=required,
            default=default,
        )

    def _get_smart_output_directory(
        self, name: str, default: str = None
    ) -> Optional[Tuple[str, str]]:
        """智能获取输出目录路径，检查内容并提供处理选择

        Returns:
            Tuple[str, str]: (目录路径, 处理方式) 或 None
            处理方式可能的值: 'create', 'merge', 'overwrite', 'backup_overwrite'
        """
        # 先获取目录路径
        output_dir = self.config.get_path_with_validation(
            path_type=name.replace(" ", "_").lower(),
            prompt=f"请输入{name}" + (f"（默认: {default}）" if default else ""),
            validator_type="dir_create",  # 允许创建不存在的目录
            required=True,
            default=default,
        )

        if not output_dir:
            return None

        # 检查目录是否存在以及内容
        if not os.path.exists(output_dir):
            # 目录不存在，询问是否创建
            if input(
                f"{Fore.CYAN}目录不存在，是否创建？[Y/n]: {Style.RESET_ALL}"
            ).lower() not in [
                "n",
                "no",
            ]:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    print(f"{Fore.GREEN}✅ 已创建目录: {output_dir}{Style.RESET_ALL}")
                    return output_dir, "create"
                except Exception as e:
                    print(f"{Fore.RED}❌ 创建目录失败: {e}{Style.RESET_ALL}")
                    return None
            else:
                return None

        # 目录存在，检查内容
        try:
            files = os.listdir(output_dir)
            csv_files = [f for f in files if f.lower().endswith(".csv")]
            other_files = [f for f in files if not f.lower().endswith(".csv")]

            if not files:
                # 目录为空
                print(f"{Fore.GREEN}✅ 输出目录为空，将直接使用{Style.RESET_ALL}")
                return output_dir, "create"

            # 目录有内容，显示信息并询问处理方式
            print(f"\n{Fore.YELLOW}⚠️ 输出目录已存在内容：{Style.RESET_ALL}")
            print(f"   目录: {output_dir}")
            print(f"   CSV文件: {len(csv_files)} 个")
            print(f"   其他文件: {len(other_files)} 个")

            if csv_files:
                print(f"{Fore.CYAN}   CSV文件列表：{Style.RESET_ALL}")
                for i, file in enumerate(csv_files[:5], 1):  # 只显示前5个
                    print(f"     {i}. {file}")
                if len(csv_files) > 5:
                    print(f"     ... 还有 {len(csv_files) - 5} 个文件")

            print(f"\n{Fore.CYAN}请选择处理方式：{Style.RESET_ALL}")
            print(
                f"1. {Fore.GREEN}合并模式{Style.RESET_ALL} - 保留现有文件，新文件与现有文件合并"
            )
            print(f"2. {Fore.YELLOW}覆盖模式{Style.RESET_ALL} - 直接覆盖同名文件")
            print(f"3. {Fore.BLUE}备份覆盖{Style.RESET_ALL} - 备份现有文件后覆盖")
            print(f"4. {Fore.RED}重新选择{Style.RESET_ALL} - 选择其他目录")
            print(f"5. {Fore.MAGENTA}取消操作{Style.RESET_ALL}")

            while True:
                choice = input(f"{Fore.CYAN}请选择 (1-5): {Style.RESET_ALL}").strip()

                if choice == "1":
                    print(f"{Fore.GREEN}✅ 选择合并模式{Style.RESET_ALL}")
                    return output_dir, "merge"
                elif choice == "2":
                    if input(
                        f"{Fore.RED}确认覆盖现有文件？[y/N]: {Style.RESET_ALL}"
                    ).lower() in [
                        "y",
                        "yes",
                    ]:
                        print(f"{Fore.YELLOW}✅ 选择覆盖模式{Style.RESET_ALL}")
                        return output_dir, "overwrite"
                    else:
                        continue  # 回到选择菜单
                elif choice == "3":
                    print(f"{Fore.BLUE}✅ 选择备份覆盖模式{Style.RESET_ALL}")
                    return output_dir, "backup_overwrite"
                elif choice == "4":
                    # 递归调用重新选择目录
                    return self._get_smart_output_directory(name, default)
                elif choice == "5":
                    print(f"{Fore.MAGENTA}操作已取消{Style.RESET_ALL}")
                    return None
                else:
                    print(f"{Fore.RED}❌ 无效选择，请输入 1-5{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}❌ 检查目录内容时出错: {e}{Style.RESET_ALL}")
            # 出错时使用简单模式
            return output_dir, "create"

    def _ask_save_current_config(self) -> bool:
        """询问是否保存当前配置"""
        if self.config.user.general.auto_mode:
            return True  # 自动模式下总是保存

        return input(
            f"{Fore.CYAN}保存当前配置供下次使用？[Y/n]: {Style.RESET_ALL}"
        ).lower() not in ["n", "no"]

    def get_csv_for_import(self) -> Optional[str]:
        """获取要导入的CSV文件路径"""
        return self.config.get_path_with_validation(
            path_type="import_csv",
            prompt="请输入CSV文件路径",
            validator_type="csv",
            default=self.config.get_remembered_path("import_csv"),
        )

    def get_csv_for_translation(self) -> Optional[Tuple[str, Optional[str]]]:
        """获取机器翻译的CSV文件路径"""
        csv_path = self.config.get_path_with_validation(
            path_type="translate_csv",
            prompt="请输入要翻译的CSV文件路径",
            validator_type="csv",
            default=self.config.get_remembered_path("translate_csv"),
        )

        if csv_path:
            # 可选择输出文件
            output_csv = self.config.get_path_with_validation(
                path_type="output_csv",
                prompt="请输入翻译后的CSV文件路径（空白使用默认）",
                validator_type="csv",
                required=False,
                default=self.config.get_remembered_path("output_csv"),
                show_history=False,
            )
            return csv_path, output_csv
        return None

    def handle_settings_menu(self):
        """处理设置中心菜单"""
        while True:
            print(f"\n{Fore.BLUE}=== 设置中心 ==={Style.RESET_ALL}")
            print(f"1. {Fore.GREEN}查看当前配置{Style.RESET_ALL}")
            print(f"2. {Fore.GREEN}核心配置{Style.RESET_ALL}（语言、目录等）")
            print(f"3. {Fore.GREEN}提取偏好{Style.RESET_ALL}（合并模式、结构等）")
            print(f"4. {Fore.GREEN}通用设置{Style.RESET_ALL}（自动模式、路径记忆等）")
            print(f"5. {Fore.GREEN}API配置{Style.RESET_ALL}（阿里云密钥等）")
            print(f"6. {Fore.GREEN}导出配置{Style.RESET_ALL}")
            print(f"7. {Fore.GREEN}导入配置{Style.RESET_ALL}")
            print(f"8. {Fore.GREEN}重置配置{Style.RESET_ALL}")
            print(f"9. {Fore.GREEN}清空路径记忆{Style.RESET_ALL}")
            print(f"b. {Fore.YELLOW}返回主菜单{Style.RESET_ALL}")

            choice = (
                input(f"\n{Fore.CYAN}请选择 (1-9, b): {Style.RESET_ALL}")
                .strip()
                .lower()
            )

            if choice == "1":
                self.config.show_config()
            elif choice == "2":
                self._configure_core_settings()
            elif choice == "3":
                print(f"{Fore.YELLOW}请提供一个模组目录以配置提取偏好{Style.RESET_ALL}")
                mod_dir = self.get_mod_directory()
                if mod_dir:
                    cancelled, extraction_config = (
                        self._configure_extraction_preferences(mod_dir)
                    )
                    if not cancelled:
                        for key, value in extraction_config.items():
                            if hasattr(self.config.user.extraction, key):
                                setattr(self.config.user.extraction, key, value)
                        self.config.save_config()
                        print(f"{Fore.GREEN}✅ 提取偏好已保存{Style.RESET_ALL}")
            elif choice == "4":
                self._configure_general_settings()
            elif choice == "5":
                self._configure_api_settings()
            elif choice == "6":
                self._export_config()
            elif choice == "7":
                self._import_config()
            elif choice == "8":
                if (
                    input(
                        f"{Fore.RED}确定要重置所有配置吗？[y/N]: {Style.RESET_ALL}"
                    ).lower()
                    == "y"
                ):
                    self.config.reset_config()
                    self.config.save_config()
                    print(f"{Fore.GREEN}✅ 配置已重置{Style.RESET_ALL}")
            elif choice == "9":
                if (
                    input(
                        f"{Fore.RED}确定要清空所有路径记忆吗？[y/N]: {Style.RESET_ALL}"
                    ).lower()
                    == "y"
                ):
                    self.config.user.remembered_paths.clear()
                    self.config.user.path_history.clear()
                    self.config.save_config()
                    print(f"{Fore.GREEN}✅ 路径记忆已清空{Style.RESET_ALL}")
            elif choice == "b":
                break
            else:
                print(f"{Fore.RED}❌ 无效选择{Style.RESET_ALL}")

    def _configure_core_settings(self):
        """配置核心设置"""
        print(f"\n{Fore.BLUE}=== 核心配置 ==={Style.RESET_ALL}")

        # 默认语言
        current = self.config.core.default_language
        new_lang = input(
            f"{Fore.CYAN}默认语言（当前: {current}）[Enter保持不变]: {Style.RESET_ALL}"
        ).strip()
        if new_lang:
            self.config.core.default_language = new_lang

        # 源语言
        current = self.config.core.source_language
        new_lang = input(
            f"{Fore.CYAN}源语言（当前: {current}）[Enter保持不变]: {Style.RESET_ALL}"
        ).strip()
        if new_lang:
            self.config.core.source_language = new_lang

        # 调试模式
        current = "是" if self.config.core.debug_mode else "否"
        debug = input(
            f"{Fore.CYAN}调试模式（当前: {current}）[y/n/Enter保持]: {Style.RESET_ALL}"
        ).lower()
        if debug in ["y", "yes"]:
            self.config.core.debug_mode = True
        elif debug in ["n", "no"]:
            self.config.core.debug_mode = False

        self.config.save_config()
        print(f"{Fore.GREEN}✅ 核心配置已保存{Style.RESET_ALL}")

    def _configure_general_settings(self):
        """配置通用设置"""
        print(f"\n{Fore.BLUE}=== 通用设置 ==={Style.RESET_ALL}")

        # 自动模式
        current_auto = "是" if self.config.user.general.auto_mode else "否"
        auto_mode = input(
            f"{Fore.CYAN}启用自动模式（当前: {current_auto}）[y/n/Enter保持]: {Style.RESET_ALL}"
        ).lower()
        if auto_mode in ["y", "yes"]:
            self.config.user.general.auto_mode = True
        elif auto_mode in ["n", "no"]:
            self.config.user.general.auto_mode = False

        # 记住路径
        current_remember = "是" if self.config.user.general.remember_paths else "否"
        remember = input(
            f"{Fore.CYAN}记住用户选择的路径（当前: {current_remember}）[y/n/Enter保持]: {Style.RESET_ALL}"
        ).lower()
        if remember in ["y", "yes"]:
            self.config.user.general.remember_paths = True
        elif remember in ["n", "no"]:
            self.config.user.general.remember_paths = False

        # 操作确认
        current_confirm = "是" if self.config.user.general.confirm_operations else "否"
        confirm = input(
            f"{Fore.CYAN}重要操作前需要确认（当前: {current_confirm}）[y/n/Enter保持]: {Style.RESET_ALL}"
        ).lower()
        if confirm in ["y", "yes"]:
            self.config.user.general.confirm_operations = True
        elif confirm in ["n", "no"]:
            self.config.user.general.confirm_operations = False

        self.config.save_config()
        print(f"{Fore.GREEN}✅ 通用设置已保存{Style.RESET_ALL}")

    def _configure_api_settings(self):
        """配置API设置"""
        print(f"\n{Fore.BLUE}=== API配置 ==={Style.RESET_ALL}")

        # 阿里云密钥
        current_key = (
            "已设置" if self.config.user.api.aliyun_access_key_id else "未设置"
        )
        print(f"阿里云Access Key ID: {current_key}")

        if input(
            f"{Fore.CYAN}是否修改阿里云Access Key ID？[y/N]: {Style.RESET_ALL}"
        ).lower() in [
            "y",
            "yes",
        ]:
            new_key = input(
                f"{Fore.CYAN}请输入新的Access Key ID: {Style.RESET_ALL}"
            ).strip()
            if new_key:
                self.config.user.api.aliyun_access_key_id = new_key

        current_secret = (
            "已设置" if self.config.user.api.aliyun_access_key_secret else "未设置"
        )
        print(f"阿里云Access Key Secret: {current_secret}")

        if input(
            f"{Fore.CYAN}是否修改阿里云Access Key Secret？[y/N]: {Style.RESET_ALL}"
        ).lower() in ["y", "yes"]:
            new_secret = input(
                f"{Fore.CYAN}请输入新的Access Key Secret: {Style.RESET_ALL}"
            ).strip()
            if new_secret:
                self.config.user.api.aliyun_access_key_secret = new_secret

        self.config.save_config()
        print(f"{Fore.GREEN}✅ API配置已保存{Style.RESET_ALL}")

    def _export_config(self):
        """导出配置"""
        export_path = self.config.get_path_with_validation(
            path_type="config_export",
            prompt="请输入配置导出路径",
            validator_type="json",
            required=False,
            show_history=False,
        )
        if export_path:
            try:
                self.config.export_config(export_path)
            except Exception as e:
                print(f"{Fore.RED}❌ 导出失败: {e}{Style.RESET_ALL}")

    def _import_config(self):
        """导入配置"""
        import_path = self.config.get_path_with_validation(
            path_type="config_import",
            prompt="请输入配置文件路径",
            validator_type="json",
            default=self.config.get_remembered_path("config_import"),
        )
        if import_path:
            try:
                self.config.import_config(import_path)
                self.config.save_config()
            except Exception as e:
                print(f"{Fore.RED}❌ 导入失败: {e}{Style.RESET_ALL}")

    def show_operation_result(
        self,
        success: bool = None,
        message: str = "",
        details: List[str] = None,
        result: OperationResult = None,
    ):
        """显示操作结果 - 支持多种参数形式"""
        if result is not None:
            # 使用 OperationResult 对象
            success = result.is_success
            message = result.message
            details = []

            # 添加统计信息
            if result.processed_count > 0:
                details.append(f"处理总数: {result.processed_count}")
                details.append(f"成功: {result.success_count}")
                details.append(f"失败: {result.failed_count}")

            # 添加错误信息
            if result.errors:
                details.extend([f"错误: {error}" for error in result.errors])

            # 添加警告信息
            if result.warnings:
                details.extend([f"警告: {warning}" for warning in result.warnings])

            # 添加详细信息
            if result.details:
                for key, value in result.details.items():
                    details.append(f"{key}: {value}")

        # 显示结果
        if success:
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")

        # 显示详细信息
        if details:
            print(f"{Fore.CYAN}详细信息：{Style.RESET_ALL}")
            for detail in details:
                print(f"  {detail}")

        # 记录日志
        logging.info(f"操作结果: {'成功' if success else '失败'} - {message}")
        if details:
            logging.info(f"详细信息: {'; '.join(details)}")

    def show_operation_error(self, error_message: str):
        """显示操作错误"""
        print(f"{Fore.RED}❌ 错误: {error_message}{Style.RESET_ALL}")
        logging.error(f"操作错误: {error_message}")

    def confirm_operation(self, operation_name: str, details: str = "") -> bool:
        """确认操作"""
        if not self.config.user.general.confirm_operations:
            return True

        print(f"\n{Fore.YELLOW}=== 操作确认 ==={Style.RESET_ALL}")
        print(f"操作：{operation_name}")
        if details:
            print(f"详情：{details}")

        response = input(f"{Fore.CYAN}确认执行此操作？[y/N]: {Style.RESET_ALL}").lower()
        return response in ["y", "yes"]

    def get_api_key(self, key_name: str) -> str:
        """获取API密钥"""
        if key_name == "ALIYUN_ACCESS_KEY_ID":
            key = self.config.user.api.aliyun_access_key_id or os.getenv(key_name)
        elif key_name == "ALIYUN_ACCESS_KEY_SECRET":
            key = self.config.user.api.aliyun_access_key_secret or os.getenv(key_name)
        else:
            key = os.getenv(key_name)

        if not key:
            key = input(f"{Fore.CYAN}请输入 {key_name}: {Style.RESET_ALL}").strip()
            if key and self.config.user.api.save_api_keys:
                if (
                    input(
                        f"{Fore.YELLOW}保存API密钥到配置？[y/N]: {Style.RESET_ALL}"
                    ).lower()
                    == "y"
                ):
                    if key_name == "ALIYUN_ACCESS_KEY_ID":
                        self.config.user.api.aliyun_access_key_id = key
                    elif key_name == "ALIYUN_ACCESS_KEY_SECRET":
                        self.config.user.api.aliyun_access_key_secret = key
                    self.config.save_config()

        return key
