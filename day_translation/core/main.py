import logging
import os
import json
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from tqdm import tqdm
from colorama import init, Fore, Style
from ..utils.unified_config import get_config, UnifiedConfig
from ..utils.unified_interaction_manager import UnifiedInteractionManager
from ..core.template_manager import TemplateManager
from ..utils.machine_translate import translate_csv
from ..utils.parallel_corpus import generate_parallel_corpus
from ..utils.batch_processor import BatchProcessor
from ..utils.filter_config import UnifiedFilterRules

# 初始化 colorama 以支持 Windows 终端颜色
init()

CONFIG = get_config()

class TranslationError(Exception):
    """翻译操作的基础异常类"""
    pass

class ConfigError(TranslationError):
    """配置相关错误"""
    pass

class ImportError(TranslationError):
    """导入相关错误"""
    pass

class ExportError(TranslationError):
    """导出相关错误"""
    pass

class TranslationFacade:
    """翻译操作的核心接口，管理模组翻译流程"""
    def __init__(self, mod_dir: str, language: str = CONFIG.default_language, template_location: str = "mod"):
        """
        初始化 TranslationFacade

        Args:
            mod_dir (str): 模组目录路径
            language (str): 目标语言，默认为 CONFIG.default_language
            template_location (str): 模板位置，默认为 'mod'

        Raises:
            ConfigError: 如果配置无效
            ImportError: 如果模组目录无效
        """
        try:
            self.mod_dir = str(Path(mod_dir).resolve())
            if not os.path.isdir(self.mod_dir):
                raise ImportError(f"无效的模组目录: {mod_dir}")
                
            self.language = language
            self.template_location = template_location
            self.template_manager = TemplateManager(self.mod_dir, language, template_location)
            self._validate_config()
            
            logging.debug(f"初始化 TranslationFacade: mod_dir={self.mod_dir}, language={self.language}")
        except Exception as e:
            raise ConfigError(f"初始化失败: {str(e)}")

    def _validate_config(self) -> None:
        """验证配置是否有效"""
        if not self.language:
            raise ConfigError("未指定目标语言")
        if not os.path.isdir(self.mod_dir):
            raise ConfigError(f"模组目录不存在: {self.mod_dir}")
        if not os.path.exists(os.path.join(self.mod_dir, "Languages")):
            logging.warning(f"模组目录中未找到 Languages 文件夹: {self.mod_dir}")

    def extract_templates_and_generate_csv(self, output_dir: str, en_keyed_dir: str = None, auto_choose_definjected: bool = False, structure_choice: str = "original", merge_mode: str = "smart-merge") -> List[Tuple[str, str, str, str]]:
        """
        提取翻译模板并生成 CSV 文件
        """
        try:
            # 记录提取操作的开始，包含所有关键参数用于调试和审计
            logging.info(f"开始提取模板: output_dir={output_dir}, en_keyed_dir={en_keyed_dir}, auto_choose_definjected={auto_choose_definjected}")
              # 调用模板管理器执行核心提取操作
            # - output_dir: 输出目录，模板和CSV文件的保存位置
            # - en_keyed_dir: 英文Keyed目录，用于确保UI文本翻译完整性
            # - auto_choose_definjected: DefInjected提取方式选择（True=自动，False=交互）
            # - structure_choice: 结构选择
            # - merge_mode: 合并模式
            translations = self.template_manager.extract_and_generate_templates(
                output_dir, en_keyed_dir, auto_choose_definjected, structure_choice, merge_mode
            )
            
            # 返回提取到的翻译数据列表，格式：[(key, text, group, file_info), ...]
            return translations
        except Exception as e:
            # 捕获并处理提取过程中的任何异常
            error_msg = f"提取模板失败: {str(e)}"           # 构建详细错误信息
            logging.error(error_msg)                        # 记录错误到日志文件
            raise ExportError(error_msg)                    # 抛出自定义异常，便于上层处理

    def import_translations_to_templates(self, csv_path: str, merge: bool = True) -> None:
        """
        将翻译后的 CSV 导入翻译模板

        Args:
            csv_path (str): 翻译 CSV 文件路径
            merge (bool): 是否合并现有翻译

        Raises:
            ImportError: 如果导入失败
        """
        try:
            if not os.path.isfile(csv_path):
                raise ImportError(f"CSV文件不存在: {csv_path}")
                
            logging.info(f"导入翻译到模板: csv_path={csv_path}, merge={merge}")
            
            if not self.template_manager.import_translations(csv_path, merge):
                raise ImportError("导入翻译失败")
                
        except Exception as e:
            error_msg = f"导入翻译失败: {str(e)}"
            logging.error(error_msg)
            raise ImportError(error_msg)

    def generate_corpus(self) -> List[Tuple[str, str]]:
        """
        生成英-中平行语料

        Returns:
            List[Tuple[str, str]]: 平行语料（英文, 中文）

        Raises:
            ExportError: 如果生成失败
        """
        try:
            logging.info("开始生成平行语料")
            corpus = generate_parallel_corpus(self.mod_dir, CONFIG.source_language, self.language)
            
            if not corpus:
                logging.warning("未找到任何平行语料")
                print(f"{Fore.YELLOW}⚠️ 未找到任何平行语料{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✅ 生成语料：{len(corpus)} 条{Style.RESET_ALL}")
                
            return corpus
        except Exception as e:
            error_msg = f"生成语料失败: {str(e)}"
            logging.error(error_msg)
            raise ExportError(error_msg)

    def machine_translate(self, csv_path: str, output_csv: str = None) -> None:
        """
        使用阿里云翻译 CSV 文件

        Args:
            csv_path (str): 输入 CSV 文件路径
            output_csv (str): 输出 CSV 文件路径

        Raises:
            ExportError: 如果翻译失败
        """
        try:
            if not os.path.isfile(csv_path):
                raise ExportError(f"CSV文件不存在: {csv_path}")
                
            logging.info(f"开始机器翻译: csv_path={csv_path}, output_csv={output_csv}")              # 获取统一配置
            config = get_config()
            
            # 获取API密钥
            access_key_id = self._get_api_key("ALIYUN_ACCESS_KEY_ID", config)
            access_key_secret = self._get_api_key("ALIYUN_ACCESS_KEY_SECRET", config)
            
            # 执行翻译
            translate_csv(
                csv_path,
                output_csv or csv_path.replace(".csv", "_translated.csv"),
                access_key_id,
                access_key_secret,
                CONFIG.source_language,
                self.language
            )
            
            print(f"{Fore.GREEN}✅ 机器翻译完成{Style.RESET_ALL}")            
        except Exception as e:
            error_msg = f"机器翻译失败: {str(e)}"
            logging.error(error_msg)
            raise ExportError(error_msg)

    def _get_api_key(self, key_name: str, config: UnifiedConfig) -> str:
        """获取API密钥，支持从环境变量、配置文件或用户输入获取"""
        key = config.get_api_key(key_name) or os.getenv(key_name)
        if not key:
            key = input(f"{Fore.CYAN}请输入 {key_name}:{Style.RESET_ALL} ").strip()
            if input(f"{Fore.YELLOW}保存到配置文件？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                config.set_api_key(key_name, key)
                config.save()
                logging.debug(f"已保存 {key_name} 到用户配置文件")
        return key

def main():
    """主函数"""
    try:        # 初始化统一交互管理器
        interaction_manager = UnifiedInteractionManager()
        interaction_manager.show_welcome()
        
        logging.info("启动主工作流")
        
        while True:
            mode = interaction_manager.show_main_menu()
            
            if mode == 'q':
                break
                
            if mode not in ['1', '2', '3', '4', '5', '6', '7', '8']:
                print(f"{Fore.RED}无效选择，请输入 1-8 或 q{Style.RESET_ALL}")
                continue

            try:
                if mode == "7":
                    # 模式7：原有配置管理（保持兼容性）
                    handle_config_management(interaction_manager)
                
                elif mode == "8":
                    # 模式8：新的偏好设置管理
                    handle_preferences_management(interaction_manager)
                
                else:
                    # 其他模式需要模组目录
                    mod_dir = interaction_manager.get_mod_directory()
                    if not mod_dir:
                        continue
                        
                    facade = TranslationFacade(mod_dir)
                    
                    if mode == "1":
                        handle_extraction_mode(facade, interaction_manager, mod_dir)
                    elif mode == "2":
                        handle_translation_mode(facade, interaction_manager)
                    elif mode == "3":
                        handle_import_mode(facade, interaction_manager)
                    elif mode == "4":
                        handle_corpus_mode(facade, interaction_manager)
                    elif mode == "5":
                        handle_complete_workflow_mode(facade, interaction_manager)
                    elif mode == "6":
                        handle_batch_processing_mode(interaction_manager)
                        
            except TranslationError as e:
                interaction_manager.show_operation_result(False, str(e))
                logging.error(f"操作失败: {str(e)}")
            except Exception as e:
                interaction_manager.show_operation_result(False, f"发生错误: {str(e)}")
                logging.exception("未预期的错误")
                
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}程序被用户中断{Style.RESET_ALL}")
        logging.info("程序被用户中断")
    except Exception as e:
        print(f"{Fore.RED}❌ 程序发生严重错误: {str(e)}{Style.RESET_ALL}")
        logging.exception("程序发生严重错误")
    finally:
        logging.info("程序结束")


def handle_extraction_mode(facade: TranslationFacade, interaction_manager: UnifiedInteractionManager, mod_dir: str):
    """处理提取模板模式"""
    config = interaction_manager.configure_extraction_operation(mod_dir)
    if not config:
        return
    
    if interaction_manager.confirm_operation("提取翻译模板", f"模组: {mod_dir}"):
        facade.extract_templates_and_generate_csv(
            output_dir=config["output_dir"],
            en_keyed_dir=config["en_keyed_dir"],
            auto_choose_definjected=config["auto_choose_definjected"],
            structure_choice=config["structure_choice"],
            merge_mode=config["merge_mode"]
        )
        interaction_manager.show_operation_result(True, "模板提取完成")


def handle_translation_mode(facade: TranslationFacade, interaction_manager: UnifiedInteractionManager):
    """处理机器翻译模式"""
    config = interaction_manager.configure_translation_operation()
    if not config:
        return
    
    if interaction_manager.confirm_operation("机器翻译", f"文件: {config['csv_path']}"):
        facade.machine_translate(config["csv_path"], config["output_csv"])
        interaction_manager.show_operation_result(True, "机器翻译完成")


def handle_import_mode(facade: TranslationFacade, interaction_manager: UnifiedInteractionManager):
    """处理导入模板模式"""
    config = interaction_manager.configure_import_operation()
    if not config:
        return
    
    facade.import_translations_to_templates(config["csv_path"])
    interaction_manager.show_operation_result(True, "翻译导入完成")


def handle_corpus_mode(facade: TranslationFacade, interaction_manager: UnifiedInteractionManager):
    """处理语料生成模式"""
    if interaction_manager.confirm_operation("生成平行语料"):
        corpus = facade.generate_corpus()
        interaction_manager.show_operation_result(True, f"语料生成完成，共 {len(corpus)} 条")


def handle_complete_workflow_mode(facade: TranslationFacade, interaction_manager: UnifiedInteractionManager):
    """处理完整工作流模式"""
    config = interaction_manager.configure_complete_workflow()
    if not config:
        return
    
    if not interaction_manager.confirm_operation("完整工作流", "提取 -> 翻译 -> 导入"):
        return
    
    # 执行提取
    translations = facade.extract_templates_and_generate_csv(
        config["export_csv"], 
        config["en_keyed_dir"], 
        auto_choose_definjected=True
    )
    
    if not translations:
        interaction_manager.show_operation_result(False, "提取失败，工作流中断")
        return
    
    # 确认继续翻译
    if input(f"{Fore.YELLOW}确认翻译并导入？[y/n]:{Style.RESET_ALL} ").lower() != 'y':
        return
    
    # 执行翻译
    facade.machine_translate(config["export_csv"], config["output_csv"])
    
    # 执行导入
    final_csv = config["output_csv"] or config["export_csv"].replace('.csv', '_translated.csv')
    facade.import_translations_to_templates(final_csv)
    
    interaction_manager.show_operation_result(True, "完整工作流执行完成")


def handle_batch_processing_mode(interaction_manager: UnifiedInteractionManager):
    """处理批量处理模式"""
    config = interaction_manager.configure_batch_processing()
    if not config:
        return
    
    if not interaction_manager.confirm_operation("批量处理", f"处理 {len(config['mod_list'])} 个模组"):
        return
    
    processor = BatchProcessor()
    results = processor.process_multiple_mods(config["mod_list"], config["csv_path"])
    
    if results:
        details = []
        success_count = 0
        for mod_dir, result in results.items():
            if result.success:
                success_count += 1
                details.append(f"✓ {Path(mod_dir).name}: 成功")
            else:
                details.append(f"✗ {Path(mod_dir).name}: {result.error or '失败'}")
        
        interaction_manager.show_operation_result(
            True, 
            f"批量处理完成 ({success_count}/{len(results)} 成功)", 
            details
        )


def handle_preferences_management(interaction_manager: UnifiedInteractionManager):
    """处理偏好设置管理"""
    while True:
        choice = interaction_manager.show_preferences_menu()
        
        if choice == 'b':
            break
        elif choice == "1":
            interaction_manager.show_current_preferences()
        elif choice == "2":
            interaction_manager.user_interaction.configure_general_preferences()
        elif choice == "3":
            interaction_manager.user_interaction.show_current_extraction_config()
        elif choice == "4":
            interaction_manager.handle_preferences_reset()
        elif choice == "5":
            interaction_manager.handle_paths_clear()
        elif choice == "6":
            interaction_manager.export_preferences()
        elif choice == "7":
            interaction_manager.import_preferences()
        else:
            print(f"{Fore.RED}无效选择{Style.RESET_ALL}")


def handle_config_management(interaction_manager: UnifiedInteractionManager):
    """处理原有配置管理（简化版，推荐使用偏好设置）"""
    while True:
        print(f"\n{Fore.BLUE}=== 配置管理 ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}注意：建议使用主菜单的「偏好设置」功能来管理配置{Style.RESET_ALL}")
        print(f"1. {Fore.GREEN}查看当前配置{Style.RESET_ALL}")
        print(f"2. {Fore.GREEN}重置配置{Style.RESET_ALL}")
        print(f"3. {Fore.CYAN}转到偏好设置{Style.RESET_ALL}（推荐）")
        print(f"b. {Fore.YELLOW}返回主菜单{Style.RESET_ALL}")
        
        config_mode = input(f"\n{Fore.CYAN}选择操作 (1-3, b):{Style.RESET_ALL} ").strip().lower()
        
        if config_mode == 'b':
            break
        elif config_mode == '1':
            # 显示当前配置
            CONFIG = get_config()
            CONFIG.show_config()
        elif config_mode == '2':
            # 重置配置            if input(f"{Fore.RED}确定要重置配置吗？[y/N]: {Style.RESET_ALL}").lower() == 'y':
                try:
                    config = get_config()
                    config.reset_to_defaults()
                    config.save()
                    print(f"{Fore.GREEN}✅ 配置已重置{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}❌ 重置失败: {e}{Style.RESET_ALL}")
        elif config_mode == '3':
            # 转到偏好设置
            interaction_manager.handle_preferences_menu()
        else:
            print(f"{Fore.RED}无效选择{Style.RESET_ALL}")
        continue

if __name__ == "__main__":
    main()