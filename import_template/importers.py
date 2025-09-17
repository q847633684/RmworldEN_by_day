"""
导入功能模块 - 实现翻译结果导入到模板的功能
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Tuple
from colorama import Fore, Style

from utils.config import (
    get_config,
    get_language_subdir,
    get_language_dir,
)
from utils.utils import XMLProcessor, get_language_folder_path

CONFIG = get_config()


def update_all_xml(
    mod_dir: str,
    translations: Dict[str, str],
    language: str = CONFIG.CN_language,
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
    processor = XMLProcessor()

    language_dir = get_language_folder_path(language, mod_dir)
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
    language: str = CONFIG.CN_language,
) -> bool:
    """
    将翻译CSV导入到翻译模板

    Args:
        csv_path (str): 翻译CSV文件路径
        mod_dir (str): 模组目录
        merge (bool): 是否合并现有翻译
        auto_create_templates (bool): 是否自动创建模板
        language (str): 目标语言

    Returns:
        bool: 导入是否成功
    """
    logging.info("开始导入翻译到模板: %s", csv_path)
    try:
        # 步骤1：确保翻译模板存在
        if auto_create_templates:
            # 检查模板目录是否存在，如果不存在则提示用户先创建模板
            if not get_language_dir(mod_dir, language).exists():
                logging.error("翻译模板目录不存在，请先使用提取功能创建翻译模板")
                print(
                    f"{Fore.RED}❌ 翻译模板目录不存在，请先使用提取功能创建翻译模板{Style.RESET_ALL}"
                )
                return False
        # 步骤2：验证CSV文件
        if not _validate_csv_file(csv_path):
            return False
        # 步骤3：加载翻译数据
        translations = _load_translations_from_csv(csv_path)
        if not translations:
            return False
        # 步骤3.1：按 Keyed/DefInjected 分流
        keyed_translations, definjected_translations = _split_translations(translations)

        # 步骤4：分别更新 Keyed 与 DefInjected 目录下的 XML 文件
        updated_count = 0
        updated_count += _update_xml_in_subdir(
            mod_dir, language, "keyed", keyed_translations, merge
        )
        updated_count += _update_xml_in_subdir(
            mod_dir, language, "definjected", definjected_translations, merge
        )
        # 步骤5：验证导入结果
        success = _verify_import_results(mod_dir, language)
        if success:
            logging.info("翻译导入到模板完成，更新了 %s 个文件", updated_count)
            print(f"{Fore.GREEN}✅ 翻译已成功导入到模板{Style.RESET_ALL}")
        else:
            logging.warning("翻译导入可能存在问题")
            print(f"{Fore.YELLOW}⚠️ 翻译导入完成，但可能存在问题{Style.RESET_ALL}")
        return success
    except FileNotFoundError as e:
        logging.error("文件未找到: %s", e)
        print(f"{Fore.RED}❌ 文件未找到: {e}{Style.RESET_ALL}")
        return False
    except PermissionError as e:
        logging.error("权限错误: %s", e)
        print(f"{Fore.RED}❌ 权限错误: {e}{Style.RESET_ALL}")
        return False
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
    except FileNotFoundError:
        logging.error("CSV文件不存在: %s", csv_path)
        return False
    except PermissionError:
        logging.error("无权限访问CSV文件: %s", csv_path)
        return False
    except UnicodeDecodeError:
        logging.error("CSV文件编码错误: %s", csv_path)
        return False
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
                key = (row.get("key") or "").strip()
                # 优先使用 translated 列，其次回退到 text 列
                value = (row.get("translated") or row.get("text") or "").strip()
                if key and value:
                    translations[key] = value
        return translations
    except FileNotFoundError:
        logging.error("CSV文件不存在: %s", csv_path)
        print(f"{Fore.RED}❌ CSV文件不存在: {csv_path}{Style.RESET_ALL}")
        return {}
    except PermissionError:
        logging.error("无权限访问CSV文件: %s", csv_path)
        print(f"{Fore.RED}❌ 无权限访问CSV文件: {csv_path}{Style.RESET_ALL}")
        return {}
    except Exception as e:
        logging.error("加载CSV文件时发生错误: %s", e)
        print(f"{Fore.RED}❌ 加载CSV文件失败: {e}{Style.RESET_ALL}")
        return {}


def _update_xml_in_subdir(
    mod_dir: str,
    language: str,
    subdir_type: str,
    translations: Dict[str, str],
    merge: bool = True,
) -> int:
    """仅在指定子目录(Keyed/DefInjected)内更新翻译"""
    if not translations:
        return 0
    subdir = get_language_subdir(mod_dir, language, subdir_type=subdir_type)
    if not subdir.exists():
        logging.warning("语言子目录不存在: %s", subdir)
        return 0
    processor = XMLProcessor()
    updated_count = 0

    # 规格化 DefInjected 键：移除前缀（如 "HediffDef/"），保留标签键（如 "Name.field"）
    if subdir_type.lower() == "definjected":
        normalized: Dict[str, str] = {}
        for key, value in translations.items():
            if "/" in key:
                normalized[key.split("/", 1)[1]] = value
            else:
                normalized[key] = value
        translations = normalized

    for xml_file in Path(subdir).rglob("*.xml"):
        try:
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                continue
            if processor.update_translations(tree, translations, merge=merge):
                processor.save_xml(tree, str(xml_file))
                updated_count += 1
                print(f"{Fore.GREEN}更新文件: {xml_file}{Style.RESET_ALL}")
        except FileNotFoundError:
            logging.error("XML文件不存在: %s", xml_file)
        except PermissionError:
            logging.error("无权限访问XML文件: %s", xml_file)
        except Exception as e:
            logging.error("处理XML文件失败: %s: %s", xml_file, e)
            print(f"{Fore.RED}处理文件失败: {xml_file}: {e}{Style.RESET_ALL}")
    return updated_count


def _split_translations(
    translations: Dict[str, str],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """将翻译按 Keyed 与 DefInjected 分组。

    规则：
    - 含有 '/' 的 key 归类为 DefInjected（例如 ThingDef/...）。
    - 否则归类为 Keyed。
    """
    keyed: Dict[str, str] = {}
    definjected: Dict[str, str] = {}
    for k, v in translations.items():
        if "/" in k:
            definjected[k] = v
        else:
            keyed[k] = v
    return keyed, definjected


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
