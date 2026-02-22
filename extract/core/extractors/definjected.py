"""
DefInjected 提取器

专门用于从 DefInjected 目录提取翻译结构。
支持三种 XML 格式的解析：nested / flat_with_li / flat_all，统一输出 key 为 DefName.field 或 DefName.field.0。
"""

from typing import List, Optional, Tuple
from pathlib import Path
from utils.constants import SUBDIR_TYPE_DEFINJECTED
from utils.logging_config import get_logger
from utils.path_utils import rel_path_str
from utils.ui_style import ui
from utils.utils import normalize_xml_entities_in_text
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
        self, source_path: str, language: str, prefix: Optional[str] = None
    ) -> List[Tuple[str, str, str, str, str]]:
        """
        从 DefInjected 目录提取翻译结构

        Args:
            source_path: 模组目录路径
            language: 语言代码
            prefix: 进度条前缀，默认 "扫描DefInjected"

        Returns:
            List[Tuple[str, str, str, str, str]]: 五元组列表 (key, text, tag, rel_path, en_text)
        """
        self.logger.info(
            "开始从 DefInjected 目录提取翻译: %s, %s", source_path, language
        )

        if not self._validate_source(source_path):
            return []

        definjected_dir = self.config.language_config.get_language_subdir(
            source_path, language, SUBDIR_TYPE_DEFINJECTED
        )
        if not definjected_dir.exists():
            self.logger.warning("DefInjected 目录不存在: %s", definjected_dir)
            return []

        translations = []
        xml_files = list(definjected_dir.rglob("*.xml"))

        # 使用进度条进行提取
        for _i, xml_file in ui.iter_with_progress(
            xml_files,
            prefix=prefix or "扫描DefInjected",
            description="",
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
            rel_path = rel_path_str(definjected_dir, xml_file)
            last_en_comment = ""

            for elem in root.iter():
                if elem is root:
                    continue  # 跳过根节点

                if type(elem).__name__ == "_Comment":
                    text = elem.text or ""
                    if text.strip().startswith("EN:"):
                        last_en_comment = text.strip()[3:].strip()
                elif isinstance(elem.tag, str) and not elem.tag.startswith("{"):
                    # 跳过仅作容器的节点（如 <stages>），只输出叶子或 <li>
                    has_element_children = any(
                        True for c in elem
                        if isinstance(getattr(c, "tag", None), str) and not str(c.tag).startswith("{")
                    )
                    if has_element_children and elem.tag != "li":
                        continue
                    key, text, tag, en_text = self._parse_comment_and_element(
                        elem, root, last_en_comment
                    )
                    if not key:
                        continue
                    translations.append((key, text, tag, rel_path, en_text))

        except (OSError, ValueError, AttributeError) as e:
            self.logger.error("处理DefInjected文件时发生错误: %s, %s", xml_file, e)

        return translations

    def _parse_comment_and_element(
        self, elem, root, last_en_comment: str
    ) -> Tuple[str, str, str, str]:
        """
        解析注释和元素，生成翻译数据。支持三种格式，统一 key 为 DefName.field 或 DefName.field.0。
        """
        # 收集父链，路径中的 <li> 用索引代替，与 flat_all 的 DefName.field.0 一致
        parent_tags = []
        p = elem.getparent()
        while p is not None and p != root:
            pt = getattr(p, "tag", None)
            if pt == "li":
                parent = p.getparent()
                if parent is not None:
                    li_siblings = [c for c in parent if getattr(c, "tag", None) == "li"]
                    try:
                        idx = li_siblings.index(p)
                    except ValueError:
                        idx = 0
                    parent_tags.append(str(idx))
                else:
                    parent_tags.append("0")
            elif isinstance(pt, str) and not pt.startswith("{"):
                parent_tags.append(pt)
            p = p.getparent()
        parent_tags = list(reversed(parent_tags))

        tag = elem.tag
        text = normalize_xml_entities_in_text((elem.text or "").strip())

        # <li> 节点：key = 父路径.索引（0-based）
        if tag == "li":
            parent = elem.getparent()
            if parent is not None:
                li_siblings = [c for c in parent if getattr(c, "tag", None) == "li"]
                try:
                    idx = li_siblings.index(elem)
                except ValueError:
                    idx = 0
                key = ".".join(parent_tags + [str(idx)])
            else:
                key = ".".join(parent_tags + ["0"])
        else:
            # 平铺格式（flat_all）：直接子元素标签名即 key（如 Sex_Anal.modExtensions.0.RMBLabel）
            if not parent_tags and "." in tag:
                key = tag
            else:
                key = ".".join(parent_tags + [tag]) if parent_tags else tag

        en_text = last_en_comment if last_en_comment else text
        return key, text, tag, en_text
