"""
Keyed 导出器

专门用于导出 Keyed 格式的翻译文件
"""

from typing import List, Tuple, Dict
from pathlib import Path
from utils.logging_config import get_logger
from utils.config import get_config, get_language_subdir
from utils.utils import XMLProcessor
from .base import BaseExporter


class KeyedExporter(BaseExporter):
    """
    Keyed 导出器

    专门用于导出 Keyed 格式的翻译文件
    """

    def __init__(self, config=None):
        """
        初始化 Keyed 导出器

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        super().__init__(config)
        self.logger = get_logger(f"{__name__}.KeyedExporter")

    def export(self, translations: List[Tuple], output_dir: str, language: str) -> bool:
        """
        导出 Keyed 翻译数据

        Args:
            translations: 翻译数据列表
            output_dir: 输出目录
            language: 语言代码

        Returns:
            bool: 是否成功
        """
        return self.export_keyed_template(output_dir, language, translations)

    def export_keyed_template(
        self, output_dir: str, output_language: str, def_translations: List[Tuple]
    ) -> None:
        """
        导出 Keyed 翻译模板，按文件分组生成 XML 文件

        Args:
            output_dir: 输出目录
            output_language: 输出语言
            def_translations: Keyed 翻译数据
        """
        self.logger.info("导出 Keyed 翻译模板")

        keyed_path = self._create_output_directory(output_dir, output_language, "keyed")

        # 按 file_path 分组翻译数据
        file_groups = self._group_by_file_path(def_translations)

        # 为每个 file_path 生成翻译文件
        for file_path, translations in file_groups.items():
            if not translations:
                continue

            # 创建目标文件路径（只保留文件名）
            output_file = keyed_path / Path(file_path).name

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
                self._log_export_stats(str(output_file), len(translations), "Keyed")

    def _group_by_file_path(
        self, def_translations: List[Tuple]
    ) -> Dict[str, List[Tuple]]:
        """按 file_path 分组翻译数据"""
        file_groups = {}
        for item in def_translations:
            key, text, tag, file_path = item[:4]
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append((key, text, tag))
        return file_groups
