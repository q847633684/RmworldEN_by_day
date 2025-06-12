import os
import shutil
import xml.etree.ElementTree as ET
import re
from pathlib import Path
import logging
import time

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 默认可翻译字段
DEFAULT_FIELDS = [
    'label', 'description', 'baseDesc', 'title', 'titleShort',
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
    'becomeVisible', 'rulePack', 'retro'
]

# 正则表达式过滤器
NON_TEXT_PATTERNS = [
    r'^\s*\(\s*\d+\s*,\s*[\d*\.]+\s*\)\s*$',  # 坐标对
    r'^\s*\d+\s*$',                          # 纯数字
    r'^\s*(true|false)\s*$',                  # 布尔值
    r'^\s*[A-Za-z0-9_]+\s*$'                  # 单单词标识符
]

def get_language_folder_path(language, mod_root_dir):
    """获取语言文件夹路径"""
    return os.path.join(mod_root_dir, language, "Languages")

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
    if len(text.strip().split()) == 1 and not any(c.isspace() for c in text.strip()):
        logging.debug(f"排除单单词：{text}")
        return False
    logging.debug(f"包含多词文本：{text}")
    return True

def extract_translatable_fields(node, path="", list_indices=None, translations=None):
    """递归提取可翻译字段"""
    if list_indices is None:
        list_indices = {}
    if translations is None:
        translations = []

    node_tag = node.tag
    current_path = f"{path}.{node_tag}" if path else node_tag

    if node_tag in ('li', 'stage', 'step', 'points'):
        parent_tag = node_tag
        if parent_tag in list_indices:
            list_indices[parent_tag] += 1
        else:
            list_indices[parent_tag] = 0
        current_path = f"{path}.{list_indices[parent_tag]}" if path else str(list_indices[parent_tag])

    if node.text and is_translatable_text(node.text, node_tag):
        translations.append((current_path, node.text, node_tag))

    for child in node:
        child_indices = list_indices.copy()
        extract_translatable_fields(child, current_path, child_indices, translations)

    return translations

def preview_translatable_fields(mod_root_dir):
    """预览可翻译字段"""
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
                    full_path = f"{def_type}/{def_name_text}.{field_path}"
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

    print("\n=== 可翻译字段 ===")
    for i, (full_path, text, tag, _) in enumerate(all_translations, 1):
        print(f"{i}. 路径: {full_path}")
        print(f"   标签: {tag}")
        print(f"   内容: {text}")
        print("-" * 50)

    print("\n确认所有字段？（y/n，或输入排除编号，用逗号分隔）")
    user_input = input("> ").strip().lower()

    if user_input == 'y':
        return all_translations
    elif user_input == 'n':
        return []
    else:
        try:
            exclude_indices = [int(x.strip()) - 1 for x in user_input.split(',')]
            return [t for i, t in enumerate(all_translations) if i not in exclude_indices]
        except ValueError:
            print("输入无效，使用所有字段。")
            return all_translations

def extract_key(mod_root_dir, active_language="ChineseSimplified", english_language="English"):
    """提取翻译键文件"""
    active_lang_path = get_language_folder_path(active_language, mod_root_dir)
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
                for elem in root.findall(".//*"):
                    if elem.text and elem.text.strip():
                        comment = ET.Comment(sanitize_xcomment(f" EN: {elem.text} "))
                        root.append(comment)
                save_xml_to_file(root, dst_file)
            except Exception as e:
                logging.error(f"无法处理 {src_file}: {e}")

def extract_definjected_from_defs(mod_root_dir, active_language="ChineseSimplified"):
    """从 Defs 提取可翻译字段"""
    active_lang_path = get_language_folder_path(active_language, mod_root_dir)
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
    
    selected_translations = preview_translatable_fields(mod_root_dir)
    if not selected_translations:
        print("未选择字段，跳过生成。")
        return
    
    def_injections = {}
    
    for xml_file in Path(defs_path).rglob("*.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            for def_node in root.findall(".//*[defName]"):
                def_type = def_node.tag
                def_name = def_node.find("defName")
                if def_name is None or not def_name.text:
                    continue
                
                def_name_text = def_name.text
                translations = extract_translatable_fields(def_node)
                logging.debug(f"提取 {def_name_text} 的字段：{translations}")
                filtered_translations = [
                    (field_path, text, tag) for full_path, text, tag, file_path in selected_translations
                    if str(file_path) == str(xml_file) and full_path == f"{def_type}/{def_name_text}.{field_path}"
                ]
                logging.debug(f"过滤字段：{filtered_translations}")
                
                if filtered_translations:
                    output_dir = def_injected_path
                    def_type_short = def_type
                    if '.' in def_type:
                        namespace = def_type.split('.')[0]
                        def_type_short = def_type.split('.')[-1]
                        output_dir = os.path.join(def_injected_path, namespace, def_type_short)
                    else:
                        output_dir = os.path.join(def_injected_path, def_type)
                    
                    output_filename = os.path.basename(xml_file)
                    
                    if output_filename not in def_injections:
                        def_injections[output_filename] = []
                    def_injections[output_filename].append((def_name_text, filtered_translations, output_dir))
        
        except ET.ParseError as e:
            logging.error(f"XML 语法错误 {xml_file}: {e}")
            continue
        except Exception as e:
            logging.error(f"无法解析 {xml_file}: {e}")
            continue
    
    logging.debug(f"Def Injections: {def_injections}")
    
    for output_filename, defs in def_injections.items():
        root = ET.Element("LanguageData")
        for def_name, translations, output_dir in defs:
            for field_path, text, tag in translations:
                if tag == 'rulesStrings':
                    full_path = f"{def_name}.{field_path}"
                else:
                    field_name = field_path.split('.')[-1]
                    full_path = f"{def_name}.{field_name}"
                field_elem = ET.SubElement(root, full_path)
                field_elem.text = text
                comment = ET.Comment(sanitize_xcomment(f" EN: {text} "))
                root.append(comment)
        
        output_path = os.path.join(output_dir, output_filename)
        save_xml_to_file(root, output_path)

def extract_translate(mod_root_dir, active_language="ChineseSimplified", english_language="English"):
    """提取翻译文件"""
    active_lang_path = get_language_folder_path(active_language, mod_root_dir)
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
        logging.info(f"找到英文 DefInjected {english_def_injected_path}，优先处理")
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
                for elem in root.findall(".//*"):
                    if elem.text and elem.text.strip():
                        comment = ET.Comment(sanitize_xcomment(f" EN: {elem.text} "))
                        root.append(comment)
                save_xml_to_file(root, dst_file)
            except Exception as e:
                logging.error(f"无法处理 {src_file}: {e}")
    else:
        logging.info(f"未找到英文 DefInjected {english_def_injected_path}，从 Defs 提取")
        extract_definjected_from_defs(mod_root_dir, active_language)

def cleanup_backstories(mod_root_dir, active_language="ChineseSimplified"):
    """清理旧背景故事文件"""
    active_lang_path = get_language_folder_path(active_language, mod_root_dir)
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
    """主函数"""
    print("=== RimWorld 模组翻译提取工具 ===")
    print("请输入模组根目录路径（例如：C:/RimWorld/Mods/MyMod）：")
    mod_root_dir = input("> ").strip()
    if not os.path.exists(mod_root_dir):
        print("错误：模组路径不存在！")
        logging.error(f"模组路径不存在：{mod_root_dir}")
        return
    
    print("开始提取翻译...")
    try:
        extract_translate(mod_root_dir)
        extract_key(mod_root_dir)
        cleanup_backstories(mod_root_dir)
        print("翻译提取完成！请检查 Languages 文件夹。")
        logging.info("翻译提取完成")
    except Exception as e:
        print(f"提取错误：{e}")
        logging.error(f"提取错误：{e}")

if __name__ == "__main__":
    main()