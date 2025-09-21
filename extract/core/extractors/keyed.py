"""
Keyed 提取器

专门用于从 Keyed 目录提取键值对翻译
"""

from typing import List, Tuple
from pathlib import Path
from utils.logging_config import get_logger
from utils.config import get_config, get_language_subdir
from utils.utils import XMLProcessor
from .base import BaseExtractor
from ..filters import ContentFilter


class KeyedExtractor(BaseExtractor):
    """
    Keyed 提取器

    专门用于从 Keyed 目录提取键值对翻译
    """

    def __init__(self, config=None):
        """
        初始化 Keyed 提取器

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        super().__init__(config)
        self.logger = get_logger(f"{__name__}.KeyedExtractor")
        self.content_filter = ContentFilter(config)

    def extract(
        self, source_path: str, language: str
    ) -> List[Tuple[str, str, str, str]]:
        """
        从 Keyed 目录提取翻译

        Args:
            source_path: 模组目录路径
            language: 语言代码

        Returns:
            List[Tuple[str, str, str, str]]: 四元组列表 (key, text, tag, rel_path)
        """
        self.logger.info("开始从 Keyed 目录提取翻译: %s, %s", source_path, language)

        if not self._validate_source(source_path):
            return []

        keyed_dir = get_language_subdir(
            base_dir=source_path, language=language, subdir_type="keyed"
        )

        if not keyed_dir.exists():
            self.logger.warning("Keyed 目录不存在: %s", keyed_dir)
            return []

        translations = []
        xml_files = list(keyed_dir.rglob("*.xml"))

        for xml_file in xml_files:
            file_translations = self._extract_from_xml_file(xml_file, keyed_dir)
            translations.extend(file_translations)

        self._log_extraction_stats("Keyed", len(translations), "Keyed")
        return translations

    def _extract_from_xml_file(
        self, xml_file: Path, keyed_dir: Path
    ) -> List[Tuple[str, str, str, str]]:
        """
        从单个XML文件提取翻译数据

        Args:
            xml_file: XML文件路径
            keyed_dir: Keyed目录路径

        Returns:
            List[Tuple[str, str, str, str]]: 四元组列表
        """
        translations = []

        try:
            tree = self._parse_xml_file(str(xml_file))
            if tree is None:
                return translations

            rel_path = str(xml_file.relative_to(keyed_dir))

            # 使用 XMLProcessor 提取翻译
            for key, text, tag in self.processor.extract_translations(
                tree, context="Keyed", filter_func=self.content_filter.filter_content
            ):
                translations.append((key, text, tag, rel_path))

            self.logger.debug(
                "从 %s 提取到 %d 条翻译", xml_file.name, len(translations)
            )

        except Exception as e:
            self.logger.error("处理Keyed文件时发生错误: %s, %s", xml_file, e)

        return translations
