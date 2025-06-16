import logging
import os
import json
from pathlib import Path
from typing import List, Tuple, Optional
from tqdm import tqdm
from colorama import init, Fore, Style
from ..utils.config import TranslationConfig
from ..utils.utils import get_history_list, update_history_list
from ..utils.config_generator import generate_default_config
from ..utils.user_config import load_user_config, save_user_config
from ..core.extractors import extract_keyed_translations, scan_defs_sync
from ..core.exporters import export_definjected, export_keyed
from ..core.generators import TemplateGenerator
from ..core.importers import import_translations
from ..core.machine_translate import translate_csv
from ..core.parallel_corpus import generate_parallel_corpus
from ..utils.batch_processor import BatchProcessor

# 初始化 colorama 以支持 Windows 终端颜色
init()

CONFIG = TranslationConfig()

class TranslationFacade:
    """翻译操作的核心接口，管理模组翻译流程"""
    def __init__(self, mod_dir: str, language: str = CONFIG.default_language, template_location: str = "mod"):
        """
        初始化 TranslationFacade

        Args:
            mod_dir (str): 模组目录路径
            language (str): 目标语言，默认为 CONFIG.default_language
            template_location (str): 模板位置，默认为 'mod'
        """
        self.mod_dir = str(Path(mod_dir).resolve())
        self.language = language
        self.template_location = template_location
        self.setup_logging()

    def setup_logging(self) -> None:
        """配置日志记录，输出到文件和控制台"""
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(CONFIG.log_file, encoding="utf-8"),
                logging.StreamHandler()
            ]
        )
        logging.debug(f"初始化 TranslationFacade: mod_dir={self.mod_dir}, language={self.language}")

    def extract_translations(self, export_csv: str = CONFIG.output_csv) -> List[Tuple[str, str, str, str]]:
        """
        从模组提取翻译到 CSV 文件

        Args:
            export_csv (str): 导出 CSV 文件路径，默认为 CONFIG.output_csv

        Returns:
            List[Tuple[str, str, str, str]]: 提取的翻译数据（key, text, tag, file）
        """
        logging.info(f"提取翻译到: {export_csv}")
        translations = []
        translations.extend(extract_keyed_translations(self.mod_dir, CONFIG.source_language))
        logging.debug(f"提取到 {len(translations)} 条 Keyed 翻译")
        translations.extend(tqdm(scan_defs_sync(self.mod_dir), desc="提取 Defs"))
        logging.debug(f"总计提取到 {len(translations)} 条翻译")
        if translations:
            self._save_to_csv(translations, export_csv)
        print(f"{Fore.GREEN}✅ 提取完成：{len(translations)} 条{Style.RESET_ALL}")
        return translations

    def generate_templates(self, en_keyed_dir: str, export_dir: str = None) -> None:
        """
        生成翻译模板（Keyed 和 DefInjected）

        Args:
            en_keyed_dir (str): 英文 Keyed 目录路径
            export_dir (str, optional): 导出目录，默认为 None
        """
        logging.info(f"生成模板: en_keyed_dir={en_keyed_dir}, export_dir={export_dir}")
        generator = TemplateGenerator(self.mod_dir, self.language, self.template_location)
        generator.generate_keyed_template(en_keyed_dir, export_dir)
        translations = self.extract_translations()
        generator.generate_keyed_template_from_data([(k, t, g, f) for k, t, g, f in translations if '/' not in k], export_dir)
        generator.generate_definjected_template([(k, t, g, f) for k, t, g, f in translations if '/' in k], export_dir)
        print(f"{Fore.GREEN}✅ 模板生成完成{Style.RESET_ALL}")

    def generate_config_template(self, config_file: str) -> None:
        """
        生成配置文件模板

        Args:
            config_file (str): 配置文件路径
        """
        logging.info(f"生成配置模板: {config_file}")
        generate_default_config(config_file)
        print(f"{Fore.GREEN}✅ 配置模板保存到: {config_file}{Style.RESET_ALL}")

    def import_translations(self, csv_path: str, merge: bool = True) -> None:
        """
        导入翻译到模组 XML 文件

        Args:
            csv_path (str): 翻译 CSV 文件路径
            merge (bool): 是否合并现有翻译，默认为 True
        """
        logging.info(f"导入翻译: csv_path={csv_path}, merge={merge}")
        import_translations(csv_path, self.mod_dir, self.language, merge)
        print(f"{Fore.GREEN}✅ 翻译导入完成{Style.RESET_ALL}")

    def machine_translate(self, csv_path: str, output_csv: str = None) -> None:
        """
        使用阿里云 API 翻译 CSV 文件

        Args:
            csv_path (str): 输入 CSV 文件路径
            output_csv (str, optional): 输出 CSV 文件路径，默认为 None
        """
        logging.info(f"开始机器翻译: csv_path={csv_path}, output_csv={output_csv}")
        user_config = load_user_config()
        access_key_id = user_config.get('ALIYUN_ACCESS_KEY_ID') or os.getenv('ALIYUN_ACCESS_KEY_ID') or input(f"{Fore.CYAN}请输入 ALIYUN_ACCESS_KEY_ID:{Style.RESET_ALL} ")
        access_secret = user_config.get('ALIYUN_ACCESS_SECRET') or os.getenv('ALIYUN_ACCESS_SECRET') or input(f"{Fore.CYAN}请输入 ALIYUN_ACCESS_SECRET:{Style.RESET_ALL} ")
        if input(f"{Fore.YELLOW}保存 API 密钥到配置文件？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
            user_config['ALIYUN_ACCESS_KEY_ID'] = access_key_id
            user_config['ALIYUN_ACCESS_SECRET'] = access_secret
            save_user_config(user_config)
            logging.debug("已保存 API 密钥到用户配置文件")
        translate_csv(csv_path, output_csv, access_key_id=access_key_id, access_secret=access_secret)
        output_path = output_csv or csv_path.replace('.csv', '_translated.csv')
        print(f"{Fore.GREEN}✅ 翻译完成，保存到: {output_path}{Style.RESET_ALL}")

    def generate_corpus(self) -> List[Tuple[str, str]]:
        """
        生成英-中平行语料

        Returns:
            List[Tuple[str, str]]: 平行语料（英文, 中文）
        """
        logging.info("生成平行语料")
        corpus = generate_parallel_corpus(self.mod_dir, CONFIG.source_language, self.language)
        logging.debug(f"生成语料: {len(corpus)} 条")
        print(f"{Fore.GREEN}✅ 生成语料：{len(corpus)} 条{Style.RESET_ALL}")
        return corpus

    def _save_to_csv(self, translations: List[Tuple[str, str, str, str]], csv_path: str) -> None:
        """
        保存翻译到 CSV 文件

        Args:
            translations: 翻译数据（key, text, tag, file）
            csv_path: CSV 文件路径

        Raises:
            PermissionError: 如果无法写入文件
        """
        logging.debug(f"保存 CSV: path={csv_path}, 翻译条数={len(translations)}")
        try:
            Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                import csv
                writer = csv.writer(f)
                writer.writerow(["key", "text", "tag", "file"])
                writer.writerows(translations)
            logging.info(f"保存 CSV 文件: {csv_path}")
        except PermissionError as e:
            logging.error(f"无法保存 CSV: {e}")
            raise

def get_user_input_with_history(prompt: str, history_key: str, required: bool = True, validate_func: Optional[callable] = None) -> Optional[str]:
    """
    获取用户输入，支持历史记录和验证

    Args:
        prompt (str): 输入提示
        history_key (str): 历史记录键
        required (bool): 是否必须输入，默认为 True
        validate_func (callable, optional): 验证函数，默认为 None

    Returns:
        Optional[str]: 用户输入或 None（如果非必须）

    Raises:
        SystemExit: 如果用户输入 'q'
    """
    history = get_history_list(history_key)
    if history:
        print(f"{Fore.BLUE}历史记录: {', '.join(history[:3])}{Style.RESET_ALL}")
    while True:
        user_input = input(f"{Fore.CYAN}{prompt}{Style.RESET_ALL}").strip()
        logging.debug(f"用户输入: {user_input}, history_key={history_key}")
        if user_input.lower() == 'q':
            logging.info("用户退出程序")
            raise SystemExit(f"{Fore.RED}用户退出{Style.RESET_ALL}")
        if user_input:
            if validate_func and not validate_func(user_input):
                print(f"{Fore.RED}输入无效，请重试{Style.RESET_ALL}")
                logging.debug(f"输入验证失败: {user_input}")
                continue
            update_history_list(history_key, user_input)
            logging.debug(f"更新历史记录: {history_key}={user_input}")
            return user_input
        if not required:
            return None
        if history:
            choice = input(f"{Fore.YELLOW}使用历史记录? (1-{len(history)}, 回车取消):{Style.RESET_ALL} ").strip()
            if choice.lower() == 'q':
                logging.info("用户退出程序")
                raise SystemExit(f"{Fore.RED}用户退出{Style.RESET_ALL}")
            if choice.isdigit() and 1 <= int(choice) <= len(history):
                logging.debug(f"选择历史记录: {history[int(choice) - 1]}")
                return history[int(choice) - 1]

def validate_dir(path: str) -> bool:
    """验证目录是否存在"""
    is_valid = os.path.isdir(path)
    logging.debug(f"验证目录: {path}, 结果={is_valid}")
    return is_valid

def validate_file(path: str) -> bool:
    """验证文件是否存在或可写入"""
    try:
        parent_dir = os.path.dirname(path) or '.'
        is_valid = os.path.isfile(path) or os.access(parent_dir, os.W_OK)
        logging.debug(f"验证文件: {path}, 结果={is_valid}")
        return is_valid
    except Exception as e:
        logging.debug(f"验证文件失败: {path}, 错误={e}")
        return False

def main():
    """主工作流，管理用户交互和翻译流程"""
    logging.info("启动主工作流")
    print(f"\n{Fore.MAGENTA}=== Day Translation 主菜单 ==={Style.RESET_ALL}")
    while True:
        print(f"\n{Fore.BLUE}可用模式：{Style.RESET_ALL}")
        print(f"1. {Fore.GREEN}提取{Style.RESET_ALL}：从模组提取文本到 CSV 文件")
        print(f"2. {Fore.GREEN}机翻{Style.RESET_ALL}：使用阿里云翻译 CSV 文件")
        print(f"3. {Fore.GREEN}导入{Style.RESET_ALL}：将翻译后的 CSV 导入模组 XML")
        print(f"4. {Fore.GREEN}语料{Style.RESET_ALL}：生成英-中平行语料")
        print(f"5. {Fore.GREEN}完整流程{Style.RESET_ALL}：提取、生成模板、翻译、导入")
        print(f"6. {Fore.GREEN}批量{Style.RESET_ALL}：处理多个模组")
        print(f"q. {Fore.RED}退出程序{Style.RESET_ALL}")
        mode = input(f"\n{Fore.CYAN}选择模式 (1-6, q):{Style.RESET_ALL} ").strip().lower()
        logging.debug(f"用户选择模式: {mode}")
        if mode == 'q':
            print(f"{Fore.RED}退出程序{Style.RESET_ALL}")
            logging.info("程序退出")
            break
        if mode not in ['1', '2', '3', '4', '5', '6']:
            print(f"{Fore.RED}无效选择，请输入 1-6 或 q{Style.RESET_ALL}")
            continue

        user_config = load_user_config()
        default_mod_dir = user_config.get('mod_dir_history', [None])[0]
        mod_dir_prompt = f"请输入模组目录（如 C:\\Mods\\MyMod）{f' [默认: {default_mod_dir}]' if default_mod_dir else ''}: "
        mod_dir = get_user_input_with_history(mod_dir_prompt, "mod_dir_history", validate_func=validate_dir)
        user_config['mod_dir_history'] = get_history_list("mod_dir_history")
        save_user_config(user_config)
        logging.debug(f"模组目录: {mod_dir}")
        facade = TranslationFacade(mod_dir)

        try:
            if mode == "1":
                export_csv = get_user_input_with_history("请输入导出 CSV 路径（如 output.csv）：", "csv_export_history", validate_func=validate_file)
                facade.extract_translations(export_csv)
            elif mode == "2":
                csv_path = get_user_input_with_history("请输入 CSV 路径（如 input.csv）：", "csv_input_history", validate_func=validate_file)
                output_csv = get_user_input_with_history("请输入输出 CSV 路径（可选，如 translated.csv）：", "csv_output_history", False)
                facade.machine_translate(csv_path, output_csv)
            elif mode == "3":
                csv_path = get_user_input_with_history("请输入 CSV 路径（如 translated.csv）：", "csv_input_history", validate_func=validate_file)
                if input(f"{Fore.YELLOW}确认导入翻译？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                    facade.import_translations(csv_path)
            elif mode == "4":
                facade.generate_corpus()
            elif mode == "5":
                export_csv = get_user_input_with_history("请输入导出 CSV 路径（如 output.csv）：", "csv_export_history", validate_func=validate_file)
                translations = facade.extract_translations(export_csv)
                en_keyed_dir = get_user_input_with_history("请输入英文 Keyed 目录（如 C:\\Mods\\Keyed）：", "en_keyed_history", validate_func=validate_dir)
                facade.generate_templates(en_keyed_dir)
                output_csv = get_user_input_with_history("请输入翻译后 CSV 路径（可选，如 translated.csv）：", "csv_output_history", False)
                if output_csv and input(f"{Fore.YELLOW}确认翻译并导入？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
                    facade.machine_translate(export_csv, output_csv)
                    facade.import_translations(output_csv or export_csv)
            elif mode == "6":
                mod_dirs = input(f"{Fore.CYAN}请输入模组目录（用逗号分隔，如 dir1,dir2）：{Style.RESET_ALL}").split(",")
                for i, d in enumerate(mod_dirs):
                    mod_dirs[i] = d.strip()
                    if not validate_dir(mod_dirs[i]):
                        print(f"{Fore.RED}错误：{mod_dirs[i]} 不是有效目录{Style.RESET_ALL}")
                        logging.error(f"无效模组目录: {mod_dirs[i]}")
                        break
                else:
                    csv_file = get_user_input_with_history("请输入 CSV 路径（可选，如 translated.csv）：", "csv_file_history", False, validate_file if csv_file else None)
                    if csv_file and not validate_file(csv_file):
                        print(f"{Fore.RED}错误：{csv_file} 不是有效文件{Style.RESET_ALL}")
                        logging.error(f"无效 CSV 文件: {csv_file}")
                        continue
                    processor = BatchProcessor()
                    processor.process_multiple_mods(mod_dirs, csv_file)
                    print(f"{Fore.GREEN}✅ 批量处理完成{Style.RESET_ALL}")
        except Exception as e:
            logging.error(f"模式 {mode} 执行错误: {e}", exc_info=True)
            print(f"{Fore.RED}❌ 错误: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}按回车键返回主菜单...{Style.RESET_ALL}")

if __name__ == "__main__":
    main()