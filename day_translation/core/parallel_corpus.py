import logging
import os
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple
from ..utils.config import TranslationConfig
from ..utils.utils import get_language_folder_path, sanitize_xcomment

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
    mod_dir = str(Path(mod_dir).resolve())
    output_path = str(Path(mod_dir).parent / "parallel_corpus.csv")
    lang_path = get_language_folder_path(CONFIG.default_language, mod_dir)
    src_lang_path = get_language_folder_path(CONFIG.source_language, mod_dir)
    
    corpus: List[Tuple[str, str]] = []
    if mode == "1":
        def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
        keyed_path = os.path.join(lang_path, CONFIG.keyed_dir)
        for xml_path in [def_injected_path, keyed_path]:
            if not os.path.exists(xml_path):
                continue
            for xml_file in Path(xml_path).rglob("*.xml"):
                try:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    for comment in root.iterfind(".//comment()"):
                        comment_text = comment.text.strip()
                        if comment_text.startswith("EN:"):
                            en_text = sanitize_xcomment(comment_text[3:].strip())
                            next_elem = comment.getnext()
                            if next_elem is not None and next_elem.text:
                                zh_text = next_elem.text.strip()
                                corpus.append((en_text, zh_text))
                except ET.ParseError as e:
                    logging.error(f"XML 解析失败: {xml_file}: {e}")
                except OSError as e:
                    logging.error(f"无法读取 {xml_file}: {e}")
    elif mode == "2":
        def_injected_path = os.path.join(src_lang_path, CONFIG.def_injected_dir)
        keyed_path = os.path.join(src_lang_path, CONFIG.keyed_dir)
        zh_def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
        zh_keyed_path = os.path.join(lang_path, CONFIG.keyed_dir)
        for src_path, zh_path in [(def_injected_path, zh_def_injected_path), (keyed_path, zh_keyed_path)]:
            if not os.path.exists(src_path) or not os.path.exists(zh_path):
                continue
            for src_file in Path(src_path).rglob("*.xml"):
                rel_path = os.path.relpath(src_file, src_path)
                zh_file = os.path.join(zh_path, rel_path)
                if not os.path.exists(zh_file):
                    continue
                try:
                    src_tree = ET.parse(src_file)
                    zh_tree = ET.parse(zh_file)
                    src_root = src_tree.getroot()
                    zh_root = zh_tree.getroot()
                    for src_elem, zh_elem in zip(src_root.iter(), zh_root.iter()):
                        if src_elem.tag == zh_elem.tag and src_elem.text and zh_elem.text:
                            en_text = src_elem.text.strip()
                            zh_text = zh_elem.text.strip()
                            if en_text and zh_text:
                                corpus.append((en_text, zh_text))
                except ET.ParseError as e:
                    logging.error(f"XML 解析失败: {src_file} 或 {zh_file}: {e}")
                except OSError as e:
                    logging.error(f"无法读取 {src_file} 或 {zh_file}: {e}")
    
    if not corpus:
        logging.warning("未提取到平行语料")
        return 0
    
    try:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["English", "Chinese"])
            writer.writerows(corpus)
        logging.info(f"生成平行语料集: {output_path}，共 {len(corpus)} 条")
        return len(corpus)
    except (csv.Error, OSError) as e:
        logging.error(f"写入语料集失败: {output_path}: {e}")
        return 0

def check_parallel_tsv() -> int:
    """
    检查平行语料集格式。

    Returns:
        错误条数
    """
    logging.info("检查平行语料集格式")
    corpus_path = "parallel_corpus.csv"
    errors = 0
    if not os.path.exists(corpus_path):
        logging.error(f"语料集文件 {corpus_path} 不存在")
        return 1
    try:
        with open(corpus_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "English" not in reader.fieldnames or "Chinese" not in reader.fieldnames:
                logging.error(f"语料集缺少必要列: {corpus_path}")
                return 1
            for row in reader:
                en_text = row.get("English", "").strip()
                zh_text = row.get("Chinese", "").strip()
                if not en_text or not zh_text:
                    logging.error(f"无效行: {row}")
                    errors += 1
    except (csv.Error, OSError) as e:
        logging.error(f"检查语料集失败: {corpus_path}: {e}")
        errors += 1
    logging.info(f"检查完成，发现 {errors} 个问题")
    return errors