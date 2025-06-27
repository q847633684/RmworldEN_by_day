"""
Day Translation 主程序模块

这是 Day Translation 项目的主要入口点，提供以下核心功能：
- 模组翻译文本提取和模板生成
- 阿里云机器翻译服务集成
- 翻译结果导入和模板管理
- 英中平行语料生成
- 批量处理多个模组
- 配置管理和用户交互

主要类：
- TranslationFacade: 翻译操作的核心接口
- TranslationError: 翻译相关异常的基类
- TranslationImportError: 导入操作异常
- ExportError: 导出操作异常

主要函数：
- main(): 程序主入口，提供交互式菜单
- validate_dir(): 验证目录路径
- validate_file(): 验证文件路径
- show_welcome(): 显示欢迎界面

使用方法:
    python main.py

作者: Day Translation Team
版本: 0.1.0
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Callable
from colorama import init, Fore, Style

# 添加当前模块的父目录到sys.path，以支持day_translation模块导入
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position
from day_translation.utils.config import ConfigError, get_config, get_user_config, save_user_config_to_file
from day_translation.utils.utils import get_history_list, update_history_list
from day_translation.utils.path_manager import PathManager
from day_translation.core.template_manager import TemplateManager
from day_translation.utils.machine_translate import translate_csv
from day_translation.utils.parallel_corpus import generate_parallel_corpus
from day_translation.utils.batch_processor import BatchProcessor
# pylint: enable=wrong-import-position

# 初始化 colorama 以支持 Windows 终端颜色
init()

CONFIG = get_config()

class TranslationError(Exception):
    """翻译操作的基础异常类"""

# class ConfigError(TranslationError):
#     """配置相关错误"""
#     pass
class TranslationImportError(TranslationError):
    """导入相关错误"""

class ExportError(TranslationError):
    """导出相关错误"""

class TranslationFacade:
    """翻译操作的核心接口，管理模组翻译流程"""
    def __init__(self, mod_dir: str, language: str = CONFIG.default_language,
                 template_location: str = "mod"):
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
                raise TranslationImportError(f"无效的模组目录: {mod_dir}")
            self.language = language
            self.template_location = template_location
            self.template_manager = TemplateManager(self.mod_dir, language, template_location)
            self._validate_config()
            logging.debug("初始化 TranslationFacade: mod_dir=%s, language=%s", self.mod_dir, self.language)
        except Exception as e:
            raise ConfigError(f"初始化失败: {str(e)}") from e

    def _validate_config(self) -> None:
        """验证配置是否有效"""
        if not self.language:
            raise ConfigError("未指定目标语言")
        if not os.path.isdir(self.mod_dir):
            raise ConfigError(f"模组目录不存在: {self.mod_dir}")
        if not os.path.exists(os.path.join(self.mod_dir, "Languages")):
            logging.warning("模组目录中未找到 Languages 文件夹: %s", self.mod_dir)

    def extract_templates_and_generate_csv(self, output_dir: str, en_keyed_dir: Optional[str] = None, auto_choose_definjected: bool = False) -> List[Tuple[str, str, str, str]]:
        """
        提取翻译模板并生成 CSV 文件
        """
        try:
            # 记录提取操作的开始，包含所有关键参数用于调试和审计
            logging.info("开始提取模板: output_dir=%s, en_keyed_dir=%s, auto_choose_definjected=%s", output_dir, en_keyed_dir, auto_choose_definjected)

            # 调用模板管理器执行核心提取操作
            # - output_dir: 输出目录，模板和CSV文件的保存位置
            # - en_keyed_dir: 英文Keyed目录，用于确保UI文本翻译完整性
            # - auto_choose_definjected: DefInjected提取方式选择（True=自动，False=交互）
            translations = self.template_manager.extract_and_generate_templates(output_dir, en_keyed_dir, auto_choose_definjected)
            # 返回提取到的翻译数据列表，格式：[(key, text, group, file_info), ...]
            return translations
        except Exception as e:
            # 捕获并处理提取过程中的任何异常
            error_msg = f"提取模板失败: {str(e)}"           # 构建详细错误信息
            logging.error(error_msg)                        # 记录错误到日志文件
            raise ExportError(error_msg) from e                    # 抛出自定义异常，便于上层处理

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
                raise TranslationImportError(f"CSV文件不存在: {csv_path}")
            logging.info("导入翻译到模板: csv_path=%s, merge=%s", csv_path, merge)
            if not self.template_manager.import_translations(csv_path, merge):
                raise TranslationImportError("导入翻译失败")

        except Exception as e:
            error_msg = f"导入翻译失败: {str(e)}"
            logging.error(error_msg)
            raise TranslationImportError(error_msg) from e

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
            # generate_parallel_corpus 函数签名：(mode: str, mod_dir: str) -> int
            # 使用模式 "2" 表示从 DefInjected 和 Keyed 提取
            corpus_count = generate_parallel_corpus("2", self.mod_dir)

            if not corpus_count:
                logging.warning("未找到任何平行语料")
                print(f"{Fore.YELLOW}⚠️ 未找到任何平行语料{Style.RESET_ALL}")
                return []
            else:
                print(f"{Fore.GREEN}✅ 生成语料：{corpus_count} 条{Style.RESET_ALL}")

            # 由于 generate_parallel_corpus 返回数量而非实际语料，这里返回空列表
            # 实际的语料文件已经保存到磁盘
            return []
        except Exception as e:
            error_msg = f"生成语料失败: {str(e)}"
            logging.error(error_msg)
            raise ExportError(error_msg) from e

    def machine_translate(self, csv_path: str, output_csv: Optional[str] = None) -> None:
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

            logging.info("开始机器翻译: csv_path=%s, output_csv=%s", csv_path, output_csv)
              # 获取用户配置
            user_config = get_user_config()

            # 获取API密钥
            access_key_id = self._get_api_key("ALIYUN_ACCESS_KEY_ID", user_config)
            access_key_secret = self._get_api_key("ALIYUN_ACCESS_KEY_SECRET", user_config)

            # 执行翻译
            translate_csv(
                csv_path,
                output_csv or csv_path.replace(".csv", "_translated.csv"),
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                source_language=CONFIG.source_language,
                target_language=self.language
            )

            print(f"{Fore.GREEN}✅ 机器翻译完成{Style.RESET_ALL}")

        except Exception as e:
            error_msg = f"机器翻译失败: {str(e)}"
            logging.error(error_msg)
            raise ExportError(error_msg) from e

    def _get_api_key(self, key_name: str, user_config: Dict[str, Any]) -> str:
        """获取API密钥，支持从环境变量、配置文件或用户输入获取"""
        key = user_config.get(key_name) or os.getenv(key_name)
        if not key:
            key = input(f"{Fore.CYAN}请输入 {key_name}:{Style.RESET_ALL} ").strip()
            if input(f"{Fore.YELLOW}保存到配置文件？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                user_config[key_name] = key
                save_user_config_to_file(user_config)
                logging.debug("已保存 %s 到用户配置文件", key_name)
        return key

def get_user_input_with_history(prompt: str, history_key: str, required: bool = True, validate_func: Optional[Callable[[str], bool]] = None) -> Optional[str]:
    """
    获取用户输入，支持历史记录和验证

    Args:
        prompt (str): 提示文本
        history_key (str): 历史记录键名
        required (bool): 是否必需输入
        validate_func (callable): 验证函数

    Returns:
        Optional[str]: 用户输入，如果验证失败则返回 None
    """
    history = get_history_list(history_key)
    while True:
        if history:
            print(f"\n{Fore.CYAN}历史记录：{Style.RESET_ALL}")
            for i, path in enumerate(history, 1):
                print(f"{i}. {path}")
            print(f"0. {Fore.YELLOW}输入新路径{Style.RESET_ALL}")

            choice = input(f"\n{Fore.CYAN}选择历史记录 (0-{len(history)}) 或直接输入新路径：{Style.RESET_ALL}").strip()

            if choice.isdigit() and 0 <= int(choice) <= len(history):
                if int(choice) == 0:
                    path = input(f"{Fore.CYAN}{prompt}{Style.RESET_ALL}").strip()
                else:
                    path = history[int(choice) - 1]
            else:
                path = choice
        else:
            path = input(f"{Fore.CYAN}{prompt}{Style.RESET_ALL}").strip()

        if not path and not required:
            return None

        if not path:
            print(f"{Fore.RED}❌ 输入不能为空{Style.RESET_ALL}")
            continue

        if validate_func and not validate_func(path):
            print(f"{Fore.RED}❌ 输入验证失败{Style.RESET_ALL}")
            continue

        update_history_list(history_key, path)
        return path

def validate_dir(path: str) -> bool:
    """验证目录是否存在且可访问"""
    try:
        path_obj = Path(path).resolve()
        is_valid = path_obj.is_dir() and os.access(path_obj, os.R_OK)
        logging.debug("验证目录: %s, 结果=%s", path, is_valid)
        return is_valid
    except (OSError, ValueError, TypeError) as e:
        logging.debug("验证目录失败: %s, 错误=%s", path, e)
        return False

def validate_file(path: str) -> bool:
    """验证文件是否存在或可写入"""
    try:
        path_obj = Path(path).resolve()
        if path_obj.exists():
            return os.access(path_obj, os.R_OK)
        return os.access(path_obj.parent, os.W_OK)
    except (OSError, ValueError, TypeError) as e:
        logging.debug("验证文件失败: %s, 错误=%s", path, e)
        return False

def show_welcome():
    """显示程序欢迎界面，包含版本和配置状态"""
    user_config = get_user_config()
    has_api_key = bool(user_config.get('ALIYUN_ACCESS_KEY_ID') or os.getenv('ALIYUN_ACCESS_KEY_ID'))
    print(f"\n{Fore.MAGENTA}=== 欢迎使用 Day Translation v0.1.0 ==={Style.RESET_ALL}")
    print("功能：模组文本提取、阿里云机器翻译、翻译导入、批量处理")
    print(f"阿里云密钥：{Fore.GREEN if has_api_key else Fore.RED}{'已配置' if has_api_key else '未配置'}{Style.RESET_ALL}")
    print(f"输入 '{Fore.RED}q{Style.RESET_ALL}' 随时退出，'{Fore.YELLOW}b{Style.RESET_ALL}' 返回主菜单")
    print(f"{Fore.MAGENTA}====================================={Style.RESET_ALL}\n")
    logging.debug("显示欢迎界面")

def main():
    """主函数"""
    try:
        show_welcome()
        logging.info("启动主工作流")

        path_manager = PathManager()

        while True:
            print(f"\n{Fore.MAGENTA}=== Day Translation 主菜单 ==={Style.RESET_ALL}")
            print(f"\n{Fore.BLUE}可用模式：{Style.RESET_ALL}")
            print(f"1. {Fore.GREEN}提取模板{Style.RESET_ALL}：提取翻译模板并生成 CSV 文件")
            print(f"2. {Fore.GREEN}机翻{Style.RESET_ALL}：使用阿里云翻译 CSV 文件")
            print(f"3. {Fore.GREEN}导入模板{Style.RESET_ALL}：将翻译后的 CSV 导入翻译模板")
            print(f"4. {Fore.GREEN}语料{Style.RESET_ALL}：生成英-中平行语料")
            print(f"5. {Fore.GREEN}完整流程{Style.RESET_ALL}：提取、翻译、导入")
            print(f"6. {Fore.GREEN}批量处理{Style.RESET_ALL}：处理多个模组")
            print(f"7. {Fore.GREEN}配置管理{Style.RESET_ALL}：管理翻译配置")
            print(f"q. {Fore.YELLOW}退出{Style.RESET_ALL}")

            mode = input(f"\n{Fore.CYAN}选择模式 (1-7, q):{Style.RESET_ALL} ").strip().lower()

            if mode == 'q':
                break

            if mode not in ['1', '2', '3', '4', '5', '6', '7']:
                print(f"{Fore.RED}无效选择，请输入 1-7 或 q{Style.RESET_ALL}")
                continue

            try:
                if mode == "7":
                    # 模式7：配置管理
                    while True:
                        print(f"\n{Fore.BLUE}=== 配置管理 ==={Style.RESET_ALL}")
                        print(f"1. {Fore.GREEN}查看当前配置{Style.RESET_ALL}")
                        print(f"2. {Fore.GREEN}修改配置{Style.RESET_ALL}")
                        print(f"3. {Fore.GREEN}重置配置{Style.RESET_ALL}")
                        print(f"4. {Fore.GREEN}导出配置{Style.RESET_ALL}")
                        print(f"5. {Fore.GREEN}导入配置{Style.RESET_ALL}")
                        print(f"6. {Fore.GREEN}加载规则配置{Style.RESET_ALL}")
                        print(f"b. {Fore.YELLOW}返回主菜单{Style.RESET_ALL}")

                        config_mode = input(f"\n{Fore.CYAN}选择操作 (1-6, b):{Style.RESET_ALL} ").strip().lower()

                        if config_mode == 'b':
                            break

                        if config_mode == "1":
                            CONFIG.show_config()
                        elif config_mode == "2":
                            print(f"\n{Fore.BLUE}可修改的配置项：{Style.RESET_ALL}")
                            print("1. 默认语言")
                            print("2. 源语言")
                            print("3. 输出CSV路径")
                            print("4. 日志文件路径")
                            print("5. 调试模式")
                            print("b. 返回")
                            item = input(f"\n{Fore.CYAN}选择要修改的项 (1-5, b):{Style.RESET_ALL} ").strip().lower()
                            if item == 'b':
                                continue
                            try:
                                if item == "1":
                                    value = path_manager.get_path(path_type="default_language", prompt="请输入默认语言（例如：ChineseSimplified）: ", validator_type="str", default=path_manager.get_remembered_path("default_language"))
                                    if value:
                                        CONFIG.update_config('default_language', value)
                                elif item == "2":
                                    value = path_manager.get_path(path_type="source_language", prompt="请输入源语言（例如：English）: ", validator_type="str", default=path_manager.get_remembered_path("source_language"))
                                    if value:
                                        CONFIG.update_config('source_language', value)
                                elif item == "3":
                                    value = path_manager.get_path(path_type="output_csv", prompt="请输入输出CSV路径（例如：output.csv）: ", validator_type="csv", default=path_manager.get_remembered_path("output_csv"))
                                    if value:
                                        CONFIG.update_config('output_csv', value)
                                elif item == "4":
                                    value = path_manager.get_path(path_type="log_file", prompt="请输入日志文件路径（例如：translation.log）: ", validator_type="file", default=path_manager.get_remembered_path("log_file"))
                                    if value:
                                        CONFIG.update_config('log_file', value)
                                elif item == "5":
                                    value = input("是否启用调试模式？[y/n]: ").lower() == 'y'
                                    CONFIG.update_config('debug_mode', value)
                                else:
                                    print(f"{Fore.RED}无效选择{Style.RESET_ALL}")
                                    continue
                                print(f"{Fore.GREEN}  ✅ 配置已更新{Style.RESET_ALL}")
                                CONFIG.save_user_config()
                            except ConfigError as e:
                                print(f"{Fore.RED}❌ {str(e)}{Style.RESET_ALL}")
                        elif config_mode == "3":
                            if input(f"{Fore.YELLOW}确认重置配置？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                                # 提示用户手动删除配置文件来重置
                                config_path = get_user_config()
                                if config_path:
                                    print(f"{Fore.YELLOW}请手动删除配置文件来重置配置：{Style.RESET_ALL}")
                                    print(f"{Fore.CYAN}配置文件位置：~/.day_translation/config.json{Style.RESET_ALL}")
                                else:
                                    print(f"{Fore.GREEN}✅ 当前已是默认配置{Style.RESET_ALL}")
                        elif config_mode == "4":
                            config_path = path_manager.get_path(path_type="config_export", prompt="请输入导出配置路径（例如：config_export.json）: ", validator_type="json", default=path_manager.get_remembered_path("config_export"))
                            if config_path:
                                try:
                                    CONFIG.export_config(config_path)
                                    print(f"{Fore.GREEN}✅ 配置已导出到：{config_path}{Style.RESET_ALL}")
                                except ConfigError as e:
                                    print(f"{Fore.RED}❌ {str(e)}{Style.RESET_ALL}")
                        elif config_mode == "5":
                            config_path = path_manager.get_path(path_type="config_import", prompt="请输入导入配置路径（例如：config_import.json）: ", validator_type="json", default=path_manager.get_remembered_path("config_import"))
                            if config_path:
                                try:
                                    CONFIG.import_config(config_path)
                                    print(f"{Fore.GREEN}✅ 配置已导入{Style.RESET_ALL}")
                                    CONFIG.save_user_config()
                                except ConfigError as e:
                                    print(f"{Fore.RED}❌ {str(e)}{Style.RESET_ALL}")
                        elif config_mode == "6":
                            rules_path = path_manager.get_path(path_type="rules_config", prompt="请输入自定义规则配置文件路径（例如：rules.json）: ", validator_type="json", default=path_manager.get_remembered_path("rules_config"))
                            if rules_path:
                                try:
                                    CONFIG.load_custom_rules(rules_path)
                                    print(f"{Fore.GREEN}✅ 规则配置已加载{Style.RESET_ALL}")
                                    CONFIG.save_user_config()
                                except ConfigError as e:
                                    print(f"{Fore.RED}❌ {str(e)}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}无效选择{Style.RESET_ALL}")
                    continue  # 配置管理完成后返回主菜单
                mod_dir = path_manager.get_path(
                    path_type="mod_dir",
                    prompt="请输入模组目录（例如：C:\\Mods\\MyMod）: ",
                    validator_type="mod",
                    default=path_manager.get_remembered_path("mod_dir")                )
                if not mod_dir:
                    continue

                facade = TranslationFacade(mod_dir)

                if mode == "1":
                    # ==================== 模式1：提取翻译模板并生成 CSV 文件 ====================
                    # 这是最核心的功能，从模组中提取所有可翻译文本并生成翻译模板
                    # 步骤1：选择输出模式
                    # 让用户选择是生成到模组内部还是外部目录
                    print(f"\n{Fore.CYAN}请选择模板输出位置：{Style.RESET_ALL}")
                    print(f"1. {Fore.GREEN}模组内部{Style.RESET_ALL}（直接集成到模组Languages目录，适合开发模组）")
                    print(f"2. {Fore.GREEN}外部目录{Style.RESET_ALL}（独立管理，适合翻译工作和分发）")
                    print(f"b. {Fore.YELLOW}返回主菜单{Style.RESET_ALL}")

                    output_choice = input(f"{Fore.CYAN}请输入选项编号（1/2/b，回车默认2）：{Style.RESET_ALL}").strip().lower()

                    if output_choice == 'b':
                        continue  # 返回主菜单

                    output_dir = None                                              # 初始化输出目录变量

                    if output_choice == "1":
                        # 选择内部模式：直接输出到模组内部
                        print(f"{Fore.GREEN}✅ 将生成模板到模组内部Languages目录{Style.RESET_ALL}")
                        output_dir = None                                          # None表示内部模式
                    else:
                        # 选择外部模式：要求用户指定外部目录
                        print(f"{Fore.GREEN}✅ 将生成模板到外部目录{Style.RESET_ALL}")
                        output_dir = path_manager.get_path(
                            path_type="output_dir",                                # 路径类型标识，用于记忆用户选择
                            prompt="请输入外部输出目录路径（例如：output 或 D:\\translations）: ",  # 用户提示信息
                            validator_type="output_dir",                           # 验证器类型，确保路径有效
                            default=path_manager.get_remembered_path("output_dir") # 使用上次记住的路径作为默认值
                        )
                        if not output_dir:                                         # 用户取消或输入无效
                            continue                                               # 返回主菜单

                    # 步骤2：处理英文 Keyed 目录选择
                    # Keyed 是 RimWorld 中UI文本的存储方式，英文模板可以确保翻译完整性
                    en_keyed_dir = None                                           # 初始化英文Keyed目录变量
                      # 步骤2a：自动检测英文 Keyed 目录
                    # 构建标准的英文Keyed目录路径：ModDir/Languages/English/Keyed
                    auto_en_keyed_dir = os.path.join(mod_dir, "Languages", "English", CONFIG.keyed_dir)

                    if os.path.exists(auto_en_keyed_dir):                         # 如果检测到英文Keyed目录存在
                        # 自动使用检测到的英文Keyed目录，确保翻译完整性
                        en_keyed_dir = auto_en_keyed_dir                          # 直接使用自动检测的目录
                        print(f"{Fore.GREEN}✅ 已自动检测并使用英文 Keyed 目录: {auto_en_keyed_dir}{Style.RESET_ALL}")
                    else:                                                         # 未检测到英文Keyed目录
                        # 步骤2b：询问用户是否手动指定英文Keyed目录
                        # 某些模组可能将英文文本放在非标准位置
                        print(f"{Fore.YELLOW}未检测到英文 Keyed 目录{Style.RESET_ALL}")
                        keyed_choice = input(f"{Fore.CYAN}是否手动指定英文Keyed目录？[y/n/b] (b=返回主菜单):{Style.RESET_ALL} ").lower().strip()

                        if keyed_choice == 'b':
                            continue  # 返回主菜单
                        elif keyed_choice == 'y':
                            # 让用户手动选择英文Keyed目录路径
                            en_keyed_dir = path_manager.get_path(
                                path_type="en_keyed_dir",                         # 路径类型：英文Keyed目录
                                prompt="请输入英文 Keyed 目录路径: ",             # 提示用户输入路径
                                validator_type="dir",                             # 验证是有效目录
                                default=path_manager.get_remembered_path("en_keyed_dir")  # 使用记住的路径
                            )
                            if not en_keyed_dir:                                 # 用户取消输入
                                continue                                         # 返回主菜单

                    # 步骤3：执行提取和生成操作
                    try:
                        # 调用核心功能：提取翻译文本、生成模板文件、导出CSV
                        # auto_choose_definjected=False 启用DefInjected智能选择交互
                        facade.extract_templates_and_generate_csv(output_dir, en_keyed_dir, auto_choose_definjected=False)
                        print(f"\n{Fore.GREEN}✅ 提取模板操作完成！{Style.RESET_ALL}")
                    except KeyboardInterrupt:
                        print(f"\n{Fore.YELLOW}⚠️ 用户取消操作，返回主菜单{Style.RESET_ALL}")
                        continue  # 返回主菜单
                    except (TranslationError, ConfigError, OSError, IOError) as e:
                        print(f"\n{Fore.RED}❌ 提取模板失败: {str(e)}{Style.RESET_ALL}")
                        logging.error("提取模板失败: %s", str(e), exc_info=True)

                elif mode == "2":
                    # 模式2：机器翻译
                    csv_path = path_manager.get_path(
                        path_type="import_csv",
                        prompt="请输入要翻译的 CSV 路径（例如：input.csv）: ",
                        validator_type="csv",
                        default=path_manager.get_remembered_path("import_csv")
                    )
                    if not csv_path:
                        continue

                    output_csv = None
                    if input(f"{Fore.YELLOW}指定输出文件？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                        output_csv = path_manager.get_path(
                            path_type="output_csv",
                            prompt="请输入输出 CSV 路径（例如：translated.csv）: ",
                            validator_type="csv",
                            default=path_manager.get_remembered_path("output_csv")
                        )
                        if not output_csv:
                            continue

                    facade.machine_translate(csv_path, output_csv)

                elif mode == "3":
                    # 模式3：将翻译后的 CSV 导入翻译模板
                    csv_path = path_manager.get_path(
                        path_type="import_csv",
                        prompt="请输入翻译后的 CSV 路径（例如：translated.csv）: ",
                        validator_type="csv",
                        default=path_manager.get_remembered_path("import_csv")
                    )
                    if not csv_path:
                        continue

                    if input(f"{Fore.YELLOW}确认导入翻译到模板？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                        facade.import_translations_to_templates(csv_path)

                elif mode == "4":
                    # 模式4：生成语料
                    facade.generate_corpus()

                elif mode == "5":
                    # 模式5：完整流程
                    export_csv = path_manager.get_path(
                        path_type="export_csv",
                        prompt="请输入导出 CSV 路径（例如：output.csv）: ",
                        validator_type="csv",
                        default=path_manager.get_remembered_path("export_csv")
                    )
                    if not export_csv:
                        continue

                    en_keyed_dir = None
                    if input(f"{Fore.YELLOW}是否指定英文 Keyed 目录？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                        en_keyed_dir = path_manager.get_path(
                            path_type="en_keyed_dir",
                            prompt="请输入英文 Keyed 目录（例如：C:\\Mods\\Keyed）: ",
                            validator_type="dir",
                            default=path_manager.get_remembered_path("en_keyed_dir")
                        )
                        if not en_keyed_dir:
                            continue

                    translations = facade.extract_templates_and_generate_csv(export_csv, en_keyed_dir, auto_choose_definjected=True)

                    if translations and input(f"{Fore.YELLOW}确认翻译并导入？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                        output_csv = None
                        if input(f"{Fore.YELLOW}指定输出文件？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                            output_csv = path_manager.get_path(
                                path_type="output_csv",
                                prompt="请输入翻译后 CSV 路径（例如：translated.csv）: ",
                                validator_type="csv",
                                default=path_manager.get_remembered_path("output_csv")
                            )
                            if not output_csv:
                                continue

                        facade.machine_translate(export_csv, output_csv)
                        final_csv = output_csv or export_csv.replace('.csv', '_translated.csv')
                        facade.import_translations_to_templates(final_csv)

                elif mode == "6":
                    # 模式6：批量处理
                    mod_list = []
                    while True:
                        mod_dir = path_manager.get_path(
                            path_type="batch_mod_dir",
                            prompt="请输入模组目录（输入空行结束）: ",
                            validator_type="mod",
                            required=False,
                            default=path_manager.get_remembered_path("batch_mod_dir")
                        )
                        if not mod_dir:
                            break
                        mod_list.append(mod_dir)

                    if not mod_list:
                        print(f"{Fore.YELLOW}未指定任何模组目录{Style.RESET_ALL}")
                        continue

                    csv_path = None
                    if input(f"{Fore.YELLOW}是否指定翻译 CSV？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                        csv_path = path_manager.get_path(
                            path_type="batch_csv",
                            prompt="请输入翻译 CSV 路径（例如：batch.csv）: ",
                            validator_type="csv",
                            default=path_manager.get_remembered_path("batch_csv")
                        )
                        if not csv_path:
                            continue

                    processor = BatchProcessor()
                    results = processor.process_multiple_mods(mod_list, csv_path)

                    if results:
                        print(f"\n{Fore.GREEN}=== 批量处理完成 ==={Style.RESET_ALL}")
                        for mod_dir, result in results.items():
                            status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if result.success else f"{Fore.RED}✗{Style.RESET_ALL}"
                            print(f"{status} {Path(mod_dir).name}: {result.error or '成功'}")

            except TranslationError as e:
                print(f"{Fore.RED}❌ {str(e)}{Style.RESET_ALL}")
                logging.error("操作失败: %s", str(e))
            except (OSError, IOError, ValueError, TypeError) as e:
                print(f"{Fore.RED}❌ 系统错误: {str(e)}{Style.RESET_ALL}")
                logging.exception("系统错误")
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"{Fore.RED}❌ 发生错误: {str(e)}{Style.RESET_ALL}")
                logging.exception("未预期的错误")

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}程序被用户中断{Style.RESET_ALL}")
        logging.info("程序被用户中断")
    except (TranslationError, ConfigError) as e:
        print(f"{Fore.RED}❌ 程序配置或翻译错误: {str(e)}{Style.RESET_ALL}")
        logging.exception("程序配置或翻译错误")
    except (OSError, IOError, PermissionError) as e:
        print(f"{Fore.RED}❌ 程序文件系统错误: {str(e)}{Style.RESET_ALL}")
        logging.exception("程序文件系统错误")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"{Fore.RED}❌ 程序发生严重错误: {str(e)}{Style.RESET_ALL}")
        logging.exception("程序发生严重错误")
    finally:
        logging.info("程序结束")

if __name__ == "__main__":
    main()
