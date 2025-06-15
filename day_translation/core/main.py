import logging
import os
import sys
import csv
from typing import List, Tuple, Optional
from pathlib import Path
from . import extractors, importers, parallel_corpus, machine_translate
from ..utils.config import TranslationConfig
from .exporters import export_keyed_to_csv, cleanup_backstories_dir
from ..utils.utils import update_history_list

CONFIG = TranslationConfig()

def setup_logging() -> None:
    """初始化日志配置"""
    logging.basicConfig(
        filename=CONFIG.log_file,
        level=logging.DEBUG if CONFIG.debug_mode else logging.INFO,
        format=CONFIG.log_format,
        encoding="utf-8",
        errors="replace"
    )
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(CONFIG.log_format))
    logging.getLogger().addHandler(console)

class TranslationFacade:
    """翻译操作的门面类，封装高层次逻辑"""
    def __init__(self, mod_dir: str, export_dir: str, language: str = CONFIG.default_language):
        self.mod_dir = str(Path(mod_dir).resolve())
        self.export_dir = str(Path(export_dir).resolve())
        self.language = language
        self.source_language = CONFIG.source_language
        self.csv_path = str(Path(self.export_dir) / CONFIG.output_csv)

    def extract_all(self) -> List[Tuple[str, str, str, str]]:
        """提取所有翻译数据，避免重复扫描"""
        logging.info(f"提取翻译: mod_dir={self.mod_dir}, export_dir={self.export_dir}")
        extractors.extract_translate(
            mod_dir=self.mod_dir,
            export_dir=self.export_dir,
            language=self.language,
            source_language=self.source_language
        )
        extractors.extract_key(
            mod_dir=self.mod_dir,
            export_dir=self.export_dir,
            language=self.language,
            source_language=self.source_language
        )
        cleanup_backstories_dir(
            mod_dir=self.mod_dir,
            export_dir=self.export_dir,
            language=self.language
        )
        translations = extractors.preview_translatable_fields(
            mod_dir=self.mod_dir,
            preview=CONFIG.preview_translatable_fields
        )
        keyed_dir = str(Path(self.export_dir) / "Languages" / self.language / CONFIG.keyed_dir)
        export_keyed_to_csv(keyed_dir, self.csv_path)
        return translations

    def import_translations(self, csv_file: str, merge: bool) -> None:
        """导入翻译"""
        logging.info(f"导入翻译: csv_file={csv_file}, merge={merge}")
        importers.import_translations(
            csv_path=csv_file,
            mod_dir=self.mod_dir,
            language=self.language,
            merge=merge
        )

    def generate_corpus(self, mode: str) -> int:
        """生成平行语料集"""
        return parallel_corpus.generate_parallel_corpus(mode, self.mod_dir)

def run_mode_1(facade: TranslationFacade) -> None:
    """运行模式 1：提取翻译到 CSV"""
    try:
        output_dir = Path(facade.export_dir)
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        if not os.access(facade.export_dir, os.W_OK):
            raise PermissionError(f"导出目录 {facade.export_dir} 无写入权限")
        translations = facade.extract_all()
        rows = [(full_path, text, tag) for full_path, text, tag, _ in translations]
        with open(facade.csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag"])
            writer.writerows(rows)
        logging.info(f"DefInjected 共导出 {len(rows)} 条到 {facade.csv_path}")
        update_history_list("extracted_csv_history", facade.csv_path)
        print(f"提取完成！导出到 {facade.csv_path}")
    except (PermissionError, csv.Error, OSError) as e:
        logging.error(f"模式 1 错误: {e}")
        print(f"错误: {e}，请检查 {CONFIG.log_file}")

def run_mode_3(facade: TranslationFacade) -> None:
    """运行模式 3：导入翻译"""
    try:
        csv_file = input("请输入翻译后的 CSV 文件路径：").strip()
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV 文件 {csv_file} 不存在")
        merge = input("是否合并已有翻译？(y/n，回车默认 n)：").strip().lower() == "y"
        facade.import_translations(csv_file, merge)
        update_history_list("translated_csv_history", csv_file)
        print("导入完成！")
    except (FileNotFoundError, csv.Error, OSError) as e:
        logging.error(f"模式 3 错误: {e}")
        print(f"错误: {e}，请检查 {CONFIG.log_file}")

def main() -> None:
    """主程序入口"""
    setup_logging()
    logging.info("程序启动")
    while True:
        print("\n=== 翻译工具菜单 ===")
        print("1. 从 Defs 和 Keyed 提取翻译到 CSV")
        print("2. 机器翻译 CSV（需阿里云 API）")
        print("3. 从翻译后的 CSV 导入到 DefInjected 和 Keyed")
        print("4. 生成中英平行语料集")
        print("5. 检查平行语料集格式")
        print("0. 退出")
        choice = input("请选择操作（0-5）：").strip()
        if choice == "0":
            logging.info("程序退出")
            break
        if choice not in {"1", "2", "3", "4", "5"}:
            print("无效选项，请重试")
            continue
        mod_dir = input("请输入模组根目录路径：").strip()
        if not os.path.exists(mod_dir):
            print(f"模组目录 {mod_dir} 不存在")
            continue
        export_dir = input("请输入导出目录路径（建议绝对路径，如 C:\\Users\\q8476\\Documents\\output）：").strip()
        facade = TranslationFacade(mod_dir, export_dir)
        try:
            if choice == "1":
                run_mode_1(facade)
            elif choice == "2":
                access_key_id = input("请输入阿里云 AccessKey ID：").strip()
                access_secret = input("请输入阿里云 AccessKey Secret：").strip()
                machine_translate.translate_csv(
                    input_path=facade.csv_path,
                    output_path=str(Path(facade.export_dir) / "translated_zh.csv"),
                    access_key_id=access_key_id,
                    access_secret=access_secret
                )
                print("机器翻译完成！")
            elif choice == "3":
                run_mode_3(facade)
            elif choice == "4":
                mode = input("请选择语料集生成模式（1=从 XML 提取注释，2=从 DefInjected 和 Keyed 提取，1/2）：").strip()
                if mode not in {"1", "2"}:
                    print("无效模式")
                    continue
                count = facade.generate_corpus(mode)
                print(f"生成语料集完成，共 {count} 条")
            elif choice == "5":
                errors = parallel_corpus.check_parallel_tsv()
                print(f"检查完成，发现 {errors} 个问题")
        except KeyboardInterrupt:
            print("\n操作被用户中断")
            logging.info("用户中断操作")
        except Exception as e:
            logging.error(f"未处理错误: {e}")
            print(f"发生错误: {e}，请检查 {CONFIG.log_file}")
        input("按回车返回主菜单...")

if __name__ == "__main__":
    main()