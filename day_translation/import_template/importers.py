"""
导入功能模块 - 实现翻译结果导入到模板的功能
"""

import logging
import os
import csv
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from colorama import Fore, Style

from day_translation.utils.config import (
    get_config,
    get_language_subdir,
    get_language_dir,
)
from day_translation.utils.utils import XMLProcessor, get_language_folder_path

CONFIG = get_config()


def update_all_xml(
    mod_dir: str,
    translations: Dict[str, str],
    language: str = CONFIG.default_language,
    merge: bool = True,
) -> None:
    """
    更新所有 XML 文件中的翻译

    Args:
        mod_dir (str): 模组目录
        translations (Dict[str, str]): 翻译字典
        language (str): 目标语言
        merge (bool): 是否合并更新
    """
    try:
        # 尝试使用 lxml
        processor = XMLProcessor(XMLProcessorConfig(use_lxml=True))
    except ImportError:
        # 回退到 ElementTree
        processor = XMLProcessor(XMLProcessorConfig(use_lxml=False))

    language_dir = get_language_folder_path(mod_dir, language)
    updated_count = 0

    for xml_file in Path(language_dir).rglob("*.xml"):
        try:
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                continue

            if processor.update_translations(tree, translations, merge=merge):
                processor.save_xml(tree, str(xml_file))
                updated_count += 1
                print(f"{Fore.GREEN}更新文件: {xml_file}{Style.RESET_ALL}")
        except Exception as e:
            logging.error("处理文件失败: %s: %s", xml_file, e)

    print(f"{Fore.GREEN}更新了 {updated_count} 个文件{Style.RESET_ALL}")


def import_translations(
    csv_path: str,
    mod_dir: str,
    merge: bool = True,
    auto_create_templates: bool = True,
    language: str = None,
) -> bool:
    """
    将翻译CSV导入到翻译模板

    Args:
        csv_path (str): 翻译CSV文件路径
        mod_dir (str): 模组目录
        merge (bool): 是否合并现有翻译
        auto_create_templates (bool): 是否自动创建模板
        language (str): 目标语言（可选）

    Returns:
        bool: 导入是否成功
    """
    if language is None:
        language = CONFIG.default_language
    logging.info("开始导入翻译到模板: %s", csv_path)
    try:
        # 步骤1：确保翻译模板存在
        if auto_create_templates:
            generator = TemplateGenerator(mod_dir, language)
            if not get_language_dir(mod_dir, language).exists():
                translations = generator.extract_and_generate_templates()
                if not translations:
                    logging.error("无法创建翻译模板")
                    print(f"{Fore.RED}❌ 无法创建翻译模板{Style.RESET_ALL}")
                    return False
        # 步骤2：验证CSV文件
        if not _validate_csv_file(csv_path):
            return False
        # 步骤3：加载翻译数据
        translations = _load_translations_from_csv(csv_path)
        if not translations:
            return False
        # 步骤4：更新XML文件
        updated_count = _update_all_xml_files(mod_dir, translations, language, merge)
        # 步骤5：验证导入结果
        success = _verify_import_results(mod_dir, language)
        if success:
            logging.info("翻译导入到模板完成，更新了 %s 个文件", updated_count)
            print(f"{Fore.GREEN}✅ 翻译已成功导入到模板{Style.RESET_ALL}")
        else:
            logging.warning("翻译导入可能存在问题")
            print(f"{Fore.YELLOW}⚠️ 翻译导入完成，但可能存在问题{Style.RESET_ALL}")
        return success
    except Exception as e:
        logging.error("导入翻译时发生错误: %s", e, exc_info=True)
        print(f"{Fore.RED}❌ 导入失败: {e}{Style.RESET_ALL}")
        return False


def _validate_csv_file(csv_path: str) -> bool:
    """验证CSV文件"""
    if not Path(csv_path).is_file():
        logging.error("CSV文件不存在: %s", csv_path)
        return False

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header or not all(col in header for col in ["key", "text"]):
                logging.error("CSV文件格式无效：缺少必要的列")
                return False
            return True
    except Exception as e:
        logging.error("验证CSV文件时发生错误: %s", e)
        return False


def _load_translations_from_csv(csv_path: str) -> Dict[str, str]:
    """从CSV文件加载翻译数据"""
    translations = {}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("key") and row.get("text"):
                    translations[row["key"]] = row["text"]
        return translations
    except Exception as e:
        logging.error("加载CSV文件时发生错误: %s", e)
        print(f"{Fore.RED}❌ 加载CSV文件失败: {e}{Style.RESET_ALL}")
        return {}


def _update_all_xml_files(
    mod_dir: str, translations: Dict[str, str], language: str, merge: bool = True
) -> int:
    """更新所有XML文件中的翻译"""
    language_dir = get_language_folder_path(mod_dir, language)
    processor = XMLProcessor()
    updated_count = 0
    for xml_file in Path(language_dir).rglob("*.xml"):
        try:
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                continue
            if processor.update_translations(tree, translations, merge=merge):
                processor.save_xml(tree, str(xml_file))
                updated_count += 1
                print(f"{Fore.GREEN}更新文件: {xml_file}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}处理文件失败: {xml_file}: {e}{Style.RESET_ALL}")
    return updated_count


def _verify_import_results(mod_dir: str, language: str) -> bool:
    """验证导入结果"""
    template_dir = get_language_dir(mod_dir, language)
    if not template_dir.exists():
        logging.error("导入后模板目录不存在")
        return False
    # 检查是否有翻译文件
    has_keyed = (
        any(
            (get_language_subdir(mod_dir, language, subdir_type="keyed").rglob("*.xml"))
        )
        if get_language_subdir(mod_dir, language, subdir_type="keyed").exists()
        else False
    )
    has_definjected = (
        any(
            (
                get_language_subdir(mod_dir, language, subdir_type="defInjected").rglob(
                    "*.xml"
                )
            )
        )
        if get_language_subdir(mod_dir, language, subdir_type="defInjected").exists()
        else False
    )
    if not has_keyed and not has_definjected:
        logging.warning("导入后未找到翻译文件")
        return False
    logging.info("导入结果验证通过")
    return True
