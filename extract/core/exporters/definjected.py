"""
DefInjected 导出器

专门用于导出 DefInjected 格式的翻译文件。
支持三种 XML 格式：
  1. nested：<DefName><description>...</description><stages><li>...</li></stages></DefName>
  2. flat_with_li：<DefName.field>text</DefName.field>，列表为 <DefName.stages><li>...</li></DefName.stages>
  3. flat_all：全部平铺 <DefName.stages.0>...</DefName.stages.0>，无 <li> 容器
"""

import re
from typing import List, Tuple, Any, Optional
from utils.logging_config import get_logger
from utils.ui_style import ui
from utils.utils import sanitize_xml
from .base import BaseExporter

DEFINJECTED_FORMAT_NESTED = "nested"
DEFINJECTED_FORMAT_FLAT_WITH_LI = "flat_with_li"
DEFINJECTED_FORMAT_FLAT_ALL = "flat_all"


class DefInjectedExporter(BaseExporter):
    """
    DefInjected 导出器

    专门用于导出 DefInjected 格式的翻译文件
    """

    def __init__(self, config=None):
        """
        初始化 DefInjected 导出器

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        super().__init__(config)
        self.logger = get_logger(f"{__name__}.DefInjectedExporter")

    def export(self, translations: List[Tuple], output_dir: str, language: str) -> bool:
        """
        导出 DefInjected 翻译数据（实现抽象方法）

        Args:
            translations: 翻译数据列表
            output_dir: 输出目录
            language: 语言代码

        Returns:
            bool: 是否成功
        """
        # 使用原始结构导出
        self.export_with_original_structure(output_dir, language, translations)
        return True

    def export_with_original_structure(
        self,
        output_dir: str,
        output_language: str,
        def_translations: List[Tuple],
        xml_format: Optional[str] = None,
    ) -> None:
        """
        按原始文件路径结构导出 DefInjected 翻译。

        Args:
            output_dir: 输出目录
            output_language: 输出语言
            def_translations: DefInjected 翻译数据
            xml_format: 可选，nested / flat_with_li / flat_all，默认从配置读取
        """
        self.logger.info("按原始文件路径结构导出 DefInjected 翻译")

        def_injected_path = self._create_output_directory(
            output_dir, output_language, "definjected"
        )

        # 按 file_path 分组，保留 en_text 用于导出注释
        file_groups = {}
        for item in def_translations:
            key, text, tag, file_path = item[:4]
            en_text = item[4] if len(item) >= 5 else text
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append((key, text, tag, en_text))

        # 使用进度条进行导出
        for _, (file_path, translations) in ui.iter_with_progress(
            file_groups.items(),
            prefix="生成DefInjected",
            description=f"正在生成 DefInjected 模板中的 {len(file_groups)} 个文件",
        ):

            output_file = def_injected_path / file_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            fmt = xml_format or self._get_definjected_xml_format()
            root = self._build_languagedata(translations, fmt)

            success = self._save_xml_file(root, str(output_file))
            if success:
                self._log_export_stats(
                    str(output_file), len(translations), "DefInjected"
                )

    def export_with_defs_structure(
        self,
        output_dir: str,
        output_language: str,
        def_translations: List[Tuple],
        xml_format: Optional[str] = None,
    ) -> None:
        """
        按 DefType 分组导出 DefInjected 翻译。

        Args:
            xml_format: 可选，nested / flat_with_li / flat_all
        """
        self.logger.info("按 DefType 分组导出 DefInjected 翻译")

        def_injected_path = self._create_output_directory(
            output_dir, output_language, "definjected"
        )

        # 按 DefType 分组，保留 en_text 用于导出注释
        file_groups = {}
        for item in def_translations:
            key, text, tag, _, en_text, def_type = item[:6]
            if def_type not in file_groups:
                file_groups[def_type] = []
            file_groups[def_type].append((key, text, tag, en_text))

        # 使用进度条进行导出
        for _, (def_type, translations) in ui.iter_with_progress(
            file_groups.items(),
            prefix="生成DefInjected",
            description=f"正在生成 DefInjected 模板中的 {len(file_groups)} 个文件",
        ):

            # 创建对应的目录结构
            type_dir = def_injected_path / def_type
            type_dir.mkdir(parents=True, exist_ok=True)

            output_file = type_dir / f"{def_type}.xml"

            fmt = xml_format or self._get_definjected_xml_format()
            root = self._build_languagedata(translations, fmt)

            success = self._save_xml_file(root, str(output_file))
            if success:
                self._log_export_stats(
                    str(output_file), len(translations), "DefInjected"
                )

    def export_with_file_structure(
        self,
        output_dir: str,
        output_language: str,
        def_translations: List[Tuple],
        xml_format: Optional[str] = None,
    ) -> None:
        """
        按原始 Defs 文件目录结构导出 DefInjected 翻译。

        Args:
            xml_format: 可选，nested / flat_with_li / flat_all
        """
        self.logger.info("按原始 Defs 文件目录结构导出 DefInjected 翻译")

        def_injected_path = self._create_output_directory(
            output_dir, output_language, "definjected"
        )

        # 按 rel_path 分组，保留 en_text 用于导出注释
        file_groups = {}
        for item in def_translations:
            key, text, tag, rel_path = item[:4]
            en_text = item[4] if len(item) >= 5 else text
            if rel_path not in file_groups:
                file_groups[rel_path] = []
            file_groups[rel_path].append((key, text, tag, en_text))

        # 使用进度条进行导出
        for _, (rel_path, translations) in ui.iter_with_progress(
            file_groups.items(),
            prefix="生成DefInjected",
            description=f"正在生成 DefInjected 模板中的 {len(file_groups)} 个文件",
        ):

            output_file = def_injected_path / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            fmt = xml_format or self._get_definjected_xml_format()
            root = self._build_languagedata(translations, fmt)

            success = self._save_xml_file(root, str(output_file))
            if success:
                self._log_export_stats(
                    str(output_file), len(translations), "DefInjected"
                )

    def _get_or_create_child(
        self, parent: Any, tag: str, text: Optional[str] = None
    ) -> Any:
        """获取父节点下名为 tag 的子节点，不存在则创建并追加。"""
        for child in parent:
            if child.tag == tag:
                if text is not None:
                    child.text = sanitize_xml(text) if text else ""
                return child
        return self.processor.create_subelement(parent, tag, text)

    def _get_definjected_xml_format(self) -> str:
        """从配置读取 DefInjected XML 格式，默认 flat_with_li。"""
        try:
            lang = getattr(self.config, "language_config", None)
            fmt = (
                lang.get_value("definjected_xml_format", DEFINJECTED_FORMAT_FLAT_WITH_LI)
                if lang is not None
                else DEFINJECTED_FORMAT_FLAT_WITH_LI
            )
        except Exception:
            return DEFINJECTED_FORMAT_FLAT_WITH_LI
        if fmt in (
            DEFINJECTED_FORMAT_NESTED,
            DEFINJECTED_FORMAT_FLAT_WITH_LI,
            DEFINJECTED_FORMAT_FLAT_ALL,
        ):
            return fmt
        return DEFINJECTED_FORMAT_FLAT_WITH_LI

    def _build_languagedata(
        self, translations: List[Tuple], xml_format: str
    ) -> Any:
        """根据 xml_format 选择构建方式：nested / flat_with_li / flat_all。"""
        if xml_format == DEFINJECTED_FORMAT_NESTED:
            return self._build_languagedata_nested(translations)
        if xml_format == DEFINJECTED_FORMAT_FLAT_ALL:
            return self._build_languagedata_flat_all(translations)
        return self._build_languagedata_flat_with_li(translations)

    def _en_comment(self, en_text: str) -> Any:
        """生成并返回 EN 注释节点（不追加到父节点）。"""
        return self.processor.create_comment(f"EN: {en_text or ''}")

    def _norm_key(self, k: str) -> str:
        k = re.sub(r"[^A-Za-z0-9_.]", ".", k)
        return k if re.match(r"^[A-Za-z_]", k) else "_" + k

    def _build_languagedata_nested(
        self, translations: List[Tuple]
    ) -> Any:
        """
        格式1：嵌套树。<DefName><description>...</description><stages><li>...</li></stages></DefName>
        每条翻译前插入 EN 注释。
        """
        root = self.processor.create_element("LanguageData")
        if not translations:
            return root
        for item in sorted(translations, key=lambda x: x[0]):
            key, text, _, en_text = item[0], item[1], item[2], (item[3] if len(item) > 3 else item[1])
            if text is None:
                text = ""
            if en_text is None:
                en_text = text
            key = self._norm_key(key)
            parts = key.split(".")
            if not parts:
                continue
            def_name = parts[0]
            def_elem = self._get_or_create_child(root, def_name, None)
            if len(parts) == 1:
                continue
            parent = def_elem
            for i in range(1, len(parts)):
                segment = parts[i]
                if segment.isdigit():
                    parent.append(self._en_comment(en_text))
                    self.processor.create_subelement(parent, "li", text)
                    break
                if i == len(parts) - 1:
                    parent.append(self._en_comment(en_text))
                    self._get_or_create_child(parent, segment, text)
                else:
                    parent = self._get_or_create_child(parent, segment, None)
        return root

    def _build_languagedata_flat_with_li(
        self, translations: List[Tuple]
    ) -> Any:
        """
        格式2：平铺标签 + 列表用 <li>，每条前插入 EN 注释。
        """
        root = self.processor.create_element("LanguageData")
        if not translations:
            return root
        simple_items: List[Tuple[str, str, str]] = []  # (key, text, en_text)
        list_groups: dict = {}  # container -> [(idx, text, en_text), ...]

        for item in translations:
            key, text = item[0], item[1]
            en_text = item[3] if len(item) > 3 else text
            if text is None:
                text = ""
            if en_text is None:
                en_text = text
            key = self._norm_key(key)
            parts = key.split(".")
            if not parts:
                continue
            last = parts[-1]
            if last.isdigit():
                container = ".".join(parts[:-1])
                idx = int(last)
                list_groups.setdefault(container, []).append((idx, text, en_text))
            else:
                simple_items.append((key, text, en_text))

        ordered: List[Tuple[str, str, str, Optional[List[Tuple[int, str, str]]]]] = []
        for k, t, en in simple_items:
            ordered.append((k, t, en, None))
        for container, items in list_groups.items():
            ordered.append((container, "", "", sorted(items, key=lambda x: x[0])))
        ordered.sort(key=lambda x: x[0])

        for sort_key, text, en_text, list_items in ordered:
            if list_items is not None:
                container_elem = self.processor.create_subelement(root, sort_key, None)
                for _, li_text, li_en in list_items:
                    container_elem.append(self._en_comment(li_en))
                    self.processor.create_subelement(container_elem, "li", li_text)
            else:
                root.append(self._en_comment(en_text))
                self.processor.create_subelement(root, sort_key, text)

        return root

    def _build_languagedata_flat_all(
        self, translations: List[Tuple]
    ) -> Any:
        """
        格式3：全部平铺，每条前插入 EN 注释。
        """
        root = self.processor.create_element("LanguageData")
        if not translations:
            return root
        for item in sorted(translations, key=lambda x: x[0]):
            key, text = item[0], item[1]
            en_text = item[3] if len(item) > 3 else text
            if text is None:
                text = ""
            if en_text is None:
                en_text = text
            key = self._norm_key(key)
            if not key:
                continue
            root.append(self._en_comment(en_text))
            self.processor.create_subelement(root, key, text)
        return root
