"""
模板管理器

负责翻译模板的完整生命周期管理，协调各个组件完成复杂的翻译提取和生成流程
"""

import csv
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from user_config import UserConfigManager
from user_config.path_manager import PathManager
from utils.logging_config import (get_logger, log_data_processing,
                                  log_user_action)
from utils.ui_style import ui
from utils.utils import sanitize_xml

from ..core.exporters import DefInjectedExporter, KeyedExporter
from ..core.extractors import DefInjectedExtractor, DefsScanner, KeyedExtractor
from ..utils import SmartMerger


def find_content_roots(
    base_path: str, language: Optional[str] = None
) -> List[str]:
    """
    发现所有「内容根目录」：含 Defs 的目录 + 含 Languages/<lang>/Keyed 或 DefInjected 的目录。
    统一逻辑：从某目录提取的 Defs/Keyed 都放在该目录下的 Languages，每个内容根自包含。

    Args:
        base_path: 模组根或版本目录（如 workshop/3232074807 或 3232074807/1.6）
        language: 用于检测 Languages 的语言名（如 English），未传则用配置的 en_language

    Returns:
        去重且排序的路径列表，每个路径为「内容根」（该目录下 Defs 或 Languages 将参与提取/输出）
    """
    base = Path(base_path)
    if not base.is_dir():
        return []
    roots = set()
    # 1) 含 Defs 的目录
    for p in base.rglob("Defs"):
        if p.is_dir():
            roots.add(p.parent)
    # 2) 含 Languages/<lang>/Keyed 或 DefInjected 的目录（Keyed 与 Defs 同逻辑：在哪就在同目录下 Languages）
    config = UserConfigManager.get_instance()
    if language is None:
        try:
            language = config.language_config.get_value(
                "en_language", "English"
            )
        except Exception:
            language = "English"
    keyed_dir_name = config.language_config.get_value("keyed_dir", "Keyed")
    definjected_dir_name = config.language_config.get_value(
        "definjected_dir", "DefInjected"
    )
    lang_lower = language.lower()
    for subdir_name in (keyed_dir_name, definjected_dir_name):
        for p in base.rglob(subdir_name):
            if not p.is_dir():
                continue
            try:
                # 期望结构: .../Languages/<lang>/Keyed（语言名不区分大小写）
                if p.parent.name.lower() != lang_lower:
                    continue
                grandparent_name = p.parent.parent.name
                # 标准：.../Languages/English/Keyed -> 内容根 = Languages 的上级（不会出现 root/语言/Keyed 无 Languages 层）
                if grandparent_name.lower() == "languages":
                    roots.add(p.parent.parent.parent)
            except (IndexError, AttributeError):
                continue
    return sorted(str(r) for r in roots)


def _parse_load_folders_from_mod(
    mod_dir: str, version: str = "1.6"
) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    """
    从原 mod 的 LoadFolders.xml 解析指定版本块：路径→属性，以及原始顺序的路径列表。
    只包含原文件中出现的路径，未在原 LoadFolders 中的目录（如 Source、RimJobWorld/Source）不应写入生成文件。

    Args:
        mod_dir: 模组根目录（其下应有 LoadFolders.xml）
        version: 版本块名，如 "1.6" -> 解析 <v1.6> 内的 <li>

    Returns:
        (path_to_attrib, ordered_paths)
        - path_to_attrib: 路径(归一化) -> { "IfModActive"/"IfModNotActive": "..." }，仅包含有属性的项
        - ordered_paths: 原文件中该版本块内 <li> 的路径顺序（归一化后），用于生成时只输出原 mod 里有的项
    """
    xml_path = Path(mod_dir) / "LoadFolders.xml"
    path_to_attrib: Dict[str, Dict[str, str]] = {}
    ordered_paths: List[str] = []
    if not xml_path.is_file():
        return path_to_attrib, ordered_paths
    version_tag = f"v{version}" if not version.startswith("v") else version
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        version_elem = root.find(version_tag)
        if version_elem is None:
            return path_to_attrib, ordered_paths
        for li in version_elem.findall("li"):
            path = (li.text or "").strip()
            if not path:
                continue
            key = path.replace("\\", "/")
            ordered_paths.append(key)
            attrib = {
                k: v
                for k, v in li.attrib.items()
                if k in ("IfModActive", "IfModNotActive")
            }
            if attrib:
                path_to_attrib[key] = attrib
    except (ET.ParseError, OSError, IOError):
        pass
    return path_to_attrib, ordered_paths


def _path_is_strict_under(path: str, ancestor: str) -> bool:
    """path 是否严格位于 ancestor 之下（ancestor 为 path 的祖先且 path != ancestor）。"""
    if path == ancestor:
        return False
    try:
        Path(path).resolve().relative_to(Path(ancestor).resolve())
        return True
    except ValueError:
        return False


def get_content_roots_from_load_folders(
    scan_base: str, version: str
) -> List[str]:
    """
    从 LoadFolders.xml 的指定版本块（如 v1.6）读取要加载的路径，作为内容根列表。
    与游戏实际加载的目录一致；仅排除「某路径下的 Languages 子目录」作为内容根
    （如存在 1.6 时排除 1.6/Languages），避免重复提取。与 1.6 同级的路径（如 Biotech）
    保留为独立内容根，各自 Defs/Keyed 写入各自目录下的 Languages。

    Args:
        scan_base: 模组根目录（其下应有 LoadFolders.xml）
        version: 版本名，如 "1.6" -> 解析 <v1.6> 内的 <li>

    Returns:
        存在的绝对路径列表 [scan_base/1.6, scan_base/Biotech, ...]，仅去掉 xxx/Languages
    """
    _, ordered_paths = _parse_load_folders_from_mod(scan_base, version)
    base = Path(scan_base)
    result = []
    for p in ordered_paths:
        # <li>/</li> 表示模组根：归一化为 base，避免 Windows 下 base / "/" 变成盘符
        p_norm = (p or "").strip().replace("\\", "/")
        if p_norm in ("", "/", "."):
            full = base
        else:
            full = base / p_norm.replace("/", os.sep)
        if full.exists() and full.is_dir():
            result.append(str(full.resolve()))
    # 只排除「某路径下的 Languages 子目录」作为内容根，避免 1.6 与 1.6/Languages 同时作为根；
    # 与 1.6 同级的路径（如 Biotech）保留为独立内容根
    result = [
        r for r in result
        if not any(
            _path_is_strict_under(r, s) and Path(r).name.lower() == "languages"
            for s in result
            if s != r
        )
    ]
    return result


def generate_load_folders_xml(
    output_dir: str,
    folder_names: List[str],
    version: str = "1.6",
    mod_dir: Optional[str] = None,
) -> Optional[Path]:
    """
    在输出目录生成 LoadFolders.xml，供外部导出时让 RimWorld 正确加载子目录。
    若提供 mod_dir：从原 mod 的 LoadFolders.xml 读取路径顺序与 IfModActive/IfModNotActive，
    只生成原文件中出现的路径（不生成 Source、RimJobWorld/Source 等原 mod 未列出的目录）。

    Args:
        output_dir: 输出根目录（xml 将写在此目录下）
        folder_names: 本次导出的目录名（相对路径）；当提供 mod_dir 时仅输出其中在原 LoadFolders 里存在的项
        version: 版本标签，如 "1.6" -> <v1.6>
        mod_dir: 原模组根目录，用于读取 LoadFolders.xml 的路径列表与属性（可选）

    Returns:
        生成的 LoadFolders.xml 路径，失败返回 None
    """
    if not folder_names:
        return None
    folder_set = {n.replace("\\", "/") for n in folder_names}
    li_attrs: Dict[str, Dict[str, str]] = {}
    ordered_paths: List[str] = []
    if mod_dir:
        li_attrs, ordered_paths = _parse_load_folders_from_mod(mod_dir, version)
        # 只保留「原 LoadFolders 中有」且「本次有导出」的路径，按原顺序
        to_output = [p for p in ordered_paths if p in folder_set]
        # 若版本结构下原文件只列了版本块（如仅 "1.6"）导致交集为空，则用本次导出的目录列表生成，避免不生成文件
        if not to_output and folder_set:
            to_output = sorted(folder_set)
    else:
        to_output = list(folder_set)
    if not to_output:
        return None
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    version_tag = f"v{version}" if not version.startswith("v") else version
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<loadFolders>",
        f"  <{version_tag}>",
    ]
    for name in to_output:
        attrs = li_attrs.get(name, {})
        if attrs:
            attr_str = " ".join(f'{k}="{v}"' for k, v in sorted(attrs.items()))
            lines.append(f"    <li {attr_str}>{name}</li>")
        else:
            lines.append(f"    <li>{name}</li>")
    lines.append(f"  </{version_tag}>")
    lines.append("</loadFolders>")
    xml_path = out / "LoadFolders.xml"
    try:
        xml_path.write_text("\n".join(lines), encoding="utf-8")
        return xml_path
    except (OSError, IOError):
        return None


def generate_total_load_folders_xml(
    output_dir: str,
    version: str,
    entries: List[Tuple[str, Dict[str, str], Optional[str]]],
) -> Optional[Path]:
    """
    生成批量导出用的总 LoadFolders.xml：每个条目为 (路径, 属性字典, 可选注释)。
    路径为相对输出根的路径（如 "Vanilla Brewing Expanded/1.6"）；无 IfModActive 时由调用方
    传入 packageId 等属性；comment 为 None 或 "<!-- Mod Name -->" 在该 <li> 前输出。
    """
    if not entries:
        return None
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    version_tag = f"v{version}" if not version.startswith("v") else version
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<loadFolders>",
        f"  <{version_tag}>",
    ]
    for path, attrs, comment_before in entries:
        if comment_before:
            lines.append(f"    {comment_before}")
        path_norm = (path or "").replace("\\", "/")
        if attrs:
            attr_str = " ".join(f'{k}="{v}"' for k, v in sorted(attrs.items()))
            lines.append(f"    <li {attr_str}>{path_norm}</li>")
        else:
            lines.append(f"    <li>{path_norm}</li>")
    lines.append(f"  </{version_tag}>")
    lines.append("</loadFolders>")
    xml_path = out / "LoadFolders.xml"
    try:
        xml_path.write_text("\n".join(lines), encoding="utf-8")
        return xml_path
    except (OSError, IOError):
        return None


class TemplateManager:
    """
    翻译模板管理器

    负责翻译模板的完整生命周期管理，协调各个组件完成复杂的翻译提取和生成流程
    """

    def __init__(self):
        """初始化模板管理器"""
        self.logger = get_logger(f"{__name__}.TemplateManager")
        self.logger.debug("初始化TemplateManager")

        # 初始化组件
        self.config = UserConfigManager.get_instance()
        self.definjected_extractor = DefInjectedExtractor(self.config)
        self.keyed_extractor = KeyedExtractor(self.config)
        self.defs_scanner = DefsScanner(self.config)
        self.definjected_exporter = DefInjectedExporter(self.config)
        self.keyed_exporter = KeyedExporter(self.config)

    def extract_and_generate_templates(
        self,
        import_dir: str,
        import_language: str,
        output_dir: str,
        output_language: str,
        data_source_choice: Optional[str] = None,
        template_structure: Optional[str] = None,
        has_input_keyed: bool = True,
        output_csv: Optional[str] = None,
    ) -> tuple[List[Tuple[str, str, str, str]], str]:
        """
        提取翻译数据并生成模板，同时导出CSV。
        Keyed/DefInjected 与 Defs 同逻辑：从当前内容根 import_dir 读取，输出到 output_dir。

        Args:
            import_dir: 当前内容根路径
            import_language: 输入语言代码
            output_dir: 输出目录路径
            output_language: 输出语言代码
            data_source_choice: 数据来源选择 ('definjected_only' 或 'defs_only')
            template_structure: 模板结构选择
            has_input_keyed: 是否包含Keyed输入
            output_csv: CSV输出文件名

        Returns:
            tuple[List[Tuple[str, str, str, str]], str]: (提取的翻译数据, CSV文件路径)
        """
        self.logger.debug(
            "开始提取翻译数据并生成模板: import_dir=%s, output_dir=%s",
            import_dir,
            output_dir,
        )
        log_user_action(
            "提取翻译模板",
            import_dir=import_dir,
            output_dir=output_dir,
            data_source=data_source_choice,
            template_structure=template_structure,
        )

        # 步骤1：提取翻译数据（Keyed/DefInjected 与 Defs 同逻辑：从当前内容根 import_dir 读取）
        keyed_translations, def_translations = self.extract_all_translations(
            import_dir,
            import_language,
            data_source_choice=data_source_choice,
            has_input_keyed=has_input_keyed,
        )

        if not keyed_translations and not def_translations:
            self.logger.warning("未找到任何翻译数据")
            ui.print_warning("未找到任何翻译数据")
            return [], ""

        # 步骤2：根据用户选择的输出模式生成翻译模板
        self._generate_templates_to_output_dir_with_structure(
            output_dir=output_dir,
            output_language=output_language,
            keyed_translations=keyed_translations,
            def_translations=def_translations,
            template_structure=template_structure,
            has_input_keyed=has_input_keyed,
        )

        # 步骤3：导出CSV到输出目录
        csv_path = self._save_translations_to_csv(
            keyed_translations,
            def_translations,
            output_dir,
            output_language,
            output_csv,
        )
        all_translations = keyed_translations + def_translations
        # 记录数据处理统计
        log_data_processing(
            "提取翻译模板",
            len(all_translations),
            data_source=data_source_choice,
            template_structure=template_structure,
        )

        self.logger.debug("模板生成完成，总计 %s 条翻译", len(all_translations))
        return all_translations, csv_path

    def extract_and_generate_templates_from_roots(
        self,
        import_dirs: List[str],
        import_language: str,
        output_dir: str,
        output_language: str,
        data_source_choice: Optional[str] = None,
        template_structure: Optional[str] = None,
        has_input_keyed: bool = True,
        output_csv: Optional[str] = None,
    ) -> tuple[List[Tuple[str, str, str, str]], str]:
        """
        从多个内容根提取并合并到同一输出目录（一个 Languages/Keyed、一个 Languages/DefInjected）。
        用于「无 LoadFolders」或 LoadFolders 中版本路径（如 1.6）时，版本目录+同级目录合并导出。
        """
        all_keyed: List[Tuple] = []
        all_def: List[Tuple] = []
        for import_dir in import_dirs:
            k, d = self.extract_all_translations(
                import_dir,
                import_language,
                data_source_choice=data_source_choice,
                has_input_keyed=has_input_keyed,
            )
            all_keyed.extend(k)
            all_def.extend(d)
        # 多根时可能同一 Keyed/Def 目录被多个根解析到，按 key 去重保留首次出现
        if len(import_dirs) > 1:
            _seen_k: set = set()
            _out_k: List[Tuple] = []
            for item in all_keyed:
                if not item:
                    continue
                key = item[0]
                if key is not None and key not in _seen_k:
                    _seen_k.add(key)
                    _out_k.append(item)
            all_keyed = _out_k
            _seen_d: set = set()
            _out_d: List[Tuple] = []
            for item in all_def:
                if not item:
                    continue
                key = item[0]
                if key is not None and key not in _seen_d:
                    _seen_d.add(key)
                    _out_d.append(item)
            all_def = _out_d
        if not all_keyed and not all_def:
            self.logger.warning("多根合并：未找到任何翻译数据")
            ui.print_warning("未找到任何翻译数据")
            return [], ""
        log_user_action(
            "提取翻译模板（多根合并）",
            import_dirs=import_dirs,
            output_dir=output_dir,
            data_source=data_source_choice,
            template_structure=template_structure,
        )
        self._generate_templates_to_output_dir_with_structure(
            output_dir=output_dir,
            output_language=output_language,
            keyed_translations=all_keyed,
            def_translations=all_def,
            template_structure=template_structure or "original_structure",
            has_input_keyed=has_input_keyed,
        )
        csv_path = self._save_translations_to_csv(
            all_keyed,
            all_def,
            output_dir,
            output_language,
            output_csv,
        )
        all_translations = all_keyed + all_def
        log_data_processing(
            "提取翻译模板（多根合并）",
            len(all_translations),
            data_source=data_source_choice,
            template_structure=template_structure,
        )
        return all_translations, csv_path

    def merge_mode(
        self,
        import_dir: str,
        import_language: str,
        output_dir: str,
        output_language: str,
        data_source_choice: str = "defs_only",
        has_input_keyed: bool = True,
        output_csv: Optional[str] = None,
        input_keyed: Optional[List[Tuple]] = None,
        input_def: Optional[List[Tuple]] = None,
    ) -> tuple[List[Tuple[str, str, str, str]], str]:
        """
        执行智能合并模式处理翻译数据。
        若提供 input_keyed/input_def（多根合并后的数据），则不再从 import_dir 提取。

        Args:
            input_keyed: 可选，预提取的 Keyed 数据（多根合并时传入）
            input_def: 可选，预提取的 DefInjected 数据（多根合并时传入）
        """
        if input_keyed is not None and input_def is not None:
            pass
        else:
            ui.print_info("【输入】英文源")
            input_keyed, input_def = self.extract_all_translations(
                import_dir,
                import_language,
                data_source_choice=data_source_choice,
                has_input_keyed=has_input_keyed,
            )

        # 步骤2：提取输出目录现有翻译（用于与输入合并）
        ui.print_info("【输出】现有翻译")
        output_keyed, output_def = self.extract_all_translations(
            output_dir,
            output_language,
            data_source_choice="definjected_only",
            has_input_keyed=has_input_keyed,
        )

        # 步骤3：智能合并翻译数据（include_unchanged=False，不变项不进入 merged，故 CSV 也不会包含）
        keyed_translations, keyed_stats = SmartMerger.smart_merge_translations(
            input_data=input_keyed,
            output_data=output_keyed,
            include_unchanged=False,
        )
        def_translations, def_stats = SmartMerger.smart_merge_translations(
            input_data=input_def,
            output_data=output_def,
            include_unchanged=False,
        )
        # 写入合并结果（仅更新、新增、过时等，不含「不变」）
        if keyed_translations:
            self._write_merged_translations(
                keyed_translations, output_dir, output_language, "Keyed", keyed_stats
            )

        if def_translations:
            self._write_merged_translations(
                def_translations, output_dir, output_language, "DefInjected", def_stats
            )
        else:
            # DefInjected 参与合并但无需写入时，与 Keyed 同格式单行统计
            total_def = def_stats.get("merged_count", 0) + def_stats.get(
                "unchanged_count", 0
            )
            if total_def or len(input_def) or len(output_def):
                u, n, c = (
                    def_stats.get("updated_count", 0),
                    def_stats.get("new_count", 0),
                    def_stats.get("unchanged_count", 0),
                )
                ui.print_success(
                    f"合并 DefInjected → {total_def} 条（更新 {u}，新增 {n}，不变 {c}）"
                )

        # 步骤4：导出CSV到输出目录（同上，仅含更新/新增/过时等，不含不变项）
        csv_path = self._save_translations_to_csv(
            keyed_translations,
            def_translations,
            output_dir,
            output_language,
            output_csv,
        )
        translations = keyed_translations + def_translations
        return translations, csv_path

    def extract_all_translations(
        self,
        import_dir: str,
        import_language: str,
        data_source_choice: Optional[str] = None,
        has_input_keyed: bool = True,
    ) -> List[Tuple[str, str, str, str, str]]:
        """
        提取所有翻译数据。
        Keyed/DefInjected 与 Defs 同逻辑：均从当前内容根 import_dir 读取（该目录下 Defs 或 Languages）。

        Args:
            import_dir: 当前内容根路径（Defs、Keyed、DefInjected 均在此目录下）
            import_language: 输入语言代码
            data_source_choice: 数据来源选择 ('definjected_only', 'defs_only')
            has_input_keyed: 是否包含Keyed输入

        Returns:
            List[Tuple[str, str, str, str, str]]: 五元组列表 (key, text, tag, rel_path, en_text)
        """
        data_source_choice = data_source_choice or "defs_only"

        # 提取Keyed翻译（与 Defs 同逻辑：从当前内容根 import_dir 下的 Languages/.../Keyed 读取）
        if has_input_keyed:
            self.logger.debug("正在扫描 Keyed 目录...")
            keyed_translations = self.keyed_extractor.extract(
                import_dir, import_language
            )
            ui.print_info(f"  Keyed → {len(keyed_translations)} 条")
            self.logger.debug(
                "从Keyed 目录提取到 %s 条 Keyed 翻译", len(keyed_translations)
            )
        else:
            keyed_translations = []

        if data_source_choice == "definjected_only":
            self.logger.debug("正在扫描 DefInjected 目录...")
            definjected_translations = self.definjected_extractor.extract(
                import_dir, import_language
            )
            ui.print_info(f"  DefInjected → {len(definjected_translations)} 条")
            self.logger.info(
                "从DefInjected 目录提取到 %s 条 DefInjected 翻译",
                len(definjected_translations),
            )
            return (keyed_translations, definjected_translations)

        elif data_source_choice == "defs_only":
            self.logger.debug("正在扫描 Defs 目录...")
            defs_translations = self.defs_scanner.extract(import_dir)
            ui.print_info(f"  Defs → {len(defs_translations)} 条")
            self.logger.debug(
                "从Defs目录提取到 %s 条 Defs 翻译", len(defs_translations)
            )
            # Defs提取器直接返回六元组，无需转换
            return (keyed_translations, defs_translations)

        # 如果到了这里，说明没有匹配的data_source_choice
        self.logger.warning("未知的data_source_choice: %s", data_source_choice)
        return []

    def _generate_templates_to_output_dir_with_structure(
        self,
        output_dir: str,
        output_language: str,
        keyed_translations: List[Tuple],
        def_translations: List[Tuple],
        template_structure: Optional[str],
        has_input_keyed: bool = True,
    ):
        """在指定输出目录生成翻译模板结构"""
        template_structure = template_structure or "original_structure"
        output_path = Path(output_dir)

        if not keyed_translations and not def_translations:
            ui.print_warning("没有翻译数据需要生成模板")
            return

        # 生成Keyed模板
        if has_input_keyed:
            if keyed_translations:
                ui.print_info(f"生成 {len(keyed_translations)} 条 Keyed 模板...")
                self.keyed_exporter.export_keyed_template(
                    output_dir, output_language, keyed_translations
                )
                self.logger.debug(
                    "生成 %s 条 Keyed 模板到 %s", len(keyed_translations), output_path
                )
                ui.print_success("Keyed 模板已生成")
            else:
                ui.print_warning("未找到 Keyed 翻译数据，已跳过 Keyed 模板生成。")
        else:
            ui.print_warning("未检测到输入 Keyed 目录，已跳过 Keyed 模板生成。")

        # 生成DefInjected模板
        if def_translations:
            ui.print_info(f"生成 {len(def_translations)} 条 DefInjected 模板...")
            self._generate_definjected_with_structure(
                def_translations,
                output_dir,
                output_language,
                template_structure,
            )

    def _generate_definjected_with_structure(
        self,
        def_translations: List[Tuple[str, str, str, str]],
        output_dir: str,
        output_language: str,
        template_structure: str,
    ):
        """根据智能配置的结构选择生成DefInjected模板"""
        if template_structure == "original_structure":
            # 使用原有结构的导出函数
            self.definjected_exporter.export_with_original_structure(
                output_dir, output_language, def_translations
            )
            self.logger.debug(
                "生成 %s 条 DefInjected 模板（保持原结构）", len(def_translations)
            )
            ui.print_success("DefInjected 模板已生成（保持原结构）")
        elif template_structure == "defs_by_type":
            # 按 Def 类型分组的导出函数（符合游戏要求）
            self.definjected_exporter.export_with_defs_structure(
                output_dir, output_language, def_translations
            )
            self.logger.debug(
                "生成 %s 条 DefInjected 模板（按DefType分组）", len(def_translations)
            )
            ui.print_success("DefInjected 模板已生成（按DefType分组）")
        else:
            # merge_logic 或未知值：按原结构写回
            self.definjected_exporter.export_with_original_structure(
                output_dir, output_language, def_translations
            )
            self.logger.debug("生成 %s 条 DefInjected 模板", len(def_translations))
            ui.print_success("DefInjected 模板已生成")

    def _write_merged_translations(
        self,
        merged: List[Tuple],
        output_dir: str,
        output_language: str,
        sub_dir: str,
        merge_stats: Optional[dict] = None,
    ) -> None:
        """
        通用写回 XML 方法，支持 DefInjected 和 Keyed

        Args:
            merged: List[(key, test, tag, rel_path, en_test, history)]
            output_dir: 输出根目录
            sub_dir: 子目录名（defInjected 或 keyed）
            merge_stats: 合并统计（含 unchanged_count 等），用于正确显示「不变」数量（因 include_unchanged=False 时不变项不在 merged 中）
        """
        logger = get_logger(f"{__name__}.write_merged_translations")

        # 使用新配置系统获取语言目录
        config_manager = UserConfigManager.get_instance()
        base_dir = (
            config_manager.language_config.get_language_dir(output_dir, output_language)
            / sub_dir
        )

        # 按 rel_path 分组
        file_groups = {}
        for item in merged:
            rel_path = item[3]
            file_groups.setdefault(rel_path, []).append(item)

        processor = self.definjected_exporter.processor
        for rel_path, items in file_groups.items():
            output_file = base_dir / rel_path

            # 检查文件是否已存在
            if output_file.exists():
                # 读取现有XML文件
                existing_tree = processor.parse_xml(str(output_file))
                if existing_tree is not None:
                    root = existing_tree.getroot()
                    logger.info("更新现有文件: %s", output_file)
                else:
                    # 文件存在但解析失败，创建新的
                    logger.warning("无法解析现有文件，将重新创建: %s", output_file)
                    root = processor.create_element("LanguageData")
                    output_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                # 文件不存在，创建新文件和目录
                logger.info("创建新文件: %s", output_file)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                root = processor.create_element("LanguageData")

            # 更新或添加翻译条目
            for key, test, _, _, en_test, history in sorted(items, key=lambda x: x[0]):
                # 清理标签名：保留连字符（defName 可含连字符如 TM_Mecha-Golem_EarthCoreHD），其余非法字符替换为点
                clean_key = re.sub(r"[^A-Za-z0-9_.\-]", ".", key)
                if not re.match(r"^[A-Za-z_]", clean_key):
                    clean_key = "_" + clean_key

                # 查找现有元素
                existing_elem = root.find(clean_key)
                if existing_elem is not None:
                    # 更新现有元素
                    original_text = existing_elem.text or ""
                    elem_index = list(root).index(existing_elem)
                    text_changed = original_text != test
                    # 无原英文时仅添加 EN 注释、不改动原中文：需插入历史+EN 注释
                    need_insert_en_only = (
                        not text_changed and (en_test or (history and history.strip()))
                    )

                    if text_changed:
                        # 删除紧挨着元素的前一个 EN 注释（匹配具体内容）
                        if elem_index > 0 and en_test:
                            prev_child = root[elem_index - 1]
                            expected_en_text = f"EN: {en_test}"
                            if (
                                type(prev_child).__name__ == "_Comment"
                                and hasattr(prev_child, "text")
                                and prev_child.text
                                and prev_child.text.strip() == expected_en_text
                            ):
                                root.remove(prev_child)
                                elem_index -= 1
                        # 若再前一个节点是历史类注释（如「翻译内容: ...,新增于」或「原中文...更新于」），一并删除，避免重复堆积
                        if elem_index > 0:
                            prev_child = root[elem_index - 1]
                            if (
                                type(prev_child).__name__ == "_Comment"
                                and hasattr(prev_child, "text")
                                and prev_child.text
                            ):
                                t = prev_child.text.strip()
                                if "新增于" in t or "更新于" in t:
                                    root.remove(prev_child)
                                    elem_index -= 1

                        # 添加历史注释
                        if history and history.strip():
                            history_comment = processor.create_comment(history)
                            root.insert(elem_index, history_comment)
                            elem_index += 1  # 调整索引

                        # 添加新的英文注释（优先用 en_test，如无则用 test）
                        en_for_comment = en_test if en_test else test
                        if en_for_comment:
                            en_comment = processor.create_comment(
                                f"EN: {en_for_comment}"
                            )
                            root.insert(elem_index, en_comment)
                            elem_index += 1  # 调整索引
                    elif need_insert_en_only:
                        # 仅添加英文注释、不改动原中文：先删旧历史注释再插入历史 + EN
                        if elem_index > 0:
                            prev_child = root[elem_index - 1]
                            if (
                                type(prev_child).__name__ == "_Comment"
                                and hasattr(prev_child, "text")
                                and prev_child.text
                            ):
                                t = prev_child.text.strip()
                                if "新增于" in t or "更新于" in t:
                                    root.remove(prev_child)
                                    elem_index -= 1
                        if history and history.strip():
                            history_comment = processor.create_comment(history)
                            root.insert(elem_index, history_comment)
                            elem_index += 1
                        if en_test:
                            en_comment = processor.create_comment(f"EN: {en_test}")
                            root.insert(elem_index, en_comment)
                            elem_index += 1  # 调整索引

                    existing_elem.text = sanitize_xml(test)
                else:
                    # 添加新元素
                    # 先添加历史注释（如果有，且不为空）
                    if history and history.strip():
                        history_comment = processor.create_comment(history)
                        root.append(history_comment)

                    # 添加英文注释（优先用 en_test，如无则用 test）
                    en_for_comment = en_test if en_test else test
                    if en_for_comment:
                        en_comment = processor.create_comment(
                            f"EN: {en_for_comment}"
                        )
                        root.append(en_comment)

                    # 创建新的翻译元素
                    processor.create_subelement(root, clean_key, sanitize_xml(test))

            # 保存更新后的文件
            success = processor.save_xml(root, output_file, pretty_print=True)
            if success:
                logger.info("成功保存文件: %s (%s 条翻译)", output_file, len(items))
            else:
                logger.error("保存文件失败: %s", output_file)

        # 单行合并结果（与 DefInjected 无写入时格式一致）
        def _hist(item):
            return (item[5] or "") if len(item) > 5 else ""

        updated_count = sum(1 for item in merged if "更新于" in _hist(item))
        new_count = sum(1 for item in merged if "新增于" in _hist(item))
        unchanged_count = (merge_stats or {}).get("unchanged_count", 0)
        if unchanged_count == 0:
            unchanged_count = sum(1 for item in merged if not _hist(item).strip())
        total_processed = len(merged) + unchanged_count
        ui.print_success(
            f"合并 {sub_dir} → {total_processed} 条（更新 {updated_count}，新增 {new_count}，不变 {unchanged_count}）"
        )

    def _save_translations_to_csv(
        self,
        keyed_translations: List[Tuple],
        def_translations: List[Tuple],
        output_dir: str,
        output_language: str,
        output_csv: Optional[str] = None,
    ) -> str:
        """保存翻译数据到CSV文件；无数据时不创建目录和文件。

        Args:
            keyed_translations: Keyed翻译数据列表
            def_translations: DefInjected翻译数据列表
            output_dir: 输出目录
            output_language: 输出语言
            output_csv: CSV文件名，默认为"translations.csv"

        Returns:
            str: CSV文件路径，无数据时返回空字符串
        """
        if not keyed_translations and not def_translations:
            return ""
        # 使用配置系统的功能生成输出路径
        config_manager = UserConfigManager.get_instance()
        csv_path = (
            config_manager.language_config.get_language_dir(output_dir, output_language)
            / output_csv
        )
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag", "file", "type"])

            # 合并所有翻译数据
            all_translations = []

            # 添加Keyed翻译数据
            for item in keyed_translations:
                if len(item) >= 4:
                    all_translations.append((*item[:4], "keyed"))

            # 添加DefInjected翻译数据
            for item in def_translations:
                if len(item) >= 4:
                    # 取前4个元素作为基础数据，添加类型标识
                    all_translations.append((*item[:4], "def"))

            # 使用进度条进行导出
            for _, item in ui.iter_with_progress(
                all_translations,
                prefix="导出CSV",
                description="",
            ):
                writer.writerow(item)

        ui.print_success(f"导出 CSV → {Path(csv_path).name}")
        self.logger.debug("翻译数据已保存到CSV: %s", csv_path)

        # 记入历史：让提取生成的 CSV 出现在后续"Python机翻/导入翻译"的历史列表
        try:
            PathManager().remember_path("import_csv", str(csv_path))
        except (OSError, IOError, PermissionError) as e:
            self.logger.warning("无法记录CSV历史路径: %s, 错误: %s", csv_path, e)

        return str(csv_path)

    def incremental_mode(
        self,
        import_dir: str,
        import_language: str,
        output_dir: str,
        output_language: str,
        data_source_choice: str,
        has_input_keyed: bool,
        output_csv: str,
        input_keyed: Optional[List[Tuple]] = None,
        input_def: Optional[List[Tuple]] = None,
    ) -> Tuple[List[Tuple], str]:
        """
        新增模式：若提供 input_keyed/input_def（多根合并后的数据），则不再从 import_dir 提取。
        """
        self.logger.info("开始新增模式处理")
        ui.print_info("=== 新增模式：扫描对比现有内容 ===")

        if input_keyed is not None and input_def is not None:
            pass
        else:
            ui.print_info("🔍 步骤1：提取输入数据...")
            input_keyed, input_def = self.extract_all_translations(
                import_dir=import_dir,
                import_language=import_language,
                data_source_choice=data_source_choice,
                has_input_keyed=has_input_keyed,
            )

        if not input_keyed and not input_def:
            ui.print_warning("未找到输入翻译数据")
            return [], ""

        ui.print_success(
            f"输入数据提取完成：Keyed {len(input_keyed)} 条，DefInjected {len(input_def)} 条"
        )

        # 步骤2：提取输出数据
        ui.print_info("📋 步骤2：提取输出数据...")
        output_keyed, output_def = self.extract_all_translations(
            import_dir=output_dir,
            import_language=output_language,
            data_source_choice="definjected_only",
            has_input_keyed=has_input_keyed,
        )

        ui.print_info(
            f"输出数据提取完成：Keyed {len(output_keyed)} 条，DefInjected {len(output_def)} 条"
        )

        # 步骤3：新增翻译数据（只保留新增的部分）
        ui.print_info("🔍 步骤3：智能对比，筛选新增翻译数据...")

        # 使用智能合并器，但只保留新增的部分
        keyed_new = self._filter_new_translations(input_keyed, output_keyed)
        def_new = self._filter_new_translations(input_def, output_def)

        if not keyed_new and not def_new:
            ui.print_success("✅ 没有发现缺少的key，所有内容都已存在")
            return [], ""

        ui.print_success(
            f"发现新增翻译：Keyed {len(keyed_new)} 条，DefInjected {len(def_new)} 条"
        )

        # 生成新增的模板文件
        ui.print_info("📝 生成新增的模板文件...")
        if keyed_new:
            ui.print_info("正在生成 Keyed 新增模板...")
            self._write_merged_translations(
                keyed_new, output_dir, output_language, "Keyed"
            )

        if def_new:
            ui.print_info("正在生成 DefInjected 新增模板...")
            self._write_merged_translations(
                def_new, output_dir, output_language, "DefInjected"
            )

        # 保存新增的CSV文件
        ui.print_info("💾 保存新增的CSV文件...")
        csv_path = self._save_translations_to_csv(
            keyed_new,
            def_new,
            output_dir,
            output_language,
            output_csv,
        )

        total_new = len(keyed_new) + len(def_new)
        ui.print_success(f"新增模式完成！新增了 {total_new} 条翻译")
        ui.print_info(f"CSV文件：{csv_path}")

        return keyed_new + def_new, csv_path

    def _filter_new_translations(
        self, input_data: List[Tuple], output_data: List[Tuple]
    ) -> List[Tuple]:
        """
        筛选出新增的翻译数据（输入中存在但输出中不存在的key）

        Args:
            input_data: 输入翻译数据
            output_data: 输出翻译数据

        Returns:
            List[Tuple]: 新增的翻译数据列表
        """
        if not input_data:
            return []

        # 创建输出数据的key映射
        output_keys = {item[0] for item in output_data}

        # 筛选出新增的翻译
        new_translations = []
        for item in input_data:
            key = item[0]
            if key not in output_keys:
                # 为新增的翻译添加历史记录
                import datetime

                today = datetime.date.today().isoformat()
                new_item = item + (f"翻译内容: '{item[1]}',新增于{today}",)
                new_translations.append(new_item)

        return new_translations
