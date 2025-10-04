import os
import xml.etree.ElementTree as ET
import logging
from utils.logging_config import get_logger, log_error_with_context
from typing import Optional, Dict, List, Tuple, Any, Callable
import re
import csv
from pathlib import Path
from dataclasses import dataclass

logger = get_logger(__name__)

try:
    import lxml.etree as etree

    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    logger.warning("lxml 未安装，将使用 ElementTree")

from user_config import UserConfigManager

# 延迟初始化配置，避免循环导入
CONFIG = None


def _get_config():
    """获取配置 - 使用新配置系统"""
    global CONFIG
    if CONFIG is None:
        CONFIG = UserConfigManager()
    return CONFIG


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


class XMLProcessor:
    """统一的 XML 处理类，专注于翻译内容的提取和更新"""

    def __init__(self, config: Optional[XMLProcessorConfig] = None):
        """
        初始化 XML 处理器

        Args:
            config (Optional[XMLProcessorConfig]): 处理器配置
        """
        self.logger = get_logger(f"{__name__}.XMLProcessor")
        self.config = config or XMLProcessorConfig()
        self.use_lxml = self.config.use_lxml and LXML_AVAILABLE
        if self.use_lxml:
            self.parser = etree.XMLParser(
                remove_comments=not self.config.preserve_comments,
                recover=not self.config.error_on_invalid,
                remove_blank_text=not self.config.preserve_whitespace,
            )
        else:
            self.parser = None  # type: ignore
        self._schema_cache: Dict[str, Any] = {}
        self._namespace_map: Dict[Optional[str], str] = {}
        if self.config.default_namespace:
            self._namespace_map[None] = self.config.default_namespace

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
            except (etree.XMLSyntaxError, OSError, IOError) as e:
                logger.error("加载 Schema 失败: %s: %s", schema_path, e)
                if self.config.error_on_invalid:
                    raise
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
        except (etree.XMLSyntaxError, ValueError) as e:
            logger.error("Schema 验证失败: %s", e)
            if self.config.error_on_invalid:
                raise
            return False

    def parse_xml(
        self, file_path: str, schema_path: Optional[str] = None
    ) -> Optional[Any]:
        """
        安全解析 XML 文件

        Args:
            file_path (str): XML 文件路径
            schema_path (Optional[str]): XML Schema 路径

        Returns:
            Optional[Any]: XML 树对象，解析失败返回 None
        """
        file_path = str(Path(file_path).resolve())
        if not os.path.exists(file_path):
            logger.error("文件不存在: %s", file_path)
            if self.config.error_on_invalid:
                raise FileNotFoundError(f"文件不存在: {file_path}")
            return None

        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > self.config.max_file_size:
            msg = f"文件过大: {file_path} ({file_size / 1024 / 1024:.1f}MB)"
            logger.warning(msg)
            if self.config.error_on_invalid:
                raise ValueError(msg)
            return None

        try:
            if self.use_lxml:
                tree = etree.parse(file_path, self.parser)
                if schema_path and not self.validate_against_schema(tree, schema_path):
                    msg = f"XML 不符合 Schema: {file_path}"
                    logger.error(msg)
                    if self.config.error_on_invalid:
                        raise ValueError(msg)
                    return None
                return tree
            else:
                tree = ET.parse(file_path)
                if schema_path:
                    logger.warning("ElementTree 不支持 Schema 验证")
                return tree
        except (etree.XMLSyntaxError, ET.ParseError) as e:
            logger.error("XML 解析失败: %s: %s", file_path, e)
            if self.config.error_on_invalid:
                raise
            return None
        except (OSError, IOError) as e:
            logger.error("处理文件失败: %s: %s", file_path, e)
            if self.config.error_on_invalid:
                raise
            return None

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
            tree (Any): XML 树对象
            file_path (str): 保存路径
            pretty_print (Optional[bool]): 是否美化输出
            encoding (Optional[str]): 文件编码

        Returns:
            bool: 是否保存成功
        """
        file_path = str(Path(file_path).resolve())
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        pretty_print = (
            self.config.pretty_print if pretty_print is None else pretty_print
        )
        encoding = self.config.encoding if encoding is None else encoding

        try:
            # 检查传入的是 Element 还是 ElementTree
            if hasattr(tree, "getroot"):
                # 这是一个 ElementTree 对象
                element_tree = tree
                root_element = tree.getroot()
            else:
                # 这是一个 Element 对象，需要包装成 ElementTree
                root_element = tree
                if "lxml" in str(type(tree)):
                    # lxml Element
                    import lxml.etree as letree

                    element_tree = letree.ElementTree(root_element)
                else:
                    # 标准库 Element
                    element_tree = ET.ElementTree(root_element)

            # 检查树对象的类型和模块
            tree_type = str(type(element_tree))
            is_lxml_tree = "lxml" in tree_type

            if self.use_lxml and is_lxml_tree:
                # 使用 lxml 的 write 方法
                element_tree.write(
                    file_path,
                    encoding=encoding,
                    xml_declaration=True,
                    pretty_print=pretty_print,
                )
            else:
                # 使用标准库的 ElementTree
                root = root_element

                # 如果需要格式化，使用 xml.dom.minidom 进行美化
                if pretty_print:
                    try:
                        import xml.dom.minidom as minidom

                        rough_string = ET.tostring(root, encoding)
                        reparsed = minidom.parseString(rough_string)
                        pretty_xml = reparsed.toprettyxml(
                            indent="  ", encoding=encoding
                        )

                        with open(file_path, "wb") as f:
                            f.write(pretty_xml)
                    except ImportError:
                        # 如果 minidom 不可用，回退到普通保存
                        new_tree = ET.ElementTree(root)
                        with open(file_path, "wb") as f:
                            f.write(
                                f'<?xml version="1.0" encoding="{encoding}"?>\n'.encode(
                                    encoding
                                )
                            )
                            new_tree.write(f, encoding=encoding)
                else:
                    # 不格式化，直接保存
                    element_tree.write(
                        file_path, encoding=encoding, xml_declaration=True
                    )
            self.logger.debug("保存 XML 文件: %s", file_path)
            return True
        except (OSError, IOError, ET.ParseError) as e:
            self.logger.error("保存 XML 失败: %s: %s", file_path, e)
            if self.config.error_on_invalid:
                raise
            return False

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
            tree (Any): XML 树对象
            translations (Dict[str, str]): 翻译字典
            generate_key_func (Optional[Callable]): 生成键的函数
            merge (bool): 是否合并更新
            include_attributes (bool): 是否更新属性

        Returns:
            bool: 是否更新成功
        """
        modified = False
        root = tree.getroot() if self.use_lxml else tree
        parent_map = (
            {c: p for p in root.iter() for c in p} if not self.use_lxml else None
        )

        # 使用 xpath 或 iter 遍历
        elements = root.xpath(".//*") if self.use_lxml else root.iter()

        for elem in elements:
            # 更新文本内容
            if elem.text and elem.text.strip():
                key = (
                    generate_key_func(elem, root, parent_map)
                    if generate_key_func
                    else self._get_element_key(elem)
                )
                if key in translations:
                    if merge and elem.text.strip() != translations[key]:
                        elem.text = sanitize_xml(translations[key])
                        modified = True
                    elif not merge:
                        elem.text = sanitize_xml(translations[key])
                        modified = True

            # 更新属性
            if include_attributes:
                for attr_name, attr_value in elem.attrib.items():
                    if isinstance(attr_value, str) and attr_value.strip():
                        key = (
                            f"{generate_key_func(elem, root, parent_map)}.{attr_name}"
                            if generate_key_func
                            else f"{self._get_element_key(elem)}.{attr_name}"
                        )
                        if key in translations:
                            if merge and attr_value.strip() != translations[key]:
                                elem.set(attr_name, sanitize_xml(translations[key]))
                                modified = True
                            elif not merge:
                                elem.set(attr_name, sanitize_xml(translations[key]))
                                modified = True

        return modified

    def _get_element_key(self, elem: Any) -> str:
        """获取元素的键"""
        if self.use_lxml:
            return elem.get("key", elem.tag)
        else:
            return elem.get("key", elem.tag)

    def add_comments(
        self,
        tree: Any,
        comment_prefix: str = "EN",
        comment_func: Optional[Callable] = None,
    ) -> None:
        """
        为 XML 元素添加注释

        Args:
            tree (Any): XML 树对象
            comment_prefix (str): 注释前缀
            comment_func (Optional[Callable]): 自定义注释生成函数
        """
        if not self.config.preserve_comments:
            logger.warning("注释功能已禁用")
            return

        root = tree.getroot() if self.use_lxml else tree
        parent_map = (
            {c: p for p in root.iter() for c in p} if not self.use_lxml else None
        )

        # 使用 xpath 或 iter 遍历
        elements = root.xpath(".//*") if self.use_lxml else root.iter()

        for elem in elements:
            if elem.text and elem.text.strip():
                original = elem.text.strip()
                comment_text = (
                    comment_func(original)
                    if comment_func
                    else f"{comment_prefix}: {original}"
                )
                comment = (
                    etree.Comment(sanitize_xcomment(comment_text))
                    if self.use_lxml
                    else ET.Comment(sanitize_xcomment(comment_text))
                )  # type: ignore

                parent = (
                    parent_map.get(elem)
                    if parent_map and not self.use_lxml
                    else elem.getparent()
                )
                if parent is not None:
                    idx = list(parent).index(elem)
                    parent.insert(idx, comment)

    def __str__(self) -> str:
        """返回处理器的字符串表示"""
        return f"XMLProcessor(use_lxml={self.use_lxml}, validate_xml={self.config.validate_xml})"

    def __repr__(self) -> str:
        """返回处理器的详细表示"""
        return f"XMLProcessor(\n  use_lxml={self.use_lxml},\n  validate_xml={self.config.validate_xml},\n  parser={self.parser}\n)"

    @staticmethod
    def generate_element_key(
        elem: Any, root: Any, parent_map: Optional[Dict[Any, Any]] = None
    ) -> str:
        """生成元素键（支持递归路径）"""
        key = elem.get("key") or elem.tag
        path_parts = []
        current = elem
        if parent_map:  # ElementTree
            while current is not None and current != root:
                if current.tag != "LanguageData":
                    path_parts.append(current.tag)
                current = parent_map.get(current)
        else:  # lxml
            while current is not None and current != root:
                if current.tag != "LanguageData":
                    path_parts.append(current.tag)
                current = current.getparent()
        path_parts.reverse()
        return ".".join(path_parts) if path_parts else key

    def create_element(
        self,
        tag: str,
        text: Optional[str] = None,
        attrib: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        创建 XML 元素

        Args:
            tag (str): 标签名
            text (Optional[str]): 文本内容
            attrib (Optional[Dict[str, str]]): 属性字典

        Returns:
            Any: XML 元素对象
        """
        if self.use_lxml:
            elem = etree.Element(tag, attrib or {})
        else:
            elem = ET.Element(tag, attrib or {})  # type: ignore

        if text is not None:
            elem.text = sanitize_xml(text)

        return elem

    def create_subelement(
        self,
        parent: Any,
        tag: str,
        text: Optional[str] = None,
        attrib: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        创建子元素

        Args:
            parent (Any): 父元素
            tag (str): 标签名
            text (Optional[str]): 文本内容
            attrib (Optional[Dict[str, str]]): 属性字典

        Returns:
            Any: 子元素对象
        """
        if self.use_lxml:
            elem = etree.SubElement(parent, tag, attrib or {})
        else:
            elem = ET.SubElement(parent, tag, attrib or {})  # type: ignore

        if text is not None:
            elem.text = sanitize_xml(text)

        return elem

    def create_comment(self, text: str) -> Any:
        """
        创建 XML 注释

        Args:
            text (str): 注释内容

        Returns:
            Any: 注释对象
        """
        cleaned_text = sanitize_xcomment(text)

        if self.use_lxml:
            return etree.Comment(cleaned_text)
        else:
            return ET.Comment(cleaned_text)

    def append_element(self, parent: Any, child: Any) -> None:
        """
        向父元素添加子元素

        Args:
            parent (Any): 父元素
            child (Any): 子元素
        """
        parent.append(child)

    # ...existing code...


def sanitize_xml(text: str) -> str:
    """清理 XML 文本，去除所有非法字符并转义"""
    if not isinstance(text, str):
        text = str(text)
    # 去除所有非法 XML 字符（包括 C0/C1 控制符）
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x84\x86-\x9F]", "", text)
    # 转义特殊字符
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
    return text


def sanitize_xcomment(text: str) -> str:
    """清理 XML 注释内容，防止非法字符和注释断裂"""
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("--", "- -")
    text = text.replace("<", "＜").replace(">", "＞").replace("&", "＆")
    # 去除所有控制字符
    text = "".join(c for c in text if c >= " " or c == "\n" or c == "\r")
    # 注释不能以 - 结尾
    if text.endswith("-"):
        text += " "
    return text


def get_language_folder_path(language: str, mod_dir: str) -> str:
    """获取语言文件夹路径"""
    return os.path.join(mod_dir, "Languages", language)


def update_history_list(key: str, value: str) -> None:
    """更新历史记录"""
    import json

    history_file = os.path.join(
        os.path.dirname(__file__), ".day_translation_history.json"
    )
    try:
        history = get_history_list(key)
        if value in history:
            history.remove(value)
        history.insert(0, value)
        history = history[:10]
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump({key: history}, f, indent=2)
    except (OSError, IOError, ValueError) as e:
        logger.error("更新历史记录失败: %s", e)


def get_history_list(key: str) -> List[str]:
    """获取历史记录"""
    import json

    history_file = os.path.join(
        os.path.dirname(__file__), ".day_translation_history.json"
    )
    try:
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(key, [])
    except (OSError, IOError, ValueError) as e:
        logger.error("读取历史记录失败: %s", e)
    return []


def load_translations_from_csv(csv_path: str) -> Dict[str, str]:
    """从 CSV 加载翻译"""
    translations = {}
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("key", "").strip()
                translated = row.get("translated", row.get("text", "")).strip()
                if key and translated:
                    translations[key] = translated
    except (OSError, IOError, csv.Error) as e:
        logger.error("CSV 解析失败: %s: %s", csv_path, e)
    return translations
