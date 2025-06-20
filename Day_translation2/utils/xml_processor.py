"""
企业级XML处理器模块
从day_translation系统迁移而来的高级XML处理工具

功能特性:
- 双引擎支持: lxml和ElementTree
- Schema验证
- 智能合并
- XPath查询
- 注释处理
- 异常处理
- 性能优化
- 缓存机制

迁移日期: 2024-12-20
原始来源: day_translation/utils/utils.py
"""

import logging
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from lxml import etree

    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    logging.warning("lxml 未安装，将使用 ElementTree")

try:
    from ..config import UnifiedConfig

    CONFIG = UnifiedConfig()
except ImportError:
    CONFIG = None

# 导入异常类
try:
    from ..models.exceptions import ImportError as TranslationImportError
    from ..models.exceptions import ProcessingError, ValidationError
except ImportError:
    # 如果无法导入，定义临时异常类用于独立运行
    class ValidationError(Exception):
        pass

    class ProcessingError(Exception):
        pass

    class TranslationImportError(Exception):
        pass


@dataclass
class XMLProcessorConfig:
    """XML 处理器配置"""

    use_lxml: bool = True
    validate_xml: bool = True
    pretty_print: bool = True
    encoding: str = "utf-8"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    preserve_comments: bool = True
    preserve_whitespace: bool = False
    schema_cache_size: int = 10
    error_on_invalid: bool = False
    default_namespace: Optional[str] = None


class AdvancedXMLProcessor:
    """企业级 XML 处理器，专注于翻译内容的提取和更新"""

    def __init__(self, config: Optional[XMLProcessorConfig] = None):
        """
        初始化 XML 处理器

        Args:
            config: 处理器配置

        Raises:
            ValidationError: 当配置无效时
        """
        try:
            self.config = config or XMLProcessorConfig()
            self.use_lxml = self.config.use_lxml and LXML_AVAILABLE

            if self.use_lxml:
                self.parser = etree.XMLParser(
                    remove_comments=not self.config.preserve_comments,
                    recover=not self.config.error_on_invalid,
                    remove_blank_text=not self.config.preserve_whitespace,
                )
            else:
                self.parser = None

            self._schema_cache = {}
            self._namespace_map = {}

            if self.config.default_namespace:
                self._namespace_map[None] = self.config.default_namespace

            logging.debug(f"XML处理器初始化完成: use_lxml={self.use_lxml}")

        except Exception as e:
            raise ValidationError(f"XML处理器初始化失败: {str(e)}")

    def _get_schema(self, schema_path: str) -> Optional[Any]:
        """获取 XML Schema"""
        if not self.use_lxml or not self.config.validate_xml:
            return None

        if schema_path not in self._schema_cache:
            try:
                schema = etree.XMLSchema(etree.parse(schema_path))
                if len(self._schema_cache) >= self.config.schema_cache_size:
                    # 移除最旧的缓存
                    self._schema_cache.pop(next(iter(self._schema_cache)))
                self._schema_cache[schema_path] = schema
            except Exception as e:
                logging.error(f"加载 Schema 失败: {schema_path}: {e}")
                if self.config.error_on_invalid:
                    raise ProcessingError(f"Schema加载失败: {str(e)}")
                return None
        return self._schema_cache[schema_path]

    def validate_against_schema(self, tree: Any, schema_path: str) -> bool:
        """验证 XML 是否符合 Schema"""
        if not self.use_lxml or not self.config.validate_xml:
            return True

        schema = self._get_schema(schema_path)
        if not schema:
            return True

        try:
            return schema.validate(tree)
        except Exception as e:
            logging.error(f"Schema 验证失败: {e}")
            if self.config.error_on_invalid:
                raise ValidationError(f"XML格式验证失败: {str(e)}")
            return False

    def parse_xml(
        self, file_path: str, schema_path: Optional[str] = None
    ) -> Optional[Any]:
        """
        安全解析 XML 文件

        Args:
            file_path: XML 文件路径
            schema_path: XML Schema 路径

        Returns:
            XML 树对象，解析失败返回 None

        Raises:
            TranslationImportError: 当文件不存在或无法读取时
            ProcessingError: 当XML解析失败时
        """
        file_path = str(Path(file_path).resolve())

        if not os.path.exists(file_path):
            raise TranslationImportError(f"文件不存在: {file_path}")

        # 检查文件大小
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.config.max_file_size:
                raise ProcessingError(
                    f"文件过大: {file_size} bytes > {self.config.max_file_size} bytes"
                )
        except OSError as e:
            raise TranslationImportError(f"无法访问文件: {file_path}, 错误: {e}")

        try:
            if self.use_lxml:
                tree = etree.parse(file_path, self.parser)
                # Schema验证
                if schema_path and not self.validate_against_schema(tree, schema_path):
                    logging.warning(f"XML Schema验证失败: {file_path}")
            else:
                tree = ET.parse(file_path)

            logging.debug(f"XML解析成功: {file_path}")
            return tree

        except (etree.XMLSyntaxError, ET.ParseError) as e:
            raise ProcessingError(f"XML解析失败: {file_path}, 错误: {e}")
        except Exception as e:
            raise ProcessingError(f"解析XML时发生未知错误: {file_path}, 错误: {e}")

    def save_xml(
        self,
        tree: Any,
        file_path: str,
        pretty_print: Optional[bool] = None,
        encoding: Optional[str] = None,
    ) -> bool:
        """
        保存 XML 文件

        Args:
            tree: XML 树对象
            file_path: 保存路径
            pretty_print: 是否美化输出
            encoding: 文件编码

        Returns:
            是否保存成功

        Raises:
            ProcessingError: 当保存失败时
        """
        file_path = str(Path(file_path).resolve())

        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            pretty_print = (
                self.config.pretty_print if pretty_print is None else pretty_print
            )
            encoding = self.config.encoding if encoding is None else encoding

            if self.use_lxml:
                tree.write(
                    file_path,
                    encoding=encoding,
                    xml_declaration=True,
                    pretty_print=pretty_print,
                )
            else:
                # ElementTree不支持pretty_print参数
                tree.write(file_path, encoding=encoding, xml_declaration=True)

                # 如果需要格式化，手动处理
                if pretty_print:
                    try:
                        import xml.dom.minidom

                        dom = xml.dom.minidom.parse(file_path)
                        with open(file_path, "w", encoding=encoding) as f:
                            f.write(dom.toprettyxml(indent="  ", encoding=None))
                    except Exception:
                        # 如果格式化失败，保持原样
                        pass

            logging.debug(f"XML保存成功: {file_path}")
            return True

        except Exception as e:
            raise ProcessingError(f"保存XML文件失败: {file_path}, 错误: {e}")

    def extract_translations(
        self,
        tree: Any,
        context: str = "",
        filter_func: Optional[Callable] = None,
        include_attributes: bool = True,
    ) -> List[Tuple[str, str, str]]:
        """
        提取可翻译内容

        Args:
            tree: XML 树对象
            context: 上下文
            filter_func: 过滤函数
            include_attributes: 是否包含属性

        Returns:
            提取的翻译列表 [(key, text, tag), ...]
        """
        translations = []
        root = tree.getroot() if hasattr(tree, "getroot") else tree

        # 使用 xpath 或 iter 遍历
        elements = root.xpath(".//*") if self.use_lxml else root.iter()

        for elem in elements:
            # 提取元素文本
            if elem.text and elem.text.strip():
                text = elem.text.strip()
                if not filter_func or filter_func(text):
                    key = self._get_element_key(elem)
                    translations.append((key, text, elem.tag))

            # 提取属性文本
            if include_attributes:
                for attr_name, attr_value in elem.attrib.items():
                    if attr_value and attr_value.strip():
                        if not filter_func or filter_func(attr_value):
                            key = f"{self._get_element_key(elem)}@{attr_name}"
                            translations.append(
                                (key, attr_value.strip(), f"{elem.tag}@{attr_name}")
                            )

        return translations

    def update_translations(
        self,
        tree: Any,
        translations: Dict[str, str],
        generate_key_func: Optional[Callable] = None,
        merge: bool = True,
        include_attributes: bool = True,
    ) -> bool:
        """
        更新 XML 中的翻译

        Args:
            tree: XML 树对象
            translations: 翻译字典
            generate_key_func: 生成键的函数
            merge: 是否合并更新
            include_attributes: 是否更新属性

        Returns:
            是否更新成功
        """
        modified = False
        root = tree.getroot() if self.use_lxml else tree

        # 使用 xpath 或 iter 遍历
        elements = root.xpath(".//*") if self.use_lxml else root.iter()

        for elem in elements:
            key = (
                generate_key_func(elem)
                if generate_key_func
                else self._get_element_key(elem)
            )

            # 更新元素文本
            if key in translations:
                if elem.text != translations[key] or not merge:
                    elem.text = self.sanitize_xml(translations[key])
                    modified = True

            # 更新属性
            if include_attributes:
                for attr_name in elem.attrib:
                    attr_key = f"{key}@{attr_name}"
                    if attr_key in translations:
                        if elem.get(attr_name) != translations[attr_key] or not merge:
                            elem.set(
                                attr_name, self.sanitize_xml(translations[attr_key])
                            )
                            modified = True

        return modified

    def _get_element_key(self, elem: Any) -> str:
        """获取元素的键"""
        if self.use_lxml:
            # lxml支持xpath
            xpath = elem.getroottree().getpath(elem)
            return xpath.replace("/", ".").lstrip(".")
        else:
            # ElementTree使用标签名
            return elem.tag

    def get_element_by_xpath(self, tree: Any, xpath: str) -> List[Any]:
        """
        使用 XPath 获取元素

        Args:
            tree: XML 树对象
            xpath: XPath 表达式

        Returns:
            匹配的元素列表
        """
        if not self.use_lxml:
            logging.warning("XPath查询需要lxml支持，当前使用ElementTree")
            return []

        try:
            root = tree.getroot() if hasattr(tree, "getroot") else tree
            return root.xpath(xpath, namespaces=self._namespace_map)
        except Exception as e:
            logging.error(f"XPath查询失败: {xpath}, 错误: {e}")
            return []

    def smart_merge_xml_translations(
        self,
        xml_file_path: str,
        new_translations: Dict[str, str],
        preserve_manual_edits: bool = True,
    ) -> bool:
        """
        智能合并XML翻译文件

        实现智能合并逻辑：
        1. 扫描现有XML中的key-text对
        2. 替换已存在的key的翻译（可选择保留手动编辑）
        3. 添加缺失的key
        4. 保留XML结构和注释

        Args:
            xml_file_path: XML文件路径
            new_translations: 新的翻译内容
            preserve_manual_edits: 是否保留手动编辑的翻译

        Returns:
            是否成功合并

        Raises:
            ProcessingError: 当合并过程中出现错误时
        """
        try:
            if not os.path.exists(xml_file_path):
                # 文件不存在，创建新文件
                return self._create_new_xml_file(xml_file_path, new_translations)

            # 读取现有XML文件
            tree = self.parse_xml(xml_file_path)
            if tree is None:
                raise ProcessingError(f"无法解析XML文件: {xml_file_path}")

            root = tree.getroot() if self.use_lxml else tree

            # 1. 扫描现有的key-text对
            existing_keys = set()
            elements_map = {}  # key -> element

            for elem in root:
                if elem.tag and elem.text:
                    key = elem.tag
                    existing_keys.add(key)
                    elements_map[key] = elem

            logging.info(f"扫描到现有翻译条目: {len(existing_keys)} 个")

            # 2. 处理现有key的翻译更新
            updated_count = 0
            for key in existing_keys:
                if key in new_translations:
                    elem = elements_map[key]
                    old_text = elem.text
                    new_text = new_translations[key]

                    # 检查是否保留手动编辑
                    if preserve_manual_edits and self._is_machine_translation(old_text):
                        # 只有当现有翻译看起来是机器翻译时才替换
                        elem.text = self.sanitize_xml(new_text)
                        updated_count += 1
                    elif not preserve_manual_edits:
                        # 不保留手动编辑，直接替换
                        elem.text = self.sanitize_xml(new_text)
                        updated_count += 1

            # 3. 添加缺失的key
            added_count = 0
            for key, translation in new_translations.items():
                if key not in existing_keys:
                    # 添加新元素
                    new_elem = self._add_element(root, key, translation)
                    if new_elem is not None:
                        added_count += 1

            # 4. 保存文件
            success = self.save_xml(tree, xml_file_path)

            if success:
                logging.info(
                    f"智能合并完成: 更新{updated_count}个, 添加{added_count}个翻译"
                )

            return success

        except Exception as e:
            raise ProcessingError(f"智能合并XML翻译失败: {str(e)}")

    def _create_new_xml_file(
        self, xml_file_path: str, translations: Dict[str, str]
    ) -> bool:
        """创建新的XML翻译文件"""
        try:
            # 创建XML结构
            if self.use_lxml:
                root = etree.Element("LanguageData")
                tree = etree.ElementTree(root)
            else:
                root = ET.Element("LanguageData")
                tree = ET.ElementTree(root)

            # 添加翻译内容
            for key, translation in translations.items():
                self._add_element(root, key, translation)

            # 保存文件
            return self.save_xml(tree, xml_file_path)

        except Exception as e:
            logging.error(f"创建新XML文件失败: {e}")
            return False

    def _add_element(self, parent: Any, tag: str, text: str) -> Optional[Any]:
        """添加新元素"""
        try:
            if self.use_lxml:
                elem = etree.SubElement(parent, tag)
            else:
                elem = ET.SubElement(parent, tag)

            elem.text = self.sanitize_xml(text)
            return elem
        except Exception as e:
            logging.error(f"添加元素失败: {tag}, 错误: {e}")
            return None

    def _is_machine_translation(self, text: str) -> bool:
        """简单的启发式检查是否是机器翻译"""
        if not text:
            return True

        machine_indicators = [
            "TODO",
            "FIXME",
            "PLACEHOLDER",
            "untranslated",
            "not translated",
            "需要翻译",
            "待翻译",
        ]

        text_lower = text.lower()
        for indicator in machine_indicators:
            if indicator.lower() in text_lower:
                return True

        # 如果文本很短且全是英文，可能是占位符
        if len(text) < 20 and text.isascii() and text.islower():
            return True

        return False

    def sanitize_xml(self, text: str) -> str:
        """清理 XML 文本"""
        if not isinstance(text, str):
            return str(text)
        # 移除无效的XML字符
        text = re.sub(r"[^\u0020-\uD7FF\uE000-\uFFFD]", "", text)
        # 转义XML特殊字符
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return text

    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        return {
            "use_lxml": self.use_lxml,
            "lxml_available": LXML_AVAILABLE,
            "schema_cache_size": len(self._schema_cache),
            "namespace_count": len(self._namespace_map),
            "config": {
                "validate_xml": self.config.validate_xml,
                "preserve_comments": self.config.preserve_comments,
                "max_file_size": self.config.max_file_size,
                "encoding": self.config.encoding,
            },
        }

    def __str__(self) -> str:
        """返回处理器的字符串表示"""
        return f"AdvancedXMLProcessor(use_lxml={self.use_lxml}, validate_xml={self.config.validate_xml})"

    def __repr__(self) -> str:
        """返回处理器的详细表示"""
        return (
            "AdvancedXMLProcessor(\n"
            f"  use_lxml={self.use_lxml},\n"
            f"  validate_xml={self.config.validate_xml},\n"
            f"  parser={self.parser}\n)"
        )


# 兼容性函数，支持旧代码调用
def get_xml_processor(
    config: Optional[XMLProcessorConfig] = None,
) -> AdvancedXMLProcessor:
    """获取XML处理器实例（兼容性函数）"""
    return AdvancedXMLProcessor(config)


# 导出主要接口
__all__ = ["AdvancedXMLProcessor", "XMLProcessorConfig", "get_xml_processor"]
