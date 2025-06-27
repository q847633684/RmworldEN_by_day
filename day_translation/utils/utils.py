import logging
import os
import re
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable, Union
from functools import wraps
from dataclasses import dataclass
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    logging.warning("lxml 未安装，将使用 ElementTree")

from .config import get_config

CONFIG = get_config()

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
        self.config = config or XMLProcessorConfig()
        self.use_lxml = self.config.use_lxml and LXML_AVAILABLE
        if self.use_lxml:
            self.parser = etree.XMLParser(
                remove_comments=not self.config.preserve_comments,
                recover=not self.config.error_on_invalid,
                remove_blank_text=not self.config.preserve_whitespace
            )
        else:
            self.parser = None
        self._schema_cache = {}
        self._namespace_map = {}
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
            except Exception as e:
                logging.error("加载 Schema 失败: %s: %s", schema_path, e)
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
        except Exception as e:
            logging.error("Schema 验证失败: %s", e)
            if self.config.error_on_invalid:
                raise
            return False

    def parse_xml(self, file_path: str, schema_path: Optional[str] = None) -> Optional[Any]:
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
            logging.error("文件不存在: %s", file_path)
            if self.config.error_on_invalid:
                raise FileNotFoundError(f"文件不存在: {file_path}")
            return None
            
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > self.config.max_file_size:
            msg = f"文件过大: {file_path} ({file_size / 1024 / 1024:.1f}MB)"
            logging.warning(msg)
            if self.config.error_on_invalid:
                raise ValueError(msg)
            return None
            
        try:
            if self.use_lxml:
                tree = etree.parse(file_path, self.parser)
                if schema_path and not self.validate_against_schema(tree, schema_path):
                    msg = f"XML 不符合 Schema: {file_path}"
                    logging.error(msg)
                    if self.config.error_on_invalid:
                        raise ValueError(msg)
                    return None
                return tree
            else:
                tree = ET.parse(file_path)
                if schema_path:
                    logging.warning("ElementTree 不支持 Schema 验证")
                return tree
        except (etree.XMLSyntaxError, ET.ParseError) as e:
            logging.error("XML 解析失败: %s: %s", file_path, e)
            if self.config.error_on_invalid:
                raise
            return None
        except Exception as e:
            logging.error("处理文件失败: %s: %s", file_path, e)
            if self.config.error_on_invalid:
                raise
            return None

    def save_xml(self, tree: Any, file_path: str, pretty_print: Optional[bool] = None,
                encoding: Optional[str] = None) -> bool:
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
        
        pretty_print = self.config.pretty_print if pretty_print is None else pretty_print
        encoding = self.config.encoding if encoding is None else encoding
        
        try:
            # 检查树对象的类型和模块
            tree_type = str(type(tree))
            is_lxml_tree = 'lxml' in tree_type
            
            if self.use_lxml and is_lxml_tree:                # 使用 lxml 的 write 方法
                tree.write(file_path, encoding=encoding, xml_declaration=True,
                          pretty_print=pretty_print)
            else:
                # 使用标准库的 ElementTree
                root = tree.getroot()
                
                # 如果需要格式化，使用 xml.dom.minidom 进行美化
                if pretty_print:
                    try:
                        import xml.dom.minidom as minidom
                        rough_string = ET.tostring(root, encoding)
                        reparsed = minidom.parseString(rough_string)
                        pretty_xml = reparsed.toprettyxml(indent="  ", encoding=encoding)
                        
                        with open(file_path, "wb") as f:
                            f.write(pretty_xml)
                    except ImportError:
                        # 如果 minidom 不可用，回退到普通保存
                        new_tree = ET.ElementTree(root)
                        with open(file_path, "wb") as f:
                            f.write(f'<?xml version="1.0" encoding="{encoding}"?>\n'.encode(encoding))
                            new_tree.write(f, encoding=encoding)
                else:
                    # 不需要格式化的普通保存
                    new_tree = ET.ElementTree(root)
                    with open(file_path, "wb") as f:
                        f.write(f'<?xml version="1.0" encoding="{encoding}"?>\n'.encode(encoding))
                        new_tree.write(f, encoding=encoding)
            logging.info("保存 XML 文件: %s", file_path)
            return True
        except Exception as e:
            logging.error("保存 XML 失败: %s: %s", file_path, e)
            if self.config.error_on_invalid:
                raise
            return False

    def extract_translations(self, tree: Any, context: str = "",
                           filter_func: Optional[Callable] = None,
                           include_attributes: bool = True) -> List[Tuple[str, str, str]]:
        """
        提取可翻译内容
        
        Args:
            tree (Any): XML 树对象
            context (str): 上下文
            filter_func (Optional[Callable]): 过滤函数
            include_attributes (bool): 是否包含属性
            
        Returns:
            List[Tuple[str, str, str]]: 提取的翻译列表
        """
        translations = []
        root = tree.getroot() if hasattr(tree, 'getroot') else tree
        
        # 使用 xpath 或 iter 遍历
        elements = root.xpath(".//*") if self.use_lxml else root.iter()
        
        for elem in elements:
            # 检查文本内容
            if elem.text and elem.text.strip():
                key = self._get_element_key(elem)
                text = elem.text.strip()
                if filter_func and not filter_func(key, text, context):
                    continue
                translations.append((key, text, elem.tag))
                
            # 检查属性
            if include_attributes:
                for attr_name, attr_value in elem.attrib.items():
                    if isinstance(attr_value, str) and attr_value.strip():
                        key = f"{self._get_element_key(elem)}.{attr_name}"
                        text = attr_value.strip()
                        if filter_func and not filter_func(key, text, context):
                            continue
                        translations.append((key, text, f"{elem.tag}.{attr_name}"))
                    
        return translations

    def update_translations(self, tree: Any, translations: Dict[str, str],
                          generate_key_func: Optional[Callable] = None,
                          merge: bool = True,
                          include_attributes: bool = True) -> bool:
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
        parent_map = {c: p for p in root.iter() for c in p} if not self.use_lxml else None
        
        # 使用 xpath 或 iter 遍历
        elements = root.xpath(".//*") if self.use_lxml else root.iter()
        
        for elem in elements:
            # 更新文本内容
            if elem.text and elem.text.strip():
                key = (generate_key_func(elem, root, parent_map) if generate_key_func
                      else self._get_element_key(elem))
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
                        key = (f"{generate_key_func(elem, root, parent_map)}.{attr_name}"
                              if generate_key_func
                              else f"{self._get_element_key(elem)}.{attr_name}")
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
            return elem.get('key', elem.tag)
        else:
            return elem.get('key', elem.tag)

    def add_comments(self, tree: Any, comment_prefix: str = "EN",
                    comment_func: Optional[Callable] = None) -> None:
        """
        为 XML 元素添加注释
        
        Args:
            tree (Any): XML 树对象
            comment_prefix (str): 注释前缀
            comment_func (Optional[Callable]): 自定义注释生成函数
        """
        if not self.config.preserve_comments:
            logging.warning("注释功能已禁用")
            return
            
        root = tree.getroot() if self.use_lxml else tree
        parent_map = {c: p for p in root.iter() for c in p} if not self.use_lxml else None
        
        # 使用 xpath 或 iter 遍历
        elements = root.xpath(".//*") if self.use_lxml else root.iter()
        
        for elem in elements:
            if elem.text and elem.text.strip():
                original = elem.text.strip()
                comment_text = (comment_func(original) if comment_func
                              else f"{comment_prefix}: {original}")
                comment = (etree.Comment(sanitize_xcomment(comment_text)) if self.use_lxml
                         else ET.Comment(sanitize_xcomment(comment_text)))
                
                parent = parent_map.get(elem) if not self.use_lxml else elem.getparent()
                if parent is not None:
                    idx = list(parent).index(elem)
                    parent.insert(idx, comment)

    def get_element_by_xpath(self, tree: Any, xpath: str) -> List[Any]:
        """
        使用 XPath 获取元素
        
        Args:
            tree (Any): XML 树对象
            xpath (str): XPath 表达式
            
        Returns:
            List[Any]: 匹配的元素列表
        """
        if not self.use_lxml:
            logging.warning("ElementTree 不支持 XPath")
            return []
            
        try:
            root = tree.getroot() if self.use_lxml else tree
            return root.xpath(xpath, namespaces=self._namespace_map)
        except Exception as e:
            logging.error("XPath 查询失败: %s", e)
            if self.config.error_on_invalid:
                raise
            return []

    def get_element_by_attr(self, tree: Any, attr_name: str,
                           attr_value: str, exact: bool = True) -> List[Any]:
        """
        通过属性获取元素
        
        Args:
            tree (Any): XML 树对象
            attr_name (str): 属性名
            attr_value (str): 属性值
            exact (bool): 是否精确匹配
            
        Returns:
            List[Any]: 匹配的元素列表
        """
        if self.use_lxml:
            if exact:
                xpath = f".//*[@{attr_name}='{attr_value}']"
            else:
                xpath = f".//*[contains(@{attr_name}, '{attr_value}')]"
            return self.get_element_by_xpath(tree, xpath)
        else:
            result = []
            root = tree.getroot() if self.use_lxml else tree
            for elem in root.iter():
                if attr_name in elem.attrib:
                    if exact and elem.attrib[attr_name] == attr_value:
                        result.append(elem)
                    elif not exact and attr_value in elem.attrib[attr_name]:
                        result.append(elem)
            return result

    def get_element_by_tag(self, tree: Any, tag: str) -> List[Any]:
        """
        通过标签获取元素
        
        Args:
            tree (Any): XML 树对象
            tag (str): 标签名
            
        Returns:
            List[Any]: 匹配的元素列表
        """
        if self.use_lxml:
            return self.get_element_by_xpath(tree, f".//{tag}")
        else:
            result = []
            root = tree.getroot() if self.use_lxml else tree
            for elem in root.iter(tag):
                result.append(elem)
            return result

    def get_element_by_text(self, tree: Any, text: str,
                           exact: bool = True) -> List[Any]:
        """
        通过文本内容获取元素
        
        Args:
            tree (Any): XML 树对象
            text (str): 文本内容
            exact (bool): 是否精确匹配
            
        Returns:
            List[Any]: 匹配的元素列表
        """
        if self.use_lxml:
            if exact:
                xpath = f".//*[text()='{text}']"
            else:
                xpath = f".//*[contains(text(), '{text}')]"
            return self.get_element_by_xpath(tree, xpath)
        else:
            result = []
            root = tree.getroot() if self.use_lxml else tree
            for elem in root.iter():
                if elem.text:
                    if exact and elem.text.strip() == text:
                        result.append(elem)
                    elif not exact and text in elem.text:
                        result.append(elem)
            return result

    def get_element_path(self, elem: Any) -> str:
        """
        获取元素的 XPath 路径
        
        Args:
            elem (Any): XML 元素
            
        Returns:
            str: XPath 路径
        """
        if not self.use_lxml:
            logging.warning("ElementTree 不支持 XPath 路径")
            return ""
            
        try:
            return elem.getroottree().getpath(elem)
        except Exception as e:
            logging.error("获取元素路径失败: %s", e)
            if self.config.error_on_invalid:
                raise
            return ""

    def get_element_depth(self, elem: Any) -> int:
        """
        获取元素的深度
        
        Args:
            elem (Any): XML 元素
            
        Returns:
            int: 元素深度
        """
        depth = 0
        current = elem
        while current is not None:
            current = current.getparent() if self.use_lxml else None
            depth += 1
        return depth - 1  # 减去根节点

    def get_element_children_count(self, elem: Any) -> int:
        """
        获取元素的子元素数量
        
        Args:
            elem (Any): XML 元素
            
        Returns:
            int: 子元素数量
        """
        return len(elem)

    def get_element_attributes(self, elem: Any) -> Dict[str, str]:
        """
        获取元素的所有属性
        
        Args:
            elem (Any): XML 元素
            
        Returns:
            Dict[str, str]: 属性字典
        """
        return dict(elem.attrib)

    def get_element_text(self, elem: Any, strip: bool = True) -> str:
        """
        获取元素的文本内容
        
        Args:
            elem (Any): XML 元素
            strip (bool): 是否去除空白
            
        Returns:
            str: 文本内容
        """
        if not elem.text:
            return ""
        return elem.text.strip() if strip else elem.text

    def set_element_text(self, elem: Any, text: str) -> None:
        """
        设置元素的文本内容
        
        Args:
            elem (Any): XML 元素
            text (str): 文本内容
        """
        elem.text = sanitize_xml(text)

    def set_element_attribute(self, elem: Any, name: str, value: str) -> None:
        """
        设置元素的属性
        
        Args:
            elem (Any): XML 元素
            name (str): 属性名
            value (str): 属性值
        """
        elem.set(name, sanitize_xml(value))

    def remove_element_attribute(self, elem: Any, name: str) -> None:
        """
        移除元素的属性
        
        Args:
            elem (Any): XML 元素
            name (str): 属性名
        """
        if name in elem.attrib:
            del elem.attrib[name]

    def add_element(self, parent: Any, tag: str, text: Optional[str] = None,
                   attributes: Optional[Dict[str, str]] = None) -> Any:
        """
        添加新元素
        
        Args:
            parent (Any): 父元素
            tag (str): 标签名
            text (Optional[str]): 文本内容
            attributes (Optional[Dict[str, str]]): 属性字典
            
        Returns:
            Any: 新创建的元素
        """
        elem = etree.SubElement(parent, tag) if self.use_lxml else ET.SubElement(parent, tag)
        if text is not None:
            elem.text = sanitize_xml(text)
        if attributes:
            for name, value in attributes.items():
                elem.set(name, sanitize_xml(value))
        return elem

    def remove_element(self, elem: Any) -> None:
        """
        移除元素
        
        Args:
            elem (Any): 要移除的元素
        """
        parent = elem.getparent() if self.use_lxml else None
        if parent is not None:
            parent.remove(elem)

    def __str__(self) -> str:
        """返回处理器的字符串表示"""
        return f"XMLProcessor(use_lxml={self.use_lxml}, validate_xml={self.config.validate_xml})"

    def __repr__(self) -> str:
        """返回处理器的详细表示"""
        return f"XMLProcessor(\n  use_lxml={self.use_lxml},\n  validate_xml={self.config.validate_xml},\n  parser={self.parser}\n)"

def sanitize_xml(text: str) -> str:
    """清理 XML 文本"""
    if not isinstance(text, str):
        return str(text)
    text = re.sub(r'[^\u0020-\uD7FF\uE000-\uFFFD]', '', text)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text

def sanitize_xcomment(text: str) -> str:
    """清理 XML 注释"""
    if not isinstance(text, str):
        return str(text)
    return re.sub(r'--+', '-', text)

def save_json(data: Dict, file_path: str) -> None:
    """保存 JSON 文件"""
    import json
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info("保存 JSON 文件: %s", file_path)
    except Exception as e:
        logging.error("保存 JSON 失败: %s: %s", file_path, e)

def get_language_folder_path(language: str, mod_dir: str) -> str:
    """获取语言文件夹路径"""
    return os.path.join(mod_dir, "Languages", language)

def update_history_list(key: str, value: str) -> None:
    """更新历史记录"""
    import json
    history_file = os.path.join(os.path.dirname(__file__), ".day_translation_history.json")
    try:
        history = get_history_list(key)
        if value in history:
            history.remove(value)
        history.insert(0, value)
        history = history[:10]
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump({key: history}, f, indent=2)
    except Exception as e:
        logging.error("更新历史记录失败: %s", e)

def get_history_list(key: str) -> List[str]:
    """获取历史记录"""
    import json
    history_file = os.path.join(os.path.dirname(__file__), ".day_translation_history.json")
    try:
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(key, [])
    except Exception as e:
        logging.error("读取历史记录失败: %s", e)
    return []

def handle_exceptions(default_return=None):
    """异常处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error("错误在 %s: %s", func.__name__, e)
                return default_return
        return wrapper
    return decorator

def generate_element_key(elem: Any, root: Any, parent_map: Dict = None) -> str:
    """生成元素键"""
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
    except Exception as e:
        logging.error("CSV 解析失败: %s: %s", csv_path, e)
    return translations

def save_xml_to_file(tree: Any, file_path: str, use_lxml: bool = LXML_AVAILABLE) -> bool:
    """兼容旧版保存 XML 文件"""
    processor = XMLProcessor(use_lxml=use_lxml)
    return processor.save_xml(tree, file_path)