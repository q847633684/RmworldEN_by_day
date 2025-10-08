"""
Keyed 提取器

专门用于从 Keyed 目录提取键值对翻译
"""

from typing import List, Tuple
from pathlib import Path
from utils.logging_config import get_logger
from utils.ui_style import ui
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
    ) -> List[Tuple[str, str, str, str, str]]:
        """
        从 Keyed 目录提取翻译

        Args:
            source_path: 模组目录路径
            language: 语言代码

        Returns:
            List[Tuple[str, str, str, str, str]]: 五元组列表 (key, text, tag, rel_path, en_text)
        """
        self.logger.info("开始从 Keyed 目录提取翻译: %s, %s", source_path, language)

        if not self._validate_source(source_path):
            return []

        keyed_dir = self.config.language_config.get_language_subdir(
            source_path, language, "keyed"
        )

        if not keyed_dir.exists():
            self.logger.warning("Keyed 目录不存在: %s", keyed_dir)
            return []

        translations = []
        xml_files = list(keyed_dir.rglob("*.xml"))

        # 使用进度条进行提取
        for _, xml_file in ui.iter_with_progress(
            xml_files,
            prefix="扫描Keyed",
            description=f"正在扫描 {language} Keyed 目录中的 {len(xml_files)} 个文件",
        ):
            file_translations = self._extract_from_xml_file(xml_file, keyed_dir)
            translations.extend(file_translations)

        self._log_extraction_stats("Keyed", len(translations), "Keyed")
        return translations

    def _extract_from_xml_file(
        self, xml_file: Path, keyed_dir: Path
    ) -> List[Tuple[str, str, str, str, str]]:
        """
        从单个XML文件提取翻译数据

        Args:
            xml_file: XML文件路径
            keyed_dir: Keyed目录路径

        Returns:
            List[Tuple[str, str, str, str, str]]: 五元组列表 (key, text, tag, rel_path, en_text)
        """
        translations = []

        try:
            tree = self._parse_xml_file(str(xml_file))
            if tree is None:
                return translations

            rel_path = str(xml_file.relative_to(keyed_dir))

            # 手动处理 XML 以提取英文注释
            last_en_comment = ""
            for elem in tree.iter():
                if type(elem).__name__ == "_Comment":
                    # 处理注释节点
                    text = elem.text or ""
                    if text.strip().startswith("EN:"):
                        last_en_comment = text.strip()[3:].strip()
                elif isinstance(elem.tag, str) and not elem.tag.startswith("{"):
                    # 处理元素节点
                    key, text, tag, en_text = self._parse_comment_and_element(
                        elem, last_en_comment
                    )
                    if self.content_filter.filter_content(key, text, "Keyed"):
                        translations.append((key, text, tag, rel_path, en_text))
                    # 注意：不清空last_en_comment，因为可能有多个元素共享同一个EN注释

            self.logger.debug(
                "从 %s 提取到 %d 条翻译", xml_file.name, len(translations)
            )

        except (OSError, IOError, ValueError, AttributeError, ImportError) as e:
            self.logger.error("处理Keyed文件时发生错误: %s, %s", xml_file, e)

        return translations

    def _parse_comment_and_element(
        self, elem, last_en_comment: str
    ) -> Tuple[str, str, str, str]:
        """
        解析注释和元素，生成翻译数据

        Args:
            elem: XML元素
            last_en_comment: 上一个EN注释内容

        Returns:
            Tuple[str, str, str, str]: (key, text, tag, en_text)
        """
        # 生成key
        key = elem.tag

        # 生成text
        text = elem.text or ""

        # 生成tag
        tag = elem.tag

        # 生成en_text
        # 如果有英文注释，使用注释；否则使用text（英文目录的情况）
        en_text = last_en_comment if last_en_comment else text

        return key, text, tag, en_text
