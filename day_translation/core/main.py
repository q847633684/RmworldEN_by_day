import logging
from pathlib import Path
from typing import List, Tuple, Optional
from ..utils.config import TranslationConfig
from ..utils.utils import get_history_list, update_history_list
from ..utils.config_generator import generate_default_config
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
            format=CONFIG.log_format,
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
        translations.extend(scan_defs_sync(self.mod_dir))
        if translations:
            self._save_to_csv(translations, export_csv)
        logging.info(f"提取到 {len(translations)} 条翻译")
        return translations

    def generate_templates(self, en_keyed_dir: str, export_dir: str = None) -> None:
        """生成翻译模板"""
        generator = TemplateGenerator(self.mod_dir, self.language, self.template_location)
        generator.generate_keyed_template(en_keyed_dir, export_dir)
        translations = self.extract_translations()
        generator.generate_keyed_template_from_data([(k, t, g, f) for k, t, g, f in translations if '/' not in k], export_dir)
        generator.generate_definjected_template([(k, t, g, f) for k, t, g, f in translations if '/' in k], export_dir)

    def generate_config_template(self, config_file: str) -> None:
        """生成配置文件模板"""
        generate_default_config(config_file)

    def import_translations(self, csv_path: str, merge: bool = True) -> None:
        """导入翻译"""
        import_translations(csv_path, self.mod_dir, self.language, merge)

    def machine_translate(self, csv_path: str, output_csv: str = None) -> None:
        """机器翻译"""
        translate_csv(csv_path, output_csv)

    def generate_corpus(self) -> List[Tuple[str, str]]:
        """生成平行语料"""
        return generate_parallel_corpus(self.mod_dir, CONFIG.source_language, self.language)

    def _save_to_csv(self, translations: List[Tuple[str, str, str, str]], csv_path: str) -> None:
        """保存翻译到 CSV"""
        import csv
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag", "file"])
            writer.writerows(translations)
        logging.info(f"保存 CSV 文件: {csv_path}")

def get_user_input_with_history(prompt: str, history_key: str, required: bool = True) -> Optional[str]:
    """获取用户输入并保存历史记录"""
    history = get_history_list(history_key)
    if history:
        logging.info(f"历史记录: {', '.join(history[:3])}")
    while True:
        user_input = input(prompt).strip()
        if user_input:
            update_history_list(history_key, user_input)
            return user_input
        if not required:
            return None
        if history:
            choice = input(f"使用历史记录? (1-{len(history)}, 回车取消): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(history):
                return history[int(choice) - 1]

def main_workflow_example():
    """主工作流示例"""
    mod_dir = get_user_input_with_history("模组目录路径: ", "mod_dir_history")
    facade = TranslationFacade(mod_dir)
    logging.info("\n模式: 1-提取 2-机翻 3-导入 4-语料 5-完整流程 6-批量")
    mode = input("选择: ").strip()
    if mode == "1":
        export_csv = get_user_input_with_history("导出 CSV 路径: ", "csv_export_history")
        facade.extract_translations(export_csv)
    elif mode == "2":
        csv_path = get_user_input_with_history("输入 CSV 路径: ", "csv_input_history")
        output_csv = get_user_input_with_history("输出 CSV 路径（可选）: ", "csv_output_history", False)
        facade.machine_translate(csv_path, output_csv)
    elif mode == "3":
        csv_path = get_user_input_with_history("输入 CSV 路径: ", "csv_input_history")
        facade.import_translations(csv_path)
    elif mode == "4":
        corpus = facade.generate_corpus()
        logging.info(f"生成语料: {len(corpus)} 条")
    elif mode == "5":
        export_csv = get_user_input_with_history("导出 CSV 路径: ", "csv_export_history")
        translations = facade.extract_translations(export_csv)
        en_keyed_dir = get_user_input_with_history("英文 Keyed 目录: ", "en_keyed_history")
        facade.generate_templates(en_keyed_dir)
        output_csv = get_user_input_with_history("翻译后 CSV 路径（可选）: ", "csv_output_history", False)
        if output_csv:
            facade.machine_translate(export_csv, output_csv)
            facade.import_translations(output_csv or export_csv)
    elif mode == "6":
        mod_dirs = input("输入模组目录（用逗号分隔）：").split(",")
        csv_file = get_user_input_with_history("CSV 文件路径（可选）：", "csv_file_history", False)
        processor = BatchProcessor()
        processor.process_multiple_mods([d.strip() for d in mod_dirs], csv_file)
        logging.info("批量处理完成")
    logging.info("✅ 工作流完成")

if __name__ == "__main__":
    main_workflow_example()