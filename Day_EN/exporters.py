import logging
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict
import csv  # 新增导入
from .utils import save_xml_to_file, sanitize_xcomment, get_language_folder_path

def move_dir(src: str, dst: str) -> None:
    """
    将目录 src 移动到 dst，已存在则覆盖。
    """
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(src, dst)
    import time; time.sleep(1)
    logging.info(f"重命名 {src} 为 {dst}")

def export_definjected_from_english(
    mod_root_dir: str,
    export_dir: str,
    active_language: str = "ChineseSimplified",
    english_language: str = "English"
) -> None:
    logging.info(f"调用 export_definjected_from_english: mod_root_dir={mod_root_dir}, export_dir={export_dir}, active_language={active_language}, english_language={english_language}")
    active_lang_path = get_language_folder_path(active_language, export_dir)
    def_injected_path = os.path.join(active_lang_path, "DefInjected")
    english_lang_path = get_language_folder_path(english_language, mod_root_dir)
    english_def_injected_path = os.path.join(english_lang_path, "DefInjected")
    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info(f"创建文件夹：{def_injected_path}")
    for xml_file in Path(def_injected_path).rglob("*.xml"):
        try:
            os.remove(xml_file)
            logging.info(f"删除文件：{xml_file}")
        except OSError as e:
            logging.error(f"无法删除 {xml_file}: {e}")
    for src_file in sorted(Path(english_def_injected_path).rglob("*.xml")):
        try:
            rel_path = os.path.relpath(src_file, english_def_injected_path)
            dst_file = os.path.join(def_injected_path, rel_path)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            logging.info(f"复制 {src_file} 到 {dst_file}")
            tree = ET.parse(dst_file)
            root = tree.getroot()
            parent_map = {c: p for p in root.iter() for c in p}
            for elem in root.findall(".//*"):
                if elem.text and elem.text.strip():
                    original = elem.text
                    comment = ET.Comment(sanitize_xcomment(f"EN: {original}"))
                    parent = parent_map.get(elem)
                    if parent is not None:
                        idx = list(parent).index(elem)
                        parent.insert(idx, comment)
            save_xml_to_file(root, dst_file)
        except ET.ParseError as e:
            logging.error(f"XML解析失败: {src_file}: {e}")
        except Exception as e:
            logging.error(f"无法处理 {src_file}: {e}")

def handle_extract_translate(
    mod_root_dir: str,
    export_dir: str,
    active_language: str = "ChineseSimplified",
    english_language: str = "English",
    extract_definjected_from_defs=None
) -> None:
    logging.info(f"调用 handle_extract_translate: mod_root_dir={mod_root_dir}, export_dir={export_dir}, active_language={active_language}")
    active_lang_path = get_language_folder_path(active_language, export_dir)
    def_injected_path = os.path.join(active_lang_path, "DefInjected")
    old_def_linked_path = os.path.join(active_lang_path, "DefLinked")
    english_lang_path = get_language_folder_path(english_language, mod_root_dir)
    english_def_injected_path = os.path.join(english_lang_path, "DefInjected")
    if os.path.exists(old_def_linked_path) and not os.path.exists(def_injected_path):
        move_dir(old_def_linked_path, def_injected_path)
    if os.path.exists(english_def_injected_path):
        print("检测到英文 DefInjected 目录。请选择处理方式：")
        print("1. 以英文 DefInjected 为基础（推荐用于已有翻译结构的情况）")
        print("2. 直接从 Defs 目录重新提取可翻译字段（推荐用于结构有变动或需全量提取时）")
        choice = input("请输入选项编号（1/2，回车默认1）：").strip()
        if choice == '2':
            logging.info("用户选择：从 Defs 目录重新提取可翻译字段")
            if extract_definjected_from_defs:
                extract_definjected_from_defs(mod_root_dir, export_dir, active_language)
            return
        else:
            logging.info("用户选择：以英文 DefInjected 为基础")
            export_definjected_from_english(
                mod_root_dir=mod_root_dir,
                export_dir=export_dir,
                active_language=active_language,
                english_language=english_language
            )
    else:
        logging.info(f"未找到英文 DefInjected {english_def_injected_path}，从 Defs 提取")
        print(f"未找到英文 DefInjected 目录 {english_def_injected_path}，将从 Defs 目录提取可翻译字段。")
        if extract_definjected_from_defs:
            extract_definjected_from_defs(mod_root_dir, export_dir, active_language)

def cleanup_backstories_dir(
    mod_root_dir: str,
    export_dir: str,
    active_language: str = "ChineseSimplified"
) -> None:
    active_lang_path = get_language_folder_path(active_language, export_dir)
    backstories_path = os.path.join(active_lang_path, "Backstories")
    if os.path.exists(backstories_path):
        delete_me_path = os.path.join(active_lang_path, "Backstories DELETE_ME")
        try:
            shutil.move(backstories_path, delete_me_path)
            logging.info(f"重命名背景故事为 {delete_me_path}")
            print(f"背景故事文件夹重命名为 {delete_me_path}，请检查并删除")
        except OSError as e:
            logging.error(f"无法重命名 {backstories_path}: {e}")

def export_keyed(
    mod_root_dir: str,
    export_dir: str,
    active_language: str = "ChineseSimplified",
    english_language: str = "English"
) -> None:
    logging.info(f"调用 export_keyed: mod_root_dir={mod_root_dir}, export_dir={export_dir}, active_language={active_language}, english_language={english_language}")
    active_lang_path = get_language_folder_path(active_language, export_dir)
    english_lang_path = get_language_folder_path(english_language, mod_root_dir)
    keyed_path = os.path.join(active_lang_path, "Keyed")
    if not os.path.exists(keyed_path):
        os.makedirs(keyed_path)
        logging.info(f"创建文件夹：{keyed_path}")
    english_keyed_path = os.path.join(english_lang_path, "Keyed")
    if not os.path.exists(english_keyed_path):
        logging.warning(f"英文 Keyed 目录 {english_keyed_path} 不存在，跳过")
        return
    xml_files = list(Path(english_keyed_path).rglob("*.xml"))
    if not xml_files:
        logging.warning(f"英文 Keyed 目录 {english_keyed_path} 没有 XML 文件，跳过")
        return
    for src_file in xml_files:
        try:
            rel_path = os.path.relpath(src_file, english_keyed_path)
            dst_file = os.path.join(keyed_path, rel_path)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            logging.info(f"复制 {src_file} 到 {dst_file}")
            tree = ET.parse(dst_file)
            root = tree.getroot()
            parent_map = {c: p for p in root.iter() for c in p}
            for elem in root.findall(".//*"):
                if elem.text and elem.text.strip():
                    original = elem.text
                    comment = ET.Comment(sanitize_xcomment(f" EN: {original} "))
                    parent = parent_map.get(elem)
                    if parent is not None:
                        idx = list(parent).index(elem)
                        parent.insert(idx, comment)
            save_xml_to_file(root, dst_file)
        except ET.ParseError as e:
            logging.error(f"XML解析失败: {src_file}: {e}")
        except OSError as e:
            logging.error(f"无法处理 {src_file}: {e}")

def export_definjected(
    mod_root_dir: str,
    export_dir: str,
    selected_translations: List[Tuple[str, str, str, str]],
    active_language: str = "ChineseSimplified"
) -> None:
    logging.info(f"调用 export_definjected: mod_root_dir={mod_root_dir}, export_dir={export_dir}, active_language={active_language}, translations_count={len(selected_translations)}")
    active_lang_path = get_language_folder_path(active_language, export_dir)
    def_injected_path = os.path.join(active_lang_path, "DefInjected")
    defs_path = os.path.join(mod_root_dir, "Defs")
    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logging.info(f"创建文件夹：{def_injected_path}")
    for xml_file in Path(def_injected_path).rglob("*.xml"):
        try:
            os.remove(xml_file)
            logging.info(f"删除文件：{xml_file}")
        except OSError as e:
            logging.error(f"无法删除 {xml_file}: {e}")
    if not os.path.exists(defs_path):
        print(f"错误：Defs 目录 {defs_path} 不存在")
        logging.error(f"Defs 目录 {defs_path} 不存在，请检查 mod_root_dir")
        return
    def_injections: Dict[str, List[Tuple[str, List[Tuple[str, str, str]]]]] = {}
    for xml_file in Path(defs_path).rglob("*.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            rel_path = os.path.relpath(xml_file, defs_path)
            output_path = os.path.join(def_injected_path, rel_path)
            for def_node in root.findall(".//*[defName]"):
                def_type = def_node.tag
                def_name = def_node.find("defName")
                if def_name is None or not def_name.text:
                    continue
                def_name_text = def_name.text
                filtered_translations = []
                prefix = f"{def_type}/{def_name_text}."
                for full_path, text, tag, file_path in selected_translations:
                    if str(file_path) == str(xml_file) and full_path.startswith(prefix):
                        field_path = full_path[len(prefix):]
                        filtered_translations.append((field_path, text, tag))
                if not filtered_translations:
                    continue
                if output_path not in def_injections:
                    def_injections[output_path] = []
                def_injections[output_path].append((def_name_text, filtered_translations))
        except ET.ParseError as e:
            logging.error(f"XML 语法错误 {xml_file}: {e}")
        except Exception as e:
            logging.error(f"无法解析 {xml_file}: {e}")
    for output_path, defs in def_injections.items():
        root = ET.Element("LanguageData")
        for def_name, translations in defs:
            if not translations:
                continue
            for field_path, text, tag in translations:
                clean_path = field_path
                full_path = f"{def_name}.{clean_path}"
                comment = ET.Comment(sanitize_xcomment(f" EN: {text} "))
                root.append(comment)
                field_elem = ET.SubElement(root, full_path)
                field_elem.text = text
        save_xml_to_file(root, output_path)

def export_keyed_to_csv(keyed_dir: str, csv_path: str) -> None:
    logging.info(f"调用 export_keyed_to_csv: keyed_dir={keyed_dir}, csv_path={csv_path}")
    rows = []
    if not os.path.exists(keyed_dir):
        logging.warning(f"Keyed 目录 {keyed_dir} 不存在，跳过 CSV 导出")
        return
    xml_files = list(Path(keyed_dir).rglob("*.xml"))
    if not xml_files:
        logging.warning(f"Keyed 目录 {keyed_dir} 没有 XML 文件，跳过 CSV 导出")
        return
    for xml_file in xml_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for elem in root.findall(".//*"):
                if isinstance(elem.tag, str) and elem.text and elem.text.strip():
                    logging.debug(f"找到 Keyed 键: {elem.tag} = {elem.text.strip()}")
                    rows.append({
                        "key": elem.tag,
                        "text": elem.text.strip(),
                        "tag": elem.tag
                    })
        except ET.ParseError as e:
            logging.error(f"Keyed XML解析失败: {xml_file}: {e}")
        except FileNotFoundError as e:
            logging.error(f"Keyed 文件未找到: {xml_file}: {e}")
    if not rows:
        logging.warning(f"Keyed目录 {keyed_dir} 未提取到任何内容，未写入 CSV")
        return
    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    with open(csv_path, "a", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["key", "text", "tag"])
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
    logging.info(f"Keyed 共导出 {len(rows)} 条到 {csv_path}")