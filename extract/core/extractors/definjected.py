"""
DefInjected 提取器

专门用于从 DefInjected 目录提取翻译结构
"""

from typing import List, Tuple
from pathlib import Path
from utils.logging_config import get_logger
from utils.config import get_language_subdir
from utils.ui_style import ui
from .base import BaseExtractor


class DefInjectedExtractor(BaseExtractor):
    """
    DefInjected 提取器

    专门用于从 DefInjected 目录提取翻译结构，支持提取 EN 注释
    """

    def __init__(self, config=None):
        """
        初始化 DefInjected 提取器

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        super().__init__(config)
        self.logger = get_logger(f"{__name__}.DefInjectedExtractor")

    def extract(
        self, source_path: str, language: str
    ) -> List[Tuple[str, str, str, str, str]]:
        """
        从 DefInjected 目录提取翻译结构

        Args:
            source_path: 模组目录路径
            language: 语言代码

        Returns:
            List[Tuple[str, str, str, str, str]]: 五元组列表 (key, text, tag, rel_path, en_text)
        """
        self.logger.info(
            "开始从 DefInjected 目录提取翻译: %s, %s", source_path, language
        )

        if not self._validate_source(source_path):
            return []

        definjected_dir = get_language_subdir(
            base_dir=source_path, language=language, subdir_type="defInjected"
        )

        if not definjected_dir.exists():
            self.logger.warning("DefInjected 目录不存在: %s", definjected_dir)
            return []

        translations = []
        xml_files = list(definjected_dir.rglob("*.xml"))

        # 使用进度条进行提取
        for i, xml_file in ui.iter_with_progress(
            xml_files,
            prefix="扫描DefInjected",
            description=f"正在扫描 {language} DefInjected 目录中的 {len(xml_files)} 个文件",
        ):
            file_translations = self._extract_from_xml_file(xml_file, definjected_dir)
            translations.extend(file_translations)

        self._log_extraction_stats("DefInjected", len(translations), "DefInjected")
        return translations

    def _extract_from_xml_file(
        self, xml_file: Path, definjected_dir: Path
    ) -> List[Tuple[str, str, str, str, str]]:
        """
        从单个XML文件提取翻译数据

        Args:
            xml_file: XML文件路径
            definjected_dir: DefInjected目录路径

        Returns:
            List[Tuple[str, str, str, str, str]]: 五元组列表
        """
        translations = []

        try:
            tree = self._parse_xml_file(str(xml_file))
            if tree is None:
                return translations

            root = tree.getroot()
            rel_path = str(xml_file.relative_to(definjected_dir))
            last_en_comment = ""

            for elem in root.iter():
                if elem is root:
                    continue  # 跳过根节点

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
                    translations.append((key, text, tag, rel_path, en_text))
                    # 注意：不清空last_en_comment，因为可能有多个元素共享同一个EN注释

        except (OSError, ValueError, AttributeError) as e:
            self.logger.error("处理DefInjected文件时发生错误: %s, %s", xml_file, e)

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
        # 生成key的逻辑与原函数一致
        parent_tags = []
        parent = elem.getparent()
        while parent is not None and parent.tag != elem.getroottree().getroot().tag:
            parent_tags.append(parent.tag)
            parent = parent.getparent()

        # 反转列表
        parent_tags = list(reversed(parent_tags))

        # 生成key
        key = "/".join(parent_tags + [elem.tag]) if parent_tags else elem.tag

        # 生成text
        text = elem.text or ""

        # 生成tag
        tag = elem.tag

        return key, text, tag, last_en_comment
