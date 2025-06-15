import os
import logging
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple
from ..utils.config import TranslationConfig
from ..utils.utils import get_language_folder_path

CONFIG = TranslationConfig()

def generate_parallel_corpus(mode: str, mod_dir: str) -> int:
    """
    生成中英平行语料集。

    Args:
        mode: 模式（1=从 XML 注释提取，2=从 DefInjected 和 Keyed 提取）
        mod_dir: 模组根目录

    Returns:
        生成的语料条数
    """
    logging.info(f"生成平行语料集: mode={mode}, mod_dir={mod_dir}")
    output_path = "parallel_corpus.csv"
    mod_dir = str(Path(mod_dir).resolve())  # 解析绝对路径
    translations: List[Tuple[str, str]] = []
    if mode == "1":
        lang_path = get_language_folder_path(CONFIG.default_language, mod_dir)
        def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
        keyed_path = os.path.join(lang_path, CONFIG.keyed_dir)
        for xml_file in list(Path(def_injected_path).rglob("*.xml")) + list(Path(keyed_path).rglob("*.xml")):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                for elem in root.findall(".//*"):
                    prev = None
                    for child in list(elem):
                        if child.tag == ET.Comment and child.text and child.text.strip().startswith("EN: "):
                            prev = child
                        elif prev is not None and child.text and child.text.strip():
                            en_text = prev.text.strip()[4:]  # Remove "EN: "
                            zh_text = child.text.strip()
                            translations.append((en_text, zh_text))
                            prev = None
            except ET.ParseError as e:
                logging.error(f"XML 解析失败: {xml_file}: {e}")
            except OSError as e:
                logging.error(f"无法读取 {xml_file}: {e}")
    elif mode == "2":
        en_path = get_language_folder_path(CONFIG.source_language, mod_dir)
        zh_path = get_language_folder_path(CONFIG.default_language, mod_dir)
        for dir_name in [CONFIG.def_injected_dir, CONFIG.keyed_dir]:
            en_dir = os.path.join(en_path, dir_name)
            zh_dir = os.path.join(zh_path, dir_name)
            if not os.path.exists(en_dir) or not os.path.exists(zh_dir):
                continue
            for xml_file in Path(zh_dir).rglob("*.xml"):
                rel_path = os.path.relpath(xml_file, zh_dir)
                en_file = os.path.join(en_dir, rel_path)
                if not os.path.exists(en_file):
                    continue
                try:
                    zh_tree = ET.parse(xml_file)
                    en_tree = ET.parse(en_file)
                    zh_root = zh_tree.getroot()
                    en_root = en_tree.getroot()
                    for zh_elem, en_elem in zip(zh_root.findall(".//*"), en_root.findall(".//*")):
                        if zh_elem.tag == en_elem.tag and zh_elem.text and en_elem.text:
                            translations.append((en_elem.text.strip(), zh_elem.text.strip()))
                except ET.ParseError as e:
                    logging.error(f"XML 解析失败: {xml_file}: {e}")
                except OSError as e:
                    logging.error(f"无法读取 {xml_file}: {e}")
    try:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["English", "Chinese"])
            writer.writerows(translations)
        logging.info(f"生成语料集: {output_path}, 共 {len(translations)} 条")
        return len(translations)
    except csv.Error as e:
        logging.error(f"CSV 写入失败: {output_path}, 错误: {e}")
        return 0
    except OSError as e:
        logging.error(f"无法写入 CSV: {output_path}, 错误: {e}")
        return 0

def check_parallel_tsv() -> int:
    """
    检查平行语料集格式。

    Returns:
        错误条数
    """
    tsv_path = "parallel_corpus.csv"
    errors = 0
    if not os.path.exists(tsv_path):
        logging.error(f"语料集文件不存在: {tsv_path}")
        return 1
    try:
        with open(tsv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("English") or not row.get("Chinese"):
                    logging.error(f"无效语料: {row}")
                    errors += 1
        logging.info(f"语料集检查完成，发现 {errors} 个问题")
        return errors
    except csv.Error as e:
        logging.error(f"CSV 解析失败: {tsv_path}, 错误: {e}")
        return 1
    except OSError as e:
        logging.error(f"无法读取 CSV: {tsv_path}, 错误: {e}")
        return 1