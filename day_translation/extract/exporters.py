"""
导出功能模块 - 实现翻译模板导出、DefInjected 导出等功能
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Tuple
from lxml import etree as LET
from day_translation.utils.config import get_config
from day_translation.utils.utils import sanitize_xcomment, sanitize_xml, XMLProcessor

CONFIG = get_config()

def export_definjected_with_original_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: list,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language
) -> None:
    """按 file_path 创建目录和文件结构导出 DefInjected 翻译，key 作为标签名，text 作为内容"""
    logging.info("按 file_path 结构导出 DefInjected: mod_dir=%s, translations_count=%s", mod_dir, len(selected_translations))
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    
    def_injected_path = os.path.join(export_dir, CONFIG.def_injected_dir)

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info("创建文件夹：%s", def_injected_path)
    # 按 file_path 分组翻译数据
    file_groups = {}  # {file_path: [(key, text, tag), ...]}

    for item in selected_translations:
        k, t, g, f = item[:4]
        if f not in file_groups:
            file_groups[f] = []
        file_groups[f].append((k, t, g))

    logging.info("按 file_path 分组完成: %s 个文件", len(file_groups))

    # 为每个 file_path 生成翻译文件
    for file_path, translations in file_groups.items():
        if not translations:
            continue

        # 创建对应的目录结构
        output_file = os.path.join(def_injected_path, file_path)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # 生成 XML 内容
        root = LET.Element("LanguageData")

        # 按键名排序，保持一致性
        for key, text, tag in sorted(translations, key=lambda x: x[0]):
            # 添加英文注释
            comment = LET.Comment(sanitize_xcomment(f"EN: {text}"))
            root.append(comment)

            # 添加翻译元素
            elem = LET.SubElement(root, key)
            elem.text = sanitize_xml(text)

        # 保存文件
        processor = XMLProcessor()
        ok = processor.save_xml(root, output_file, pretty_print=True)
        if ok:
            logging.info("生成 DefInjected 文件: %s (%s 条翻译)", output_file, len(translations))
        else:
            logging.error("写入失败: %s", output_file)

def export_definjected_with_defs_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: list,
    language: str = CONFIG.default_language
) -> None:
    """按照按DefType分组导出DefInjected翻译"""
    logging.info("按Defs结构导出 DefInjected: mod_dir=%s, translations_count=%s", mod_dir, len(selected_translations))
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    
    def_injected_path = os.path.join(export_dir, CONFIG.def_injected_dir)

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info("创建文件夹：%s", def_injected_path)

    # 按DefType分组翻译内容（基于 full_path 中的 def_type 信息）
    file_groups = {}

    for item in selected_translations:
        full_path, text, tag, rel_path = item[:4]
        # 从 full_path 生成键名和提取 def_type
        if '/' in full_path:
            def_type_part, field_part = full_path.split('/', 1)
            if '.' in field_part:
                def_name, field_path = field_part.split('.', 1)
                full_key = f"{def_name}.{field_path}"
            else:
                full_key = field_part
            
            # 清理 def_type 名称
            if '.' in def_type_part:
                def_type = def_type_part.split('.')[-1]
            else:
                def_type = def_type_part
        else:
            full_key = full_path
            def_type = "UnknownDef"

        # 使用 def_type 作为分组依据
        if def_type not in file_groups:
            file_groups[def_type] = []
        file_groups[def_type].append((full_key, text, tag))

    logging.info("按DefType分组完成: %s 个类型", len(file_groups))

    # 为每个 DefType 生成 XML 文件
    for def_type, translations in file_groups.items():
        if not translations:
            continue

        # 创建对应的目录结构
        type_dir = os.path.join(def_injected_path, f"{def_type}Defs")
        os.makedirs(type_dir, exist_ok=True)

        output_file = os.path.join(type_dir, f"{def_type}Defs.xml")

        # 生成 XML 内容
        root = LET.Element("LanguageData")

        # 按键名排序，保持一致性
        for full_key, text, tag in sorted(translations, key=lambda x: x[0]):
            # 添加英文注释
            comment = LET.Comment(sanitize_xcomment(f"EN: {text}"))
            root.append(comment)

            # 添加翻译元素
            elem = LET.SubElement(root, full_key)
            elem.text = sanitize_xml(text)

        # 保存文件
        processor = XMLProcessor()
        ok = processor.save_xml(root, output_file, pretty_print=True)
        if ok:
            logging.info(f"生成 DefInjected 文件: {output_file} ({len(translations)} 条翻译)")
        else:
            logging.error(f"写入失败: {output_file}")

def export_definjected_with_file_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: list,
    language: str = CONFIG.default_language
) -> None:
    """按原始Defs文件目录结构导出DefInjected翻译，key 结构为 DefType/defName.字段，导出时去除 DefType/ 只保留 defName.字段作为标签名，目录结构用 rel_path，内容用 text。"""
    logging.info("按文件结构导出 DefInjected: mod_dir=%s, translations_count=%s", mod_dir, len(selected_translations))
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    
    def_injected_path = os.path.join(export_dir, CONFIG.def_injected_dir)

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info("创建文件夹：%s", def_injected_path)

    file_groups = {}
    for item in selected_translations:
        key, text, tag, rel_path = item[:4]
        if rel_path not in file_groups:
            file_groups[rel_path] = []
        file_groups[rel_path].append((key, text, tag))

    logging.info("按文件结构分组完成: %s 个文件", len(file_groups))

    for rel_path, translations in file_groups.items():
        if not translations:
            continue
        output_file = os.path.join(def_injected_path, rel_path)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        root = LET.Element("LanguageData")
        for key, text, tag in sorted(translations, key=lambda x: x[0]):
            if text is None:
                text = ""
            assert isinstance(text, str), f"text 非字符串: {text}"
            # 去除 DefType/ 只保留 defName.字段
            if '/' in key:
                _, tag_name = key.split('/', 1)
            else:
                tag_name = key
            # 合法性修复：只允许字母、数字、下划线、点号，其它替换为点号
            tag_name = re.sub(r'[^A-Za-z0-9_.]', '.', tag_name)
            if not re.match(r'^[A-Za-z_]', tag_name):
                tag_name = '_' + tag_name
            comment = LET.Comment(sanitize_xcomment(f"EN: {text}"))
            root.append(comment)
            elem = LET.SubElement(root, tag_name)
            elem.text = sanitize_xml(text)
        processor = XMLProcessor()
        ok = processor.save_xml(root, output_file, pretty_print=True)
        if ok:
            logging.info(f"生成 DefInjected 文件: {output_file} ({len(translations)} 条翻译)")
        else:
            logging.error(f"写入失败: {output_file}")

def export_keyed_template(
    mod_dir: str,
    export_dir: str,
    selected_translations: list,
    language: str = CONFIG.default_language
) -> None:
    """导出 Keyed 翻译模板，按文件分组生成 XML 文件"""
    logging.info("导出 Keyed 翻译模板: mod_dir=%s, translations_count=%s", mod_dir, len(selected_translations))
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    
    keyed_path = os.path.join(export_dir, CONFIG.keyed_dir)

    if not os.path.exists(keyed_path):
        os.makedirs(keyed_path)
        logging.info("创建文件夹：%s", keyed_path)

    # 按 file_path 分组翻译数据
    file_groups = {}  # {file_path: [(key, text, tag), ...]}

    for item in selected_translations:
        key, text, tag, file_path = item[:4]
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append((key, text, tag))

    logging.info("按文件分组完成: %s 个文件", len(file_groups))

    # 为每个 file_path 生成翻译文件
    for file_path, translations in file_groups.items():
        if not translations:
            continue

        # 创建目标文件路径（只保留文件名）
        output_file = os.path.join(keyed_path, Path(file_path).name)

        # 生成 XML 内容
        root = LET.Element("LanguageData")

        # 按键名排序，保持一致性
        for key, text, tag in sorted(translations, key=lambda x: x[0]):
            # 添加英文注释
            comment = LET.Comment(sanitize_xcomment(f"EN: {text}"))
            root.append(comment)
            
            # 添加翻译元素
            elem = LET.SubElement(root, key)
            elem.text = sanitize_xml(text)

        # 保存文件
        processor = XMLProcessor()
        ok = processor.save_xml(root, output_file, pretty_print=True)
        if ok:
            logging.info("生成 Keyed 文件: %s (%s 条翻译)", output_file, len(translations))
        else:
            logging.error("写入失败: %s", output_file)

def write_merged_definjected_translations(
    merged, 
    export_dir, 
    def_injected_dir="DefInjected"
) -> None:
    """
    将合并后的六元组写回 XML 文件
    merged: List[(key, test, tag, rel_path, en_test, history)]
    export_dir: 输出根目录
    def_injected_dir: DefInjected 目录名
    """
    # 1. 按 rel_path 分组
    file_groups = {}
    for item in merged:
        rel_path = item[3]
        file_groups.setdefault(rel_path, []).append(item)

    base_dir = Path(export_dir) / def_injected_dir
    for rel_path, items in file_groups.items():
        output_file = base_dir / rel_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        root = LET.Element("LanguageData")
        for key, test, tag, _, en_test, history in sorted(items, key=lambda x: x[0]):
            # 历史注释
            if history:
                history_comment = LET.Comment(sanitize_xcomment(f"HISTORY: 原翻译内容：{history}，替换于YYYY-MM-DD"))
                root.append(history_comment)
            # EN注释
            if en_test:
                en_comment = LET.Comment(sanitize_xcomment(f"EN: {en_test}"))
                root.append(en_comment)
            # 翻译内容
            elem = LET.SubElement(root, key)
            elem.text = sanitize_xml(test)
        processor = XMLProcessor()
        processor.save_xml(root, output_file, pretty_print=True)           