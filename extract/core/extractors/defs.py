"""
Defs 扫描器

专门用于扫描 Defs 目录中的可翻译内容
"""

from typing import List, Tuple, Dict, Optional
from pathlib import Path
from utils.logging_config import get_logger
from utils.ui_style import ui
from .base import BaseExtractor
from ..filters import ContentFilter


class DefsScanner(BaseExtractor):
    """
    Defs 扫描器

    专门用于扫描 Defs 目录中的可翻译内容
    """

    def __init__(self, config=None):
        """
        初始化 Defs 扫描器

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        super().__init__(config)
        self.logger = get_logger(f"{__name__}.DefsScanner")
        self.content_filter = ContentFilter(config)

    def extract(
        self, source_path: str, language: str = None
    ) -> List[Tuple[str, str, str, str, str, str]]:
        """
        扫描 Defs 目录中的可翻译内容

        Args:
            source_path: 模组目录路径
            language: 语言代码（Defs扫描不需要语言参数）

        Returns:
            List[Tuple[str, str, str, str, str, str]]: 六元组列表 (key, text, tag, rel_path, en_text, def_type)
        """
        self.logger.info("开始扫描 Defs 目录: %s", source_path)

        if not self._validate_source(source_path):
            return []

        defs_dir = Path(source_path) / "Defs"

        if not defs_dir.exists():
            self.logger.warning("Defs 目录不存在: %s", defs_dir)
            return []

        translations = []
        xml_files = list(defs_dir.rglob("*.xml"))

        # 使用进度条进行提取
        for _, xml_file in ui.iter_with_progress(
            xml_files,
            prefix="扫描Defs",
            description=f"正在扫描 Defs 目录中的 {len(xml_files)} 个文件",
        ):
            file_translations = self._extract_from_xml_file(xml_file, defs_dir)
            translations.extend(file_translations)

        self._log_extraction_stats("Defs", len(translations), "Defs")
        return translations

    def _extract_from_xml_file(
        self, xml_file: Path, defs_dir: Path
    ) -> List[Tuple[str, str, str, str]]:
        """
        从单个XML文件提取翻译数据

        Args:
            xml_file: XML文件路径
            defs_dir: Defs目录路径

        Returns:
            List[Tuple[str, str, str, str]]: 四元组列表
        """
        translations = []

        try:
            tree = self._parse_xml_file(str(xml_file))
            if tree is None:
                return translations

            root = tree.getroot() if hasattr(tree, "getroot") else tree

            # 查找所有有 defName 的节点（RimWorld 标准）
            def_nodes = self._find_def_nodes(root)

            self.logger.debug(
                "在 %s 中找到 %d 个定义节点", xml_file.name, len(def_nodes)
            )

            for def_node in def_nodes:
                def_type = def_node.tag
                defname_elem = def_node.find("defName")

                if defname_elem is None or not defname_elem.text:
                    continue

                def_name = defname_elem.text
                field_translations = self._extract_translatable_fields_recursive(
                    def_node, def_type, def_name, "", {}, def_type
                )

                # 转换为标准格式，清理重复的 def_type
                for field_path, text, tag in field_translations:
                    # 清理路径中重复的 def_type 前缀
                    clean_path = field_path
                    if clean_path.startswith(def_type + "."):
                        clean_path = clean_path[len(def_type) + 1 :]

                    full_path = f"{def_type}/{def_name}.{clean_path}"
                    # 去除DefType/前缀，只保留defName.field
                    key = full_path.split("/", 1)[-1] if "/" in full_path else full_path
                    rel_path = str(xml_file.relative_to(defs_dir))
                    # 导出六元组：(key, text, tag, rel_path, en_text, def_type)
                    translations.append((key, text, tag, rel_path, text, def_type))

                self.logger.debug(
                    "从 %s 提取到 %d 条翻译", def_name, len(field_translations)
                )

        except (OSError, IOError, ValueError, TypeError, AttributeError) as e:
            self.logger.error("处理Defs文件时发生错误: %s, %s", xml_file, e)

        return translations

    def _find_def_nodes(self, root) -> List:
        """
        查找所有有 defName 的节点

        Args:
            root: XML根节点

        Returns:
            List: 定义节点列表
        """
        def_nodes = []
        for elem in root.iter():
            defname_elem = elem.find("defName")
            if defname_elem is not None and defname_elem.text:
                def_nodes.append(elem)
        return def_nodes

    def _extract_translatable_fields_recursive(
        self,
        node,
        def_type: str,
        def_name: str,
        path: str = "",
        list_indices: Optional[Dict[str, int]] = None,
        parent_tag: Optional[str] = None,
    ) -> List[Tuple[str, str, str]]:
        """
        递归提取可翻译字段

        Args:
            node: 当前节点
            def_type: 定义类型
            def_name: 定义名称
            path: 当前路径
            list_indices: 列表索引字典
            parent_tag: 父标签

        Returns:
            List[Tuple[str, str, str]]: 三元组列表 (field_path, text, tag)
        """
        if list_indices is None:
            list_indices = {}

        translations = []
        node_tag = node.tag

        # 跳过 defName 节点
        if node_tag == "defName":
            return translations

        # 构建当前路径
        if node_tag == "li":
            # 处理列表项索引
            index_key = f"{path}|li"
            if index_key in list_indices:
                list_indices[index_key] += 1
            else:
                list_indices[index_key] = 0
            current_path = (
                f"{path}.{list_indices[index_key]}"
                if path
                else str(list_indices[index_key])
            )
        else:
            current_path = f"{path}.{node_tag}" if path else node_tag

        # 检查当前节点的文本内容
        if node.text and node.text.strip():
            should_extract = False

            # 安全获取默认字段集合
            try:
                default_fields = self.content_filter.default_fields or set()
                default_fields_lower = set()
                if hasattr(default_fields, "__iter__"):
                    for f in default_fields:
                        if isinstance(f, str):
                            default_fields_lower.add(f.lower())
            except (AttributeError, TypeError, ValueError) as e:
                self.logger.warning("获取 default_fields 失败: %s", e)
                default_fields_lower = set()

            if node_tag == "li":
                # li 节点特殊处理：只有当父标签在默认字段中时才提取
                if (
                    parent_tag
                    and isinstance(parent_tag, str)
                    and parent_tag.lower() in default_fields_lower
                ):
                    should_extract = True
            else:
                # 非 li 节点：检查当前标签是否在默认字段中
                if (
                    isinstance(node_tag, str)
                    and node_tag.lower() in default_fields_lower
                ):
                    should_extract = True

            if should_extract and self.content_filter.filter_content(
                current_path, node.text.strip(), "DefInjected"
            ):
                translations.append((current_path, node.text.strip(), node_tag))

        # 递归处理子节点
        for child in node:
            if child.tag == "li":
                # li 子节点传递当前节点作为父标签，但保持 list_indices 引用
                child_translations = self._extract_translatable_fields_recursive(
                    child,
                    def_type,
                    def_name,
                    current_path,
                    list_indices,
                    parent_tag=node_tag,
                )
            else:
                # 非 li 子节点复制 list_indices，传递当前节点作为父标签
                child_translations = self._extract_translatable_fields_recursive(
                    child,
                    def_type,
                    def_name,
                    current_path,
                    list_indices.copy(),
                    parent_tag=node_tag,
                )
            translations.extend(child_translations)

        return translations
