"""
Day Translation 2 - XML处理器

提供统一的XML文件解析、修改和保存功能。
遵循提示文件标准：PEP 8规范、具体异常处理、用户友好错误信息。
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Optional

try:
    # 尝试相对导入 (包内使用)
    from ..models.exceptions import ImportError as TranslationImportError
    from ..models.exceptions import ProcessingError
except ImportError:
    # 回退到绝对导入 (直接运行时)
    from models.exceptions import ImportError as TranslationImportError
    from models.exceptions import ProcessingError


class XMLProcessor:
    """XML文件处理器"""

    def __init__(self, use_lxml: bool = False):
        """
        初始化XML处理器

        Args:
            use_lxml: 是否使用lxml库（可选，性能更好）
        """
        self.use_lxml = use_lxml

        if use_lxml:
            try:
                import lxml.etree as lxml_et

                self.lxml_et = lxml_et
                logging.debug("使用lxml作为XML解析器")
            except ImportError:
                self.use_lxml = False
                logging.warning("lxml不可用，回退到ElementTree")

    def parse_xml(self, file_path: str) -> Optional[ET.ElementTree]:
        """
        解析XML文件

        Args:
            file_path: XML文件路径

        Returns:
            ElementTree对象，解析失败时返回None

        Raises:
            TranslationImportError: 当文件不存在或无法读取时
            ProcessingError: 当XML解析失败时
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise TranslationImportError(
                    f"XML文件不存在: {file_path}", file_path=str(file_path)
                )

            if self.use_lxml:
                try:
                    tree = self.lxml_et.parse(str(file_path))
                    # 转换为ElementTree格式以保持兼容性
                    return ET.ElementTree(ET.fromstring(self.lxml_et.tostring(tree)))
                except Exception:
                    # 如果lxml解析失败，回退到ElementTree
                    self.use_lxml = False
                    logging.warning(f"lxml解析{file_path}失败，回退到ElementTree")

            return ET.parse(str(file_path))

        except ET.ParseError as e:
            raise ProcessingError(
                f"XML解析错误: {str(e)}",
                operation="parse_xml",
                stage="XML解析",
                affected_items=[str(file_path)],
            )
        except Exception as e:
            raise TranslationImportError(f"读取XML文件失败: {str(e)}", file_path=str(file_path))

    def save_xml(self, tree: ET.ElementTree, file_path: str, encoding: str = "utf-8") -> None:
        """
        保存XML文件

        Args:
            tree: ElementTree对象
            file_path: 输出文件路径
            encoding: 文件编码

        Raises:
            ProcessingError: 当保存失败时
        """
        try:
            # 确保目录存在
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            tree.write(str(output_path), encoding=encoding, xml_declaration=True)

        except Exception as e:
            raise ProcessingError(
                f"保存XML文件失败: {str(e)}",
                operation="save_xml",
                stage="文件保存",
                affected_items=[str(file_path)],
            )

    def update_translations(
        self,
        tree: ET.ElementTree,
        translations: Dict[str, str],
        generate_key_func=None,
        merge: bool = True,
    ) -> bool:
        """
        更新XML文件中的翻译内容

        Args:
            tree: ElementTree对象
            translations: 翻译字典 {key: translated_text}
            generate_key_func: 生成key的函数
            merge: 是否合并现有翻译

        Returns:
            是否有更新

        Raises:
            ProcessingError: 当更新过程中出现错误时
        """
        try:
            updated = False
            root = tree.getroot()

            # 遍历LanguageData节点
            for lang_data in root.findall("LanguageData"):
                for element in lang_data:
                    key = element.tag

                    if generate_key_func:
                        try:
                            key = generate_key_func(element)
                        except Exception:
                            key = element.tag

                    if key in translations:
                        new_text = translations[key]
                        current_text = element.text or ""

                        # 根据merge参数决定是否更新
                        if not merge or not current_text.strip():
                            element.text = new_text
                            updated = True

            return updated

        except Exception as e:
            raise ProcessingError(
                f"更新翻译失败: {str(e)}", operation="update_translations", stage="翻译更新"
            )
