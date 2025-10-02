"""
基础导出器抽象类

定义所有导出器的通用接口和行为规范
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from pathlib import Path
import os
from utils.logging_config import get_logger
from user_config import UserConfigManager
from utils.utils import XMLProcessor


class BaseExporter(ABC):
    """
    基础导出器抽象类

    定义所有导出器的通用接口和行为规范
    """

    def __init__(self, config=None):
        """
        初始化基础导出器

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        if config is None:
            config = UserConfigManager()
        self.config = config
        self.processor = XMLProcessor()

    @abstractmethod
    def export(self, translations: List[Tuple], output_dir: str, language: str) -> bool:
        """
        导出翻译数据的抽象方法

        Args:
            translations: 翻译数据列表
            output_dir: 输出目录
            language: 语言代码

        Returns:
            bool: 是否成功
        """
        raise NotImplementedError("子类必须实现 export 方法")

    def _create_output_directory(
        self, output_dir: str, language: str, subdir_type: str
    ) -> Path:
        """
        创建输出目录

        Args:
            output_dir: 基础输出目录
            language: 语言代码
            subdir_type: 子目录类型

        Returns:
            Path: 创建的输出目录路径
        """
        # 使用新配置系统获取语言子目录
        config_manager = UserConfigManager()
        output_path = config_manager.language_config.get_language_subdir(
            output_dir, language, subdir_type
        )

        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug("创建输出目录: %s", output_path)

        return output_path

    def _generate_xml_content(
        self, translations: List[Tuple], processor: XMLProcessor = None
    ) -> object:
        """
        生成XML内容

        Args:
            translations: 翻译数据列表
            processor: XML处理器，如果为None则使用默认处理器

        Returns:
            ElementTree根元素
        """
        if processor is None:
            processor = self.processor

        root = processor.create_element("LanguageData")

        # 按键名排序，保持一致性
        for item in sorted(translations, key=lambda x: x[0]):
            key, text, _, _ = item[:4]  # tag 和 rel_path 暂时未使用

            # 添加英文注释
            comment = processor.create_comment(f"EN: {text}")
            root.append(comment)

            # 添加翻译元素
            processor.create_subelement(root, key, text)

        return root

    def _save_xml_file(
        self, root: object, output_file: str, processor: XMLProcessor = None
    ) -> bool:
        """
        保存XML文件

        Args:
            root: XML根元素
            output_file: 输出文件路径
            processor: XML处理器，如果为None则使用默认处理器

        Returns:
            bool: 是否成功
        """
        if processor is None:
            processor = self.processor

        # 确保目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # 保存文件
        success = processor.save_xml(root, output_file, pretty_print=True)
        if success:
            self.logger.debug("成功保存XML文件: %s", output_file)
        else:
            self.logger.error("保存XML文件失败: %s", output_file)

        return success

    def _log_export_stats(self, output_file: str, count: int, file_type: str = ""):
        """
        记录导出统计信息

        Args:
            output_file: 输出文件路径
            count: 导出数量
            file_type: 文件类型描述
        """
        self.logger.info("导出 %d 条 %s 翻译到: %s", count, file_type, output_file)
