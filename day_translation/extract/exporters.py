"""
导出功能模块 - 实现翻译模板导出、DefInjected 导出等功能
"""

import logging
import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple
import csv
from day_translation.utils.config import get_config
from day_translation.utils.utils import XMLProcessor, get_language_folder_path
from day_translation.extract.xml_utils import save_xml, save_xml_lxml, sanitize_xcomment, sanitize_xml
from colorama import Fore, Style
import pprint
from lxml import etree as LET

CONFIG = get_config()

def safe_element(tag, attrib=None, **extra):
    assert isinstance(tag, str) and tag, f"标签名非法: {tag}"
    if attrib:
        for k, v in attrib.items():
            assert isinstance(k, str), f"属性名非法: {k}"
            assert isinstance(v, str), f"属性值非法: {v}"
    return ET.Element(tag, attrib or {}, **extra)

def safe_subelement(parent, tag, attrib=None, **extra):
    assert isinstance(tag, str) and tag, f"标签名非法: {tag}"
    if attrib:
        for k, v in attrib.items():
            assert isinstance(k, str), f"属性名非法: {k}"
            assert isinstance(v, str), f"属性值非法: {v}"
    return ET.SubElement(parent, tag, attrib or {}, **extra)

def export_definjected_with_original_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
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

    for key, text, tag, file_path in selected_translations:
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append((key, text, tag))

    logging.info("按 file_path 分组完成: %s 个文件", len(file_groups))

    # 为每个 file_path 生成翻译文件
    for file_path, translations in file_groups.items():
        if not translations:
            continue

        # 创建对应的目录结构
        output_file = os.path.join(def_injected_path, file_path)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # 生成 XML 内容
        root = ET.Element("LanguageData")

        # 按键名排序，保持一致性
        for key, text, tag in sorted(translations, key=lambda x: x[0]):
            # 添加英文注释
            comment = ET.Comment(sanitize_xcomment(f"EN: {text}"))
            root.append(comment)

            # 添加翻译元素
            elem = ET.SubElement(root, key)
            elem.text = sanitize_xml(text)

        # 保存文件
        tree = ET.ElementTree(root)
        processor = XMLProcessor()
        processor.save_xml(tree, output_file, pretty_print=True)
        logging.info("生成 DefInjected 文件: %s (%s 条翻译)", output_file, len(translations))

def export_definjected_with_defs_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
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

    for full_path, text, tag, rel_path in selected_translations:
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
        ok = save_xml(tree, output_file, pretty_print=True)
        if ok:
            logging.info(f"生成 DefInjected 文件: {output_file} ({len(translations)} 条翻译)")
        else:
            logging.error(f"写入失败: {output_file}")

def export_definjected_with_file_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
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
    for key, text, tag, rel_path in selected_translations:
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
            comment = LET.Comment(sanitize_xcomment(f"EN: {text} (来源文件: {rel_path})"))
            root.append(comment)
            elem = LET.SubElement(root, tag_name)
            elem.text = sanitize_xml(text)
        ok = save_xml_lxml(root, output_file, pretty_print=True)
        if ok:
            logging.info(f"生成 DefInjected 文件: {output_file} ({len(translations)} 条翻译)")
        else:
            logging.error(f"写入失败: {output_file}")

def export_keyed_template(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
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

    for key, text, tag, file_path in selected_translations:
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
        root = ET.Element("LanguageData")

        # 按键名排序，保持一致性
        for key, text, tag in sorted(translations, key=lambda x: x[0]):
            # 添加翻译元素
            elem = ET.SubElement(root, key)
            elem.text = sanitize_xml(text)

        # 保存文件
        tree = ET.ElementTree(root)
        processor = XMLProcessor()
        processor.save_xml(tree, output_file, pretty_print=True)
        logging.info("生成 Keyed 文件: %s (%s 条翻译)", output_file, len(translations))
def export_keyed(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language
) -> None:
    """导出 Keyed 翻译，添加 EN 注释"""
    logging.info("导出 Keyed: mod_dir=%s, export_dir=%s", mod_dir, export_dir)
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    keyed_path = os.path.join(lang_path, CONFIG.keyed_dir)
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_keyed_path = os.path.join(src_lang_path, CONFIG.keyed_dir)

    if not os.path.exists(keyed_path):
        os.makedirs(keyed_path)
        logging.info("创建文件夹：%s", keyed_path)

    if not os.path.exists(src_keyed_path):
        logging.warning("英文 Keyed 目录 %s 不存在，跳过", src_keyed_path)
        return

    xml_files = list(Path(src_keyed_path).rglob("*.xml"))
    if not xml_files:
        logging.warning("英文 Keyed 目录 %s 没有 XML 文件，跳过", src_keyed_path)
        return

    processor = XMLProcessor()

    for src_file in xml_files:
        try:
            rel_path = os.path.relpath(src_file, src_keyed_path)
            dst_file = os.path.join(keyed_path, rel_path)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            logging.info("复制 %s 到 %s", src_file, dst_file)

            tree = processor.parse_xml(str(dst_file))
            if tree is None:
                continue
                  # 添加英文注释
            processor.add_comments(tree, comment_prefix="EN")
            processor.save_xml(tree, str(dst_file), pretty_print=True)

        except Exception as e:
            logging.error("处理文件失败: %s: %s", src_file, e)