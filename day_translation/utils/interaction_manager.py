"""
用户交互层模块
负责处理所有用户交互逻辑，与业务逻辑分离
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from colorama import Fore, Style

from .user_preferences import UserPreferencesManager, UserInteraction, ExtractionPreferences
from ..utils.config import get_user_config


class InteractionManager:
    """交互管理器，统一处理用户交互"""
    
    def __init__(self):
        self.preferences_manager = UserPreferencesManager()
        self.user_interaction = UserInteraction(self.preferences_manager)
    
    def show_welcome(self):
        """显示程序欢迎界面"""
        user_config = get_user_config()
        has_api_key = bool(user_config.get('ALIYUN_ACCESS_KEY_ID') or os.getenv('ALIYUN_ACCESS_KEY_ID'))
        
        print(f"\n{Fore.MAGENTA}=== 欢迎使用 Day Translation v0.1.0 ==={Style.RESET_ALL}")
        print(f"功能：模组文本提取、阿里云机器翻译、翻译导入、批量处理")
        print(f"阿里云密钥：{Fore.GREEN if has_api_key else Fore.RED}{'已配置' if has_api_key else '未配置'}{Style.RESET_ALL}")
        
        # 显示当前配置状态
        prefs = self.preferences_manager.get_preferences()
        auto_status = f"{Fore.GREEN}开启{Style.RESET_ALL}" if prefs.general.auto_mode else f"{Fore.YELLOW}关闭{Style.RESET_ALL}"
        print(f"自动模式：{auto_status}")
        
        print(f"输入 '{Fore.RED}q{Style.RESET_ALL}' 随时退出，'{Fore.YELLOW}b{Style.RESET_ALL}' 返回主菜单")
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
        print(f"8. {Fore.CYAN}偏好设置{Style.RESET_ALL}：管理用户偏好和自动化设置")
        print(f"q. {Fore.YELLOW}退出{Style.RESET_ALL}")
        
        return input(f"\n{Fore.CYAN}选择模式 (1-8, q):{Style.RESET_ALL} ").strip().lower()
    
    def get_mod_directory(self) -> Optional[str]:
        """获取模组目录"""
        return self.preferences_manager.get_path_with_validation(
            path_type="mod_dir",
            prompt="请输入模组目录（例如：C:\\Mods\\MyMod）",
            validator_type="mod",
            default=self.preferences_manager.get_remembered_path("mod_dir")
        )
    
    def configure_extraction_operation(self, mod_dir: str) -> Optional[Dict[str, Any]]:
        """配置提取操作的所有参数"""
        try:
            # 询问是否使用上次配置
            if self.user_interaction.ask_use_previous_config("提取模板"):
                prefs = self.preferences_manager.get_preferences()
                return {
                    "structure_choice": prefs.extraction.structure_choice,
                    "merge_mode": prefs.extraction.merge_mode,
                    "output_location": prefs.extraction.output_location,
                    "output_dir": prefs.extraction.output_dir,
                    "en_keyed_dir": prefs.extraction.en_keyed_dir,
                    "auto_detect_en_keyed": prefs.extraction.auto_detect_en_keyed,
                    "auto_choose_definjected": prefs.extraction.auto_choose_definjected
                }
            
            # 重新配置
            cancelled, extraction_prefs = self.user_interaction.configure_extraction_preferences(mod_dir)
            if cancelled:
                return None
            
            # 保存偏好设置
            if self.user_interaction.ask_save_current_config():
                old_prefs = self.preferences_manager.get_preferences()
                old_prefs.extraction = extraction_prefs
                self.preferences_manager.save_preferences()
                print(f"{Fore.GREEN}✅ 配置已保存{Style.RESET_ALL}")
            
            return {
                "structure_choice": extraction_prefs.structure_choice,
                "merge_mode": extraction_prefs.merge_mode,
                "output_location": extraction_prefs.output_location,
                "output_dir": extraction_prefs.output_dir,
                "en_keyed_dir": extraction_prefs.en_keyed_dir,
                "auto_detect_en_keyed": extraction_prefs.auto_detect_en_keyed,
                "auto_choose_definjected": extraction_prefs.auto_choose_definjected
            }
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}操作已取消{Style.RESET_ALL}")
            return None
        except Exception as e:
            logging.error(f"配置提取操作失败: {e}")
            print(f"{Fore.RED}❌ 配置失败: {e}{Style.RESET_ALL}")
            return None
    
    def get_csv_for_import(self) -> Optional[str]:
        """获取要导入的CSV文件路径"""
        return self.preferences_manager.get_path_with_validation(
            path_type="import_csv",
            prompt="请输入CSV文件路径",
            validator_type="csv",
            default=self.preferences_manager.get_remembered_path("import_csv")
        )
    
    def get_csv_for_translation(self) -> Optional[Tuple[str, Optional[str]]]:
        """获取机器翻译的CSV文件路径"""
        csv_path = self.preferences_manager.get_path_with_validation(
            path_type="translate_csv",
            prompt="请输入要翻译的CSV文件路径",
            validator_type="csv",
            default=self.preferences_manager.get_remembered_path("translate_csv")
        )
        
        if csv_path:
            # 可选择输出文件
            output_csv = self.preferences_manager.get_path_with_validation(
                path_type="output_csv",
                prompt="请输入翻译后的CSV文件路径（空白使用默认）",
                validator_type="csv",
                required=False,
                default=self.preferences_manager.get_remembered_path("output_csv"),
                show_history=False
            )
            return csv_path, output_csv
        return None
    
    def get_csv_for_corpus(self) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
        """获取生成语料的参数"""
        csv_path = self.preferences_manager.get_path_with_validation(
            path_type="corpus_csv",
            prompt="请输入CSV文件路径",
            validator_type="csv",
            default=self.preferences_manager.get_remembered_path("corpus_csv")
        )
        
        if not csv_path:
            return None
        
        # 询问是否需要英文Keyed目录
        need_en_keyed = input(f"{Fore.CYAN}是否使用英文Keyed目录补充语料？[y/N]: {Style.RESET_ALL}").lower() in ['y', 'yes']
        en_keyed_dir = None
        if need_en_keyed:
            en_keyed_dir = self.preferences_manager.get_path_with_validation(
                path_type="en_keyed_dir",
                prompt="请输入英文Keyed目录路径",
                validator_type="dir",
                required=False,
                default=self.preferences_manager.get_remembered_path("en_keyed_dir")
            )
        
        # 输出路径
        output_csv = self.preferences_manager.get_path_with_validation(
            path_type="corpus_output",
            prompt="请输入语料输出路径",
            validator_type="csv",
            required=False,
            default=self.preferences_manager.get_remembered_path("corpus_output"),
            show_history=False
        )
        
        return csv_path, en_keyed_dir, output_csv
    
    def get_batch_operation_params(self) -> Optional[Dict[str, Any]]:
        """获取批量操作参数"""
        # 获取模组根目录
        mod_dir = self.preferences_manager.get_path_with_validation(
            path_type="batch_mod_dir",
            prompt="请输入模组根目录（包含多个模组的目录）",
            validator_type="dir",
            default=self.preferences_manager.get_remembered_path("batch_mod_dir")
        )
        
        if not mod_dir:
            return None
        
        # 选择操作类型
        print(f"\n{Fore.CYAN}选择批量操作类型：{Style.RESET_ALL}")
        print(f"1. {Fore.GREEN}批量提取{Style.RESET_ALL}")
        print(f"2. {Fore.GREEN}批量翻译{Style.RESET_ALL}")
        print(f"3. {Fore.GREEN}批量导入{Style.RESET_ALL}")
        
        operation = input(f"{Fore.CYAN}请选择 (1-3): {Style.RESET_ALL}").strip()
        
        if operation == "1":
            return {"type": "extract", "mod_dir": mod_dir}
        elif operation == "2":
            csv_path = self.preferences_manager.get_path_with_validation(
                path_type="batch_csv",
                prompt="请输入要翻译的CSV文件路径",
                validator_type="csv",
                default=self.preferences_manager.get_remembered_path("batch_csv")
            )
            return {"type": "translate", "mod_dir": mod_dir, "csv_path": csv_path}
        elif operation == "3":
            return {"type": "import", "mod_dir": mod_dir}
        else:
            print(f"{Fore.RED}❌ 无效选择{Style.RESET_ALL}")
            return None
    
    def handle_preferences_menu(self):
        """处理偏好设置菜单"""
        while True:
            print(f"\n{Fore.BLUE}=== 偏好设置 ==={Style.RESET_ALL}")
            print(f"1. {Fore.GREEN}查看当前配置{Style.RESET_ALL}")
            print(f"2. {Fore.GREEN}配置提取偏好{Style.RESET_ALL}")
            print(f"3. {Fore.GREEN}配置通用设置{Style.RESET_ALL}")
            print(f"4. {Fore.GREEN}重置所有偏好{Style.RESET_ALL}")
            print(f"5. {Fore.GREEN}清空路径记忆{Style.RESET_ALL}")
            print(f"6. {Fore.GREEN}导出配置{Style.RESET_ALL}")
            print(f"7. {Fore.GREEN}导入配置{Style.RESET_ALL}")
            print(f"b. {Fore.YELLOW}返回主菜单{Style.RESET_ALL}")
            
            choice = input(f"\n{Fore.CYAN}请选择 (1-7, b): {Style.RESET_ALL}").strip().lower()
            
            if choice == "1":
                self.user_interaction.show_current_extraction_config()
            elif choice == "2":
                print(f"{Fore.YELLOW}请提供一个模组目录以配置提取偏好{Style.RESET_ALL}")
                mod_dir = self.get_mod_directory()
                if mod_dir:
                    cancelled, extraction_prefs = self.user_interaction.configure_extraction_preferences(mod_dir)
                    if not cancelled:
                        old_prefs = self.preferences_manager.get_preferences()
                        old_prefs.extraction = extraction_prefs
                        self.preferences_manager.save_preferences()
                        print(f"{Fore.GREEN}✅ 提取偏好已保存{Style.RESET_ALL}")
            elif choice == "3":
                self.user_interaction.configure_general_preferences()
            elif choice == "4":
                if input(f"{Fore.RED}确定要重置所有偏好吗？[y/N]: {Style.RESET_ALL}").lower() == 'y':
                    self.preferences_manager.reset_preferences()
                    print(f"{Fore.GREEN}✅ 偏好已重置{Style.RESET_ALL}")
            elif choice == "5":
                if input(f"{Fore.RED}确定要清空所有路径记忆吗？[y/N]: {Style.RESET_ALL}").lower() == 'y':
                    self.preferences_manager.clear_remembered_paths()
                    print(f"{Fore.GREEN}✅ 路径记忆已清空{Style.RESET_ALL}")
            elif choice == "6":
                export_path = self.preferences_manager.get_path_with_validation(
                    path_type="preferences_export",
                    prompt="请输入配置导出路径",
                    validator_type="json",
                    required=False,
                    show_history=False
                )
                if export_path:
                    try:
                        import shutil
                        shutil.copy2(self.preferences_manager.preferences_file, export_path)
                        print(f"{Fore.GREEN}✅ 配置已导出到: {export_path}{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"{Fore.RED}❌ 导出失败: {e}{Style.RESET_ALL}")
            elif choice == "7":
                import_path = self.preferences_manager.get_path_with_validation(
                    path_type="preferences_import",
                    prompt="请输入配置文件路径",
                    validator_type="json",
                    default=self.preferences_manager.get_remembered_path("preferences_import")
                )
                if import_path:
                    try:
                        import shutil
                        shutil.copy2(import_path, self.preferences_manager.preferences_file)
                        self.preferences_manager.load_preferences()
                        print(f"{Fore.GREEN}✅ 配置已导入{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"{Fore.RED}❌ 导入失败: {e}{Style.RESET_ALL}")
            elif choice == "b":
                break
            else:
                print(f"{Fore.RED}❌ 无效选择{Style.RESET_ALL}")
    
    def confirm_operation(self, operation_name: str, details: str = "") -> bool:
        """确认操作"""
        prefs = self.preferences_manager.get_preferences()
        if not prefs.general.confirm_operations:
            return True
        
        print(f"\n{Fore.YELLOW}=== 操作确认 ==={Style.RESET_ALL}")
        print(f"操作：{operation_name}")
        if details:
            print(f"详情：{details}")
        
        return input(f"{Fore.CYAN}确认执行？[Y/n]: {Style.RESET_ALL}").lower() not in ['n', 'no']
    
    def show_operation_success(self, operation_name: str, details: str = ""):
        """显示操作成功信息"""
        print(f"\n{Fore.GREEN}✅ {operation_name} 完成{Style.RESET_ALL}")
        if details:
            print(f"详情：{details}")
    
    def show_operation_error(self, operation_name: str, error: str):
        """显示操作错误信息"""
        print(f"\n{Fore.RED}❌ {operation_name} 失败{Style.RESET_ALL}")
        print(f"错误：{error}")
        logging.error(f"{operation_name} 失败: {error}")
