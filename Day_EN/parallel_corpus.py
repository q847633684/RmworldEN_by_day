"""
parallel_corpus.py
------------------
中英平行语料集的生成与检查工具。

包含：
    - extract_pairs_from_definjected: 提取 DefInjected/Keyed 下的中英文对
    - extract_pairs_from_file: 提取带 EN: 注释的中英文对
    - generate_parallel_corpus: 生成 parallel_corpus.csv/tsv
    - check_parallel_tsv: 检查 parallel_corpus.tsv 格式
"""
import os
import re
import csv
import xml.etree.ElementTree as ET
from typing import List, Tuple

def extract_pairs_from_definjected(english_dir: str, chinese_dir: str) -> List[Tuple[str, str]]:
    """
    提取 DefInjected 或 Keyed 下所有同名文件、同名字段的中英文对。

    Args:
        english_dir (str): 英文 xml 目录（Keyed 或 DefInjected）
        chinese_dir (str): 中文 xml 目录（Keyed 或 DefInjected）
    Returns:
        List[Tuple[str, str]]: (英文文本, 中文文本) 对列表
    """
    pairs = []
    en_dict = {}
    zh_dict = {}
    for root, _, files in os.walk(english_dir):
        for file in files:
            if not file.endswith('.xml'):
                continue
            en_path = os.path.join(root, file)
            try:
                en_tree = ET.parse(en_path)
                en_root = en_tree.getroot()
                for elem in en_root:
                    if elem.text and elem.tag:
                        key = elem.tag
                        text = elem.text.strip()
                        if text:
                            en_dict[key] = text
            except Exception as e:
                print(f"[ERROR] 解析英文失败: {en_path}，错误: {e}")
    for root, _, files in os.walk(chinese_dir):
        for file in files:
            if not file.endswith('.xml'):
                continue
            zh_path = os.path.join(root, file)
            try:
                zh_tree = ET.parse(zh_path)
                zh_root = zh_tree.getroot()
                for elem in zh_root:
                    if elem.text and elem.tag:
                        key = elem.tag
                        text = elem.text.strip()
                        if text:
                            zh_dict[key] = text
            except Exception as e:
                print(f"[ERROR] 解析中文失败: {zh_path}，错误: {e}")
    for key in en_dict:
        if key in zh_dict:
            en_text = en_dict[key]
            zh_text = zh_dict[key]
            if en_text and zh_text and en_text != zh_text:
                pairs.append((en_text, zh_text))
    return pairs

def find_xml_files(root: str):
    """
    递归查找目录下所有 xml 文件。
    """
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith('.xml'):
                yield os.path.join(dirpath, filename)

def extract_pairs_from_file(filepath: str) -> List[Tuple[str, str]]:
    """
    提取单个 xml 文件中带 EN: 注释的中英文对。
    Args:
        filepath (str): xml 文件路径
    Returns:
        List[Tuple[str, str]]: (英文文本, 中文文本) 对列表
    """
    pairs = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
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

def generate_parallel_corpus(mode: str, user_dir: str, output_csv: str = 'parallel_corpus.csv', output_tsv: str = 'parallel_corpus.tsv') -> int:
    """
    生成中英平行语料集，写入 parallel_corpus.csv/tsv。

    Args:
        mode (str): '1' 为 EN 注释，'2' 为 Keyed/DefInjected
        user_dir (str): 根目录
        output_csv (str): 输出 csv 路径
        output_tsv (str): 输出 tsv 路径
    Returns:
        int: 对数
    """
    # 统一输出文件名
    output_csv = "extracted_translations.csv"
    output_tsv = "extracted_translations.tsv"
    all_pairs = []
    seen = set()
    if mode == '1':
        for xml_file in find_xml_files(user_dir):
            pairs = extract_pairs_from_file(xml_file)
            for en, zh in pairs:
                key = (en, zh)
                if key not in seen:
                    all_pairs.append((en, zh))
                    seen.add(key)
    elif mode == '2':
        mod_root = user_dir
        en_keyed = os.path.join(mod_root, 'Languages', 'English', 'Keyed')
        zh_keyed = os.path.join(mod_root, 'Languages', 'ChineseSimplified', 'Keyed')
        if os.path.exists(en_keyed) and os.path.exists(zh_keyed):
            keyed_pairs = extract_pairs_from_definjected(en_keyed, zh_keyed)
            for en, zh in keyed_pairs:
                key = (en, zh)
                if key not in seen:
                    all_pairs.append((en, zh))
                    seen.add(key)
        en_def = os.path.join(mod_root, 'Languages', 'English', 'DefInjected')
        zh_def = os.path.join(mod_root, 'Languages', 'ChineseSimplified', 'DefInjected')
        if os.path.exists(en_def) and os.path.exists(zh_def):
            def_pairs = extract_pairs_from_definjected(en_def, zh_def)
            for en, zh in def_pairs:
                key = (en, zh)
                if key not in seen:
                    all_pairs.append((en, zh))
                    seen.add(key)
    # 写入csv
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for en, zh in all_pairs:
            writer.writerow([en, zh])
    # 写入tsv
    with open(output_tsv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        for en, zh in all_pairs:
            writer.writerow([en, zh])
    return len(all_pairs)

def check_parallel_tsv(file_path: str = 'parallel_corpus.tsv') -> int:
    """
    检查 parallel_corpus.tsv 格式，输出问题，返回错误数。

    Args:
        file_path (str): tsv 文件路径
    Returns:
        int: 错误数
    """
    errors = []
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()
    for idx, line in enumerate(lines, 1):
        line = line.rstrip('\n\r')
        if not line.strip():
            errors.append(f"第{idx}行是空行")
            continue
        cols = line.split('\t')
        if len(cols) != 2:
            errors.append(f"第{idx}行列数不是2列: {line}")
        if any(c.strip() == '' for c in cols):
            errors.append(f"第{idx}行有空单元格: {line}")
        for c in cols:
            if '\u3000' in c or '\u200b' in c:
                errors.append(f"第{idx}行含有异常字符: {line}")
    if errors:
        print("发现以下问题：")
        for e in errors:
            print(e)
    else:
        print("检查通过，未发现格式问题。")
    return len(errors)
