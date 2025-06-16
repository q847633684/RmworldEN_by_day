"""
模板生成模块 - 负责生成翻译模板文件
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict
import logging
from ..utils.config import TranslationConfig
from ..utils.utils import save_xml_to_file  # 🔧 复用 utils 的 XML 保存逻辑

CONFIG = TranslationConfig()
TranslationData = Tuple[str, str, str, str]  # (key, text, tag, file_path)

class TemplateGenerator:
    """翻译模板生成器"""
    
    def __init__(self, mod_dir: str, language: str, template_location: str = "mod"):
        """
        初始化模板生成器
        
        Args:
            mod_dir: 模组目录
            language: 目标语言
            template_location: "mod" 或 "export"
        """
        self.mod_dir = Path(mod_dir)
        self.language = language
        self.template_location = template_location
    
    def get_template_base_dir(self, export_dir: str = None) -> Path:
        """获取模板生成的基础目录"""
        if self.template_location == "export" and export_dir:
            return Path(export_dir) / "templates"
        else:
            return self.mod_dir
    
    def generate_keyed_template(self, en_keyed_dir: str, export_dir: str = None) -> None:
        """生成中文 Keyed 翻译模板（从英文目录读取）"""
        print("📋 正在生成中文 Keyed 翻译模板...")
        
        base_dir = self.get_template_base_dir(export_dir)
        zh_keyed_dir = base_dir / "Languages" / self.language / CONFIG.keyed_dir
        zh_keyed_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  📍 模板位置: {zh_keyed_dir}")
        
        en_path = Path(en_keyed_dir)
        xml_files = list(en_path.rglob("*.xml"))
        
        for en_xml_file in xml_files:
            try:
                tree = ET.parse(en_xml_file)
                root = tree.getroot()
                
                # 🔧 使用统一的 XML 创建方法
                zh_root = self._create_keyed_xml_from_source(root)
                
                if len(zh_root) > 0:
                    rel_path = en_xml_file.relative_to(en_path)
                    zh_xml_file = zh_keyed_dir / rel_path
                    zh_xml_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 🔧 使用统一的保存方法
                    self._save_xml_with_comments(zh_root, zh_xml_file, root)
                    print(f"  ✅ 生成 Keyed 模板: {zh_xml_file.name}")
                
            except Exception as e:
                logging.error(f"生成 Keyed 模板失败: {en_xml_file}: {e}")
                print(f"  ❌ 生成失败: {en_xml_file.name}")
    
    def generate_keyed_template_from_data(self, keyed_translations: List[TranslationData], export_dir: str = None) -> None:
        """从已提取的数据生成 Keyed 模板（避免重复读取文件）"""
        print("📋 正在生成中文 Keyed 翻译模板...")
        
        base_dir = self.get_template_base_dir(export_dir)
        zh_keyed_dir = base_dir / "Languages" / self.language / CONFIG.keyed_dir
        zh_keyed_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  📍 模板位置: {zh_keyed_dir}")
        
        # 按文件分组
        file_groups = self._group_translations_by_file(keyed_translations)
        
        # 为每个文件生成模板
        for file_path, translations in file_groups.items():
            try:
                # 🔧 使用统一的文件路径处理
                zh_xml_file = self._get_target_file_path(file_path, zh_keyed_dir)
                zh_xml_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 🔧 使用统一的 XML 创建方法
                zh_root = self._create_keyed_xml_from_data(translations)
                
                if len(zh_root) > 0:
                    # 🔧 使用统一的保存方法
                    save_xml_to_file(zh_root, str(zh_xml_file))
                    print(f"  ✅ 生成 Keyed 模板: {zh_xml_file.name} ({len(translations)} 条)")
                
            except Exception as e:
                logging.error(f"生成 Keyed 模板失败: {file_path}: {e}")
                print(f"  ❌ 生成失败: {Path(file_path).name}")
    
    def generate_definjected_template(self, defs_translations: List[TranslationData], export_dir: str = None) -> None:
        """生成 DefInjected 翻译模板（带英文注释）"""
        print("🔧 正在生成 DefInjected 翻译模板...")
        
        base_dir = self.get_template_base_dir(export_dir)
        zh_definjected_dir = base_dir / "Languages" / self.language / CONFIG.def_injected_dir
        zh_definjected_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  📍 模板位置: {zh_definjected_dir}")
        
        # 🔧 使用统一的分组方法
        def_groups = self._group_defs_by_type(defs_translations)
        
        # 为每个 DefType 生成模板文件
        for def_type, fields in def_groups.items():
            if not fields:
                continue
                
            type_dir = zh_definjected_dir / f"{def_type}Defs"
            type_dir.mkdir(exist_ok=True)
            
            output_file = type_dir / f"{def_type}Defs.xml"
            
            # 🔧 使用统一的 XML 创建和保存方法
            root = self._create_definjected_xml_from_data(fields)
            save_xml_to_file(root, str(output_file))
            print(f"  ✅ 生成 DefInjected 模板: {def_type}Defs.xml ({len(fields)} 条)")
    
    def generate_definjected_template_from_data(self, defs_translations: List[TranslationData], export_dir: str = None) -> None:
        """从已提取的数据生成 DefInjected 模板（委托给主方法）"""
        self.generate_definjected_template(defs_translations, export_dir)
    
    # 🔧 统一的辅助方法 - 避免重复代码
    
    def _create_keyed_xml_from_source(self, source_root: ET.Element) -> ET.Element:
        """从源 XML 创建 Keyed XML"""
        zh_root = ET.Element("LanguageData")
        
        for elem in source_root:
            if isinstance(elem.tag, str) and elem.text and elem.text.strip():
                zh_elem = ET.SubElement(zh_root, elem.tag)
                zh_elem.text = elem.text.strip()
        
        return zh_root
    
    def _create_keyed_xml_from_data(self, translations: List[Tuple[str, str, str]]) -> ET.Element:
        """从翻译数据创建 Keyed XML"""
        zh_root = ET.Element("LanguageData")
        
        for key, text, tag in translations:
            zh_elem = ET.SubElement(zh_root, key)
            zh_elem.text = text
        
        return zh_root
    
    def _create_definjected_xml_from_data(self, fields: Dict[str, str]) -> ET.Element:
        """从字段数据创建 DefInjected XML"""
        root = ET.Element("LanguageData")
        
        for field_key, text in fields.items():
            elem = ET.SubElement(root, field_key)
            elem.text = text
        
        return root
    
    def _group_translations_by_file(self, translations: List[TranslationData]) -> Dict[str, List[Tuple[str, str, str]]]:
        """按文件分组翻译数据"""
        file_groups = {}
        for key, text, tag, file_path in translations:
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append((key, text, tag))
        return file_groups
    
    def _group_defs_by_type(self, defs_translations: List[TranslationData]) -> Dict[str, Dict[str, str]]:
        """按 DefType 分组 Defs 翻译"""
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
        """获取目标文件路径"""
        source_path = Path(source_file_path)
        return target_dir / source_path.name
    
    def _save_xml_with_comments(self, root: ET.Element, file_path: Path, en_root: ET.Element = None) -> None:
        """保存带注释的 XML 文件"""
        try:
            en_dict = {}
            if en_root is not None:
                for elem in en_root:
                    if isinstance(elem.tag, str) and elem.text:
                        en_dict[elem.tag] = elem.text.strip()
            
            lines = ['<?xml version="1.0" encoding="utf-8"?>']
            lines.append('<LanguageData>')
            
            for elem in root:
                if isinstance(elem.tag, str):
                    en_text = en_dict.get(elem.tag, '')
                    if en_text:
                        lines.append(f'  <!-- EN: {en_text} -->')
                    lines.append(f'  <{elem.tag}>{elem.text or ""}</{elem.tag}>')
            
            lines.append('</LanguageData>')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
                
        except Exception as e:
            logging.error(f"保存带注释 XML 失败: {file_path}: {e}")
            # 降级：使用基本保存方法
            save_xml_to_file(root, str(file_path))
