"""
Day Translation 2 - 模板生成器模块

提供游戏本地化模板生成功能，包括：
- Keyed翻译模板生成
- DefInjected翻译模板生成
- XML模板创建和保存
- 翻译数据分组和组织
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 标准库导入
import sys
from services.config_service import config_service
from utils.file_utils import ensure_directory_exists
from utils.xml_processor import AdvancedXMLProcessor
# 确保能够导入项目模块
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 项目模块导入

# 创建别名以保持代码简洁
ensure_directory = ensure_directory_exists

# 类型定义
TranslationData = Tuple[str, str, str, str]  # (key, text, tag, file_path)
KeyedTranslation = Tuple[str, str, str]  # (key, text, tag)


def sanitize_xml(text: str) -> str:
    """
    清理XML文本，移除非法字符并转义特殊字符

    Args:
        text: 要清理的文本

    Returns:
        清理后的文本
    """
    if not isinstance(text, str):
        return str(text)

    # 移除XML非法字符 (FFFD是Unicode替换字符)
    text = re.sub(r"[^\u0020-\uD7FF\uE000-\uFFFD]", "", text)

    # 转义XML特殊字符
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return text


class TemplateGenerator:
    """
    模板生成器主类

    负责生成游戏本地化的XML模板文件，支持：
    - Keyed翻译模板（键值对翻译）
    - DefInjected翻译模板（定义注入翻译）
    - 从源文件或数据生成模板
    """

    def __init__(self, mod_dir: str, language: str, template_location: str = "mod"):
        """
        初始化模板生成器

        Args:
            mod_dir: 模组目录路径
            language: 目标语言代码
            template_location: 模板位置 ("mod" 或 "export")
        """
        self.mod_dir = Path(mod_dir)
        self.language = language
        self.template_location = template_location
        self.processor = AdvancedXMLProcessor()
        self.config = config_service.get_unified_config()

        # 设置日志
        self.logger = logging.getLogger(__name__)

    def get_template_base_dir(self, export_dir: Optional[str] = None) -> Path:
        """
        获取模板基础目录

        Args:
            export_dir: 导出目录路径

        Returns:
            模板基础目录路径
        """
        if self.template_location == "export" and export_dir:
            return Path(export_dir) / "templates"
        return self.mod_dir

    def generate_keyed_template(self, en_keyed_dir: str, export_dir: Optional[str] = None) -> None:
        """
        从英文Keyed目录生成中文翻译模板

        Args:
            en_keyed_dir: 英文Keyed目录路径
            export_dir: 导出目录路径（可选）
        """
        self.logger.info("正在生成中文 Keyed 翻译模板...")

        base_dir = self.get_template_base_dir(export_dir)
        zh_keyed_dir = base_dir / "Languages" / self.language / self.config.core.keyed_dir
        ensure_directory(str(zh_keyed_dir))

        en_path = Path(en_keyed_dir)
        processed_count = 0

        for en_xml_file in en_path.rglob("*.xml"):
            try:
                tree = self.processor.parse_xml(str(en_xml_file))
                if tree:
                    zh_root = self._create_keyed_xml_from_source(tree.getroot())
                    rel_path = en_xml_file.relative_to(en_path)
                    zh_xml_file = zh_keyed_dir / rel_path

                    # 确保目标目录存在
                    ensure_directory(str(zh_xml_file.parent))

                    self.processor.save_xml(ET.ElementTree(zh_root), str(zh_xml_file))
                    processed_count += 1
                    self.logger.info(f"生成 Keyed 模板: {zh_xml_file.name}")

            except Exception as e:
                self.logger.error(f"处理文件 {en_xml_file} 时出错: {e}")

        self.logger.info(f"Keyed 模板生成完成，共处理 {processed_count} 个文件")

    def generate_keyed_template_from_data(
        self,
        keyed_translations: List[TranslationData],
        export_dir: Optional[str] = None,
    ) -> None:
        """
        从翻译数据生成Keyed翻译模板

        Args:
            keyed_translations: 翻译数据列表
            export_dir: 导出目录路径（可选）
        """
        self.logger.info("正在从数据生成中文 Keyed 翻译模板...")

        base_dir = self.get_template_base_dir(export_dir)
        zh_keyed_dir = base_dir / "Languages" / self.language / self.config.core.keyed_dir
        ensure_directory(str(zh_keyed_dir))

        # 按文件分组翻译数据
        file_groups = self._group_translations_by_file(keyed_translations)
        processed_count = 0

        for file_path, translations in file_groups.items():
            try:
                zh_xml_file = self._get_target_file_path(file_path, zh_keyed_dir)
                ensure_directory(str(zh_xml_file.parent))

                zh_root = self._create_keyed_xml_from_data(translations)
                self.processor.save_xml(ET.ElementTree(zh_root), str(zh_xml_file))
                processed_count += 1
                self.logger.info(f"生成 Keyed 模板: {zh_xml_file.name}")

            except Exception as e:
                self.logger.error(f"处理文件 {file_path} 时出错: {e}")

        self.logger.info(f"Keyed 模板生成完成，共处理 {processed_count} 个文件")

    def generate_definjected_template(
        self, defs_translations: List[TranslationData], export_dir: Optional[str] = None
    ) -> None:
        """
        生成DefInjected翻译模板

        Args:
            defs_translations: DefInjected翻译数据列表
            export_dir: 导出目录路径（可选）"""
        self.logger.info("正在生成 DefInjected 翻译模板...")

        base_dir = self.get_template_base_dir(export_dir)
        zh_definjected_dir = (
            base_dir / "Languages" / self.language / self.config.core.definjected_dir
        )
        ensure_directory(str(zh_definjected_dir))

        # 按定义类型分组
        def_groups = self._group_defs_by_type(defs_translations)
        processed_count = 0

        for def_type, fields in def_groups.items():
            try:
                type_dir = zh_definjected_dir / f"{def_type}Defs"
                ensure_directory(str(type_dir))

                output_file = type_dir / f"{def_type}Defs.xml"
                root = self._create_definjected_xml_from_data(fields)
                self.processor.save_xml(ET.ElementTree(root), str(output_file))
                processed_count += 1
                self.logger.info(f"生成 DefInjected 模板: {def_type}Defs.xml")

            except Exception as e:
                self.logger.error(f"处理定义类型 {def_type} 时出错: {e}")

        self.logger.info(f"DefInjected 模板生成完成，共处理 {processed_count} 个类型")

    def _create_keyed_xml_from_source(self, source_root: ET.Element) -> ET.Element:
        """
        从源XML元素创建Keyed XML模板

        Args:
            source_root: 源XML根元素

        Returns:
            中文翻译XML根元素
        """
        zh_root = ET.Element("LanguageData")

        for elem in source_root:
            if isinstance(elem.tag, str) and elem.text and elem.text.strip():
                zh_elem = ET.SubElement(zh_root, elem.tag)
                zh_elem.text = sanitize_xml(elem.text.strip())

        return zh_root

    def _create_keyed_xml_from_data(self, translations: List[KeyedTranslation]) -> ET.Element:
        """
        从翻译数据创建Keyed XML模板

        Args:
            translations: 翻译数据列表

        Returns:
            中文翻译XML根元素
        """
        zh_root = ET.Element("LanguageData")

        for key, text, _ in translations:
            zh_elem = ET.SubElement(zh_root, key)
            zh_elem.text = sanitize_xml(text) if text else ""

        return zh_root

    def _create_definjected_xml_from_data(self, fields: Dict[str, str]) -> ET.Element:
        """
        从字段数据创建DefInjected XML模板

        Args:
            fields: 字段数据字典

        Returns:
            DefInjected XML根元素
        """
        root = ET.Element("LanguageData")

        for field_key, text in fields.items():
            elem = ET.SubElement(root, field_key)
            elem.text = sanitize_xml(text) if text else ""

        return root

    def _group_translations_by_file(
        self, translations: List[TranslationData]
    ) -> Dict[str, List[KeyedTranslation]]:
        """
        按文件分组翻译数据

        Args:
            translations: 翻译数据列表

        Returns:
            按文件分组的翻译数据字典
        """
        file_groups: Dict[str, List[KeyedTranslation]] = {}
        for key, text, tag, file_path in translations:
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append((key, text, tag))
        return file_groups

    def _group_defs_by_type(
        self, defs_translations: List[TranslationData]
    ) -> Dict[str, Dict[str, str]]:
        """
        按定义类型分组DefInjected翻译数据

        Args:
            defs_translations: DefInjected翻译数据列表

        Returns:
            按定义类型分组的翻译数据字典
        """
        def_groups: Dict[str, Dict[str, str]] = {}
        for full_path, text, _, _ in defs_translations:
            if "/" in full_path:
                def_type_part, field_part = full_path.split("/", 1)
                def_type = def_type_part

                if def_type not in def_groups:
                    def_groups[def_type] = {}
                def_groups[def_type][field_part] = text

        return def_groups

    def _get_target_file_path(self, source_file_path: str, target_dir: Path) -> Path:
        """
        获取目标文件路径

        Args:
            source_file_path: 源文件路径
            target_dir: 目标目录

        Returns:
            目标文件路径
        """
        return target_dir / Path(source_file_path).name


# 导出类和函数
__all__ = [
    "TemplateGenerator",
    "TranslationData",
    "KeyedTranslation",
]
