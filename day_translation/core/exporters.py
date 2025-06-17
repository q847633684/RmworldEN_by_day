"""
导出功能模块 - 实现翻译模板导出、DefInjected 导出等功能
"""

import logging
import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict
import csv
from multiprocessing import Pool
from tqdm import tqdm
from ..utils.config import get_config
from ..utils.utils import XMLProcessor, save_xml_to_file, sanitize_xcomment, get_language_folder_path, sanitize_xml
from colorama import Fore, Style

CONFIG = get_config()

def move_dir(src: str, dst: str) -> None:
    """移动目录，覆盖已存在目录"""
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(src, dst)
    import time
    time.sleep(1)
    print(f"{Fore.GREEN}重命名 {src} 为 {dst}{Style.RESET_ALL}")

def export_definjected_from_english(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language
) -> None:
    """从英文导出 DefInjected 翻译，添加 EN 注释"""
    logging.info(f"导出 DefInjected: mod_dir={mod_dir}, export_dir={export_dir}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_def_injected_path = os.path.join(src_lang_path, CONFIG.def_injected_dir)
    
    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info(f"创建文件夹：{def_injected_path}")
        
    if not os.path.exists(src_def_injected_path):
        logging.warning(f"英文 DefInjected 目录 {src_def_injected_path} 不存在，跳过")
        return
        
    processor = XMLProcessor()
    
    for src_file in sorted(Path(src_def_injected_path).rglob("*.xml")):
        try:
            rel_path = os.path.relpath(src_file, src_def_injected_path)
            dst_file = os.path.join(def_injected_path, rel_path)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            logging.info(f"复制 {src_file} 到 {dst_file}")
            
            tree = processor.parse_xml(str(dst_file))
            if tree is None:
                continue
                
            # 添加英文注释
            processor.add_comments(tree, comment_prefix="EN")
            processor.save_xml(tree, str(dst_file))
            
        except Exception as e:
            logging.error(f"处理文件失败: {src_file}: {e}")

def handle_extract_translate(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language,
    extract_definjected_from_defs=None
) -> None:
    """处理翻译提取逻辑，选择 DefInjected 或 Defs"""
    logging.info(f"处理翻译提取: mod_dir={mod_dir}, export_dir={export_dir}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
    old_def_linked_path = os.path.join(lang_path, "DefLinked")
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_def_injected_path = os.path.join(src_lang_path, CONFIG.def_injected_dir)
    if os.path.exists(old_def_linked_path) and not os.path.exists(def_injected_path):
        move_dir(old_def_linked_path, def_injected_path)
    if os.path.exists(src_def_injected_path):
        print("检测到英文 DefInjected 目录。请选择处理方式：")
        print("1. 以英文 DefInjected 为基础（推荐用于已有翻译结构的情况）")
        print("2. 直接从 Defs 目录重新提取可翻译字段（推荐用于结构有变动或需全量提取时）")
        choice = input("请输入选项编号（1/2，回车默认1）：").strip()
        if choice == "2":
            logging.info("用户选择：从 Defs 目录重新提取")
            if extract_definjected_from_defs:
                extract_definjected_from_defs(mod_dir, export_dir, language)
            return
        logging.info("用户选择：以英文 DefInjected 为基础")
        export_definjected_from_english(
            mod_dir=mod_dir,
            export_dir=export_dir,
            language=language,
            source_language=source_language
        )
    else:
        logging.info(f"未找到英文 DefInjected {src_def_injected_path}，从 Defs 提取")
        print(f"未找到英文 DefInjected 目录 {src_def_injected_path}，将从 Defs 提取可翻译字段。")
        if extract_definjected_from_defs:
            extract_definjected_from_defs(mod_dir, export_dir, language)

def cleanup_backstories_dir(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language
) -> None:
    """清理背景故事目录"""
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    backstories_path = os.path.join(lang_path, "Backstories")
    if os.path.exists(backstories_path):
        delete_me_path = os.path.join(lang_path, "Backstories DELETE_ME")
        try:
            shutil.move(backstories_path, delete_me_path)
            logging.info(f"重命名背景故事为 {delete_me_path}")
            print(f"背景故事文件夹重命名为 {delete_me_path}，请检查并删除")
        except OSError as e:
            logging.error(f"无法重命名 {backstories_path}: {e}")

def export_keyed(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language
) -> None:
    """导出 Keyed 翻译，添加 EN 注释"""
    logging.info(f"导出 Keyed: mod_dir={mod_dir}, export_dir={export_dir}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    keyed_path = os.path.join(lang_path, CONFIG.keyed_dir)
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_keyed_path = os.path.join(src_lang_path, CONFIG.keyed_dir)
    
    if not os.path.exists(keyed_path):
        os.makedirs(keyed_path)
        logging.info(f"创建文件夹：{keyed_path}")
        
    if not os.path.exists(src_keyed_path):
        logging.warning(f"英文 Keyed 目录 {src_keyed_path} 不存在，跳过")
        return
        
    xml_files = list(Path(src_keyed_path).rglob("*.xml"))
    if not xml_files:
        logging.warning(f"英文 Keyed 目录 {src_keyed_path} 没有 XML 文件，跳过")
        return
        
    processor = XMLProcessor()
    
    for src_file in xml_files:
        try:
            rel_path = os.path.relpath(src_file, src_keyed_path)
            dst_file = os.path.join(keyed_path, rel_path)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            logging.info(f"复制 {src_file} 到 {dst_file}")
            
            tree = processor.parse_xml(str(dst_file))
            if tree is None:
                continue
                
            # 添加英文注释
            processor.add_comments(tree, comment_prefix="EN")
            processor.save_xml(tree, str(dst_file))
            
        except Exception as e:
            logging.error(f"处理文件失败: {src_file}: {e}")

def process_def_file(
    xml_file: Path,
    selected_translations: List[Tuple[str, str, str, str]],
    processor: XMLProcessor
) -> Tuple[str, List[Tuple[str, List[Tuple[str, str, str]]]]]:
    """处理单个 Def XML 文件"""
    try:
        tree = processor.parse_xml(str(xml_file))
        if tree is None:
            return str(xml_file), []
            
        root = tree.getroot() if processor.use_lxml else tree
        output_path = str(xml_file)
        pairs = []
        
        for def_node in root.findall(".//*[defName]"):
            def_type = def_node.tag
            def_name = def_node.find("defName")
            if def_name is None or not def_name.text:
                continue
                
            def_name_text = def_name.text
            prefix = f"{def_type}/{def_name_text}."
            filtered_translations = [
                (full_path[len(prefix):], text, tag)
                for full_path, text, tag, file_path in selected_translations
                if str(file_path) == str(xml_file) and full_path.startswith(prefix)
            ]
            
            if filtered_translations:
                pairs.append((def_name_text, filtered_translations))
                
        return output_path, pairs
        
    except Exception as e:
        logging.error(f"处理文件失败: {xml_file}: {e}")
        return str(xml_file), []

def process_def_file_wrapper(args: Tuple[Path, List[Tuple[str, str, str, str]]]) -> Tuple[str, List[Tuple[str, List[Tuple[str, str, str]]]]]:
    """包装函数，供 multiprocessing 使用"""
    xml_file, selected_translations = args
    processor = XMLProcessor()
    return process_def_file(xml_file, selected_translations, processor)

def export_definjected(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
    language: str = CONFIG.default_language
) -> None:
    """从 Defs 导出 DefInjected 翻译，确保包含所有字段"""
    logging.info(f"导出 DefInjected: mod_dir={mod_dir}, translations_count={len(selected_translations)}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
    defs_path = os.path.join(mod_dir, "Defs")
    
    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info(f"创建文件夹：{def_injected_path}")
        
    # 清理现有文件
    for xml_file in Path(def_injected_path).rglob("*.xml"):
        try:
            os.remove(xml_file)
            logging.info(f"删除文件：{xml_file}")
        except OSError as e:
            logging.error(f"无法删除 {xml_file}: {e}")
            
    if not os.path.exists(defs_path):
        logging.warning(f"Defs 目录 {defs_path} 不存在，跳过")
        return
        
    processor = XMLProcessor()
    
    # 按 DefType 分组翻译内容
    def_groups = {}
    for full_path, text, tag, file_path in selected_translations:
        if '/' in full_path:
            def_type_part, field_part = full_path.split('/', 1)
            def_type = def_type_part
            
            if '.' in field_part:
                def_name, field_path = field_part.split('.', 1)
            else:
                def_name = field_part
                field_path = ""
                
            if def_type not in def_groups:
                def_groups[def_type] = {}
            if def_name not in def_groups[def_type]:
                def_groups[def_type][def_name] = []
                
            def_groups[def_type][def_name].append((field_path, text, tag))
            
    # 为每个 DefType 生成 XML 文件
    for def_type, def_items in def_groups.items():
        if not def_items:
            continue
            
        # 创建对应的目录结构
        type_dir = os.path.join(def_injected_path, f"{def_type}Defs")
        os.makedirs(type_dir, exist_ok=True)
        
        output_file = os.path.join(type_dir, f"{def_type}Defs.xml")
        
        # 生成 XML 内容
        root = ET.Element("LanguageData")
        
        for def_name, fields in def_items.items():
            for field_path, text, tag in fields:
                # 生成完整的键名
                if field_path:
                    full_key = f"{def_name}.{field_path}"
                else:
                    full_key = def_name
                    
                # 添加英文注释
                comment = ET.Comment(sanitize_xcomment(f"EN: {text}"))
                root.append(comment)
                
                # 添加翻译元素
                elem = ET.SubElement(root, full_key)
                elem.text = sanitize_xml(text)
                
        # 保存文件
        tree = ET.ElementTree(root)
        processor.save_xml(tree, output_file)
        logging.info(f"生成 DefInjected 文件: {output_file}")

def export_definjected_to_csv(definjected_dir: str, output_csv: str) -> None:
    """将 DefInjected 翻译导出到 CSV"""
    logging.info(f"导出 DefInjected 到 CSV: {definjected_dir} -> {output_csv}")
    processor = XMLProcessor()
    rows = []
    
    for xml_file in Path(definjected_dir).rglob("*.xml"):
        try:
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                continue
                
            root = tree.getroot() if processor.use_lxml else tree
            file_rows = 0
            
            # 处理 DefInjected 的特殊结构
            for elem in root:
                if isinstance(elem.tag, str) and elem.text and elem.text.strip():
                    key = elem.tag
                    text = elem.text.strip()
                    
                    # 获取前一个注释作为英文原文
                    en_text = ""
                    prev = root.getprevious() if processor.use_lxml else None
                    if prev is not None and isinstance(prev, ET.Comment):
                        en_match = re.match(r'\s*EN:\s*(.*?)\s*$', prev.text)
                        if en_match:
                            en_text = en_match.group(1).strip()
                    
                    rows.append({
                        "key": key,
                        "text": sanitize_xml(text),
                        "en_text": sanitize_xml(en_text) if en_text else "",
                        "tag": key.split('.')[-1] if '.' in key else key
                    })
                    file_rows += 1
                    
            logging.info(f"从 {xml_file.name} 提取了 {file_rows} 条翻译")
            
        except Exception as e:
            logging.error(f"处理文件失败: {xml_file}: {e}")
            
    if rows:
        try:
            with open(output_csv, 'a', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["key", "text", "en_text", "tag"])
                writer.writerows(rows)
            logging.info(f"追加 {len(rows)} 条翻译到 {output_csv}")
        except Exception as e:
            logging.error(f"写入 CSV 失败: {output_csv}: {e}")
    else:
        logging.warning(f"没有找到可导出的翻译")

def export_keyed_to_csv(keyed_dir: str, output_csv: str) -> None:
    """将 Keyed 翻译导出到 CSV"""
    logging.info(f"导出 Keyed 到 CSV: {keyed_dir} -> {output_csv}")
    processor = XMLProcessor()
    rows = []
    
    for xml_file in Path(keyed_dir).rglob("*.xml"):
        try:
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                continue
                
            root = tree.getroot() if processor.use_lxml else tree
            file_rows = 0
            
            for elem in root:
                if isinstance(elem.tag, str) and elem.text and elem.text.strip():
                    key = elem.tag
                    text = elem.text.strip()
                    
                    rows.append({
                        "key": key,
                        "text": sanitize_xml(text),
                        "tag": key.split('.')[-1] if '.' in key else key
                    })
                    file_rows += 1
            
            logging.info(f"从 {xml_file.name} 提取了 {file_rows} 条翻译")
            
        except Exception as e:
            logging.error(f"处理文件失败: {xml_file}: {e}")
            
    if rows:
        try:
            with open(output_csv, 'a', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["key", "text", "tag"])
                writer.writerows(rows)
            logging.info(f"追加 {len(rows)} 条翻译到 {output_csv}")
        except Exception as e:
            logging.error(f"写入 CSV 失败: {output_csv}: {e}")
    else:
        logging.warning(f"没有找到可导出的翻译")