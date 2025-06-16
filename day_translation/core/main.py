import logging
import os
import json
from pathlib import Path
from typing import List, Tuple, Optional
from tqdm import tqdm
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

CONFIG = TranslationConfig()

class TranslationFacade:
    def __init__(self, mod_dir: str, language: str = CONFIG.default_language, template_location: str = "mod"):
        self.mod_dir = str(Path(mod_dir).resolve())
        self.language = language
        self.template_location = template_location
        self.setup_logging()

    def setup_logging(self) -> None:
        """设置日志"""
        logging.basicConfig(
            level=logging.DEBUG if CONFIG.debug_mode else logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(CONFIG.log_file, encoding="utf-8"),
                logging.StreamHandler()
            ]
        )

    def extract_translations(self, export_csv: str = CONFIG.output_csv) -> List[Tuple[str, str, str, str]]:
        """提取翻译"""
        logging.info(f"提取翻译到: {export_csv}")
        translations = []
        translations.extend(extract_keyed_translations(self.mod_dir, CONFIG.source_language))
        translations.extend(tqdm(scan_defs_sync(self.mod_dir), desc="提取 Defs"))
        if translations:
            self._save_to_csv(translations, export_csv)
        logging.info(f"提取到 {len(translations)} 条翻译")
        print(f"✅ 提取完成：{len(translations)} 条")
        return translations

    def generate_templates(self, en_keyed_dir: str, export_dir: str = None) -> None:
        """生成翻译模板"""
        generator = TemplateGenerator(self.mod_dir, self.language, self.template_location)
        generator.generate_keyed_template(en_keyed_dir, export_dir)
        translations = self.extract_translations()
        generator.generate_keyed_template_from_data([(k, t, g, f) for k, t, g, f in translations if '/' not in k], export_dir)
        generator.generate_definjected_template([(k, t, g, f) for k, t, g, f in translations if '/' in k], export_dir)
        print("✅ 模板生成完成")

    def generate_config_template(self, config_file: str) -> None:
        """生成配置文件模板"""
        generate_default_config(config_file)
        print(f"✅ 配置模板保存到: {config_file}")

    def import_translations(self, csv_path: str, merge: bool = True) -> None:
        """导入翻译"""
        import_translations(csv_path, self.mod_dir, self.language, merge)
        print("✅ 翻译导入完成")

    def machine_translate(self, csv_path: str, output_csv: str = None) -> None:
        """机器翻译，使用阿里云翻译 API"""
        user_config = load_user_config()
        access_key_id = user_config.get('ALIYUN_ACCESS_KEY_ID') or os.getenv('ALIYUN_ACCESS_KEY_ID') or input("请输入 ALIYUN_ACCESS_KEY_ID: ")
        access_secret = user_config.get('ALIYUN_ACCESS_SECRET') or os.getenv('ALIYUN_ACCESS_SECRET') or input("请输入 ALIYUN_ACCESS_SECRET: ")
        if input("保存 API 密钥到配置文件？[y/n]: ").lower() == 'y':
            user_config['ALIYUN_ACCESS_KEY_ID'] = access_key_id
            user_config['ALIYUN_ACCESS_SECRET'] = access_secret
            save_user_config(user_config)
        translate_csv(csv_path, output_csv, access_key_id=access_key_id, access_secret=access_secret)
        print(f"✅ 翻译完成，保存到: {output_csv or csv_path.replace('.csv', '_translated.csv')}")

    def generate_corpus(self) -> List[Tuple[str, str]]:
        """生成平行语料"""
        corpus = generate_parallel_corpus(self.mod_dir, CONFIG.source_language, self.language)
        logging.info(f"生成语料: {len(corpus)} 条")
        print(f"✅ 生成语料：{len(corpus)} 条")
        return corpus

    def _save_to_csv(self, translations: List[Tuple[str, str, str, str]], csv_path: str) -> None:
        """保存翻译到 CSV"""
        import csv
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag", "file"])
            writer.writerows(translations)
        logging.info(f"保存 CSV 文件: {csv_path}")

def get_user_input_with_history(prompt: str, history_key: str, required: bool = True, validate_func: Optional[callable] = None) -> Optional[str]:
    """获取用户输入，支持历史记录和验证"""
    history = get_history_list(history_key)
    if history:
        print(f"历史记录: {', '.join(history[:3])}")
    while True:
        user_input = input(prompt).strip()
        if user_input.lower() == 'q':
            raise SystemExit("用户退出")
        if user_input:
            if validate_func and not validate_func(user_input):
                print("输入无效，请重试")
                continue
            update_history_list(history_key, user_input)
            return user_input
        if not required:
            return None
        if history:
            choice = input(f"使用历史记录? (1-{len(history)}, 回车取消): ").strip()
            if choice.lower() == 'q':
                raise SystemExit("用户退出")
            if choice.isdigit() and 1 <= int(choice) <= len(history):
                return history[int(choice) - 1]

def validate_dir(path: str) -> bool:
    """验证目录是否存在"""
    return os.path.isdir(path)

def validate_file(path: str) -> bool:
    """验证文件是否存在"""
    return os.path.isfile(path)

def main():
    """主工作流"""
    print("\n=== Day Translation 主菜单 ===")
    while True:
        print("\n可用模式：")
        print("1. 提取：从模组提取文本到 CSV 文件")
        print("2. 机翻：使用阿里云翻译 CSV 文件")
        print("3. 导入：将翻译后的 CSV 导入模组 XML")
        print("4. 语料：生成英-中平行语料")
        print("5. 完整流程：提取、生成模板、翻译、导入")
        print("6. 批量：处理多个模组")
        print("q. 退出程序")
        mode = input("\n选择模式 (1-6, q): ").strip().lower()
        if mode == 'q':
            print("退出程序")
            break
        if mode not in ['1', '2', '3', '4', '5', '6']:
            print("无效选择，请输入 1-6 或 q")
            continue

        user_config = load_user_config()
        default_mod_dir = user_config.get('mod_dir_history', [None])[0]
        mod_dir_prompt = f"请输入模组目录（如 C:\\Mods\\MyMod）{f' [默认: {default_mod_dir}]' if default_mod_dir else ''}: "
        mod_dir = get_user_input_with_history(mod_dir_prompt, "mod_dir_history", validate_func=validate_dir)
        user_config['mod_dir_history'] = get_history_list("mod_dir_history")
        save_user_config(user_config)
        facade = TranslationFacade(mod_dir)

        if mode == "1":
            export_csv = get_user_input_with_history("请输入导出 CSV 路径（如 output.csv）：", "csv_export_history")
            facade.extract_translations(export_csv)
        elif mode == "2":
            csv_path = get_user_input_with_history("请输入 CSV 路径（如 input.csv）：", "csv_input_history", validate_func=validate_file)
            output_csv = get_user_input_with_history("请输入输出 CSV 路径（可选）：", "csv_output_history", False)
            facade.machine_translate(csv_path, output_csv)
        elif mode == "3":
            csv_path = get_user_input_with_history("请输入 CSV 路径（如 translated.csv）：", "csv_input_history", validate_func=validate_file)
            if input("确认导入翻译？[y/n]: ").lower() == 'y':
                facade.import_translations(csv_path)
        elif mode == "4":
            facade.generate_corpus()
        elif mode == "5":
            export_csv = get_user_input_with_history("请输入导出 CSV 路径（如 output.csv）：", "csv_export_history")
            translations = facade.extract_translations(export_csv)
            en_keyed_dir = get_user_input_with_history("请输入英文 Keyed 目录（如 C:\\Mods\\Keyed）：", "en_keyed_history", validate_func=validate_dir)
            facade.generate_templates(en_keyed_dir)
            output_csv = get_user_input_with_history("请输入翻译后 CSV 路径（可选）：", "csv_output_history", False)
            if output_csv and input("确认翻译并导入？[y/n]: ").lower() == 'y':
                facade.machine_translate(export_csv, output_csv)
                facade.import_translations(output_csv or export_csv)
        elif mode == "6":
            mod_dirs = input("请输入模组目录（用逗号分隔，如 dir1,dir2）：").split(",")
            for i, d in enumerate(mod_dirs):
                mod_dirs[i] = d.strip()
                if not validate_dir(mod_dirs[i]):
                    print(f"错误：{mod_dirs[i]} 不是有效目录")
                    break
            else:
                csv_file = get_user_input_with_history("请输入 CSV 路径（可选）：", "csv_file_history", False, validate_file if csv_file else None)
                if csv_file and not validate_file(csv_file):
                    print(f"错误：{csv_file} 不是有效文件")
                    continue
                processor = BatchProcessor()
                processor.process_multiple_mods(mod_dirs, csv_file)
                print("✅ 批量处理完成")
        input("\n按回车键返回主菜单...")

if __name__ == "__main__":
    main()