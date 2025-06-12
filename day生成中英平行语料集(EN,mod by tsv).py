def extract_pairs_from_definjected(english_dir, chinese_dir):
    """提取 DefInjected 或 Keyed 下所有同名文件、同名字段的中英文对"""
    import xml.etree.ElementTree as ET
    pairs = []
    en_dict = {}
    zh_dict = {}
    # 收集所有英文 key→text
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
                # print(f"[DEBUG] 英文文件: {en_path} 标签数: {len(en_root)}")
            except Exception as e:
                print(f"[ERROR] 解析英文失败: {en_path}，错误: {e}")
    # 收集所有中文 key→text
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
                # print(f"[DEBUG] 中文文件: {zh_path} 标签数: {len(zh_root)}")
            except Exception as e:
                print(f"[ERROR] 解析中文失败: {zh_path}，错误: {e}")
    # 全局比对 key
    print(f"[DEBUG] 英文key数: {len(en_dict)} 中文key数: {len(zh_dict)}")
    for key in en_dict:
        if key in zh_dict:
            en_text = en_dict[key]
            zh_text = zh_dict[key]
            if en_text and zh_text and en_text != zh_text:
                pairs.append([en_text, zh_text])
                print(f"[DEBUG] 匹配: key={key} EN={en_text} ZH={zh_text}")
    print(f"[DEBUG] 共提取中英对: {len(pairs)}")
    return pairs

import os
import re
import csv
import xml.etree.ElementTree as ET

def find_xml_files(root):
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith('.xml'):
                yield os.path.join(dirpath, filename)

def extract_pairs_from_file(filepath):
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
                pairs.append([en, zh])
            en = None
        else:
            en = None
    return pairs

def main():

    print("请选择提取方式：")
    print("1. 提取带 EN: 注释的中文翻译文件")
    print("2. 提取 Keyed/DefInjected 目录下的中英文对")
    mode = input("输入 1 或 2 并回车：").strip()

    output_csv = 'parallel_corpus.csv'
    output_tsv = 'parallel_corpus.tsv'
    all_pairs = []
    seen = set()

    # 统一目录输入提示，允许留空，留空则用当前目录
    if mode == '1':
        dir_tip = "请输入要递归查找的目录（可留空，留空则从当前目录开始）："
    elif mode == '2':
        dir_tip = "请输入mod根目录（可留空，留空则从当前目录开始）："
    else:
        print("无效选择，已退出。")
        return

    user_dir = input(dir_tip).strip()
    if not user_dir:
        user_dir = '.'

    if mode == '1':
        # EN: 注释方式，目录可留空
        for xml_file in find_xml_files(user_dir):
            pairs = extract_pairs_from_file(xml_file)
            for en, zh in pairs:
                key = (en, zh)
                if key not in seen:
                    all_pairs.append([en, zh])
                    seen.add(key)
    elif mode == '2':
        # Keyed/DefInjected 方式，mod根目录可留空
        mod_root = user_dir
        en_keyed = os.path.join(mod_root, 'Languages', 'English', 'Keyed')
        zh_keyed = os.path.join(mod_root, 'Languages', 'ChineseSimplified', 'Keyed')
        keyed_count = 0
        def_count = 0
        if os.path.exists(en_keyed) and os.path.exists(zh_keyed):
            keyed_pairs = extract_pairs_from_definjected(en_keyed, zh_keyed)
            for en, zh in keyed_pairs:
                key = (en, zh)
                if key not in seen:
                    all_pairs.append([en, zh])
                    seen.add(key)
            keyed_count = len(keyed_pairs)
        en_def = os.path.join(mod_root, 'Languages', 'English', 'DefInjected')
        zh_def = os.path.join(mod_root, 'Languages', 'ChineseSimplified', 'DefInjected')
        if os.path.exists(en_def) and os.path.exists(zh_def):
            def_pairs = extract_pairs_from_definjected(en_def, zh_def)
            for en, zh in def_pairs:
                key = (en, zh)
                if key not in seen:
                    all_pairs.append([en, zh])
                    seen.add(key)
            def_count = len(def_pairs)
        print(f"[统计] Keyed 提取了 {keyed_count} 条，DefInjected 提取了 {def_count} 条。")

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
    print(f'已生成 {output_csv} 和 {output_tsv}，共{len(all_pairs)} 条中英对。')

if __name__ == '__main__':
    main()