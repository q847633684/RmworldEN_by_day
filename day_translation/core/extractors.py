from typing import List, Tuple, Set, Dict, Optional
import logging
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from functools import lru_cache
import asyncio
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    logging.warning("aiofiles 未安装，将使用同步方式读取文件")

from ..utils.config import TranslationConfig
from ..utils.utils import get_language_folder_path
from ..utils.fields import extract_translatable_fields
from .exporters import export_keyed, export_definjected

CONFIG = TranslationConfig()

# 🔧 合并：将 EnhancedExtractor 功能整合到统一提取器
class UnifiedExtractor:
    """统一的内容提取器 - 合并基础和增强功能"""
    
    def __init__(self, mod_dir: str, filter_mode: str = "standard", config_file: str = None):
        """
        初始化提取器
        
        Args:
            mod_dir: 模组目录
            filter_mode: 过滤模式
            config_file: 配置文件路径（可选）
        """
        self.mod_dir = Path(mod_dir)
        self._xml_cache: Dict[str, List[Tuple[str, str, str, str]]] = {}
        
        # 🔧 延迟加载过滤器，避免循环导入
        self._content_filter = None
        self.filter_mode = filter_mode
        self.config_file = config_file
    
    @property
    def content_filter(self):
        """延迟初始化过滤器"""
        if self._content_filter is None:
            from .filters import ContentFilter
            self._content_filter = ContentFilter(self.filter_mode, self.config_file)
        return self._content_filter
    
    def extract_keyed_translations(self, keyed_dir: str, progress_callback=None) -> List[Tuple[str, str, str, str]]:
        """提取 Keyed 翻译 - 统一版本"""
        translations = []
        xml_files = list(Path(keyed_dir).rglob("*.xml"))
        
        if progress_callback:
            progress_callback(f"扫描 {len(xml_files)} 个 XML 文件...")
        
        for i, xml_file in enumerate(xml_files, 1):
            if progress_callback and i % 10 == 0:
                progress_callback(f"进度: {i}/{len(xml_files)}")
                
            try:
                # 🔧 使用缓存机制
                file_key = str(xml_file)
                if file_key in self._xml_cache:
                    translations.extend(self._xml_cache[file_key])
                    continue
                
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                file_translations = []
                for elem in root:
                    if isinstance(elem.tag, str) and elem.text:
                        if self.content_filter.is_translatable(elem.tag, elem.text, "Keyed"):
                            translation = (elem.tag, elem.text.strip(), elem.tag, str(xml_file))
                            file_translations.append(translation)
                            translations.append(translation)
                        else:
                            logging.debug(f"过滤非翻译内容: {elem.tag}={elem.text}")
                
                self._xml_cache[file_key] = file_translations
                
            except ET.ParseError as e:
                logging.error(f"XML解析失败: {xml_file}: {e}")
                if progress_callback:
                    progress_callback(f"❌ {xml_file.name}: XML 解析失败")
            except OSError as e:
                logging.error(f"文件读取失败: {xml_file}: {e}")
                if progress_callback:
                    progress_callback(f"❌ {xml_file.name}: 文件读取失败")
        
        return translations
    
    def extract_defs_translations(self, preview_limit: int = 1000) -> List[Tuple[str, str, str, str]]:
        """从 Defs 目录提取翻译 - 委托给 preview_translatable_fields"""
        # 🔧 修复参数传递问题
        return preview_translatable_fields(
            mod_dir=str(self.mod_dir),
            preview=preview_limit,
            facade=self  # 传递自身而不是 self
        )
    
    def is_translatable_content(self, tag: str, text: str, context: str = "") -> bool:
        """🔧 修复方法名和兼容性"""
        return self.content_filter.is_translatable(tag, text, context)

# 🔧 保持向后兼容的函数接口
def extract_keyed_translations(keyed_dir: str, content_filter=None) -> List[Tuple[str, str, str, str]]:
    """提取 Keyed 翻译 - 向后兼容接口"""
    if content_filter:
        # 使用传入的过滤器
        extractor = UnifiedExtractor(str(Path(keyed_dir).parent.parent.parent))
        extractor._content_filter = content_filter
        return extractor.extract_keyed_translations(keyed_dir)
    else:
        # 使用基本过滤
        translations = []
        xml_files = list(Path(keyed_dir).rglob("*.xml"))
        
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                for elem in root:
                    if isinstance(elem.tag, str) and elem.text:
                        if _basic_translatable_check(elem.tag, elem.text):
                            translations.append((elem.tag, elem.text.strip(), elem.tag, str(xml_file)))
                            
            except ET.ParseError as e:
                logging.error(f"XML解析失败: {xml_file}: {e}")
            except OSError as e:
                logging.error(f"文件读取失败: {xml_file}: {e}")
        
        return translations

@lru_cache(maxsize=1)
def preview_translatable_fields(
    mod_dir: str,
    preview: int = 100,
    facade=None
) -> List[Tuple[str, str, str, str]]:
    """预览可翻译字段 - 简化版本"""
    results = []
    defs_dir = Path(mod_dir) / "Defs"
    
    if not defs_dir.exists():
        logging.warning(f"Defs 目录不存在: {defs_dir}")
        return results
    
    xml_files = list(defs_dir.rglob("*.xml"))
    processed_count = 0
    
    for xml_file in xml_files:
        if processed_count >= preview:
            break
            
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            for def_elem in root.findall('.//Defs/*'):
                if processed_count >= preview:
                    break
                
                def_name_elem = def_elem.find('defName')
                if def_name_elem is None or not def_name_elem.text:
                    continue
                
                def_name = def_name_elem.text.strip()
                def_type = def_elem.tag
                
                for field_name, field_text in _extract_translatable_fields_recursive(def_elem):
                    if processed_count >= preview:
                        break
                    
                    # 🔧 简化过滤逻辑
                    filter_passed = False
                    if facade and hasattr(facade, 'content_filter'):
                        filter_passed = facade.content_filter.is_translatable(field_name, field_text, "Defs")
                    elif facade and hasattr(facade, '_is_translatable_content'):
                        filter_passed = facade._is_translatable_content(field_name, field_text, "Defs")
                    else:
                        filter_passed = _basic_translatable_check(field_name, field_text)
                    
                    if filter_passed:
                        key = f"{def_type}/{def_name}.{field_name}"
                        results.append((key, field_text, field_name, str(xml_file)))
                        processed_count += 1
                    
        except Exception as e:
            logging.error(f"文件处理失败 {xml_file}: {e}")
    
    return results

def _extract_translatable_fields_recursive(element: ET.Element, prefix: str = "") -> List[Tuple[str, str]]:
    """递归提取 - 简化版本"""
    results = []
    translatable_fields = {
        'label', 'description', 'labelShort', 'descriptionShort',
        'title', 'text', 'message', 'tooltip', 'baseDesc',
        'skillDescription', 'backstoryDesc', 'jobString',
        'gerundLabel', 'verb', 'deathMessage', 'summary',
        'note', 'flavor', 'quote', 'caption'
    }
    
    for child in element:
        if not isinstance(child.tag, str):
            continue
            
        field_name = f"{prefix}.{child.tag}" if prefix else child.tag
        
        if child.tag.lower() in translatable_fields and child.text and child.text.strip():
            results.append((field_name, child.text.strip()))
        
        if len(child) > 0 and len(field_name.split('.')) < 4:  # 限制深度
            results.extend(_extract_translatable_fields_recursive(child, field_name))
    
    return results

def _basic_translatable_check(tag: str, text: str) -> bool:
    """基本检查 - 最简版本"""
    if not text or len(text.strip()) < 2:
        return False
    
    blacklist = {'defName', 'id', 'cost', 'damage', 'x', 'y', 'z'}
    if tag.lower() in blacklist:
        return False
    
    if text.isdigit():
        return False
    
    return True

# 🔧 保持向后兼容的其他函数
def extract_key(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language
) -> None:
    """提取 Keyed 翻译"""
    logging.info(f"提取 Keyed 翻译: mod_dir={mod_dir}, export_dir={export_dir}")
    try:
        export_keyed(
            mod_dir=mod_dir,
            export_dir=export_dir,
            language=language,
            source_language=source_language
        )
    except (ET.ParseError, OSError) as e:
        logging.error(f"提取 Keyed 翻译失败: {e}")

def extract_definjected_from_defs(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language
) -> None:
    """从 Defs 提取 DefInjected 翻译"""
    selected_translations = preview_translatable_fields(mod_dir, preview=CONFIG.preview_translatable_fields)
    if not selected_translations:
        if CONFIG.preview_translatable_fields:
            print("未选择字段，跳过生成。")
        return
    try:
        export_definjected(
            mod_dir=mod_dir,
            export_dir=export_dir,
            selected_translations=selected_translations,
            language=language
        )
    except (ET.ParseError, OSError) as e:
        logging.error(f"提取 DefInjected 翻译失败: {e}")

def extract_translate(
    mod_dir: str,
    export_dir: str,
    language: str = CONFIG.default_language,
    source_language: str = CONFIG.source_language
) -> None:
    """提取所有翻译"""
    from .exporters import handle_extract_translate
    try:
        handle_extract_translate(
            mod_dir=mod_dir,
            export_dir=export_dir,
            language=language,
            source_language=source_language,
            extract_definjected_from_defs=extract_definjected_from_defs
        )
    except (ET.ParseError, OSError) as e:
        logging.error(f"提取翻译失败: {e}")

# 🔧 简化的同步扫描函数
def scan_defs_sync(defs_path: Path) -> List[Tuple[str, str, str, str]]:
    """同步扫描 Defs 目录 - 简化版"""
    all_translations = []
    for file in defs_path.rglob("*.xml"):
        translations = read_xml_sync(file)
        all_translations.extend(translations)
    return all_translations

def read_xml_sync(file: Path) -> List[Tuple[str, str, str, str]]:
    """同步读取 XML 文件 - 简化版"""
    translations = []
    try:
        tree = ET.parse(file)
        def_nodes = tree.findall(".//*[defName]")
        for def_node in def_nodes:
            def_type = def_node.tag
            def_name = def_node.find("defName")
            if def_name is None or not def_name.text:
                continue
            def_name_text = def_name.text
            fields = extract_translatable_fields(def_node)
            for field_path, text, tag in fields:
                clean_path = field_path
                if clean_path.startswith(f"{def_type}."):
                    clean_path = clean_path[len(def_type) + 1:]
                full_path = f"{def_type}/{def_name_text}.{clean_path}"
                translations.append((full_path, text, tag, str(file)))
    except Exception as e:
        logging.error(f"处理文件失败 {file}: {e}")
    return translations

# 🔧 异步功能（可选，如果需要高性能）
async def read_xml(file: Path) -> List[Tuple[str, str, str, str]]:
    """异步读取并解析 XML 文件"""
    translations = []
    try:
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(file, encoding="utf-8") as f:
                content = await f.read()
        else:
            with open(file, encoding="utf-8") as f:
                content = f.read()
        
        tree = ET.fromstring(content)
        def_nodes = tree.findall(".//*[defName]")
        for def_node in def_nodes:
            def_type = def_node.tag
            def_name = def_node.find("defName")
            if def_name is None or not def_name.text:
                continue
            def_name_text = def_name.text
            fields = extract_translatable_fields(def_node)
            for field_path, text, tag in fields:
                clean_path = field_path
                if clean_path.startswith(f"{def_type}."):
                    clean_path = clean_path[len(def_type) + 1:]
                full_path = f"{def_type}/{def_name_text}.{clean_path}"
                translations.append((full_path, text, tag, str(file)))
    except Exception as e:
        logging.error(f"异步处理失败 {file}: {e}")
    return translations

async def scan_defs(defs_path: Path) -> List[Tuple[str, str, str, str]]:
    """异步扫描 Defs 目录"""
    all_translations = []
    tasks = [read_xml(file) for file in defs_path.rglob("*.xml")]
    for task in await asyncio.gather(*tasks, return_exceptions=True):
        if isinstance(task, Exception):
            logging.error(f"异步任务失败: {task}")
        else:
            all_translations.extend(task)
    return all_translations

# 🗑️ 向后兼容：提供 EnhancedExtractor 别名
EnhancedExtractor = UnifiedExtractor