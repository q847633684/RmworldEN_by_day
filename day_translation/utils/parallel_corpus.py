"""
平行语料集生成模块 - 实现中英平行语料集的提取和生成
"""

import logging
import os
import csv
import re
from pathlib import Path
from typing import List, Tuple
from .config import get_config
from .utils import XMLProcessor, get_language_folder_path, sanitize_xcomment
from colorama import Fore, Style

CONFIG = get_config()

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
    print(f"{Fore.BLUE}正在生成平行语料集: mode={mode}, mod_dir={mod_dir}...{Style.RESET_ALL}")
    mod_dir = str(Path(mod_dir).resolve())
    
    output_csv = str(Path(mod_dir).parent / "parallel_corpus.csv")
    output_tsv = str(Path(mod_dir).parent / "parallel_corpus.tsv")
    
    lang_path = get_language_folder_path(CONFIG.default_language, mod_dir)
    src_lang_path = get_language_folder_path(CONFIG.source_language, mod_dir)
    
    corpus: List[Tuple[str, str]] = []
    seen = set()
    
    processor = XMLProcessor()
    
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
                    src_tree = processor.parse_xml(str(src_file))
                    zh_tree = processor.parse_xml(str(zh_file))
                    if src_tree is None or zh_tree is None:
                        continue
                        
                    src_root = src_tree.getroot() if processor.use_lxml else src_tree
                    zh_root = zh_tree.getroot() if processor.use_lxml else zh_tree
                    
                    for src_elem, zh_elem in zip(src_root.iter(), zh_root.iter()):
                        if src_elem.tag == zh_elem.tag and src_elem.text and zh_elem.text:
                            en_text = src_elem.text.strip()
                            zh_text = zh_elem.text.strip()
                            if en_text and zh_text:
                                corpus.append((en_text, zh_text))
                except Exception as e:
                    logging.error(f"处理文件失败: {src_file} 或 {zh_file}: {e}")
    
    if not corpus:
        print(f"{Fore.YELLOW}未提取到平行语料{Style.RESET_ALL}")
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
            
        print(f"{Fore.GREEN}生成平行语料集: {output_csv} 和 {output_tsv}，共 {len(corpus)} 条{Style.RESET_ALL}")
        return len(corpus)
    except (csv.Error, OSError) as e:
        print(f"{Fore.RED}写入语料集失败: {e}{Style.RESET_ALL}")
        return 0

def check_parallel_tsv(file_path: str = "parallel_corpus.tsv") -> int:
    """检查平行语料集格式"""
    if not os.path.exists(file_path):
        print(f"{Fore.RED}文件不存在: {file_path}{Style.RESET_ALL}")
        return 1
    
    errors = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            line = line.rstrip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) != 2:
                print(f"{Fore.YELLOW}第 {i} 行格式错误: 应为2列，实际{len(parts)}列{Style.RESET_ALL}")
                errors += 1
            elif not parts[0].strip() or not parts[1].strip():
                print(f"{Fore.YELLOW}第 {i} 行有空内容{Style.RESET_ALL}")
                errors += 1
        
        if errors == 0:
            print(f"{Fore.GREEN}格式检查通过{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}检查失败: {e}{Style.RESET_ALL}")
        errors += 1
    
    return errors