import logging
import os
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple
from ..utils.config import TranslationConfig
from ..utils.utils import get_language_folder_path, sanitize_xcomment

CONFIG = TranslationConfig()

def extract_pairs_from_file(filepath: str) -> List[Tuple[str, str]]:
    """
    提取单个 xml 文件中带 EN: 注释的中英文对。
    参考 Day_EN 的实现。
    """
    pairs = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (FileNotFoundError, UnicodeDecodeError) as e:
        logging.error(f"文件读取失败: {filepath}，错误: {e}")
        return pairs
    
    en = None
    for line in lines:
        import re
        en_match = re.match(r'\s*<!--\s*EN:\s*(.*?)\s*-->', line)
        zh_match = re.match(r'\s*<[^>]+>(.*?)</[^>]+>', line)
        
        if en_match:
            en = en_match.group(1).strip()
        elif en and zh_match:
            zh = zh_match.group(1).strip()
            if en and zh and en != zh:
                pairs.append((en, zh))
            en = None
        else:
            en = None
    
    return pairs

def generate_parallel_corpus(mode: str, mod_dir: str) -> int:
    """
    生成中英平行语料集，同时支持 CSV 和 TSV 格式。

    Args:
        mode: 模式（1=从 XML 注释提取，2=从 DefInjected 和 Keyed 提取）
        mod_dir: 模组根目录

    Returns:
        生成的语料条数
    """
    logging.info(f"生成平行语料集: mode={mode}, mod_dir={mod_dir}")
    mod_dir = str(Path(mod_dir).resolve())
    
    output_csv = str(Path(mod_dir).parent / "parallel_corpus.csv")
    output_tsv = str(Path(mod_dir).parent / "parallel_corpus.tsv")
    
    lang_path = get_language_folder_path(CONFIG.default_language, mod_dir)
    src_lang_path = get_language_folder_path(CONFIG.source_language, mod_dir)
    
    corpus: List[Tuple[str, str]] = []
    seen = set()
    
    if mode == "1":
        # 从带 EN: 注释的文件提取
        for xml_file in Path(lang_path).rglob("*.xml"):
            pairs = extract_pairs_from_file(str(xml_file))
            for en, zh in pairs:
                key = (en, zh)
                if key not in seen:
                    corpus.append((en, zh))
                    seen.add(key)
    elif mode == "2":
        # 从 DefInjected 和 Keyed 对比提取
        def_injected_path = os.path.join(src_lang_path, CONFIG.def_injected_dir)
        keyed_path = os.path.join(src_lang_path, CONFIG.keyed_dir)
        zh_def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
        zh_keyed_path = os.path.join(lang_path, CONFIG.keyed_dir)
        
        # 检查 DefInjured 兼容性
        if not os.path.exists(def_injected_path):
            def_injected_path = os.path.join(src_lang_path, "DefInjured")
        if not os.path.exists(zh_def_injected_path):
            zh_def_injected_path = os.path.join(lang_path, "DefInjured")
        
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
        # 同时写入 CSV 和 TSV
        with open(output_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["en", "zh"])
            writer.writerows(corpus)
        
        with open(output_tsv, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(["en", "zh"])
            writer.writerows(corpus)
            
        logging.info(f"生成平行语料集: {output_csv} 和 {output_tsv}，共 {len(corpus)} 条")
        return len(corpus)
    except (csv.Error, OSError) as e:
        logging.error(f"写入语料集失败: {e}")
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