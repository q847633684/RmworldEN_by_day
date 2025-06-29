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
from day_translation.utils.utils import XMLProcessor, sanitize_xcomment, get_language_folder_path, sanitize_xml
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
    logging.info("导出 DefInjected: mod_dir=%s, export_dir=%s", mod_dir, export_dir)
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_def_injected_path = os.path.join(src_lang_path, CONFIG.def_injected_dir)

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info("创建文件夹：%s", def_injected_path)

    if not os.path.exists(src_def_injected_path):
        logging.warning("英文 DefInjected 目录 %s 不存在，跳过", src_def_injected_path)
        return

    processor = XMLProcessor()

    for src_file in sorted(Path(src_def_injected_path).rglob("*.xml")):
        try:
            rel_path = os.path.relpath(src_file, src_def_injected_path)
            dst_file = os.path.join(def_injected_path, rel_path)
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

def handle_extract_translate(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language,
    extract_definjected_from_defs=None
) -> str:
    """
    处理翻译提取逻辑，选择 DefInjected 或 Defs

    Returns:
        str: 选择的提取方式 ('definjected' 或 'defs')
    """
    logging.info("处理翻译提取: mod_dir=%s, export_dir=%s", mod_dir, export_dir)
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
    old_def_linked_path = os.path.join(lang_path, "DefLinked")
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_def_injected_path = os.path.join(src_lang_path, CONFIG.def_injected_dir)

    # 处理旧的 DefLinked 目录
    if os.path.exists(old_def_linked_path) and not os.path.exists(def_injected_path):
        move_dir(old_def_linked_path, def_injected_path)

    if os.path.exists(src_def_injected_path):
        print(f"\n{Fore.CYAN}检测到英文 DefInjected 目录: {src_def_injected_path}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}请选择 DefInjected 处理方式：{Style.RESET_ALL}")
        print(f"1. {Fore.GREEN}以英文 DefInjected 为基础{Style.RESET_ALL}")
        print("   💡 基于现有翻译结构，保持文件组织一致性")
        print("   💡 生成带'[待翻译]'标记的模板，包含英文原文作参考")
        print("   💡 推荐用于已有翻译基础或希望保持结构稳定的情况")
        print(f"2. {Fore.GREEN}直接从 Defs 目录重新提取可翻译字段{Style.RESET_ALL}")
        print("   💡 全量扫描模组定义文件，确保不遗漏任何可翻译内容")
        print("   💡 推荐用于首次翻译、结构有变动或需要完整提取的情况")
        print(f"b. {Fore.YELLOW}返回上级菜单{Style.RESET_ALL}")

        while True:
            choice = input(f"\n{Fore.CYAN}请输入选项编号（1/2/b，回车默认1）：{Style.RESET_ALL}").strip().lower()

            if choice == 'b':
                raise KeyboardInterrupt("用户选择返回")  # 使用异常来中断流程
            elif choice == "2":
                logging.info("用户选择：从 Defs 目录重新提取")
                print(f"{Fore.GREEN}✅ 将从 Defs 目录重新提取可翻译字段{Style.RESET_ALL}")
                return "defs"
            elif choice == "" or choice == "1":
                logging.info("用户选择：以英文 DefInjected 为基础")
                print(f"{Fore.GREEN}✅ 将以英文 DefInjected 为基础生成模板{Style.RESET_ALL}")
                return "definjected"
            else:
                print(f"{Fore.RED}❌ 无效选择，请输入 1、2 或 b{Style.RESET_ALL}")
    else:
        logging.info("未找到英文 DefInjected %s，从 Defs 提取", src_def_injected_path)
        print(f"{Fore.YELLOW}未找到英文 DefInjected 目录，将从 Defs 提取可翻译字段{Style.RESET_ALL}")
        return "defs"

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
            logging.info("重命名背景故事为 %s", delete_me_path)
            print(f"背景故事文件夹重命名为 {delete_me_path}，请检查并删除")
        except OSError as e:
            logging.error("无法重命名 %s: %s", backstories_path, e)

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

def export_definjected(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
    language: str = CONFIG.default_language
) -> None:
    """从 Defs 导出 DefInjected 翻译，确保包含所有字段"""
    logging.info("导出 DefInjected: mod_dir=%s, translations_count=%s", mod_dir, len(selected_translations))
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    lang_path = get_language_folder_path(language, export_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
    defs_path = os.path.join(mod_dir, "Defs")

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info("创建文件夹：%s", def_injected_path)

    # 清理现有文件
    for xml_file in Path(def_injected_path).rglob("*.xml"):
        try:
            os.remove(xml_file)
            logging.info("删除文件：%s", xml_file)
        except OSError as e:
            logging.error("无法删除 %s: %s", xml_file, e)

    if not os.path.exists(defs_path):
        logging.warning("Defs 目录 %s 不存在，跳过", defs_path)
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
        logging.info("生成 DefInjected 文件: %s", output_file)

def export_definjected_with_original_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language
) -> None:
    """按照原英文DefInjected目录结构导出翻译，保持文件组织一致"""
    logging.info("按原结构导出 DefInjected: mod_dir=%s, translations_count=%s", mod_dir, len(selected_translations))
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    
    # 直接使用export_dir作为基础路径
    def_injected_path = os.path.join(export_dir, CONFIG.def_injected_dir)

    # 获取原英文DefInjected目录
    src_lang_path = get_language_folder_path(source_language, mod_dir)
    src_def_injected_path = os.path.join(src_lang_path, CONFIG.def_injected_dir)

    if not os.path.exists(src_def_injected_path):
        logging.warning("原英文DefInjected目录不存在: %s，回退到默认结构", src_def_injected_path)
        # 回退到原来的函数
        export_definjected(mod_dir, export_dir, selected_translations, language)
        return

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info("创建文件夹：%s", def_injected_path)

    # 清理现有文件
    for xml_file in Path(def_injected_path).rglob("*.xml"):
        try:
            os.remove(xml_file)
            logging.info("删除文件：%s", xml_file)
        except OSError as e:
            logging.error("无法删除 %s: %s", xml_file, e)

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
            logging.error("解析原文件失败 %s: %s", xml_file, e)

    logging.info("建立键映射: %s 个键", len(key_to_file_map))

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

    logging.info("文件分组完成: %s 个文件, %s 个未匹配", len(file_groups), len(unmatched_translations))

    # 4. 为每个文件生成翻译内容
    for rel_path, translations in file_groups.items():
        if not translations:
            continue

        # 创建对应的目录结构
        output_file = os.path.join(def_injected_path, rel_path)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

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
        logging.info("生成 DefInjected 文件: %s (%s 条翻译)", output_file, len(translations))

    # 5. 处理未匹配的翻译（可选：生成到额外文件）
    if unmatched_translations:
        logging.warning("发现 %s 条未匹配的翻译", len(unmatched_translations))
        print(f"{Fore.YELLOW}⚠️ 发现 {len(unmatched_translations)} 条未匹配的翻译，将生成到 _Additional.xml{Style.RESET_ALL}")

        # 生成额外文件
        additional_file = os.path.join(def_injected_path, "_Additional.xml")
        root = ET.Element("LanguageData")

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

            comment = ET.Comment(sanitize_xcomment(f"EN: {text} (来源: {file_path})"))
            root.append(comment)

            elem = ET.SubElement(root, full_key)
            elem.text = sanitize_xml(text)

        tree = ET.ElementTree(root)
        processor.save_xml(tree, additional_file, pretty_print=True)
        logging.info("生成额外翻译文件: %s", additional_file)

def export_definjected_with_defs_structure(
    mod_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
    language: str = CONFIG.default_language
) -> None:
    """按照原Defs目录结构导出DefInjected翻译"""
    logging.info("按Defs结构导出 DefInjected: mod_dir=%s, translations_count=%s", mod_dir, len(selected_translations))
    mod_dir = str(Path(mod_dir).resolve())
    export_dir = str(Path(export_dir).resolve())
    
    # 直接使用export_dir作为基础路径
    def_injected_path = os.path.join(export_dir, CONFIG.def_injected_dir)
    
    defs_path = os.path.join(mod_dir, "Defs")

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info("创建文件夹：%s", def_injected_path)

    # 清理现有文件
    for xml_file in Path(def_injected_path).rglob("*.xml"):
        try:
            os.remove(xml_file)
            logging.info("删除文件：%s", xml_file)
        except OSError as e:
            logging.error("无法删除 %s: %s", xml_file, e)

    if not os.path.exists(defs_path):
        logging.warning("Defs 目录 %s 不存在，跳过", defs_path)
        return

    processor = XMLProcessor()

    # 按DefType分组翻译内容（基于 full_path 中的 def_type 信息）
    file_groups = {}

    for full_path, text, tag, file_path in selected_translations:
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
        processor.save_xml(tree, output_file, pretty_print=True)
        logging.info("生成 DefInjected 文件: %s (%s 条翻译)", output_file, len(translations))
