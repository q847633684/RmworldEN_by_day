"""
清理过时/重复 key 模块

扫描 DefInjected 与 Keyed 下的 XML，删除带有「过时key，需删除」或「重复key，需删除」注释的条目及其注释。
"""

from pathlib import Path
from typing import Tuple
from utils.constants import SUBDIR_TYPE_DEFINJECTED, SUBDIR_TYPE_KEYED
from utils.logging_config import get_logger
from utils.ui_style import ui
from utils.utils import XMLProcessor
from user_config import UserConfigManager

logger = get_logger(__name__)

# 需删除的注释标记（与 merger 中写入的文案一致）
MARKER_OUTDATED = "过时key，需删除"
MARKER_DUPLICATE = "重复key，需删除"


def _is_comment(node) -> bool:
    """判断节点是否为注释节点（lxml Comment 的 tag 非字符串）"""
    if not hasattr(node, "tag"):
        return False
    # lxml.etree.Comment 的 tag 是 Comment 类型，不是 str
    return not isinstance(node.tag, str)


def _is_element(node) -> bool:
    """判断节点是否为普通元素（非注释）"""
    return hasattr(node, "tag") and isinstance(node.tag, str)


def _cleanup_one_file(processor: XMLProcessor, xml_path: Path) -> int:
    """
    清理单个 XML 文件中带「过时key，需删除」或「重复key，需删除」的注释及其紧邻的 key 元素。
    返回本文件删除的条目数（每对 注释+元素 计为 1）。
    """
    tree = processor.parse_xml(str(xml_path))
    if tree is None:
        return 0
    root = tree.getroot()
    children = list(root)
    to_remove = []
    for i in range(len(children) - 1):
        curr = children[i]
        next_node = children[i + 1]
        if not _is_comment(curr) or not _is_element(next_node):
            continue
        text = (getattr(curr, "text", None) or "").strip()
        if MARKER_OUTDATED in text or MARKER_DUPLICATE in text:
            to_remove.append(curr)
            to_remove.append(next_node)
    for node in to_remove:
        root.remove(node)
    if not to_remove:
        return 0
    pairs = len(to_remove) // 2
    if processor.save_xml(root, str(xml_path), pretty_print=True):
        logger.info("已清理 %s：删除 %d 条", xml_path.name, pairs)
        return pairs
    logger.warning("保存失败: %s", xml_path)
    return 0


def cleanup_mod_outdated_keys(
    mod_dir: str,
    language: str = None,
) -> Tuple[int, int]:
    """
    清理指定模组语言目录下 DefInjected 与 Keyed 中的过时/重复 key。

    Args:
        mod_dir: 模组根目录
        language: 语言目录名，默认从配置读取 cn_language

    Returns:
        (删除的条目总数, 涉及的文件数)
    """
    config = UserConfigManager.get_instance()
    if language is None:
        language = config.language_config.get_default_cn_language()
    lang_dir = config.language_config.get_language_dir(mod_dir, language)
    if not lang_dir.exists():
        logger.warning("语言目录不存在: %s", lang_dir)
        return 0, 0

    processor = XMLProcessor()
    total_deleted = 0
    files_modified = 0

    for subdir_name in (SUBDIR_TYPE_DEFINJECTED, SUBDIR_TYPE_KEYED):
        subdir = config.language_config.get_language_subdir(mod_dir, language, subdir_name)
        if not subdir.exists():
            continue
        for xml_path in subdir.rglob("*.xml"):
            try:
                n = _cleanup_one_file(processor, xml_path)
                if n > 0:
                    total_deleted += n
                    files_modified += 1
            except Exception as e:
                logger.exception("清理文件时出错 %s: %s", xml_path, e)

    return total_deleted, files_modified


def handle_cleanup_outdated_keys():
    """交互式执行：选择模组目录后清理过时/重复 key"""
    from utils.interaction import select_mod_path_with_version_detection
    from utils.interaction import confirm_action

    logger_local = get_logger(f"{__name__}.handle_cleanup_outdated_keys")
    ui.print_section_header("清理过时/重复 key", ui.Icons.SETTINGS)
    ui.print_info("将删除带有「过时key，需删除」或「重复key，需删除」注释的条目。")

    result = select_mod_path_with_version_detection(allow_multidlc=False)
    if not result:
        return
    mod_dir = result if isinstance(result, str) else result[0]
    config = UserConfigManager.get_instance()
    language = config.language_config.get_default_cn_language()

    if not confirm_action(f"确认清理模组内 {language} 的过时/重复 key？"):
        ui.print_warning("已取消")
        return

    try:
        total, files = cleanup_mod_outdated_keys(mod_dir, language)
        if total > 0:
            ui.print_success(f"清理完成：共删除 {total} 条，涉及 {files} 个文件。")
        else:
            ui.print_info("未发现需删除的过时/重复 key。")
    except Exception as e:
        ui.print_error(f"清理失败: {e}")
        logger_local.exception("清理过时/重复 key 失败")
