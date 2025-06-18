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

from .unified_config import get_config

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
                logging.error(f"加载 Schema 失败: {schema_path}: {e}")
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
            logging.error(f"Schema 验证失败: {e}")
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
            logging.error(f"文件不存在: {file_path}")
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
            logging.error(f"XML 解析失败: {file_path}: {e}")
            if self.config.error_on_invalid:
                raise
            return None
        except Exception as e:
            logging.error(f"处理文件失败: {file_path}: {e}")
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
            logging.info(f"保存 XML 文件: {file_path}")
            return True
        except Exception as e:
            logging.error(f"保存 XML 失败: {file_path}: {e}")
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
            logging.error(f"XPath 查询失败: {e}")
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
            logging.error(f"获取元素路径失败: {e}")
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
        logging.info(f"保存 JSON 文件: {file_path}")
    except Exception as e:
        logging.error(f"保存 JSON 失败: {file_path}: {e}")

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
        logging.error(f"更新历史记录失败: {e}")

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
        logging.error(f"读取历史记录失败: {e}")
    return []

def handle_exceptions(default_return=None):
    """异常处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"错误在 {func.__name__}: {e}")
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
        logging.error(f"CSV 解析失败: {csv_path}: {e}")
    return translations

def save_xml_to_file(tree: Any, file_path: str, use_lxml: bool = LXML_AVAILABLE) -> bool:
    """兼容旧版保存 XML 文件"""
    processor = XMLProcessor(use_lxml=use_lxml)
    return processor.save_xml(tree, file_path)

def handle_existing_translations_choice(output_dir_path: str, file_pattern: str = "*.xml", 
                                      backup_enabled: bool = True, 
                                      auto_mode: str = None,
                                      enable_advanced_options: bool = False) -> str:
    """
    处理现有翻译文件的用户选择
    
    Args:
        output_dir_path (str): 输出目录路径
        file_pattern (str): 文件匹配模式，默认为 "*.xml"
        backup_enabled (bool): 是否启用备份选项
        auto_mode (str): 自动模式 ("replace", "merge", "backup", "incremental", "preview", None)
        enable_advanced_options (bool): 是否启用高级选项
        
    Returns:
        str: 处理模式 ("replace", "merge", "backup", "skip", "incremental", "preview")
    """
    from colorama import Fore, Style
    
    # 检查是否存在现有翻译文件
    existing_files = list(Path(output_dir_path).rglob(file_pattern))
    
    if not existing_files:
        # 没有现有文件，直接返回替换模式
        return "replace"
      # 自动模式处理
    if auto_mode:
        valid_auto_modes = ["replace", "merge", "smart-merge", "backup", "skip", "incremental", "preview"]
        if auto_mode in valid_auto_modes:
            logging.info(f"自动模式: {auto_mode}")
            return _execute_choice(auto_mode, existing_files, output_dir_path)
        else:
            logging.warning(f"无效的自动模式: {auto_mode}，转为交互模式")
    
    # 显示现有文件信息
    print(f"\n{Fore.YELLOW}检测到输出目录中已存在 {len(existing_files)} 个翻译文件{Style.RESET_ALL}")
    
    # 显示文件列表（如果文件不多）
    if len(existing_files) <= 10:
        print(f"{Fore.CYAN}现有文件：{Style.RESET_ALL}")
        for i, file_path in enumerate(existing_files[:10], 1):
            rel_path = Path(file_path).relative_to(Path(output_dir_path))
            print(f"  {i}. {rel_path}")
    elif len(existing_files) > 10:
        print(f"{Fore.CYAN}现有文件（显示前5个）：{Style.RESET_ALL}")
        for i, file_path in enumerate(existing_files[:5], 1):
            rel_path = Path(file_path).relative_to(Path(output_dir_path))
            print(f"  {i}. {rel_path}")
        print(f"  ... 还有 {len(existing_files) - 5} 个文件")
      # 显示处理选项
    print(f"\n{Fore.CYAN}请选择处理方式：{Style.RESET_ALL}")
    print(f"1. {Fore.GREEN}替换{Style.RESET_ALL}（删除现有文件，重新生成）")
    print(f"2. {Fore.GREEN}合并{Style.RESET_ALL}（保留现有翻译，仅更新新内容）")
    print(f"3. {Fore.MAGENTA}智能合并{Style.RESET_ALL}（扫描XML内容，替换已有key，添加缺失key）")
    
    option_count = 4
    choice_map = {"1": "replace", "2": "merge", "3": "smart-merge"}
    
    if backup_enabled:
        print(f"4. {Fore.BLUE}备份并替换{Style.RESET_ALL}（备份现有文件，然后重新生成）")
        choice_map["4"] = "backup"
        option_count += 1
    
    if enable_advanced_options:
        print(f"{option_count}. {Fore.MAGENTA}增量更新{Style.RESET_ALL}（只更新有变化的文件）")
        choice_map[str(option_count)] = "incremental"
        option_count += 1
        
        print(f"{option_count}. {Fore.CYAN}预览模式{Style.RESET_ALL}（先预览变化，再确认执行）")
        choice_map[str(option_count)] = "preview"
        option_count += 1
    
    print(f"{option_count}. {Fore.YELLOW}跳过{Style.RESET_ALL}（不生成新文件，保持现状）")
    choice_map[str(option_count)] = "skip"
    
    valid_choices = list(choice_map.keys())
    default_choice = "2"
    
    choice = input(f"{Fore.CYAN}请输入选项编号（回车默认{default_choice}）：{Style.RESET_ALL}").strip()
    
    if not choice:
        choice = default_choice
    
    if choice not in valid_choices:
        print(f"{Fore.RED}无效选择，使用默认选项：合并模式{Style.RESET_ALL}")
        choice = default_choice
    
    mode = choice_map[choice]
    return _execute_choice(mode, existing_files, output_dir_path)


def _execute_choice(mode: str, existing_files: list, output_dir_path: str) -> str:
    """执行用户选择的操作"""
    from colorama import Fore, Style
    
    if mode == "replace":
        # 替换模式：删除现有文件
        logging.info("选择替换模式，删除现有翻译文件")
        print(f"{Fore.GREEN}✅ 将删除现有文件并重新生成{Style.RESET_ALL}")
        
        deleted_count = 0
        for xml_file in existing_files:
            try:
                os.remove(xml_file)
                logging.info(f"删除文件：{xml_file}")
                deleted_count += 1
            except OSError as e:
                logging.error(f"无法删除 {xml_file}: {e}")
        
        print(f"{Fore.GREEN}✅ 已删除 {deleted_count} 个文件{Style.RESET_ALL}")
        
    elif mode == "merge":
        # 合并模式：保留现有文件
        logging.info("选择合并模式，保留现有翻译文件")
        print(f"{Fore.GREEN}✅ 将保留现有翻译，仅更新新内容{Style.RESET_ALL}")
        
    elif mode == "backup":
        # 备份并替换模式
        logging.info("选择备份并替换模式")
        print(f"{Fore.BLUE}🔄 正在备份现有文件...{Style.RESET_ALL}")
        
        backup_success = _backup_existing_files(existing_files, output_dir_path)
        if backup_success:
            print(f"{Fore.GREEN}✅ 备份完成，将重新生成翻译文件{Style.RESET_ALL}")
            # 备份成功后删除原文件
            for xml_file in existing_files:
                try:
                    os.remove(xml_file)
                    logging.info(f"删除文件：{xml_file}")
                except OSError as e:
                    logging.error(f"无法删除 {xml_file}: {e}")
        else:
            print(f"{Fore.RED}❌ 备份失败，切换到合并模式{Style.RESET_ALL}")
            mode = "merge"
            
    elif mode == "skip":
        # 跳过模式：不做任何操作
        logging.info("选择跳过模式，保持现状")
        print(f"{Fore.YELLOW}⏭️ 已跳过，保持现有文件不变{Style.RESET_ALL}")
        
    elif mode == "incremental":
        # 增量更新模式：只更新有变化的文件
        logging.info("选择增量更新模式")
        print(f"{Fore.MAGENTA}🔄 正在分析文件变化...{Style.RESET_ALL}")
        
        changed_files = _analyze_file_changes(existing_files, output_dir_path)
        if changed_files:
            print(f"{Fore.MAGENTA}📊 检测到 {len(changed_files)} 个文件需要更新{Style.RESET_ALL}")
            for file_path in changed_files[:5]:  # 显示前5个
                rel_path = Path(file_path).relative_to(Path(output_dir_path))
                print(f"  - {rel_path}")
            if len(changed_files) > 5:
                print(f"  ... 还有 {len(changed_files) - 5} 个文件")
        else:
            print(f"{Fore.GREEN}✅ 所有文件都是最新的，无需更新{Style.RESET_ALL}")
            mode = "skip"  # 没有变化时转为跳过模式
        
    elif mode == "preview":
        # 预览模式：显示将要发生的变化
        logging.info("选择预览模式")
        print(f"{Fore.CYAN}👁️ 预览将要发生的变化...{Style.RESET_ALL}")
        
        preview_info = _generate_preview(existing_files, output_dir_path)
        _display_preview(preview_info)
        
        # 询问用户是否确认执行
        confirm = input(f"\n{Fore.CYAN}确认执行这些变化吗？(y/N): {Style.RESET_ALL}").strip().lower()
        if confirm in ['y', 'yes', '是']:
            # 让用户选择具体执行什么操作
            print(f"\n{Fore.CYAN}请选择执行方式：{Style.RESET_ALL}")
            print(f"1. {Fore.GREEN}替换{Style.RESET_ALL}（执行替换操作）")
            print(f"2. {Fore.GREEN}合并{Style.RESET_ALL}（执行合并操作）")
            print(f"3. {Fore.BLUE}备份并替换{Style.RESET_ALL}（执行备份并替换）")
            
            exec_choice = input(f"{Fore.CYAN}请选择（默认合并）：{Style.RESET_ALL}").strip()
            exec_map = {"1": "replace", "2": "merge", "3": "backup"}
            actual_mode = exec_map.get(exec_choice, "merge")
            
            # 递归调用执行实际操作
            return _execute_choice(actual_mode, existing_files, output_dir_path)
        else:
            print(f"{Fore.YELLOW}⏭️ 用户取消操作{Style.RESET_ALL}")
            mode = "skip"
    
    elif mode == "smart-merge":
        # 智能合并模式：扫描XML内容，替换已有key，添加缺失key
        logging.info("选择智能合并模式")
        print(f"{Fore.MAGENTA}🧠 正在进行智能合并...{Style.RESET_ALL}")
        
        # 这里需要翻译数据，在导出函数中会提供
        # 暂时记录模式，实际处理在导出函数中进行
        print(f"{Fore.GREEN}✅ 将使用智能合并模式处理翻译文件{Style.RESET_ALL}")
        
    return mode


def _backup_existing_files(existing_files: list, output_dir_path: str) -> bool:
    """备份现有文件"""
    from datetime import datetime
    from colorama import Fore, Style
    
    try:
        # 创建备份目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(output_dir_path) / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_count = 0
        for file_path in existing_files:
            # 计算相对路径
            rel_path = Path(file_path).relative_to(Path(output_dir_path))
            backup_file = backup_dir / rel_path
            
            # 确保备份目录存在
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            import shutil
            shutil.copy2(file_path, backup_file)
            logging.info(f"备份文件：{file_path} -> {backup_file}")
            backup_count += 1
        
        print(f"{Fore.GREEN}✅ 已备份 {backup_count} 个文件到：{backup_dir}{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        logging.error(f"备份文件失败：{e}")
        print(f"{Fore.RED}❌ 备份失败：{e}{Style.RESET_ALL}")
        return False

def _analyze_file_changes(existing_files: list, output_dir_path: str) -> list:
    """
    分析文件变化，返回需要更新的文件列表
    
    Args:
        existing_files (list): 现有文件列表
        output_dir_path (str): 输出目录路径
        
    Returns:
        list: 需要更新的文件列表
    """
    changed_files = []
    
    try:
        # 这里简化处理，实际可以根据时间戳、文件大小、内容哈希等判断
        # 目前假设所有文件都可能需要更新，实际使用时需要更复杂的逻辑
        
        import time
        current_time = time.time()
        
        for file_path in existing_files:
            try:
                # 获取文件修改时间
                file_mtime = os.path.getmtime(file_path)
                
                # 如果文件修改时间超过1小时，认为可能需要更新
                # 这是一个简化的判断逻辑，实际可以更复杂
                if current_time - file_mtime > 3600:  # 1小时
                    changed_files.append(file_path)
                    
            except OSError as e:
                logging.warning(f"无法获取文件信息 {file_path}: {e}")
                # 如果无法获取文件信息，保守起见认为需要更新
                changed_files.append(file_path)
                
    except Exception as e:
        logging.error(f"分析文件变化时出错: {e}")
        # 出错时返回所有文件
        return existing_files
    
    return changed_files

def _generate_preview(existing_files: list, output_dir_path: str) -> dict:
    """
    生成预览信息
    
    Args:
        existing_files (list): 现有文件列表
        output_dir_path (str): 输出目录路径
        
    Returns:
        dict: 预览信息
    """
    preview_info = {
        "total_files": len(existing_files),
        "will_be_affected": len(existing_files),
        "files_list": [],
        "estimated_size": 0
    }
    
    try:
        total_size = 0
        for file_path in existing_files:
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                rel_path = Path(file_path).relative_to(Path(output_dir_path))
                preview_info["files_list"].append({
                    "path": str(rel_path),
                    "size": file_size,
                    "full_path": str(file_path)
                })
                
            except OSError as e:
                logging.warning(f"无法获取文件大小 {file_path}: {e}")
        
        preview_info["estimated_size"] = total_size
        
    except Exception as e:
        logging.error(f"生成预览信息时出错: {e}")
    
    return preview_info


def _display_preview(preview_info: dict) -> None:
    """
    显示预览信息
    
    Args:
        preview_info (dict): 预览信息
    """
    from colorama import Fore, Style
    
    print(f"\n{Fore.CYAN}📊 预览信息：{Style.RESET_ALL}")
    print(f"  总文件数：{preview_info['total_files']}")
    print(f"  将受影响的文件：{preview_info['will_be_affected']}")
    
    # 格式化文件大小
    size_mb = preview_info['estimated_size'] / (1024 * 1024)
    if size_mb >= 1:
        size_str = f"{size_mb:.2f} MB"
    else:
        size_kb = preview_info['estimated_size'] / 1024
        size_str = f"{size_kb:.2f} KB"
    
    print(f"  估计文件大小：{size_str}")
    
    # 显示文件列表（限制显示数量）
    if preview_info["files_list"]:
        print(f"\n{Fore.CYAN}文件列表：{Style.RESET_ALL}")
        
        display_count = min(10, len(preview_info["files_list"]))
        for i, file_info in enumerate(preview_info["files_list"][:display_count]):
            file_size_kb = file_info["size"] / 1024
            print(f"  {i+1}. {file_info['path']} ({file_size_kb:.1f} KB)")
        
        if len(preview_info["files_list"]) > display_count:
            remaining = len(preview_info["files_list"]) - display_count
            print(f"  ... 还有 {remaining} 个文件")
    
    print(f"\n{Fore.YELLOW}⚠️ 注意：{Style.RESET_ALL}")
    print(f"  - 替换操作将删除现有文件并重新生成")
    print(f"  - 合并操作将保留现有翻译内容")
    print(f"  - 备份操作将先备份现有文件")

def smart_merge_xml_translations(xml_file_path: str, new_translations: Dict[str, str], 
                                 preserve_manual_edits: bool = True) -> bool:
    """
    智能合并XML翻译文件
    
    这个函数实现了你提到的方案1：
    1. 扫描现有XML中的key-text对
    2. 替换已存在的key的翻译（可选择保留手动编辑）
    3. 添加缺失的key
    4. 保留XML结构和注释
    
    Args:
        xml_file_path (str): XML文件路径
        new_translations (Dict[str, str]): 新的翻译内容
        preserve_manual_edits (bool): 是否保留手动编辑的翻译
        
    Returns:
        bool: 是否成功合并
        
    Example:
        现有XML内容：
        <?xml version="1.0" encoding="utf-8"?>
        <LanguageData>
          <!--EN: insertable-->
          <AnalInsertableBondage.label>insertable</AnalInsertableBondage.label>
          <!--EN: outer-->
          <ArmsOuterBondage.label>outer</ArmsOuterBondage.label>
        </LanguageData>
        
        新翻译：
        {
            "AnalInsertableBondage.label": "可插入的",
            "ArmsOuterBondage.label": "外层的", 
            "NewItem.label": "新项目"
        }
        
        合并后：
        <?xml version="1.0" encoding="utf-8"?>
        <LanguageData>
          <!--EN: insertable-->
          <AnalInsertableBondage.label>可插入的</AnalInsertableBondage.label>
          <!--EN: outer-->
          <ArmsOuterBondage.label>外层的</ArmsOuterBondage.label>
          <!--EN: new item-->
          <NewItem.label>新项目</NewItem.label>
        </LanguageData>
    """
    from colorama import Fore, Style
    
    try:
        # 使用XMLProcessor来处理
        processor = XMLProcessor()
        
        if not os.path.exists(xml_file_path):
            # 文件不存在，创建新文件
            return _create_new_xml_file(xml_file_path, new_translations)
          # 读取现有XML文件
        tree = processor.parse_xml(xml_file_path)
        if tree is None:
            logging.error(f"无法解析XML文件: {xml_file_path}")
            return False
            
        root = tree.getroot() if processor.use_lxml else tree
        
        # 1. 扫描现有的key-text对
        existing_keys = set()
        elements_map = {}  # key -> element
        
        for elem in root:
            if elem.tag != 'LanguageData' and elem.text:
                key = elem.tag
                existing_keys.add(key)
                elements_map[key] = elem
                
        logging.info(f"扫描到现有翻译条目: {len(existing_keys)} 个")
        
        # 2. 处理现有key的翻译更新
        updated_count = 0
        for key in existing_keys:
            if key in new_translations:
                elem = elements_map[key]
                old_text = elem.text.strip() if elem.text else ""
                new_text = new_translations[key].strip()
                
                # 检查是否需要更新
                if old_text != new_text:
                    if preserve_manual_edits:
                        # 检查是否是手动编辑（简单启发式：如果翻译不是原文且不为空，可能是手动编辑）
                        if old_text and old_text != key and not _is_machine_translation(old_text):
                            logging.info(f"保留手动编辑的翻译: {key} = '{old_text}'")
                            continue
                    
                    elem.text = sanitize_xml(new_text)
                    updated_count += 1
                    logging.debug(f"更新翻译: {key} = '{new_text}'")
        
        # 3. 添加缺失的key
        added_count = 0
        for key, translation in new_translations.items():
            if key not in existing_keys:
                # 创建新元素
                if processor.use_lxml:
                    new_elem = processor.parser.makeelement(key)
                else:
                    new_elem = ET.Element(key)
                    
                new_elem.text = sanitize_xml(translation)
                
                # 添加注释（如果有原文）
                if translation != key:  # 避免为相同的key-value添加注释
                    comment_text = f"EN: {key.split('.')[-1]}"  # 简化的注释
                    if processor.use_lxml:
                        comment = etree.Comment(comment_text)
                        root.insert(-1, comment)
                    else:
                        # ElementTree不直接支持注释，在这里跳过
                        pass
                
                root.append(new_elem)
                added_count += 1
                logging.debug(f"添加新翻译: {key} = '{translation}'")
        
        # 4. 保存文件
        success = processor.save_xml(tree, xml_file_path)
        
        if success:
            logging.info(f"智能合并完成: 更新 {updated_count} 个, 添加 {added_count} 个翻译")
            print(f"{Fore.GREEN}✅ 智能合并完成: 更新 {updated_count} 个, 添加 {added_count} 个翻译{Style.RESET_ALL}")
        else:
            logging.error(f"保存XML文件失败: {xml_file_path}")
            
        return success
        
    except Exception as e:
        logging.error(f"智能合并XML翻译失败: {e}")
        print(f"{Fore.RED}❌ 智能合并失败: {e}{Style.RESET_ALL}")
        return False


def _is_machine_translation(text: str) -> bool:
    """
    简单的启发式检查是否是机器翻译
    
    Args:
        text (str): 待检查的文本
        
    Returns:
        bool: 是否可能是机器翻译
    """
    # 简单的启发式规则：
    # 1. 如果包含常见的机器翻译痕迹
    # 2. 如果是纯英文且格式简单，可能是占位符
    machine_indicators = [
        "TODO", "FIXME", "PLACEHOLDER", 
        "untranslated", "not translated",
        "需要翻译", "待翻译"
    ]
    
    text_lower = text.lower()
    for indicator in machine_indicators:
        if indicator.lower() in text_lower:
            return True
    
    # 如果文本很短且全是英文，可能是占位符
    if len(text) < 20 and text.isascii() and text.islower():
        return True
        
    return False


def _create_new_xml_file(xml_file_path: str, translations: Dict[str, str]) -> bool:
    """
    创建新的XML翻译文件
    
    Args:
        xml_file_path (str): XML文件路径
        translations (Dict[str, str]): 翻译内容
        
    Returns:
        bool: 是否创建成功
    """
    try:
        processor = XMLProcessor()
        
        # 创建XML结构
        if processor.use_lxml:
            root = etree.Element("LanguageData")
        else:
            root = ET.Element("LanguageData")
            
        # 添加翻译内容
        for key, translation in translations.items():
            if processor.use_lxml:
                elem = etree.Element(key)
            else:
                elem = ET.Element(key)
                
            elem.text = sanitize_xml(translation)
            root.append(elem)
        
        # 创建树
        if processor.use_lxml:
            tree = etree.ElementTree(root)
        else:
            tree = ET.ElementTree(root)
        
        # 保存文件
        success = processor.save_xml(tree, xml_file_path)
        
        if success:
            logging.info(f"创建新的XML翻译文件: {xml_file_path}, 包含 {len(translations)} 个翻译")
            
        return success
        
    except Exception as e:
        logging.error(f"创建新XML文件失败: {e}")
        return False

def export_with_smart_merge(output_file_path: str, translations: Dict[str, str], 
                          merge_mode: str = "replace") -> bool:
    """
    根据合并模式导出翻译文件
    
    Args:
        output_file_path (str): 输出文件路径
        translations (Dict[str, str]): 翻译内容
        merge_mode (str): 合并模式 ("replace", "merge", "smart-merge", "backup")
        
    Returns:
        bool: 是否成功导出
    """
    if merge_mode == "smart-merge":
        # 使用智能合并逻辑
        return smart_merge_xml_translations(output_file_path, translations, preserve_manual_edits=True)
    elif merge_mode == "merge":
        # 使用原有的合并逻辑
        if os.path.exists(output_file_path):
            processor = XMLProcessor()
            tree = processor.parse_xml(output_file_path)
            if tree:
                processor.update_translations(tree, translations, merge=True)
                return processor.save_xml(tree, output_file_path)
        # 文件不存在，创建新文件
        return _create_new_xml_file(output_file_path, translations)
    else:
        # replace 模式：直接创建新文件
        return _create_new_xml_file(output_file_path, translations)