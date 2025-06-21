"""
Day Translation 2 - 数据提取核心模块

负责从游戏模组中提取可翻译的文本内容，支持Keyed和DefInjected两种格式。
遵循提示文件标准：具体异常类型、详细错误上下文、完整类型注解。

核心功能:
- Keyed翻译提取: 从Keyed目录提取界面文本
- DefInjected翻译提取: 从DefInjected目录提取游戏定义文本
- Defs扫描: 从Defs目录扫描可翻译字段
- 递归字段提取: 智能识别XML中的可翻译内容
"""

import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from colorama import Fore, Style

# 统一导入配置和异常处理
from services.config_service import config_service
from models.exceptions import ImportError as TranslationImportError
from models.exceptions import ProcessingError, TranslationError, ValidationError
from models.translation_data import TranslationData, TranslationType
from utils.file_utils import get_language_folder_path
from utils.filter_rules import AdvancedFilterRules
from utils.xml_processor import AdvancedXMLProcessor

# 确保能够导入项目模块
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
# tqdm处理 - 避免重定义问题
try:
    from tqdm import tqdm as TqdmProgressBar
except ImportError:
    # 如果没有安装tqdm，提供一个简单的替代
    def TqdmProgressBar(*args, **kwargs):
        class _TqdmProgressBar:
            def __init__(self, *args, **kwargs):
                self.total = kwargs.get("total", 0)
                self.current = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def update(self, n=1):
                self.current += n

        return _TqdmProgressBar(*args, **kwargs)


# 获取配置实例
CONFIG = config_service.get_unified_config()


def extract_keyed_translations(
    mod_dir: str, language: str = CONFIG.core.source_language
) -> List[TranslationData]:
    """
    提取Keyed翻译数据

    Args:
        mod_dir: 模组目录路径
        language: 目标语言代码

    Returns:
        提取的翻译条目列表

    Raises:
        ValidationError: 模组目录无效
        ProcessingError: XML处理失败
        TranslationImportError: 语言目录不存在
    """
    print(
        f"{Fore.GREEN}正在提取 Keyed 翻译（模组：{mod_dir}, 语言：{language}）...{Style.RESET_ALL}"
    )
    # 参数验证
    if not mod_dir or not Path(mod_dir).exists():
        raise ValidationError(f"无效的模组目录: {mod_dir}")

    if not language:
        raise ValidationError("语言代码不能为空")

    try:
        # 初始化新的高级处理器
        xml_processor = AdvancedXMLProcessor()
        filter_rules = AdvancedFilterRules()
        translations: List[TranslationData] = []

        # 构建Keyed目录路径
        lang_path = get_language_folder_path(language, mod_dir)
        keyed_dir = Path(lang_path) / CONFIG.core.keyed_dir

        logging.debug(f"语言路径: {lang_path}")
        logging.debug(f"Keyed目录: {keyed_dir}")

        if not keyed_dir.exists():
            logging.warning(f"Keyed 目录不存在: {keyed_dir}")
            raise TranslationImportError(f"语言目录不存在: {keyed_dir}")

        # 查找所有XML文件
        xml_files = list(keyed_dir.rglob("*.xml"))
        logging.info(f"找到 {len(xml_files)} 个Keyed XML文件")
        if not xml_files:
            logging.warning(f"Keyed目录中未找到XML文件: {keyed_dir}")
            return translations

        # 处理每个XML文件
        for xml_file in xml_files:
            try:
                logging.debug(f"处理文件: {xml_file}")
                tree = xml_processor.parse_xml(str(xml_file))

                if tree:
                    file_translations = []
                    # 使用新的高级XML处理器提取翻译
                    translations_raw = xml_processor.extract_translations(tree, context="Keyed")

                    for key, text, tag in translations_raw:
                        # 应用高级过滤规则
                        if filter_rules.should_translate_keyed(text, key):
                            # 创建翻译条目
                            entry = TranslationData(
                                key=key,
                                original_text=text,
                                translated_text="",  # 待翻译
                                translation_type=TranslationType.KEYED,
                                file_path=str(xml_file.relative_to(keyed_dir)),
                                tag=tag,
                                context=f"语言:{language}, 模组:{mod_dir}",
                            )
                            file_translations.append(entry)

                    logging.debug(f"从 {xml_file.name} 提取到 {len(file_translations)} 条翻译")
                    translations.extend(file_translations)
                else:
                    logging.error(f"无法解析XML文件: {xml_file}")

            except Exception as e:
                logging.error(f"处理XML文件失败 {xml_file}: {str(e)}")
                # 继续处理其他文件，不中断整个流程
                continue

        print(f"{Fore.GREEN}✅ 提取到 {len(translations)} 条 Keyed 翻译{Style.RESET_ALL}")
        logging.info(f"Keyed翻译提取完成: {len(translations)} 条")

        return translations

    except (ValidationError, TranslationImportError):
        # 重新抛出已知异常
        raise
    except Exception as e:
        error_msg = f"Keyed翻译提取失败: {str(e)}"
        logging.error(error_msg)
        raise ProcessingError(
            error_msg,
            operation="extract_keyed_translations",
            stage="数据提取",
            affected_items=[mod_dir, language],
        )


def scan_defs_sync(
    mod_dir: str,
    def_types: Optional[Set[str]] = None,
    language: str = CONFIG.core.source_language,
    max_workers: int = 4,
) -> List[TranslationData]:
    """
    同步扫描Defs目录中的可翻译内容（支持多线程）

    Args:
        mod_dir: 模组目录路径
        def_types: 要扫描的定义类型集合，None表示扫描所有类型
        language: 目标语言代码
        max_workers: 最大并发工作线程数

    Returns:
        提取的翻译条目列表

    Raises:
        ValidationError: 参数验证失败
        ProcessingError: 扫描处理失败
    """
    print(
        f"{Fore.GREEN}正在扫描 Defs 目录（模组：{mod_dir}, 语言：{language}）...{Style.RESET_ALL}"
    )

    # 参数验证
    if not mod_dir or not Path(mod_dir).exists():
        raise ValidationError(f"无效的模组目录: {mod_dir}")

    try:
        # 使用新的高级处理器
        xml_processor = AdvancedXMLProcessor()  # 使用新的高级XML处理器
        filter_rules = AdvancedFilterRules()  # 使用新的高级过滤规则
        translations: List[TranslationData] = []
        defs_dir = Path(mod_dir) / "Defs"

        if not defs_dir.exists():
            logging.warning(f"Defs 目录不存在: {defs_dir}")
            return translations
        logging.debug(f"Defs目录: {defs_dir}")
        # 查找所有XML文件
        xml_files = list(defs_dir.rglob("*.xml"))

        if not xml_files:
            logging.info(f"在 {defs_dir} 中没有找到XML文件")
            return translations

        # 根据文件数量决定是否使用多线程
        logging.debug(f"扫描到 {len(xml_files)} 个Defs XML文件")
        if len(xml_files) <= 3 or max_workers <= 1:
            # 单线程处理（文件少或指定单线程）
            for xml_file in xml_files:
                file_translations = _process_single_defs_file(
                    xml_file,
                    xml_processor,
                    filter_rules,
                    def_types,
                    language,
                    defs_dir,
                    mod_dir,
                )
                translations.extend(file_translations)
        else:
            # 多线程处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交任务
                future_to_file = {
                    executor.submit(
                        _process_single_defs_file,
                        xml_file,
                        xml_processor,
                        filter_rules,
                        def_types,
                        language,
                        defs_dir,
                        mod_dir,
                    ): xml_file
                    for xml_file in xml_files
                }

                # 收集结果，使用进度条
                with TqdmProgressBar(
                    total=len(xml_files), desc="扫描Defs文件", unit="文件"
                ) as progress_bar:
                    for future in as_completed(future_to_file):
                        xml_file = future_to_file[future]
                        try:
                            file_translations = future.result()
                            translations.extend(file_translations)
                        except Exception as e:
                            logging.error(f"处理Defs文件失败: {xml_file}, 错误: {e}")
                        finally:
                            progress_bar.update(1)

        print(f"{Fore.GREEN}✅ 扫描到 {len(translations)} 条 Defs 翻译{Style.RESET_ALL}")
        logging.info(f"Defs扫描完成: {len(translations)} 条")

        return translations

    except ValidationError:
        raise
    except Exception as e:
        error_msg = f"Defs扫描失败: {str(e)}"
        logging.error(error_msg)
        raise ProcessingError(
            error_msg,
            operation="scan_defs_sync",
            stage="文件扫描",
            affected_items=[mod_dir, language],
        )


def extract_definjected_translations(
    mod_dir: str, language: str = CONFIG.core.source_language
) -> List[TranslationData]:
    """
    提取DefInjected翻译数据

    Args:
        mod_dir: 模组目录路径
        language: 目标语言代码

    Returns:
        提取的翻译条目列表

    Raises:
        ValidationError: 参数验证失败
        ProcessingError: 提取处理失败
    """
    print(
        f"{Fore.GREEN}正在提取 DefInjected 翻译（模组：{mod_dir}, 语言：{language}）...{Style.RESET_ALL}"
    )  # 参数验证
    if not mod_dir or not Path(mod_dir).exists():
        raise ValidationError(f"无效的模组目录: {mod_dir}")

    try:
        processor = AdvancedXMLProcessor()
        filter_rules = AdvancedFilterRules()
        translations: List[TranslationData] = []

        # 构建DefInjected目录路径
        lang_path = get_language_folder_path(language, mod_dir)
        definjected_dir = Path(lang_path) / CONFIG.core.definjected_dir

        if not definjected_dir.exists():
            logging.warning(f"DefInjected 目录不存在: {definjected_dir}")
            return translations

        # 查找所有XML文件
        xml_files = list(definjected_dir.rglob("*.xml"))
        logging.info(f"找到 {len(xml_files)} 个DefInjected XML文件")

        for xml_file in xml_files:
            try:
                logging.debug(f"处理DefInjected文件: {xml_file}")
                tree = processor.parse_xml(str(xml_file))

                if tree:
                    file_translations = []

                    # 使用DefInjected专用的过滤函数
                    def def_filter_func(text: str) -> bool:
                        """DefInjected过滤函数，只接收text参数"""
                        # 使用简化的过滤逻辑
                        return bool(filter_rules.should_translate_field("", text))

                    for key, text, tag in processor.extract_translations(
                        tree, context="DefInjected", filter_func=def_filter_func
                    ):
                        entry = TranslationData(
                            key=key,
                            original_text=text,
                            translated_text="",
                            translation_type=TranslationType.DEFINJECTED,
                            file_path=str(xml_file.relative_to(definjected_dir)),
                            tag=tag,
                            context=f"语言:{language}, 模组:{mod_dir}",
                        )
                        file_translations.append(entry)

                    logging.debug(f"从 {xml_file.name} 提取到 {len(file_translations)} 条翻译")
                    translations.extend(file_translations)
                else:
                    logging.error(f"无法解析DefInjected XML文件: {xml_file}")

            except Exception as e:
                logging.error(f"处理DefInjected XML文件失败 {xml_file}: {str(e)}")
                continue

        print(f"{Fore.GREEN}✅ 提取到 {len(translations)} 条 DefInjected 翻译{Style.RESET_ALL}")
        logging.info(f"DefInjected翻译提取完成: {len(translations)} 条")

        return translations

    except ValidationError:
        raise
    except Exception as e:
        error_msg = f"DefInjected翻译提取失败: {str(e)}"
        logging.error(error_msg)
        raise ProcessingError(
            error_msg,
            operation="extract_definjected_translations",
            stage="XML处理",
            affected_items=[mod_dir, language],
        )


def _extract_translatable_fields_recursive(
    element: Any,
    def_type: str,
    def_name: str,
    filter_rules: AdvancedFilterRules,
    current_path: str,
    parent_tag: Optional[str],
    root_def_type: str,
) -> List[Tuple[str, str, str]]:
    """
    递归提取XML节点中的可翻译字段

    Args:
        element: XML元素节点
        def_type: 定义类型
        def_name: 定义名称
        filter_rules: 高级过滤规则
        current_path: 当前路径
        parent_tag: 父标签
        root_def_type: 根定义类型

    Returns:
        可翻译字段列表: [(field_path, text, tag), ...]"""
    results: List[Tuple[str, str, str]] = []

    if element is None:
        return results

    try:
        # 检查当前元素是否包含可翻译文本
        if hasattr(element, "text") and element.text:
            text = element.text.strip()
            if text and filter_rules.should_translate_def_field(text, element.tag, def_type):
                # 构建字段路径
                field_path = current_path if current_path else element.tag
                results.append((field_path, text, element.tag))

        # 递归处理子元素
        if hasattr(element, "iter"):
            for child in element:
                child_path = f"{current_path}.{child.tag}" if current_path else child.tag
                child_results = _extract_translatable_fields_recursive(
                    child,
                    def_type,
                    def_name,
                    filter_rules,
                    child_path,
                    element.tag,
                    root_def_type,
                )
                results.extend(child_results)

    except Exception as e:
        logging.warning(f"递归提取字段时出错: {str(e)}")

    return results


def _extract_keyed_from_file(file_path: str, processor) -> List[Tuple[str, str, str, str]]:
    """
    从单个Keyed XML文件提取翻译数据

    Args:
        file_path: XML文件路径
        processor: XML处理器实例

    Returns:
        List[Tuple[str, str, str, str]]: 翻译数据列表
    """
    translations: List[Tuple[str, str, str, str]] = []

    try:
        tree = processor.parse_xml(file_path)
        if tree is None:
            return translations

        root = tree.getroot()

        # 处理LanguageData节点
        for lang_data in root.findall("LanguageData"):
            for element in lang_data:
                key = element.tag
                text = element.text

                if key and text:
                    translations.append((key, text.strip(), element.tag, file_path))

        return translations

    except Exception as e:
        raise ProcessingError(
            f"解析Keyed文件失败: {str(e)}",
            operation="_extract_keyed_from_file",
            stage="XML解析",
            affected_items=[file_path],
        )


def _extract_definjected_from_file(file_path: str, processor) -> List[Tuple[str, str, str, str]]:
    """
    从单个DefInjected XML文件提取翻译数据

    Args:
        file_path: XML文件路径
        processor: XML处理器实例

    Returns:
        List[Tuple[str, str, str, str]]: 翻译数据列表
    """
    translations: List[Tuple[str, str, str, str]] = []

    try:
        tree = processor.parse_xml(file_path)
        if tree is None:
            return translations

        root = tree.getroot()

        # 处理LanguageData节点
        for lang_data in root.findall("LanguageData"):
            for element in lang_data:
                # DefInjected的key格式通常是 DefType.DefName.FieldPath
                key = element.tag
                text = element.text

                if key and text and "." in key:
                    translations.append((key, text.strip(), element.tag, file_path))

        return translations

    except Exception as e:
        raise ProcessingError(
            f"解析DefInjected文件失败: {str(e)}",
            operation="_extract_definjected_from_file",
            stage="XML解析",
            affected_items=[file_path],
        )


def _process_single_defs_file(
    xml_file: Path,
    xml_processor: "AdvancedXMLProcessor",
    filter_rules: "AdvancedFilterRules",
    def_types: Optional[Set[str]],
    language: str,
    defs_dir: Path,
    mod_dir: str,
) -> List[TranslationData]:
    """
    处理单个Defs XML文件，提取可翻译内容

    Args:
        xml_file: XML文件路径
        xml_processor: XML处理器实例
        filter_rules: 过滤规则实例
        def_types: 定义类型过滤集合
        language: 目标语言
        defs_dir: Defs目录路径
        mod_dir: 模组目录路径

    Returns:
        该文件中提取的翻译条目列表
    """
    translations: List[TranslationData] = []

    try:
        logging.debug(f"处理Defs文件: {xml_file}")
        tree = xml_processor.parse_xml(str(xml_file))

        if tree:
            root = tree.getroot() if hasattr(tree, "getroot") else tree

            # 查找所有有defName的节点（RimWorld标准）
            # Note: defName是RimWorld游戏中的标准字段名，不是拼写错误
            definition_nodes = []
            for elem in root.iter():
                def_name_elem = elem.find("defName")
                if def_name_elem is not None and def_name_elem.text:
                    definition_nodes.append(elem)

            logging.debug(f"在 {xml_file.name} 中找到 {len(definition_nodes)} 个定义节点")

            for def_node in definition_nodes:
                def_type = def_node.tag
                def_name_elem = def_node.find("defName")

                if def_name_elem is None or not def_name_elem.text:
                    continue

                # 如果指定了类型过滤，检查是否匹配
                if def_types and def_type not in def_types:
                    continue

                def_name = def_name_elem.text

                # 递归提取可翻译字段
                field_translations = _extract_translatable_fields_recursive(
                    def_node, def_type, def_name, filter_rules, "", None, def_type
                )

                # 转换为TranslationData格式
                for field_path, text, tag in field_translations:
                    # 清理路径中重复的def_type前缀
                    clean_path = field_path
                    if clean_path.startswith(def_type + "."):
                        clean_path = clean_path[len(def_type) + 1 :]

                    full_path = f"{def_type}/{def_name}.{clean_path}"

                    entry = TranslationData(
                        key=full_path,
                        original_text=text,
                        translated_text="",
                        translation_type=TranslationType.DEFINJECTED,
                        file_path=str(xml_file.relative_to(defs_dir)),
                        tag=tag,
                        context=f"类型:{def_type}, 名称:{def_name}",
                    )
                    translations.append(entry)

                logging.debug(f"从 {def_name} 提取到 {len(field_translations)} 条翻译")
        else:
            logging.error(f"无法解析Defs XML文件: {xml_file}")

    except Exception as e:
        logging.error(f"处理Defs XML文件失败 {xml_file}: {str(e)}")
        # 在多线程环境中，我们抛出异常让调用者处理
        raise ProcessingError(
            f"处理文件失败: {str(e)}",
            operation="_process_single_defs_file",
            stage="XML解析",
            affected_items=[str(xml_file)],
        )

    return translations


class AdvancedExtractor:
    """
    高级提取器类 - 游戏本地化文本提取的门面类

    提供统一的接口来提取各种类型的翻译数据：
    - Keyed翻译提取
    - DefInjected翻译提取
    - Defs定义扫描
    - 批量处理和过滤
    """

    def __init__(self, mod_dir: str, language: Optional[str] = None):
        """
        初始化高级提取器

        Args:
            mod_dir: 模组目录路径
            language: 源语言，默认使用配置中的源语言
        """
        self.mod_dir = mod_dir
        self.language = language or CONFIG.core.source_language
        self.config = CONFIG

        # 初始化组件
        self.xml_processor = AdvancedXMLProcessor()
        self.filter_rules = AdvancedFilterRules()

        # 设置日志
        self.logger = logging.getLogger(__name__)

    def extract_keyed(self) -> List[TranslationData]:
        """
        提取Keyed翻译数据

        Returns:
            提取的翻译数据列表
        """
        return extract_keyed_translations(self.mod_dir, self.language)

    def extract_definjected(self) -> List[TranslationData]:
        """
        提取DefInjected翻译数据

        Returns:
            提取的翻译数据列表
        """
        return extract_definjected_translations(self.mod_dir, self.language)

    def scan_defs(self, def_types: Optional[Set[str]] = None) -> List[TranslationData]:
        """
        扫描Defs定义

        Args:
            def_types: 要扫描的定义类型集合，None表示扫描所有类型

        Returns:
            扫描到的定义数据列表
        """
        return scan_defs_sync(self.mod_dir, def_types, self.language)

    def extract_all(self) -> Dict[str, List[TranslationData]]:
        """
        提取所有类型的翻译数据

        Returns:
            按类型分组的翻译数据字典
        """
        results = {}

        try:
            # 提取Keyed翻译
            self.logger.info("开始提取Keyed翻译...")
            results["keyed"] = self.extract_keyed()
            self.logger.info(f"Keyed翻译提取完成，共 {len(results['keyed'])} 条")

            # 提取DefInjected翻译
            self.logger.info("开始提取DefInjected翻译...")
            results["definjected"] = self.extract_definjected()
            self.logger.info(f"DefInjected翻译提取完成，共 {len(results['definjected'])} 条")

            # 扫描Defs定义
            self.logger.info("开始扫描Defs定义...")
            results["defs"] = self.scan_defs()
            self.logger.info(f"Defs定义扫描完成，共 {len(results['defs'])} 条")

        except Exception as e:
            self.logger.error(f"提取过程中出现错误: {e}")
            raise

        total_count = sum(len(data) for data in results.values())
        self.logger.info(f"所有提取完成，总计 {total_count} 条数据")

        return results

    def get_statistics(self) -> Dict[str, int]:
        """
        获取提取统计信息

        Returns:
            统计信息字典
        """
        try:
            all_data = self.extract_all()
            return {
                "keyed_count": len(all_data.get("keyed", [])),
                "definjected_count": len(all_data.get("definjected", [])),
                "defs_count": len(all_data.get("defs", [])),
                "total_count": sum(len(data) for data in all_data.values()),
            }
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {
                "keyed_count": 0,
                "definjected_count": 0,
                "defs_count": 0,
                "total_count": 0,
            }


# 导出所有函数和类
__all__ = [
    # 主要提取函数
    "extract_keyed_translations",
    "extract_definjected_translations",
    "scan_defs_sync",
    # 高级提取器类
    "AdvancedExtractor",
]
