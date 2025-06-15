from typing import List, Tuple, Set
import logging
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from functools import lru_cache
import asyncio
import aiofiles
from ..utils.config import TranslationConfig
from ..utils.utils import get_language_folder_path
from ..utils.fields import extract_translatable_fields
from .exporters import export_keyed, export_definjected

CONFIG = TranslationConfig()

@lru_cache(maxsize=1)
def preview_translatable_fields(
    mod_dir: str,
    preview: bool = CONFIG.preview_translatable_fields
) -> List[Tuple[str, str, str, str]]:
    """
    扫描 Defs 目录，提取可翻译字段。

    Args:
        mod_dir: 模组根目录
        preview: 是否交互式预览字段

    Returns:
        List of tuples (full_path, text, tag, file_path)
    """
    logging.info(f"扫描 Defs 目录：{os.path.join(mod_dir, 'Defs')}")
    print(f"扫描 Defs 目录：{os.path.join(mod_dir, 'Defs')}")
    defs_path = Path(mod_dir) / "Defs"
    if not defs_path.exists():
        logging.warning(f"Defs 目录 {defs_path} 不存在")
        return []

    async def read_xml(file: Path) -> List[Tuple[str, str, str, str]]:
        """异步读取并解析 XML 文件"""
        translations = []
        try:
            async with aiofiles.open(file, encoding="utf-8") as f:
                content = await f.read()
            tree = ET.fromstring(content)
            def_nodes = tree.findall(".//*[defName]")
            for def_node in def_nodes:
                def_type = def_node.tag
                def_name = def_node.find("defName")
                if def_name is None or not def_name.text:
                    logging.debug(f"在 {file} 未找到 defName，跳过")
                    continue
                def_name_text = def_name.text
                fields = extract_translatable_fields(def_node)
                for field_path, text, tag in fields:
                    clean_path = field_path
                    if clean_path.startswith(f"{def_type}."):
                        clean_path = clean_path[len(def_type) + 1:]
                    full_path = f"{def_type}/{def_name_text}.{clean_path}"
                    translations.append((full_path, text, tag, str(file)))
        except ET.ParseError as e:
            logging.error(f"XML 语法错误 {file}: {e}")
        except OSError as e:
            logging.error(f"无法读取 {file}: {e}")
        return translations

    async def scan_defs() -> List[Tuple[str, str, str, str]]:
        """异步扫描 Defs 目录"""
        all_translations = []
        tasks = [read_xml(file) for file in defs_path.rglob("*.xml")]
        for task in await asyncio.gather(*tasks):
            all_translations.extend(task)
        return all_translations

    all_translations = asyncio.run(scan_defs())
    if not all_translations:
        logging.info("未找到可翻译字段")
        print("未找到可翻译字段。")
        return []

    if preview:
        def parse_indices(input_str: str, total: int) -> Set[int]:
            indices = set()
            for part in input_str.split(","):
                part = part.strip()
                if "-" in part:
                    try:
                        start, end = part.split("-")
                        indices.update(range(int(start) - 1, int(end)))
                    except ValueError:
                        continue
                elif part.isdigit():
                    indices.add(int(part) - 1)
            return {i for i in indices if 0 <= i < total}

        selected = set(range(len(all_translations)))
        while True:
            print(f"\n=== 可翻译字段（共{len(all_translations)}，已选{len(selected)}）===")
            for i, (full_path, text, tag, _) in enumerate(all_translations, 1):
                mark = "√" if i - 1 in selected else " "
                print(f"{mark}{i}. 路径: {full_path}")
                print(f"   标签: {tag}")
                print(f"   内容: {text}")
                print("-" * 50)
            print("\n操作说明：a=全选，n=全不选，r=反选，直接回车=确认，或输入排除/选择编号（如1-5,8,10），前加-为排除，+为选择")
            user_input = input("> ").strip().lower()
            if user_input == "":
                break
            elif user_input == "a":
                selected = set(range(len(all_translations)))
            elif user_input == "n":
                selected = set()
            elif user_input == "r":
                selected = set(range(len(all_translations))) - selected
            elif user_input.startswith("-"):
                indices = parse_indices(user_input[1:], len(all_translations))
                selected -= indices
            elif user_input.startswith("+"):
                indices = parse_indices(user_input[1:], len(all_translations))
                selected |= indices
            else:
                indices = parse_indices(user_input, len(all_translations))
                selected -= indices
            print(f"当前已选 {len(selected)} 个字段。")
        return [all_translations[i] for i in sorted(selected)]
    return all_translations

def extract_key(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language
) -> None:
    """提取 Keyed 翻译"""
    logging.info(f"提取 Keyed 翻译: mod_dir={mod_dir}, export_dir={export_dir}")
    try:
        export_keyed(
            mod_dir=mod_dir,
            export_dir=export_dir,
            language=language,
            source_language=source_language
        )
    except (ET.ParseError, OSError) as e:
        logging.error(f"提取 Keyed 翻译失败: {e}")

def extract_definjected_from_defs(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language
) -> None:
    """从 Defs 提取 DefInjected 翻译"""
    selected_translations = preview_translatable_fields(mod_dir, preview=CONFIG.preview_translatable_fields)
    if not selected_translations:
        if CONFIG.preview_translatable_fields:
            print("未选择字段，跳过生成。")
        return
    try:
        export_definjected(
            mod_dir=mod_dir,
            export_dir=export_dir,
            selected_translations=selected_translations,
            language=language
        )
    except (ET.ParseError, OSError) as e:
        logging.error(f"提取 DefInjected 翻译失败: {e}")

def extract_translate(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language
) -> None:
    """提取所有翻译"""
    from .exporters import handle_extract_translate
    try:
        handle_extract_translate(
            mod_dir=mod_dir,
            export_dir=export_dir,
            language=language,
            source_language=source_language,
            extract_definjected_from_defs=extract_definjected_from_defs
        )
    except (ET.ParseError, OSError) as e:
        logging.error(f"提取翻译失败: {e}")