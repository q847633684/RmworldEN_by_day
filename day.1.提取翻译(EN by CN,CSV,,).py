
import os
import shutil
import xml.etree.ElementTree as ET
import re
from pathlib import Path
import logging
import time

# 可翻译字段预览/确认开关
PREVIEW_TRANSLATABLE_FIELDS = False  # True: 显示预览界面，False: 跳过预览直接导出
# 日志级别控制
DEBUG_MODE = True  # True 显示 debug 日志，False 只显示 info 及以上
LOG_FILE = "extract_translate.log"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
log_format = '%(asctime)s - %(levelname)s - %(message)s'
# 清空 root logger 的 handler，防止重复
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
# 控制台 handler
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter(log_format))
# 文件 handler
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter(log_format))
logging.basicConfig(level=log_level, handlers=[console_handler, file_handler])

# 默认可翻译字段
DEFAULT_FIELDS = [
    'label', 'RMBLabel', 'description', 'baseDesc', 'title', 'titleShort',
    'rulesStrings', 'labelNoun', 'gerund', 'reportString',
    'text', 'message', 'verb', 'skillLabel', 'pawnLabel'
]

# 默认不可翻译字段
IGNORE_FIELDS = [
    'defName', 'ParentName', 'visible', 'baseMoodEffect', 'Class',
    'ignoreIllegalLabelCharacterConfigError', 'identifier', 'slot',
    'spawnCategories', 'skillGains', 'workDisables', 'requiredWorkTags',
    'bodyTypeGlobal', 'bodyTypeFemale', 'bodyTypeMale', 'forcedTraits',
    'initialSeverity', 'minSeverity', 'maxSeverity', 'isBad', 'tendable',
    'scenarioCanAdd', 'comps', 'defaultLabelColor', 'hediffDef',
    'becomeVisible', 'rulePack', 'retro' ,'Social'
]

# 正则表达式过滤器
NON_TEXT_PATTERNS = [
    r'^\s*\(\s*\d+\s*,\s*[\d*\.]+\s*\)\s*$',  # 坐标对
    r'^\s*[\d.]+\s*$',                          # 纯数字
    r'^\s*(true|false)\s*$',                  # 布尔值
    #r'^\s*[A-Za-z0-9_]+\s*$'                  # 单单词标识符
]

def get_language_folder_path(language, root_dir):
    """获取语言文件夹路径"""
    # 修正为 RimWorld 标准结构，先 Languages 再语言名
    return os.path.join(root_dir, "Languages", language)

def sanitize_xcomment(text):
    """清理 XML 注释中的非法字符"""
    return re.sub(r'-{2,}', ' ', text)

def save_xml_to_file(root, path):
    """保存 XML 文件，保持原始文本格式"""
    def element_to_string(elem, level=0):
        indent = "  " * level
        result = []

        # 处理注释
        if elem.tag is ET.Comment:
            text = elem.text if elem.text is not None else ""
            return f"{indent}<!--{text}-->\n"

        # 处理元素
        tag = elem.tag
        if elem.text and '\n' not in elem.text.strip():
            # 单行文本不换行
            result.append(f"{indent}<{tag}>{elem.text}</{tag}>\n")
        else:
            result.append(f"{indent}<{tag}>\n")
            # 处理多行文本
            if elem.text:
                text_lines = elem.text.splitlines()
                for line in text_lines:
                    result.append(f"{indent}  {line.rstrip()}\n")

        # 处理子元素
        for child in elem:
            result.append(element_to_string(child, level + 1))

        # 结束标签（仅在多行或子元素时）
        if not (elem.text and '\n' not in elem.text.strip()):
            result.append(f"{indent}</{tag}>\n")

        return "".join(result)

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_str += element_to_string(root)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        logging.info(f"保存 XML 文件：{path}")
    except Exception as e:
        logging.error(f"无法保存 XML 文件 {path}: {e}")

def is_translatable_text(text, tag):
    """判断文本是否需要翻译"""
    if not text or not isinstance(text, str) or not text.strip():
        logging.debug(f"排除空文本：{text}")
        return False
    if tag.lower() in [f.lower() for f in IGNORE_FIELDS]:
        logging.debug(f"排除不可翻译标签 {tag}：{text}")
        return False
    for pattern in NON_TEXT_PATTERNS:
        if re.match(pattern, text.strip()):
            logging.debug(f"排除正则匹配 {pattern}：{text}")
            return False
    if tag.lower() in [f.lower() for f in DEFAULT_FIELDS]:
        logging.debug(f"包含可翻译标签 {tag}：{text}")
        return True
    # if len(text.strip().split()) == 1 and not any(c.isspace() for c in text.strip()):
    #     logging.debug(f"排除单单词：{text}")
    #     return False
    logging.debug(f"包含多词文本：{text}")
    return True


def extract_translatable_fields(node, path="", list_indices=None, translations=None, parent_tag=None):
    """递归提取可翻译字段"""
    if list_indices is None:
        list_indices = {}
    if translations is None:
        translations = []

    node_tag = node.tag
    # 如果当前节点是defName，直接返回，不递归也不加入translations
    if node_tag == 'defName':
        return translations
    current_path = f"{path}.{node_tag}" if path else node_tag

    # 用父路径+tag做key，保证每组li独立编号
    index_key = f"{path}|{node_tag}"
    if node_tag == 'li':
        if index_key in list_indices:
            list_indices[index_key] += 1
        else:
            list_indices[index_key] = 0
        current_path = f"{path}.{list_indices[index_key]}" if path else str(list_indices[index_key])

    # 判断是否导出
    if node_tag == 'li':
        # 只有父级标签在 DEFAULT_FIELDS 时才导出
        if parent_tag and parent_tag.lower() in [f.lower() for f in DEFAULT_FIELDS]:
            if node.text and is_translatable_text(node.text, node_tag):
                translations.append((current_path, node.text, node_tag))
    else:
        # 只有自己在 DEFAULT_FIELDS 时导出
        if node_tag.lower() in [f.lower() for f in DEFAULT_FIELDS]:
            if node.text and is_translatable_text(node.text, node_tag):
                translations.append((current_path, node.text, node_tag))

    # 递归子节点，li 子节点共享 list_indices，其它子节点 copy
    for child in node:
        if child.tag == 'li':
            extract_translatable_fields(child, current_path, list_indices, translations, parent_tag=node_tag)
        else:
            extract_translatable_fields(child, current_path, list_indices.copy(), translations, parent_tag=node_tag)

    return translations

def preview_translatable_fields(mod_root_dir, preview=PREVIEW_TRANSLATABLE_FIELDS):
    """预览可翻译字段，可通过 preview 参数控制是否显示"""
    logging.info(f"扫描 Defs 目录：{os.path.join(mod_root_dir, 'Defs')}")
    defs_path = os.path.join(mod_root_dir, "Defs")
    if not os.path.exists(defs_path):
        logging.warning(f"Defs 目录 {defs_path} 不存在")
        return []

    all_translations = []
    for xml_file in Path(defs_path).rglob("*.xml"):
        logging.info(f"处理 XML 文件：{xml_file}")
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            def_nodes = root.findall(".//*[defName]")
            logging.debug(f"在 {xml_file} 中找到 {len(def_nodes)} 个 defName 节点")
            for def_node in def_nodes:
                def_type = def_node.tag
                def_name = def_node.find("defName")
                if def_name is None or not def_name.text:
                    logging.warning(f"在 {xml_file} 未找到 defName，跳过")
                    continue
                def_name_text = def_name.text
                translations = extract_translatable_fields(def_node)
                logging.debug(f"在 {def_name_text} 找到 {len(translations)} 个翻译字段")
                for field_path, text, tag in translations:
                    # 移除路径中的 defType（父标签）
                    # 只保留 defName 作为前缀，后面跟真正的字段路径（去掉 BackstoryDef. 前缀）
                    clean_path = field_path
                    if clean_path.startswith(def_type + "."):
                        clean_path = clean_path[len(def_type) + 1:]
                    full_path = f"{def_type}/{def_name_text}.{clean_path}"
                    all_translations.append((full_path, text, tag, str(xml_file)))
        except ET.ParseError as e:
            logging.error(f"XML 语法错误 {xml_file}: {e}")
            continue
        except Exception as e:
            logging.error(f"无法解析 {xml_file}: {e}")
            continue

    if not all_translations:
        logging.info("未找到可翻译字段")
        print("未找到可翻译字段。")
        return []

    if PREVIEW_TRANSLATABLE_FIELDS:
        def parse_indices(input_str, total):
            """解析用户输入的编号字符串，支持范围和逗号分隔"""
            indices = set()
            for part in input_str.split(','):
                part = part.strip()
                if '-' in part:
                    try:
                        start, end = part.split('-')
                        indices.update(range(int(start)-1, int(end)))
                    except Exception:
                        continue
                elif part.isdigit():
                    indices.add(int(part)-1)
            return {i for i in indices if 0 <= i < total}

        selected = set(range(len(all_translations)))
        while True:
            print(f"\n=== 可翻译字段（共{len(all_translations)}，已选{len(selected)}）===")
            for i, (full_path, text, tag, _) in enumerate(all_translations, 1):
                mark = "√" if i-1 in selected else " "
                print(f"{mark}{i}. 路径: {full_path}")
                print(f"   标签: {tag}")
                print(f"   内容: {text}")
                print("-" * 50)
            print("\n操作说明：a=全选，n=全不选，r=反选，直接回车=确认，或输入排除/选择编号（如1-5,8,10），前加-为排除，+为选择")
            user_input = input("> ").strip().lower()
            if user_input == '':
                break
            elif user_input == 'a':
                selected = set(range(len(all_translations)))
            elif user_input == 'n':
                selected = set()
            elif user_input == 'r':
                selected = set(range(len(all_translations))) - selected
            elif user_input.startswith('-'):
                indices = parse_indices(user_input[1:], len(all_translations))
                selected -= indices
            elif user_input.startswith('+'):
                indices = parse_indices(user_input[1:], len(all_translations))
                selected |= indices
            else:
                # 默认排除
                indices = parse_indices(user_input, len(all_translations))
                selected -= indices
            print(f"当前已选 {len(selected)} 个字段。")

        return [all_translations[i] for i in sorted(selected)]
    else:
        # 直接返回所有字段，不再确认
        return all_translations

def extract_key(mod_root_dir, export_dir, active_language="ChineseSimplified", english_language="English"):
    """
    提取 Keyed 类型的翻译文件。
    作用：
    - 读取英文 Keyed 目录下的所有 xml 文件，复制到导出目录下的对应 Keyed 目录。
    - 在每个字段前插入英文原文注释，方便后续翻译。
    - 只在 export_dir 下写入和清理，不影响原始 mod 目录。
    参数：
    - mod_root_dir: 原始 mod 根目录（只读）
    - export_dir: 导出目录（所有写入都在这里）
    - active_language: 目标语言（默认 ChineseSimplified）
    - english_language: 英文目录名（默认 English）
    """
    active_lang_path = get_language_folder_path(active_language, export_dir)
    english_lang_path = get_language_folder_path(english_language, mod_root_dir)

    keyed_path = os.path.join(active_lang_path, "Keyed")
    old_keyed_path = os.path.join(active_lang_path, "CodeLinked")

    if os.path.exists(old_keyed_path) and not os.path.exists(keyed_path):
        try:
            shutil.move(old_keyed_path, keyed_path)
            time.sleep(1)
            logging.info(f"重命名 {old_keyed_path} 为 {keyed_path}")
        except Exception as e:
            logging.error(f"无法重命名 {old_keyed_path}: {e}")

    if not os.path.exists(keyed_path):
        os.makedirs(keyed_path)
        logging.info(f"创建文件夹：{keyed_path}")

    english_keyed_path = os.path.join(english_lang_path, "Keyed")

    if not os.path.exists(english_keyed_path) and "Core" not in mod_root_dir:
        logging.warning(f"英文 Keyed 目录 {english_keyed_path} 不存在，跳过")
        return

    for xml_file in Path(keyed_path).rglob("*.xml"):
        try:
            os.remove(xml_file)
            logging.info(f"删除文件：{xml_file}")
        except Exception as e:
            logging.error(f"无法删除 {xml_file}: {e}")

    if os.path.exists(english_keyed_path):
        for src_file in Path(english_keyed_path).rglob("*.xml"):
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
                        # 字段内容保留原文
                        comment = ET.Comment(sanitize_xcomment(f" EN: {original} "))
                        parent = parent_map.get(elem)
                        if parent is not None:
                            idx = list(parent).index(elem)
                            parent.insert(idx, comment)
                save_xml_to_file(root, dst_file)
            except Exception as e:
                logging.error(f"无法处理 {src_file}: {e}")

def extract_definjected_from_defs(mod_root_dir, export_dir, active_language="ChineseSimplified"):
    """
    从 Defs 目录递归提取所有可翻译字段，生成 DefInjected 结构的 xml 文件。
    作用：
    - 只读取 mod_root_dir/Defs 下的 xml 文件。
    - 根据字段筛选和用户选择，生成 DefInjected 目录下的翻译模板。
    - 只在 export_dir 下写入和清理，不影响原始 mod 目录。
    参数：
    - mod_root_dir: 原始 mod 根目录（只读）
    - export_dir: 导出目录（所有写入都在这里）
    - active_language: 目标语言（默认 ChineseSimplified）
    """
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
        except Exception as e:
            logging.error(f"无法删除 {xml_file}: {e}")

    if not os.path.exists(defs_path):
        logging.warning(f"Defs 目录 {defs_path} 不存在，跳过")
        return

    selected_translations = preview_translatable_fields(mod_root_dir, preview=PREVIEW_TRANSLATABLE_FIELDS)
    if not selected_translations:
        if PREVIEW_TRANSLATABLE_FIELDS:
            print("未选择字段，跳过生成。")
        return

    def_injections = {}

    for xml_file in Path(defs_path).rglob("*.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            rel_path = os.path.relpath(xml_file, defs_path)  # 计算相对路径
            output_path = os.path.join(def_injected_path, rel_path)

            for def_node in root.findall(".//*[defName]"):
                def_type = def_node.tag
                def_name = def_node.find("defName")
                if def_name is None or not def_name.text:
                    continue

                def_name_text = def_name.text
                translations = extract_translatable_fields(def_node)
                logging.debug(f"提取 {def_name_text} 的字段：{translations}")
                filtered_translations = []
                prefix = f"{def_type}/{def_name_text}."
                for full_path, text, tag, file_path in selected_translations:
                    if str(file_path) == str(xml_file) and full_path.startswith(prefix):
                        field_path = full_path[len(prefix):]
                        filtered_translations.append((field_path, text, tag))
                logging.debug(f"过滤字段：{filtered_translations}")
                if not filtered_translations:
                    continue
                # 以 output_path 作为 key，直接导出到 DefInjected 下的相对路径
                if output_path not in def_injections:
                    def_injections[output_path] = []
                def_injections[output_path].append((def_name_text, filtered_translations))

        except ET.ParseError as e:
            logging.error(f"XML 语法错误 {xml_file}: {e}")
            continue
        except Exception as e:
            logging.error(f"无法解析 {xml_file}: {e}")
            continue

    logging.debug(f"Def Injections: {def_injections}")

    for output_path, defs in def_injections.items():
        root = ET.Element("LanguageData")
        for def_name, translations in defs:
            if not translations:
                continue
            for field_path, text, tag in translations:
                # 去掉 field_path 前缀中的 defType（如 BackstoryDef.）
                clean_path = field_path
                # 这里 def_type 变量不可用，但 clean_path 已经是去掉前缀的
                full_path = f"{def_name}.{clean_path}"
                comment = ET.Comment(sanitize_xcomment(f" EN: {text} "))
                root.append(comment)
                field_elem = ET.SubElement(root, full_path)
                field_elem.text = text
        save_xml_to_file(root, output_path)

def extract_translate(mod_root_dir, export_dir, active_language="ChineseSimplified", english_language="English"):
    """
    提取 DefInjected 类型的翻译文件。
    作用：
    - 检查英文 DefInjected 目录是否存在，若存在可选择以英文为模板或重新提取。
    - 复制英文 DefInjected 下的 xml 文件到导出目录，并插入英文注释。
    - 或直接调用 extract_definjected_from_defs 重新生成。
    - 只在 export_dir 下写入和清理，不影响原始 mod 目录。
    参数：
    - mod_root_dir: 原始 mod 根目录（只读）
    - export_dir: 导出目录（所有写入都在这里）
    - active_language: 目标语言（默认 ChineseSimplified）
    - english_language: 英文目录名（默认 English）
    """
    active_lang_path = get_language_folder_path(active_language, export_dir)
    def_injected_path = os.path.join(active_lang_path, "DefInjected")
    old_def_linked_path = os.path.join(active_lang_path, "DefLinked")

    if os.path.exists(old_def_linked_path) and not os.path.exists(def_injected_path):
        try:
            shutil.move(old_def_linked_path, def_injected_path)
            time.sleep(1)
            logging.info(f"重命名 {old_def_linked_path} 为 {def_injected_path}")
        except Exception as e:
            logging.error(f"无法重命名：{e}")

    english_lang_path = get_language_folder_path(english_language, mod_root_dir)
    english_def_injected_path = os.path.join(english_lang_path, "DefInjected")

    if os.path.exists(english_def_injected_path):
        print("检测到英文 DefInjected 目录。请选择处理方式：")
        print("1. 以英文 DefInjected 为基础（推荐用于已有翻译结构的情况）")
        print("2. 直接从 Defs 目录重新提取可翻译字段（推荐用于结构有变动或需全量提取时）")
        choice = input("请输入选项编号（1/2，回车默认1）：").strip()
        if choice == '2':
            logging.info("用户选择：从 Defs 目录重新提取可翻译字段")
            extract_definjected_from_defs(mod_root_dir, export_dir, active_language)
            return
        else:
            logging.info("用户选择：以英文 DefInjected 为基础")
            if not os.path.exists(def_injected_path):
                os.makedirs(def_injected_path)
                logging.info(f"创建文件夹：{def_injected_path}")
            for xml_file in Path(def_injected_path).rglob("*.xml"):
                try:
                    os.remove(xml_file)
                    logging.info(f"删除文件：{xml_file}")
                except Exception as e:
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
                            # 字段内容保留原文
                            comment = ET.Comment(sanitize_xcomment(f" EN: {original} "))
                            parent = parent_map.get(elem)
                            if parent is not None:
                                idx = list(parent).index(elem)
                                parent.insert(idx, comment)
                    save_xml_to_file(root, dst_file)
                except Exception as e:
                    logging.error(f"无法处理 {src_file}: {e}")
    else:
        logging.info(f"未找到英文 DefInjected {english_def_injected_path}，从 Defs 提取")
        extract_definjected_from_defs(mod_root_dir, export_dir, active_language)


def cleanup_backstories(mod_root_dir, export_dir, active_language="ChineseSimplified"):
    """
    清理旧的 Backstories 目录。
    作用：
    - 只在导出目录下查找 Backstories 文件夹，如存在则重命名为 Backstories DELETE_ME，提示用户手动检查。
    - 不影响原始 mod 目录。
    参数：
    - mod_root_dir: 原始 mod 根目录（只读）
    - export_dir: 导出目录（所有写入都在这里）
    - active_language: 目标语言（默认 ChineseSimplified）
    """
    active_lang_path = get_language_folder_path(active_language, export_dir)
    backstories_path = os.path.join(active_lang_path, "Backstories")

    if os.path.exists(backstories_path):
        delete_me_path = os.path.join(active_lang_path, "Backstories DELETE_ME")
        try:
            shutil.move(backstories_path, delete_me_path)
            logging.info(f"重命名背景故事为 {delete_me_path}")
            print(f"背景故事文件夹重命名为 {delete_me_path}，请检查并删除")
        except Exception as e:
            logging.error(f"无法重命名 {backstories_path}: {e}")

def main():
    """
    主函数，程序入口。
    作用：
    - 交互式输入原始 mod 路径和导出目录。
    - 调用 extract_translate、extract_key、cleanup_backstories 完成翻译文件的提取和清理。
    - 自动导出所有可翻译字段到 extracted_translations.csv，便于后续人工翻译或校对。
    - 所有写入和生成都只发生在导出目录，不影响原始 mod。
    """
    print("=== RimWorld 模组翻译提取工具 ===")
    print("请输入模组根目录路径（例如：C:/RimWorld/Mods/MyMod）：")
    mod_root_dir = input("> ").strip()
    if not os.path.exists(mod_root_dir):
        print("错误：模组路径不存在！")
        logging.error(f"模组路径不存在：{mod_root_dir}")
        return

    print("请输入导出目标文件夹路径（如 D:/output 或留空则为当前目录）：")
    export_dir = input("> ").strip()
    if not export_dir:
        export_dir = os.getcwd()
    if not os.path.exists(export_dir):
        try:
            os.makedirs(export_dir)
            print(f"已创建导出目录：{export_dir}")
        except Exception as e:
            print(f"无法创建导出目录：{e}")
            logging.error(f"无法创建导出目录：{export_dir}，错误：{e}")
            return

    # 复制整个 Languages 目录到目标文件夹
    #import shutil
    #src_languages = os.path.join(mod_root_dir, "Languages")
    #dst_languages = os.path.join(export_dir, "Languages")
    #if os.path.exists(src_languages):
    #    if os.path.exists(dst_languages):
    #        shutil.rmtree(dst_languages)
    #    shutil.copytree(src_languages, dst_languages)

    print("开始提取翻译...")
    try:
        # 下面三个函数需要以 mod_root_dir 作为根目录，所有写入都在 export_dir
        extract_translate(mod_root_dir, export_dir)
        extract_key(mod_root_dir, export_dir)
        cleanup_backstories(mod_root_dir, export_dir)

        # 自动导出所有可翻译字段到 extracted_translations.csv（含 DefInjected 和 Keyed）
        csv_path = os.path.join(export_dir, "extracted_translations.csv")
        all_translations = preview_translatable_fields(mod_root_dir, preview=False)
        import csv
        # Keyed 导出
        keyed_dir = os.path.join(export_dir, "Languages", "English", "Keyed")
        keyed_rows = []
        if os.path.exists(keyed_dir):
            from pathlib import Path
            for xml_file in Path(keyed_dir).rglob("*.xml"):
                try:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    for elem in root:
                        if elem.tag is ET.Comment:
                            continue
                        if elem.text and elem.text.strip():
                            keyed_rows.append((elem.tag, elem.text.strip(), elem.tag))
                except Exception as e:
                    logging.error(f"Keyed导出失败: {xml_file}: {e}")

        with open(csv_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag"])
            # DefInjected
            for full_path, text, tag, _ in all_translations:
                writer.writerow([full_path, text, tag])
            # Keyed
            for key, text, tag in keyed_rows:
                writer.writerow([key, text, tag])
        print(f"已自动导出所有可翻译字段到 {csv_path}")
        logging.info(f"已自动导出所有可翻译字段到 {csv_path}")

        print("翻译提取完成！请检查导出文件夹。")
        logging.info("翻译提取完成")
    except Exception as e:
        print(f"提取错误：{e}")
        logging.error(f"提取错误：{e}")

if __name__ == "__main__":
    main()