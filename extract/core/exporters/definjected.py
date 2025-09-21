"""
DefInjected 导出器

专门用于导出 DefInjected 格式的翻译文件
"""

import os
import re
from typing import List, Tuple, Dict
from pathlib import Path
from utils.logging_config import get_logger
from utils.config import get_config, get_language_subdir
from utils.utils import XMLProcessor
from .base import BaseExporter


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
        导出 DefInjected 翻译数据

        Args:
            translations: 翻译数据列表
            output_dir: 输出目录
            language: 语言代码

        Returns:
            bool: 是否成功
        """
        # 默认使用按类型分组的方式
        return self.export_with_defs_structure(output_dir, language, translations)

    def export_with_original_structure(
        self, output_dir: str, output_language: str, def_translations: List[Tuple]
    ) -> None:
        """
        按原始文件路径结构导出 DefInjected 翻译

        Args:
            output_dir: 输出目录
            output_language: 输出语言
            def_translations: DefInjected 翻译数据
        """
        self.logger.info("按原始文件路径结构导出 DefInjected 翻译")

        def_injected_path = self._create_output_directory(
            output_dir, output_language, "defInjected"
        )

        # 按 file_path 分组翻译数据
        file_groups = self._group_by_file_path(def_translations)

        # 为每个 file_path 生成翻译文件
        for file_path, translations in file_groups.items():
            if not translations:
                continue

            output_file = def_injected_path / file_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 生成 XML 内容
            root = self.processor.create_element("LanguageData")

            # 按键名排序，保持一致性
            for key, text, _ in sorted(translations, key=lambda x: x[0]):
                # 添加英文注释
                comment = self.processor.create_comment(f"EN: {text}")
                root.append(comment)

                # 添加翻译元素
                self.processor.create_subelement(root, key, text)

            # 保存文件
            success = self._save_xml_file(root, str(output_file))
            if success:
                self._log_export_stats(
                    str(output_file), len(translations), "DefInjected"
                )

    def export_with_defs_structure(
        self, output_dir: str, output_language: str, def_translations: List[Tuple]
    ) -> None:
        """
        按 DefType 分组导出 DefInjected 翻译

        Args:
            output_dir: 输出目录
            output_language: 输出语言
            def_translations: DefInjected 翻译数据
        """
        self.logger.info("按 DefType 分组导出 DefInjected 翻译")

        def_injected_path = self._create_output_directory(
            output_dir, output_language, "defInjected"
        )

        # 按 DefType 分组翻译内容
        file_groups = self._group_by_def_type(def_translations)

        # 为每个 DefType 生成 XML 文件
        for def_type, translations in file_groups.items():
            if not translations:
                continue

            # 创建对应的目录结构
            type_dir = def_injected_path / f"{def_type}Defs"
            type_dir.mkdir(parents=True, exist_ok=True)

            output_file = type_dir / f"{def_type}Defs.xml"

            # 生成 XML 内容
            root = self.processor.create_element("LanguageData")

            # 按键名排序，保持一致性
            for full_key, text, _ in sorted(translations, key=lambda x: x[0]):
                # 添加英文注释
                comment = self.processor.create_comment(f"EN: {text}")
                root.append(comment)

                # 添加翻译元素
                self.processor.create_subelement(root, full_key, text)

            # 保存文件
            success = self._save_xml_file(root, str(output_file))
            if success:
                self._log_export_stats(
                    str(output_file), len(translations), "DefInjected"
                )

    def export_with_file_structure(
        self, output_dir: str, output_language: str, def_translations: List[Tuple]
    ) -> None:
        """
        按原始 Defs 文件目录结构导出 DefInjected 翻译

        Args:
            output_dir: 输出目录
            output_language: 输出语言
            def_translations: DefInjected 翻译数据
        """
        self.logger.info("按原始 Defs 文件目录结构导出 DefInjected 翻译")

        def_injected_path = self._create_output_directory(
            output_dir, output_language, "defInjected"
        )

        # 按 rel_path 分组翻译数据
        file_groups = self._group_by_rel_path(def_translations)

        for rel_path, translations in file_groups.items():
            if not translations:
                continue

            output_file = def_injected_path / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            root = self.processor.create_element("LanguageData")

            for key, text, _ in sorted(translations, key=lambda x: x[0]):
                if text is None:
                    text = ""
                assert isinstance(text, str), f"text 非字符串: {text}"

                # 去除 DefType/ 只保留 defName.字段
                if "/" in key:
                    _, tag_name = key.split("/", 1)
                else:
                    tag_name = key

                # 合法性修复：只允许字母、数字、下划线、点号，其它替换为点号
                tag_name = re.sub(r"[^A-Za-z0-9_.]", ".", tag_name)
                if not re.match(r"^[A-Za-z_]", tag_name):
                    tag_name = "_" + tag_name

                # 添加英文注释
                comment = self.processor.create_comment(f"EN: {text}")
                root.append(comment)

                # 添加翻译元素
                self.processor.create_subelement(root, tag_name, text)

            success = self._save_xml_file(root, str(output_file))
            if success:
                self._log_export_stats(
                    str(output_file), len(translations), "DefInjected"
                )

    def _group_by_file_path(
        self, def_translations: List[Tuple]
    ) -> Dict[str, List[Tuple]]:
        """按 file_path 分组翻译数据"""
        file_groups = {}
        for item in def_translations:
            k, t, g, f = item[:4]
            if f not in file_groups:
                file_groups[f] = []
            file_groups[f].append((k, t, g))
        return file_groups

    def _group_by_def_type(
        self, def_translations: List[Tuple]
    ) -> Dict[str, List[Tuple]]:
        """按 DefType 分组翻译内容"""
        file_groups = {}
        for item in def_translations:
            full_path, text, tag, _ = item[:4]
            # 从 full_path 生成键名和提取 def_type
            if "/" in full_path:
                def_type_part, field_part = full_path.split("/", 1)
                if "." in field_part:
                    def_name, field_path = field_part.split(".", 1)
                    full_key = f"{def_name}.{field_path}"
                else:
                    full_key = field_part

                # 清理 def_type 名称
                if "." in def_type_part:
                    def_type = def_type_part.split(".")[-1]
                else:
                    def_type = def_type_part
            else:
                full_key = full_path
                def_type = "UnknownDef"

            # 使用 def_type 作为分组依据
            if def_type not in file_groups:
                file_groups[def_type] = []
            file_groups[def_type].append((full_key, text, tag))

        return file_groups

    def _group_by_rel_path(
        self, def_translations: List[Tuple]
    ) -> Dict[str, List[Tuple]]:
        """按 rel_path 分组翻译数据"""
        file_groups = {}
        for item in def_translations:
            key, text, tag, rel_path = item[:4]
            if rel_path not in file_groups:
                file_groups[rel_path] = []
            file_groups[rel_path].append((key, text, tag))
        return file_groups
