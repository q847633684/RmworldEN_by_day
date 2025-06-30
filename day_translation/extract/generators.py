from pathlib import Path
from typing import List, Tuple, Dict
import logging
import xml.etree.ElementTree as ET
from day_translation.utils.config import get_config
from day_translation.utils.utils import XMLProcessor
from day_translation.extract.xml_utils import save_xml, sanitize_xml
from colorama import Fore, Style

CONFIG = get_config()
TranslationData = Tuple[str, str, str, str]

class TemplateGenerator:
    def __init__(self, mod_dir: str, language: str, template_location: str = "mod"):
        self.mod_dir = Path(mod_dir)
        self.language = language
        self.template_location = template_location
        self.processor = XMLProcessor()

    def get_template_base_dir(self, export_dir: str = None) -> Path:
        if self.template_location == "export" and export_dir:
            return Path(export_dir)
        return self.mod_dir

    def generate_definjected_template(self, defs_translations: List[TranslationData], export_dir: str = None) -> None:
        logging.info("%s正在生成 DefInjected 翻译模板...%s", Fore.GREEN, Style.RESET_ALL)
        # 在export_dir下创建DefInjected目录
        zh_definjected_dir = Path(export_dir) / CONFIG.def_injected_dir
        def_groups = self._group_defs_by_type(defs_translations)
        for def_type, fields in def_groups.items():
            type_dir = zh_definjected_dir / f"{def_type}Defs"
            output_file = type_dir / f"{def_type}Defs.xml"
            root = self._create_definjected_xml_from_data(fields)
            ok = save_xml(ET.ElementTree(root), str(output_file))
            if ok:
                logging.info(f"生成 DefInjected 模板: {def_type}Defs.xml{Style.RESET_ALL}{Style.RESET_ALL}")
            else:
                logging.error(f"写入失败: {output_file}")

    def _create_definjected_xml_from_data(self, fields: Dict[str, str]) -> ET.Element:
        root = ET.Element("LanguageData")
        for field_key, text in fields.items():
            elem = ET.SubElement(root, field_key)
            elem.text = sanitize_xml(text)
        return root

    def _group_defs_by_type(self, defs_translations: List[TranslationData]) -> Dict[str, Dict[str, str]]:
        def_groups = {}
        for full_path, text, tag, file_path in defs_translations:
            if '/' in full_path:
                def_type_part, field_part = full_path.split('/', 1)
                def_type = def_type_part
                if def_type not in def_groups:
                    def_groups[def_type] = {}
                def_groups[def_type][field_part] = text
        return def_groups

    def _get_target_file_path(self, source_file_path: str, target_dir: Path) -> Path:
        return target_dir / Path(source_file_path).name
