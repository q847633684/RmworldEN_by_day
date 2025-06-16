from pathlib import Path
from typing import List, Tuple, Dict
import logging
import xml.etree.ElementTree as ET
from ..utils.config import get_config
from ..utils.utils import XMLProcessor, save_json, sanitize_xml
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
            return Path(export_dir) / "templates"
        return self.mod_dir

    def generate_keyed_template(self, en_keyed_dir: str, export_dir: str = None) -> None:
        print(f"{Fore.GREEN}正在生成中文 Keyed 翻译模板...{Style.RESET_ALL}")
        base_dir = self.get_template_base_dir(export_dir)
        zh_keyed_dir = base_dir / "Languages" / self.language / CONFIG.keyed_dir
        zh_keyed_dir.mkdir(parents=True, exist_ok=True)
        en_path = Path(en_keyed_dir)
        for en_xml_file in en_path.rglob("*.xml"):
            tree = self.processor.parse_xml(str(en_xml_file))
            if tree:
                zh_root = self._create_keyed_xml_from_source(tree.getroot() if self.processor.use_lxml else tree)
                rel_path = en_xml_file.relative_to(en_path)
                zh_xml_file = zh_keyed_dir / rel_path
                self.processor.save_xml(ET.ElementTree(zh_root), str(zh_xml_file))
                print(f"{Fore.GREEN}生成 Keyed 模板: {zh_xml_file.name}{Style.RESET_ALL}")

    def generate_keyed_template_from_data(self, keyed_translations: List[TranslationData], export_dir: str = None) -> None:
        logging.info("正在生成中文 Keyed 翻译模板...")
        base_dir = self.get_template_base_dir(export_dir)
        zh_keyed_dir = base_dir / "Languages" / self.language / CONFIG.keyed_dir
        file_groups = self._group_translations_by_file(keyed_translations)
        for file_path, translations in file_groups.items():
            zh_xml_file = self._get_target_file_path(file_path, zh_keyed_dir)
            zh_root = self._create_keyed_xml_from_data(translations)
            self.processor.save_xml(ET.ElementTree(zh_root), str(zh_xml_file))
            logging.info(f"生成 Keyed 模板: {zh_xml_file.name}")

    def generate_definjected_template(self, defs_translations: List[TranslationData], export_dir: str = None) -> None:
        print(f"{Fore.GREEN}正在生成 DefInjected 翻译模板...{Style.RESET_ALL}")
        base_dir = self.get_template_base_dir(export_dir)
        zh_definjected_dir = base_dir / "Languages" / self.language / CONFIG.def_injected_dir
        def_groups = self._group_defs_by_type(defs_translations)
        for def_type, fields in def_groups.items():
            type_dir = zh_definjected_dir / f"{def_type}Defs"
            output_file = type_dir / f"{def_type}Defs.xml"
            root = self._create_definjected_xml_from_data(fields)
            self.processor.save_xml(ET.ElementTree(root), str(output_file))
            print(f"{Fore.GREEN}生成 DefInjected 模板: {def_type}Defs.xml{Style.RESET_ALL}")

    def _create_keyed_xml_from_source(self, source_root: ET.Element) -> ET.Element:
        zh_root = ET.Element("LanguageData")
        for elem in source_root:
            if isinstance(elem.tag, str) and elem.text and elem.text.strip():
                zh_elem = ET.SubElement(zh_root, elem.tag)
                zh_elem.text = sanitize_xml(elem.text.strip())
        return zh_root

    def _create_keyed_xml_from_data(self, translations: List[Tuple[str, str, str]]) -> ET.Element:
        zh_root = ET.Element("LanguageData")
        for key, text, tag in translations:
            zh_elem = ET.SubElement(zh_root, key)
            zh_elem.text = sanitize_xml(text)
        return zh_root

    def _create_definjected_xml_from_data(self, fields: Dict[str, str]) -> ET.Element:
        root = ET.Element("LanguageData")
        for field_key, text in fields.items():
            elem = ET.SubElement(root, field_key)
            elem.text = sanitize_xml(text)
        return root

    def _group_translations_by_file(self, translations: List[TranslationData]) -> Dict[str, List[Tuple[str, str, str]]]:
        file_groups = {}
        for key, text, tag, file_path in translations:
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append((key, text, tag))
        return file_groups

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