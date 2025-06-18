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
from tqdm import tqdm
from ..utils.unified_config import get_config
from ..utils.utils import XMLProcessor, save_xml_to_file, sanitize_xcomment, get_language_folder_path, sanitize_xml, handle_existing_translations_choice, smart_merge_xml_translations
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
    language: str = CONFIG.core.default_language,
    source_language: str = CONFIG.core.source_language
) -> None:
    """从英文导出 DefInjected 翻译，添加 EN 注释"""
    logging.info(f"导出 DefInjected: mod_dir={mod_dir}, export_dir={export_dir}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.core.definjected_dir)
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_def_injected_path = os.path.join(src_lang_path, CONFIG.core.definjected_dir)
    
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
            processor.save_xml(tree, str(dst_file), pretty_print=True)
            
        except Exception as e:
            logging.error(f"处理文件失败: {src_file}: {e}")

def handle_extract_translate(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.core.default_language,
    source_language: str = CONFIG.core.source_language,
    extract_definjected_from_defs=None
) -> str:
    """
    处理翻译提取逻辑，选择 DefInjected 或 Defs
    
    Returns:
        str: 选择的提取方式 ('definjected' 或 'defs')
    """
    logging.info(f"处理翻译提取: mod_dir={mod_dir}, export_dir={export_dir}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.core.definjected_dir)
    old_def_linked_path = os.path.join(lang_path, "DefLinked")
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_def_injected_path = os.path.join(src_lang_path, CONFIG.core.definjected_dir)
    
    # 处理旧的 DefLinked 目录
    if os.path.exists(old_def_linked_path) and not os.path.exists(def_injected_path):
        move_dir(old_def_linked_path, def_injected_path)
    
    if os.path.exists(src_def_injected_path):
        print(f"\n{Fore.CYAN}检测到英文 DefInjected 目录: {src_def_injected_path}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}请选择 DefInjected 处理方式：{Style.RESET_ALL}")
        print(f"1. {Fore.GREEN}以英文 DefInjected 为基础{Style.RESET_ALL}（推荐用于已有翻译结构的情况）")
        print(f"2. {Fore.GREEN}直接从 Defs 目录重新提取可翻译字段{Style.RESET_ALL}（推荐用于结构有变动或需全量提取时）")
        
        choice = input(f"{Fore.CYAN}请输入选项编号（1/2，回车默认1）：{Style.RESET_ALL}").strip()
        
        if choice == "2":
            logging.info("用户选择：从 Defs 目录重新提取")
            print(f"{Fore.GREEN}✅ 将从 Defs 目录重新提取可翻译字段{Style.RESET_ALL}")
            return "defs"
        else:
            logging.info("用户选择：以英文 DefInjected 为基础")
            print(f"{Fore.GREEN}✅ 将以英文 DefInjected 为基础{Style.RESET_ALL}")
            return "definjected"
    else:
        logging.info(f"未找到英文 DefInjected {src_def_injected_path}，从 Defs 提取")
        print(f"{Fore.YELLOW}未找到英文 DefInjected 目录，将从 Defs 提取可翻译字段{Style.RESET_ALL}")
        return "defs"

def cleanup_backstories_dir(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.core.default_language
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
    language: str = CONFIG.core.default_language,
    source_language: str = CONFIG.core.source_language
) -> None:
    """导出 Keyed 翻译，添加 EN 注释"""
    logging.info(f"导出 Keyed: mod_dir={mod_dir}, export_dir={export_dir}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    keyed_path = os.path.join(lang_path, CONFIG.core.keyed_dir)
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_keyed_path = os.path.join(src_lang_path, CONFIG.core.keyed_dir)
    
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
            processor.save_xml(tree, str(dst_file), pretty_print=True)
            
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
    language: str = CONFIG.core.default_language
) -> None:
    """从 Defs 导出 DefInjected 翻译，确保包含所有字段"""
    logging.info(f"导出 DefInjected: mod_dir={mod_dir}, translations_count={len(selected_translations)}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.core.definjected_dir)
    defs_path = os.path.join(mod_dir, "Defs")
    
    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info(f"创建文件夹：{def_injected_path}")
    else:
        # 使用封装的用户选择函数
        choice = handle_existing_translations_choice(def_injected_path)
        if choice == "skip":
            logging.info("用户选择跳过，停止生成 DefInjected 文件")
            return
            
    if not os.path.exists(defs_path):
        logging.warning(f"Defs 目录 {defs_path} 不存在，跳过")
        return
        
    processor = XMLProcessor()
      # 按 DefType 分组翻译内容
    def_groups = {}
    for full_path, text, tag, file_path in selected_translations:
        if '/' in full_path:
            def_type_part, field_part = full_path.split('/', 1)
            
            # 清理 def_type：移除命名空间前缀，只保留类型名
            # 例如：rjw.SexFluidDef -> SexFluidDef
            if '.' in def_type_part:
                def_type = def_type_part.split('.')[-1]  # 取最后一个部分
            else:
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
        
        # 构建翻译字典，用于智能合并或传统合并
        translations = {}
        for def_name, fields in def_items.items():
            for field_path, text, tag in fields:
                # 生成完整的键名
                if field_path:
                    full_key = f"{def_name}.{field_path}"
                else:
                    full_key = def_name
                translations[full_key] = text
        
        # 根据用户选择的模式处理文件
        if choice == "smart-merge":
            # 使用智能合并
            from ..utils.utils import smart_merge_xml_translations
            smart_merge_xml_translations(output_file, translations, preserve_manual_edits=True)
        elif choice == "merge":
            # 使用传统合并（只更新现有元素）
            if os.path.exists(output_file):
                tree = processor.parse_xml(output_file)
                if tree:
                    processor.update_translations(tree, translations, merge=True)
                    processor.save_xml(tree, output_file, pretty_print=True)
                    logging.info(f"合并更新 DefInjected 文件: {output_file}")
                else:
                    _create_new_definjected_file(output_file, def_items, processor)
            else:
                _create_new_definjected_file(output_file, def_items, processor)
        else:
            # 替换模式或备份模式（重新生成文件）
            _create_new_definjected_file(output_file, def_items, processor)


def _create_new_definjected_file(output_file: str, def_items: dict, processor):
    """创建新的 DefInjected 文件"""
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
    processor.save_xml(tree, output_file, pretty_print=True)
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

def export_definjected_with_original_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
    language: str = CONFIG.core.default_language,
    source_language: str = CONFIG.core.source_language,
    merge_mode: str = "smart-merge"
) -> None:
    """按照原英文DefInjected目录结构导出翻译，保持文件组织一致"""
    logging.info(f"按原结构导出 DefInjected: mod_dir={mod_dir}, translations_count={len(selected_translations)}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.core.definjected_dir)    
    # 获取原英文DefInjected目录
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_def_injected_path = os.path.join(src_lang_path, CONFIG.core.definjected_dir)
    
    if not os.path.exists(src_def_injected_path):
        logging.warning(f"原英文DefInjected目录不存在: {src_def_injected_path}，回退到默认结构")
        # 回退到原来的函数
        export_definjected(mod_dir, export_dir, selected_translations, language)
        return
    
    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info(f"创建文件夹：{def_injected_path}")
    else:
        # 使用封装的用户选择函数
        choice = handle_existing_translations_choice(def_injected_path)
        if choice == "skip":
            logging.info("用户选择跳过，停止生成 DefInjected 文件")
            return
    
    processor = XMLProcessor()
    
    # 1. 分析原英文DefInjected文件结构
    original_files = {}  # {relative_path: xml_file_path}
    for xml_file in Path(src_def_injected_path).rglob("*.xml"):
        rel_path = str(xml_file.relative_to(Path(src_def_injected_path)))
        original_files[rel_path] = xml_file
    
    print(f"{Fore.CYAN}发现原英文DefInjected文件结构：{Style.RESET_ALL}")
    for rel_path in sorted(original_files.keys()):
        print(f"  📁 {rel_path}")
    
    # 2. 解析原文件，建立键到文件的映射
    key_to_file_map = {}  # {full_key: relative_path}
    
    for rel_path, xml_file in original_files.items():
        try:
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                continue
                
            root = tree.getroot() if processor.use_lxml else tree
            
            # 提取所有键
            for elem in root:
                if isinstance(elem.tag, str) and not elem.tag.startswith('{'):
                    key_to_file_map[elem.tag] = rel_path
                    
        except Exception as e:
            logging.error(f"解析原文件失败 {xml_file}: {e}")
    
    logging.info(f"建立键映射: {len(key_to_file_map)} 个键")
    
    # 3. 按文件分组翻译数据
    file_groups = {}  # {relative_path: [(key, text, tag), ...]}
    unmatched_translations = []
    
    for full_path, text, tag, file_path in selected_translations:
        # 从full_path提取键名
        if '/' in full_path:
            def_type_part, field_part = full_path.split('/', 1)
            if '.' in field_part:
                def_name, field_path = field_part.split('.', 1)
                full_key = f"{def_name}.{field_path}"
            else:
                full_key = field_part
        else:
            full_key = full_path
        
        # 查找对应的原文件
        target_file = key_to_file_map.get(full_key)
        
        if target_file:
            if target_file not in file_groups:
                file_groups[target_file] = []
            file_groups[target_file].append((full_key, text, tag))
        else:
            # 无法匹配到原文件的翻译
            unmatched_translations.append((full_path, text, tag, file_path))
    
    logging.info(f"文件分组完成: {len(file_groups)} 个文件, {len(unmatched_translations)} 个未匹配")
      # 4. 为每个文件生成翻译内容
    for rel_path, translation_list in file_groups.items():
        if not translation_list:
            continue
            
        # 创建对应的目录结构
        output_file = os.path.join(def_injected_path, rel_path)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 构建翻译字典
        translations = {full_key: text for full_key, text, tag in translation_list}
        
        # 根据用户选择的模式处理文件
        if choice == "smart-merge":
            # 使用智能合并
            from ..utils.utils import smart_merge_xml_translations
            smart_merge_xml_translations(output_file, translations, preserve_manual_edits=True)
        elif choice == "merge":
            # 使用传统合并（只更新现有元素）
            if os.path.exists(output_file):
                tree = processor.parse_xml(output_file)
                if tree:
                    processor.update_translations(tree, translations, merge=True)
                    processor.save_xml(tree, output_file, pretty_print=True)
                    logging.info(f"合并更新 DefInjected 文件: {output_file} ({len(translations)} 条翻译)")
                else:
                    _create_new_original_structure_file(output_file, translation_list, processor)
            else:
                _create_new_original_structure_file(output_file, translation_list, processor)
        else:
            # 替换模式或备份模式（重新生成文件）
            _create_new_original_structure_file(output_file, translation_list, processor)

    # 5. 处理未匹配的翻译（可选：生成到额外文件）
    if unmatched_translations:
        logging.warning(f"发现 {len(unmatched_translations)} 条未匹配的翻译")
        print(f"{Fore.YELLOW}⚠️ 发现 {len(unmatched_translations)} 条未匹配的翻译，将生成到 _Additional.xml{Style.RESET_ALL}")
        
        # 生成额外文件
        additional_file = os.path.join(def_injected_path, "_Additional.xml")
        
        # 构建未匹配翻译的字典
        unmatched_dict = {}
        additional_content = []
        for full_path, text, tag, file_path in unmatched_translations:
            # 从full_path生成键名
            if '/' in full_path:
                def_type_part, field_part = full_path.split('/', 1)
                if '.' in field_part:
                    def_name, field_path = field_part.split('.', 1)
                    full_key = f"{def_name}.{field_path}"
                else:
                    full_key = field_part
            else:
                full_key = full_path
            
            unmatched_dict[full_key] = text
            additional_content.append((full_key, text, tag, file_path))
        
        # 根据用户选择的模式处理额外文件
        if choice == "smart-merge":
            # 使用智能合并
            smart_merge_xml_translations(additional_file, unmatched_dict, preserve_manual_edits=True)
        elif choice == "merge":
            # 使用传统合并
            if os.path.exists(additional_file):
                tree = processor.parse_xml(additional_file)
                if tree:
                    processor.update_translations(tree, unmatched_dict, merge=True)
                    processor.save_xml(tree, additional_file, pretty_print=True)
                    logging.info(f"合并更新额外翻译文件: {additional_file}")
                else:
                    _create_additional_file(additional_file, additional_content, processor)
            else:
                _create_additional_file(additional_file, additional_content, processor)
        else:
            # 替换模式或备份模式
            _create_additional_file(additional_file, additional_content, processor)


def _create_new_original_structure_file(output_file: str, translation_list: list, processor):
    """创建新的原始结构 DefInjected 文件"""
    # 生成 XML 内容
    root = ET.Element("LanguageData")
    
    # 按键名排序，保持一致性
    for full_key, text, tag in sorted(translation_list, key=lambda x: x[0]):
        # 添加英文注释
        comment = ET.Comment(sanitize_xcomment(f"EN: {text}"))
        root.append(comment)
        
        # 添加翻译元素
        elem = ET.SubElement(root, full_key)
        elem.text = sanitize_xml(text)
    
    # 保存文件
    tree = ET.ElementTree(root)
    processor.save_xml(tree, output_file, pretty_print=True)
    logging.info(f"生成 DefInjected 文件: {output_file} ({len(translation_list)} 条翻译)")

    
def export_definjected_with_defs_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
    language: str = CONFIG.core.default_language,
    merge_mode: str = "smart-merge"
) -> None:
    """按照原Defs目录结构导出DefInjected翻译"""
    logging.info(f"按Defs结构导出 DefInjected: mod_dir={mod_dir}, translations_count={len(selected_translations)}")
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.core.definjected_dir)
    defs_path = os.path.join(mod_dir, "Defs")
    
    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info(f"创建文件夹：{def_injected_path}")
    else:
        # 使用封装的用户选择函数
        choice = handle_existing_translations_choice(def_injected_path)
        if choice == "skip":
            logging.info("用户选择跳过，停止生成 DefInjected 文件")
            return
        
    if not os.path.exists(defs_path):
        logging.warning(f"Defs 目录 {defs_path} 不存在，跳过")
        return
        
    processor = XMLProcessor()
    
    # 按原始文件路径分组翻译内容（基于 file_path 信息）
    file_groups = {}  # {original_file_path: [(key, text, tag), ...]}
    
    for full_path, text, tag, file_path in selected_translations:
        # 从 full_path 生成键名
        if '/' in full_path:
            def_type_part, field_part = full_path.split('/', 1)
            if '.' in field_part:
                def_name, field_path = field_part.split('.', 1)
                full_key = f"{def_name}.{field_path}"
            else:
                full_key = field_part
        else:
            full_key = full_path
        
        # 使用 file_path 作为分组依据
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append((full_key, text, tag))
    
    logging.info(f"按文件分组完成: {len(file_groups)} 个文件")
    
    # 为每个原始文件生成对应的 DefInjected 文件
    for original_file_path, translations in file_groups.items():
        if not translations:
            continue
        
        # 生成 DefInjected 文件路径
        # 例如：Defs/ThingDefs/Weapons.xml -> DefInjected/ThingDefs/Weapons.xml
        file_name = Path(original_file_path).stem  # 获取不带扩展名的文件名
        
        # 从第一个翻译项中提取 DefType
        first_translation = translations[0]
        first_full_path = None
        for full_path, text, tag, fp in selected_translations:
            if fp == original_file_path:
                first_full_path = full_path
                break
        
        if first_full_path and '/' in first_full_path:
            def_type_part = first_full_path.split('/', 1)[0]
            # 清理 def_type 名称
            if '.' in def_type_part:
                def_type = def_type_part.split('.')[-1]
            else:
                def_type = def_type_part
        else:
            def_type = "UnknownDef"
        
        # 创建目录结构：DefInjected/ThingDefs/
        type_dir = os.path.join(def_injected_path, f"{def_type}Defs")
        os.makedirs(type_dir, exist_ok=True)
          # 生成文件：DefInjected/ThingDefs/Weapons.xml
        output_file = os.path.join(type_dir, f"{file_name}.xml")
        
        # 构建翻译字典
        translation_dict = {full_key: text for full_key, text, tag in translations}
        
        # 根据用户选择的模式处理文件
        if choice == "smart-merge":
            # 使用智能合并
            smart_merge_xml_translations(output_file, translation_dict, preserve_manual_edits=True)
        elif choice == "merge":
            # 使用传统合并（只更新现有元素）
            if os.path.exists(output_file):
                tree = processor.parse_xml(output_file)
                if tree:
                    processor.update_translations(tree, translation_dict, merge=True)
                    processor.save_xml(tree, output_file, pretty_print=True)
                    logging.info(f"合并更新 DefInjected 文件: {output_file} ({len(translations)} 条翻译)")
                else:
                    _create_new_defs_structure_file(output_file, translations, processor)
            else:
                _create_new_defs_structure_file(output_file, translations, processor)
        else:
            # 替换模式或备份模式（重新生成文件）
            _create_new_defs_structure_file(output_file, translations, processor)


def _create_new_defs_structure_file(output_file: str, translations: list, processor):
    """创建新的 Defs 结构 DefInjected 文件"""
    # 生成 XML 内容
    root = ET.Element("LanguageData")
    
    # 按键名排序，保持一致性
    for full_key, text, tag in sorted(translations, key=lambda x: x[0]):
        # 添加英文注释
        comment = ET.Comment(sanitize_xcomment(f"EN: {text}"))
        root.append(comment)
        
        # 添加翻译元素
        elem = ET.SubElement(root, full_key)
        elem.text = sanitize_xml(text)
    
    # 保存文件
    tree = ET.ElementTree(root)
    processor.save_xml(tree, output_file, pretty_print=True)
    logging.info(f"生成 DefInjected 文件: {output_file} ({len(translations)} 条翻译)")

def _create_additional_file(additional_file: str, additional_content: list, processor):
    """创建额外翻译文件"""
    root = ET.Element("LanguageData")
    
    for full_key, text, tag, file_path in additional_content:
        comment = ET.Comment(sanitize_xcomment(f"EN: {text} (来源: {file_path})"))
        root.append(comment)
        
        elem = ET.SubElement(root, full_key)
        elem.text = sanitize_xml(text)
    
    tree = ET.ElementTree(root)
    processor.save_xml(tree, additional_file, pretty_print=True)
    logging.info(f"生成额外翻译文件: {additional_file}")