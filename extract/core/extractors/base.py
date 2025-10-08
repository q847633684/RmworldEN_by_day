"""
基础提取器抽象类

定义所有提取器的通用接口和行为规范
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Union
from pathlib import Path
import xml.etree.ElementTree as ET
from utils.logging_config import get_logger
from user_config import UserConfigManager
from utils.utils import XMLProcessor

try:
    import lxml.etree as etree  # type: ignore

    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    etree = None  # type: ignore


class BaseExtractor(ABC):
    """
    基础提取器抽象类

    定义所有提取器的通用接口和行为规范
    """

    def __init__(self, config=None):
        """
        初始化基础提取器

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        if config is None:
            config = UserConfigManager()
        self.config = config
        self.processor = XMLProcessor()

    @abstractmethod
    def extract(self, source_path: str, language: str) -> Union[
        List[Tuple[str, str, str, str]],
        List[Tuple[str, str, str, str, str]],
        List[Tuple[str, str, str, str, str, str]],
    ]:
        """
        提取翻译数据的抽象方法

        Args:
            source_path: 源路径
            language: 语言代码

        Returns:
            四元组、五元组或六元组列表
            - DefsScanner 返回六元组 (key, text, tag, rel_path, en_text, def_type)
            - KeyedExtractor 和 DefInjectedExtractor 返回五元组 (key, text, tag, rel_path, en_text)
        """
        raise NotImplementedError("子类必须实现extract方法")

    def _validate_source(self, source_path: str) -> bool:
        """
        验证源路径是否有效

        Args:
            source_path: 源路径

        Returns:
            bool: 是否有效
        """
        path = Path(source_path)
        if not path.exists():
            self.logger.warning("源路径不存在: %s", source_path)
            return False
        if not path.is_dir():
            self.logger.warning("源路径不是目录: %s", source_path)
            return False
        return True

    def _parse_xml_file(self, file_path: str) -> Optional[object]:
        """
        解析XML文件

        Args:
            file_path: XML文件路径

        Returns:
            ElementTree对象或None
        """
        try:
            tree = self.processor.parse_xml(file_path)
            if tree is None:
                self.logger.error("无法解析XML文件: %s", file_path)
            return tree
        except (FileNotFoundError, ValueError, OSError, IOError, ET.ParseError) as e:
            self.logger.error("解析XML文件时发生错误: %s, %s", file_path, e)
            return None
        except (OSError, IOError, ValueError) as e:
            # 处理lxml异常（如果可用）
            if LXML_AVAILABLE and isinstance(e, etree.XMLSyntaxError):
                self.logger.error("XML语法错误: %s, %s", file_path, e)
            else:
                self.logger.error("解析XML文件时发生未知错误: %s, %s", file_path, e)
            return None

    def _log_extraction_stats(self, source: str, count: int, file_type: str = ""):
        """
        记录提取统计信息

        Args:
            source: 源描述
            count: 提取数量
            file_type: 文件类型描述
        """
        self.logger.info("从 %s 提取到 %d 条 %s 翻译", source, count, file_type)
