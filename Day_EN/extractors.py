from typing import List, Tuple, Set
from pathlib import Path
from .config import PREVIEW_TRANSLATABLE_FIELDS
from .utils import get_language_folder_path
from .fields import extract_translatable_fields
from .exporters import export_keyed, export_definjected
# 预览可翻译字段
def preview_translatable_fields(
    mod_root_dir: str,
    preview: bool = PREVIEW_TRANSLATABLE_FIELDS
) -> List[Tuple[str, str, str, str]]:
    import os
    import xml.etree.ElementTree as ET
    logging.info(f"扫描 Defs 目录：{os.path.join(mod_root_dir, 'Defs')}")
    print(f"扫描 Defs 目录：{os.path.join(mod_root_dir, 'Defs')}")
    defs_path = os.path.join(mod_root_dir, "Defs")
    if not os.path.exists(defs_path):
        logging.warning(f"Defs 目录 {defs_path} 不存在")
        return []
    all_translations: List[Tuple[str, str, str, str]] = []
    # 遍历所有 XML 文件
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
    if preview:
        # 预览模式，允许用户选择翻译字段
        def parse_indices(input_str: str, total: int) -> Set[int]:
            """解析用户输入的编号字符串，支持范围和逗号分隔。"""
            indices: Set[int] = set()
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
        selected: Set[int] = set(range(len(all_translations)))
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
                indices = parse_indices(user_input, len(all_translations))
                selected -= indices
            print(f"当前已选 {len(selected)} 个字段。")
        return [all_translations[i] for i in sorted(selected)]
    else:
        return all_translations

# 高层调度函数，提取 Keyed 类型的翻译文件,只做 Keyed 目录的复制和注释
def extract_key(
    mod_root_dir: str,
    export_dir: str,
    active_language: str = "ChineseSimplified",
    english_language: str = "English"
) -> None:
    from .exporters import export_keyed
    export_keyed(
        mod_root_dir=mod_root_dir,
        export_dir=export_dir,
        active_language=active_language,
        english_language=english_language
    )
# 高层调度函数，提取 DefInjected 类型的翻译文件,从 Defs 目录递归提取所有可翻译字段，生成 DefInjected 结构的 xml 文件。
def extract_definjected_from_defs(
    mod_root_dir: str,
    export_dir: str,
    active_language: str = "ChineseSimplified"
) -> None:
    selected_translations = preview_translatable_fields(mod_root_dir, preview=PREVIEW_TRANSLATABLE_FIELDS)
    if not selected_translations:
        if PREVIEW_TRANSLATABLE_FIELDS:
            print("未选择字段，跳过生成。")
        return
    from .exporters import export_definjected
    export_definjected(
        mod_root_dir=mod_root_dir,
        export_dir=export_dir,
        selected_translations=selected_translations,
        active_language=active_language
    )
# 高层调度函数，提取 DefInjected 类型的翻译文件（包括 Keyed 和 DefInjected）据用户选择，决定是用英文 DefInjected 目录为基础，还是从 Defs 目录全量提取。
def extract_translate(
    mod_root_dir: str,
    export_dir: str,
    active_language: str = "ChineseSimplified",
    english_language: str = "English"
) -> None:
    from .exporters import handle_extract_translate
    handle_extract_translate(
        mod_root_dir=mod_root_dir,
        export_dir=export_dir,
        active_language=active_language,
        english_language=english_language,
        extract_definjected_from_defs=extract_definjected_from_defs
    )
# 高层调度函数，清理旧的 Backstories 目录
def cleanup_backstories(
    mod_root_dir: str,
    export_dir: str,
    active_language: str = "ChineseSimplified"
) -> None:
    from .exporters import cleanup_backstories_dir
    cleanup_backstories_dir(
        mod_root_dir=mod_root_dir,
        export_dir=export_dir,
        active_language=active_language
    )