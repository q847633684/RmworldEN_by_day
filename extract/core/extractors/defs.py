"""
Defs 扫描器

专门用于扫描 Defs 目录中的可翻译内容
"""

from typing import List, Tuple, Dict, Optional
from pathlib import Path
from utils.logging_config import get_logger
from utils.path_utils import rel_path_str
from utils.ui_style import ui
from utils.xml_utils import local_tag
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
        self, source_path: str, language: str = None, prefix: Optional[str] = None
    ) -> List[Tuple[str, str, str, str, str, str]]:
        """
        扫描 Defs 目录中的可翻译内容

        Args:
            source_path: 模组目录路径
            language: 语言代码（Defs扫描不需要语言参数）
            prefix: 进度条前缀，默认 "扫描Defs"

        Returns:
            List[Tuple[str, str, str, str, str, str]]: 六元组列表 (key, text, tag, rel_path, en_text, def_type)
        """
        self.logger.info("开始扫描 Defs 目录: %s", source_path)

        if not self._validate_source(source_path):
            return []

        defs_dir = self._find_defs_directory(source_path)
        if defs_dir is None:
            self.logger.warning("未找到 Defs 目录: %s", source_path)
            return []

        translations = []
        xml_files = list(defs_dir.rglob("*.xml"))

        # 首先收集所有抽象定义
        all_abstract_nodes = {}
        for xml_file in xml_files:
            try:
                tree = self._parse_xml_file(str(xml_file))
                if tree is None:
                    continue
                root = tree.getroot() if hasattr(tree, "getroot") else tree
                abstract_nodes = self._find_abstract_nodes(root)
                all_abstract_nodes.update(abstract_nodes)
            except Exception as e:
                self.logger.warning("解析文件时出错: %s, %s", xml_file, e)

        self.logger.debug("收集到 %d 个抽象定义", len(all_abstract_nodes))

        # 使用进度条进行提取
        for _, xml_file in ui.iter_with_progress(
            xml_files,
            prefix=prefix or "扫描Defs",
            description="",
        ):
            file_translations = self._extract_from_xml_file(
                xml_file, defs_dir, all_abstract_nodes
            )
            translations.extend(file_translations)

        self._log_extraction_stats("Defs", len(translations), "Defs")
        return translations

    def _extract_from_xml_file(
        self, xml_file: Path, _defs_dir: Path, all_abstract_nodes: Dict[str, any] = None
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
            # 使用传入的抽象定义，如果没有则查找当前文件的抽象定义
            if all_abstract_nodes is not None:
                abstract_nodes = all_abstract_nodes
            else:
                abstract_nodes = self._find_abstract_nodes(root)

            self.logger.debug(
                "在 %s 中找到 %d 个定义节点，使用 %d 个抽象定义节点",
                xml_file.name,
                len(def_nodes),
                len(abstract_nodes),
            )

            # rel_path 为该 xml 相对 Defs 目录的路径；def_type 在六元组第 6 项；合并前 manager 将 rel_path 规范为 def_type/文件名.xml，按 (key, rel_path) 匹配
            file_rel_path = rel_path_str(_defs_dir, xml_file)

            for def_node in def_nodes:
                # 去掉 XML 命名空间，保证输出目录为 HediffDef 而非 {uri}HediffDef
                tag_local = local_tag(def_node.tag)
                # DefInjected 子文件夹须与 RimWorld Def 类型一致：有 Class 属性时用 Class 最后一段（如 OpinionDef_SexPart），无则用标签名（如 BackstoryDef）
                # 155-169 内层循环用到的 def_type 即为此「class 的 def」类型名
                class_attr = (def_node.get("Class") or "").strip()
                def_type = class_attr.split(".")[-1] if class_attr else tag_local
                defname_elem = def_node.find("defName")
                if defname_elem is None:
                    # 带命名空间时 find("defName") 找不到，尝试按本地名查找
                    defname_elem = self._find_child_by_local_name(def_node, "defName")
                if defname_elem is None or not (defname_elem.text or "").strip():
                    continue

                def_name = defname_elem.text
                field_translations = self._extract_translatable_fields_recursive(
                    def_node, def_type, def_name, "", {}, def_type
                )

                # 检查是否需要继承父类的 stages
                inherited_stages = self._extract_inherited_stages(
                    def_node, abstract_nodes, def_name, def_type
                )
                field_translations.extend(inherited_stages)

                # 转换为标准格式，清理重复的 def_type 或根节点标签（如 <Def Class="..."> 时路径会带 Def.，应去掉）
                for field_path, text, tag in field_translations:
                    clean_path = field_path
                    if clean_path.startswith(def_type + "."):
                        clean_path = clean_path[len(def_type) + 1 :]
                    # 当 XML 根为 <Def Class="..."> 时，递归路径会带 "Def."，RimWorld 键应为 defName.field 不含 Def
                    if tag_local != def_type and clean_path.startswith(tag_local + "."):
                        clean_path = clean_path[len(tag_local) + 1 :]

                    full_path = f"{def_type}/{def_name}.{clean_path}"
                    key = full_path  # key 含 def_type：def_type/def_name.field_path
                    rel_path = file_rel_path
                    # 导出六元组：(key, text, tag, rel_path, en_text, def_type)
                    translations.append((key, text, tag, rel_path, text, def_type))

                self.logger.debug(
                    "从 %s 提取到 %d 条翻译（包含 %d 条继承的 stages）",
                    def_name,
                    len(field_translations),
                    len(inherited_stages),
                )

        except (OSError, IOError, ValueError, TypeError, AttributeError) as e:
            self.logger.error("处理Defs文件时发生错误: %s, %s", xml_file, e)

        return translations

    def _find_defs_directory(self, source_path: str) -> Optional[Path]:
        """
        查找 Defs 目录（无 LoadFolders 时用）。
        只查两处：版本号下 Defs、根目录 Defs。

        Args:
            source_path: 当前路径（版本目录或模组根）

        Returns:
            Optional[Path]: 找到的 Defs 目录路径，未找到则返回 None
        """
        try:
            source_root = Path(source_path).resolve()
        except (OSError, ValueError, TypeError):
            source_root = Path(source_path)
        defs_path = source_root / "Defs"
        if defs_path.exists() and defs_path.is_dir():
            self.logger.info("找到 Defs 目录: %s", defs_path)
            return defs_path
        return None

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
            if defname_elem is None:
                defname_elem = self._find_child_by_local_name(elem, "defName")
            if defname_elem is not None and (defname_elem.text or "").strip():
                def_nodes.append(elem)
        return def_nodes

    @staticmethod
    def _find_child_by_local_name(parent, local_name: str):
        """按本地名查找子节点（兼容带命名空间的 XML）"""
        for child in parent:
            if local_tag(child.tag) == local_name:
                return child
        return None

    def _find_abstract_nodes(self, root) -> Dict[str, any]:
        """
        查找所有抽象定义节点（有 Name 属性的节点）

        Args:
            root: XML根节点

        Returns:
            Dict[str, any]: 抽象定义字典，键为 Name 属性值
        """
        abstract_nodes = {}
        for elem in root.iter():
            name_attr = elem.get("Name")
            if name_attr:
                abstract_nodes[name_attr] = elem
        return abstract_nodes

    def _extract_inherited_stages(
        self, def_node, abstract_nodes: Dict[str, any], def_name: str, _def_type: str
    ) -> List[Tuple[str, str, str]]:
        """
        提取继承的 stages

        Args:
            def_node: 具体定义节点
            abstract_nodes: 抽象定义节点字典
            def_name: 具体定义名称
            def_type: 定义类型

        Returns:
            List[Tuple[str, str, str]]: 继承的 stages 列表
        """
        inherited_stages = []

        # 检查具体定义是否有自己的 stages
        if def_node.find("stages") is not None:
            # 有自己的 stages，不需要继承
            return inherited_stages

        # 查找父类
        parent_name = def_node.get("ParentName")
        if not parent_name or parent_name not in abstract_nodes:
            return inherited_stages

        parent_node = abstract_nodes[parent_name]
        stages_node = parent_node.find("stages")
        if stages_node is None:
            return inherited_stages

        # 提取父类的 stages
        stage_index = 0
        for stage_elem in stages_node.findall("li"):
            label_elem = stage_elem.find("label")
            if label_elem is not None and label_elem.text:
                # 生成键名：defName.stages.index.label
                field_path = f"stages.{stage_index}.label"
                text = label_elem.text.strip()
                tag = "label"
                inherited_stages.append((field_path, text, tag))
                stage_index += 1

        self.logger.debug(
            "从父类 %s 为 %s 继承了 %d 个 stages",
            parent_name,
            def_name,
            len(inherited_stages),
        )

        return inherited_stages

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
        node_tag_local = local_tag(node_tag)

        # 跳过 defName 节点
        if node_tag_local == "defName":
            return translations

        # 构建当前路径（用本地名，便于 key 一致）
        if node_tag_local == "li":
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
            current_path = f"{path}.{node_tag_local}" if path else node_tag_local

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

            if node_tag_local == "li":
                # li 节点特殊处理：只有当父标签在默认字段中时才提取
                parent_local = (
                    local_tag(parent_tag) if isinstance(parent_tag, str) else ""
                )
                if parent_local and parent_local.lower() in default_fields_lower:
                    should_extract = True
            else:
                # 非 li 节点：检查当前标签（本地名）是否在默认字段中
                if (
                    isinstance(node_tag_local, str)
                    and node_tag_local.lower() in default_fields_lower
                ):
                    should_extract = True

            if should_extract and self.content_filter.filter_content(
                current_path, node.text.strip(), "DefInjected"
            ):
                translations.append((current_path, node.text.strip(), node_tag_local))

        # 递归处理子节点
        for child in node:
            if local_tag(child.tag) == "li":
                # li 子节点传递当前节点作为父标签，但保持 list_indices 引用
                child_translations = self._extract_translatable_fields_recursive(
                    child,
                    def_type,
                    def_name,
                    current_path,
                    list_indices,
                    parent_tag=node_tag_local,
                )
            else:
                # 非 li 子节点复制 list_indices，传递当前节点作为父标签
                child_translations = self._extract_translatable_fields_recursive(
                    child,
                    def_type,
                    def_name,
                    current_path,
                    list_indices.copy(),
                    parent_tag=node_tag_local,
                )
            translations.extend(child_translations)

        return translations
