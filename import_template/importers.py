"""
导入功能模块 - 实现翻译结果导入到模板的功能
"""

import csv
from utils.logging_config import get_logger
from utils.ui_style import ui
from pathlib import Path
from typing import Dict, Tuple, Any, Optional, Callable, List, Union
from utils.utils import XMLProcessor
from user_config.path_manager import PathManager

# 使用新配置系统
from user_config import UserConfigManager

# 使用全局配置实例，避免重复初始化
CONFIG = UserConfigManager.get_instance()
logger = get_logger(__name__)


def import_translations(
    csv_path: str,
    mod_dir: str,
    merge: bool = True,
    auto_create_templates: bool = True,
    language: str = CONFIG.language_config.get_value(
        "cn_language", "ChineseSimplified"
    ),
) -> bool:
    """
    将翻译CSV导入到翻译模板

    Args:
        csv_path (str): 翻译CSV文件路径
        mod_dir (str): 模组目录
        merge (bool): 是否合并现有翻译
        auto_create_templates (bool): 是否自动创建模板
        language (str): 目标语言

    Returns:
        bool: 导入是否成功
    """
    logger.info("开始导入翻译到模板: %s", csv_path)
    try:
        # 步骤1：确保翻译模板存在
        if auto_create_templates:
            # 检查模板目录是否存在，如果不存在则提示用户先创建模板
            if not CONFIG.language_config.get_language_dir(mod_dir, language).exists():
                logger.error("翻译模板目录不存在，请先使用提取功能创建翻译模板")
                ui.print_error("❌ 翻译模板目录不存在，请先使用提取功能创建翻译模板")
                return False
        # 步骤2：验证CSV文件
        if not _validate_csv_file(csv_path):
            return False
        # 步骤3：加载翻译数据并按类型分组
        keyed_translations, definjected_translations = _load_translations_from_csv(
            csv_path
        )
        if not keyed_translations and not definjected_translations:
            return False

        # 步骤4：分别更新 Keyed 与 DefInjected 目录下的 XML 文件
        updated_count = 0
        updated_count += _update_xml_in_subdir(
            mod_dir, language, "keyed", keyed_translations, merge
        )
        updated_count += _update_xml_in_subdir(
            mod_dir, language, "definjected", definjected_translations, merge
        )
        # 步骤5：验证导入结果
        had_translations = bool(keyed_translations or definjected_translations)
        if had_translations and updated_count == 0:
            logger.warning(
                "CSV 中有 %s 条 Keyed、%s 条 DefInjected，但未匹配到任何 XML 节点，未写入任何文件",
                len(keyed_translations),
                len(definjected_translations),
            )
            ui.print_warning(
                "⚠️ 未导入任何内容：CSV 的 key 与模板 XML 节点不匹配，请确认 CSV 与当前模板来自同一模组/同一提取。"
            )
            return False
        success = _verify_import_results(mod_dir, language)
        if success:
            logger.info("翻译导入到模板完成，更新了 %s 个文件", updated_count)
            ui.print_success("翻译已成功导入到模板")
        else:
            logger.warning("翻译导入可能存在问题")
            ui.print_warning("⚠️ 翻译导入完成，但可能存在问题")
        return success
    except FileNotFoundError as e:
        logger.error("文件未找到: %s", e)
        ui.print_error(f"❌ 文件未找到: {e}")
        return False
    except PermissionError as e:
        logger.error("权限错误: %s", e)
        ui.print_error(f"❌ 权限错误: {e}")
        return False
    except (OSError, ValueError, TypeError, RuntimeError) as e:
        logger.error("导入翻译时发生错误: %s", e, exc_info=True)
        ui.print_error(f"❌ 导入失败: {e}")
        return False


def _validate_csv_file(csv_path: str) -> bool:
    """验证CSV文件"""
    if not Path(csv_path).is_file():
        logger.error("CSV文件不存在: %s", csv_path)
        return False

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            if not header or not all(col in header for col in ["key", "text"]):
                logger.error("CSV文件格式无效：缺少必要的列 (key, text)")
                return False

            # 检查是否有type列，如果没有则使用兼容模式
            has_type_column = "type" in header
            if has_type_column:
                logger.info("检测到新格式CSV文件（包含type列）")
            else:
                logger.info("检测到旧格式CSV文件（无type列），将使用兼容模式")

            return True
    except FileNotFoundError:
        logger.error("CSV文件不存在: %s", csv_path)
        return False
    except PermissionError:
        logger.error("无权限访问CSV文件: %s", csv_path)
        return False
    except UnicodeDecodeError:
        logger.error("CSV文件编码错误: %s", csv_path)
        return False
    except (OSError, ValueError, TypeError) as e:
        logger.error("验证CSV文件时发生错误: %s", e)
        return False


def _load_translations_from_csv(csv_path: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """从CSV文件加载翻译数据，按类型分组

    Returns:
        Tuple[Dict[str, str], Dict[str, str]]: (keyed_translations, definjected_translations)
    """
    keyed_translations = {}
    definjected_translations = {}

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row.get("key") or "").strip()
                # 优先使用 translated 列，其次回退到 text 列
                value = (row.get("translated") or row.get("text") or "").strip()
                translation_type = (row.get("type") or "").strip().lower()

                if key and value:
                    if translation_type == "keyed":
                        keyed_translations[key] = value
                    elif translation_type == "def":
                        definjected_translations[key] = value
                    else:
                        # 兼容旧格式：如果没有type列或type为空，使用原来的规则
                        if "/" in key:
                            definjected_translations[key] = value
                        else:
                            keyed_translations[key] = value

        return keyed_translations, definjected_translations
    except FileNotFoundError:
        logger.error("CSV文件不存在: %s", csv_path)
        ui.print_error(f"❌ CSV文件不存在: {csv_path}")
        return {}, {}
    except PermissionError:
        logger.error("无权限访问CSV文件: %s", csv_path)
        ui.print_error(f"❌ 无权限访问CSV文件: {csv_path}")
        return {}, {}
    except (OSError, ValueError, TypeError) as e:
        logger.error("加载CSV文件时发生错误: %s", e)
        ui.print_error(f"❌ 加载CSV文件失败: {e}")
        return {}, {}


def _definjected_get_parent(elem: Any, root: Any, parent_map: Optional[dict]) -> Any:
    """获取元素的父节点，兼容 lxml（getparent）与标准库（parent_map）。"""
    if parent_map is not None:
        return parent_map.get(elem)
    getparent = getattr(elem, "getparent", None)
    if callable(getparent):
        return getparent()
    return None


def _looks_like_en_placeholder(text: str) -> bool:
    """
    判断文本是否像 DefInjected 中的英文占位（新模板常带 EN 注释格式），
    这类内容在迁移时应视为可覆盖，即使用户选了「仅填充空项」。
    """
    if not text or len(text) < 20:
        return False
    t = text.strip()
    # 常见 EN 占位：tag=... -> 英文句子、或 -&gt; 英文
    if "->" in t or "&gt;" in t or "-&gt;" in t:
        # 大部分为 ASCII 或拉丁字符则视为英文占位
        try:
            ascii_or_latin = sum(1 for c in t if ord(c) < 256)
            if ascii_or_latin >= len(t) * 0.85:
                return True
        except Exception:
            pass
    # 以常见规则前缀开头（RimWorld / AROM 等）
    lower = t.lower()
    for prefix in ("creation(", "episode(", "intro(", "conflict(", "victory(", "setup(", "story(", "lesson", "archist", "animist", "founder"):
        if lower.startswith(prefix) and ("->" in t or "&gt;" in t):
            return True
    return False


def _definjected_tag_local(tag: Any) -> str:
    """取标签的本地名（去掉命名空间），便于与 CSV 的 key 一致。"""
    if not isinstance(tag, str):
        return ""
    if tag.startswith("{"):
        return tag.split("}", 1)[-1]
    return tag


def _definjected_li_siblings(parent: Any) -> list:
    """取父节点下所有 <li> 子元素（排除注释等），保证索引与旧版 flat_all 的 .0/.1 一致。"""
    return [
        c
        for c in parent
        if isinstance(getattr(c, "tag", None), str)
        and _definjected_tag_local(getattr(c, "tag", None)) == "li"
    ]


def _definjected_key_func(elem: Any, root: Any, parent_map: Optional[dict]) -> str:
    """
    DefInjected 用「父路径.标签」或「父路径.索引」生成 key，与提取器一致。
    约定：容器下的第 1 个 <li> -> 容器路径.0，第 2 个 -> .1，与旧版 flat_all 的 key 一致。
    支持的格式示例（根为 <LanguageData>）：
      - 平铺标签：<DefName.field>text</...> → key = "DefName.field"
      - 列表容器+<li>：<DefName.xxx.rulesStrings><li>...</li><li>...</li></...>
        → 第 1 个 li 的 key = "DefName.xxx.rulesStrings.0"，第 2 个 = ".1"
    兼容 lxml（parent_map 为 None 时用 elem.getparent()）与标准库 XML。
    带命名空间的标签使用本地名，以便与 CSV 中通常无命名空间的 key 匹配。
    """
    tag = getattr(elem, "tag", None)
    tag_local = _definjected_tag_local(tag)
    if not tag_local:
        return ""
    parent_tags = []
    p = _definjected_get_parent(elem, root, parent_map)
    while p is not None and p is not root:
        pt = getattr(p, "tag", None)
        pt_local = _definjected_tag_local(pt) if isinstance(pt, str) else ""
        if pt_local == "li":
            parent = _definjected_get_parent(p, root, parent_map)
            if parent is not None:
                li_siblings = _definjected_li_siblings(parent)
                try:
                    idx = li_siblings.index(p)
                except ValueError:
                    idx = 0
                parent_tags.append(str(idx))
            else:
                parent_tags.append("0")
        elif pt_local:
            parent_tags.append(pt_local)
        p = _definjected_get_parent(p, root, parent_map)
    parent_tags.reverse()
    if tag_local == "li":
        parent = _definjected_get_parent(elem, root, parent_map)
        if parent is not None:
            li_siblings = _definjected_li_siblings(parent)
            try:
                idx = li_siblings.index(elem)
            except ValueError:
                idx = 0
            return ".".join(parent_tags + [str(idx)])
        return ".".join(parent_tags + ["0"])
    if not parent_tags and "." in tag_local:
        return tag_local
    return ".".join(parent_tags + [tag_local]) if parent_tags else tag_local


def _get_language_subdir_path(base_dir: str, language: str, subdir_type: str) -> Path:
    """
    解析语言子目录路径。支持四种情况：
    1) base_dir 下直接有 Keyed/DefInjected -> 视为语言目录
    2) base_dir 下有 language/Keyed（如 Languages2/ChineseSimplified/Keyed）-> 视为 Languages 父目录
    3) base_dir 下递归查找第一个 Keyed/DefInjected 目录（支持补丁目录如 Cumpilation/ould）
    4) 否则按模组根：base_dir/Languages/language/Keyed
    """
    base = Path(base_dir)
    keyed_name = CONFIG.language_config.get_value("keyed_dir", "Keyed")
    def_name = CONFIG.language_config.get_value("definjected_dir", "DefInjected")
    if (base / keyed_name).exists() or (base / def_name).exists():
        sub = keyed_name if subdir_type.lower() == "keyed" else def_name
        return base / sub
    if (base / language / keyed_name).exists() or (base / language / def_name).exists():
        sub = keyed_name if subdir_type.lower() == "keyed" else def_name
        return base / language / sub
    # 补丁目录：在 base 下递归找 Keyed/DefInjected 目录，优先最浅层
    sub = keyed_name if subdir_type.lower() == "keyed" else def_name
    candidates = [p for p in base.rglob(sub) if p.is_dir()]
    if candidates:
        candidates.sort(key=lambda p: len(p.relative_to(base).parts))
        return candidates[0]
    return CONFIG.language_config.get_language_subdir(
        base_dir, language, subdir_type
    )


def _collect_old_translations(
    old_base_dir: str,
    language: str,
) -> Tuple[Dict[str, str], Dict[Tuple[str, str], str]]:
    """
    扫描旧翻译目录，收集 Keyed 与 DefInjected 中已有翻译。
    Keyed: key → 非空译文。
    DefInjected: (key, scope) → 非空译文，按 Def 类型(scope)区分，避免同 key 不同 Def 类型互相覆盖。

    Args:
        old_base_dir: 旧模组根目录、语言目录、或直接 Keyed/DefInjected 文件夹
        language: 语言代码，如 ChineseSimplified

    Returns:
        (keyed_map, definjected_map) 其中 definjected_map 的 key 为 (key, scope)
    """
    processor = XMLProcessor()
    keyed_map: Dict[str, str] = {}
    definjected_map: Dict[Tuple[str, str], str] = {}

    for subdir_type, use_def_key in [("keyed", False), ("definjected", True)]:
        subdir = _get_language_subdir_path(old_base_dir, language, subdir_type)
        if not subdir.exists():
            continue
        xml_files = list(Path(subdir).rglob("*.xml"))
        for xml_file in xml_files:
            try:
                # DefInjected：scope = 相对 subdir 的首段路径（Def 类型，如 HediffDef）
                rel = xml_file.relative_to(subdir)
                scope = rel.parts[0] if rel.parts else (xml_file.stem or "")
                tree = processor.parse_xml(str(xml_file))
                if tree is None:
                    continue
                root = tree.getroot() if processor.use_lxml else tree
                parent_map = (
                    {c: p for p in root.iter() for c in p}
                    if not processor.use_lxml
                    else None
                )
                for elem in root.xpath(".//*") if processor.use_lxml else root.iter():
                    key = (
                        _definjected_key_func(elem, root, parent_map)
                        if use_def_key
                        else processor._get_element_key(elem)
                    )
                    if not key:
                        continue
                    text = (elem.text or "").strip()
                    if text:
                        if use_def_key:
                            definjected_map[(key, scope)] = text
                        else:
                            keyed_map[key] = text
            except (OSError, ValueError, TypeError) as e:
                logger.debug("跳过 %s: %s", xml_file, e)

    return keyed_map, definjected_map


def migrate_translations_to_new(
    old_base_dirs: Union[str, List[str]],
    new_base_dir: str,
    language: str,
    only_fill_empty: bool = True,
) -> int:
    """
    从多个旧翻译目录收集所有 key→译文，合并后按 key 一一对应写入新模板；无需移动文件。

    old_base_dirs 可为单个路径或路径列表；多个目录时从各处收集并合并（同 key 后者覆盖）。
    DefInjected 的 nested / flat_with_li / flat_all 可任意互导，读写时统一按 key 匹配。

    Args:
        old_base_dirs: 旧模组根/语言目录或 Keyed/DefInjected 文件夹；多个用列表，将合并收集
        new_base_dir: 新模组/模板根目录、语言目录、或 Keyed/DefInjected 文件夹
        language: 语言代码
        only_fill_empty: 为 True 时仅填充新文件中空项，不覆盖已有翻译

    Returns:
        更新的文件数量
    """
    if isinstance(old_base_dirs, str):
        old_base_dirs = [old_base_dirs]
    keyed_map: Dict[str, str] = {}
    definjected_map: Dict[Tuple[str, str], str] = {}  # (key, scope) -> text
    for old_base_dir in old_base_dirs:
        old_base_dir = old_base_dir.strip()
        if not old_base_dir:
            continue
        k_map, d_map = _collect_old_translations(old_base_dir, language)
        keyed_map.update(k_map)
        # 同 (key, scope) 后者覆盖
        definjected_map.update(d_map)
    # DefInjected 按 scope 分组，写入时每个文件用对应 scope 的 key→text
    definjected_by_scope: Dict[str, Dict[str, str]] = {}
    for (k, scope), text in definjected_map.items():
        definjected_by_scope.setdefault(scope, {})[k] = text
    total_def = sum(len(m) for m in definjected_by_scope.values())
    ui.print_info(
        f"从 %s 个旧目录合并收集到 Keyed %s 条、DefInjected %s 条（按 Def 类型分组）。"
        % (len(old_base_dirs), len(keyed_map), total_def)
    )
    if not keyed_map and not definjected_map:
        logger.warning("未从旧目录收集到任何翻译，请确认旧目录下存在 Keyed/DefInjected 且 XML 中含译文")
        return 0
    new_base = Path(new_base_dir)
    if (new_base / "Keyed").exists() or (new_base / "DefInjected").exists():
        new_lang_dir = str(new_base)
    elif (new_base / language).exists():
        new_lang_dir = str(new_base / language)
    else:
        new_lang_dir = str(
            CONFIG.language_config.get_language_dir(new_base_dir, language)
        )
    if not Path(new_lang_dir).exists():
        logger.warning("新语言目录不存在: %s", new_lang_dir)
        ui.print_warning(f"新语言目录不存在: {new_lang_dir}")
        return 0
    updated = 0
    if keyed_map:
        updated += _update_xml_in_subdir(
            new_base_dir,
            language,
            "keyed",
            keyed_map,
            merge=True,
            only_fill_empty=only_fill_empty,
            language_dir_override=new_lang_dir,
        )
    if definjected_by_scope:
        updated += _update_definjected_by_scope(
            new_base_dir,
            language,
            definjected_by_scope,
            only_fill_empty=only_fill_empty,
            language_dir_override=new_lang_dir,
        )
    return updated


def _update_definjected_by_scope(
    mod_dir: str,
    language: str,
    definjected_by_scope: Dict[str, Dict[str, str]],
    only_fill_empty: bool = False,
    language_dir_override: Optional[str] = None,
) -> int:
    """按 Def 类型(scope)更新 DefInjected：每个 XML 文件只使用对应 scope 的 key→译文。"""
    if not definjected_by_scope:
        return 0
    def_name = CONFIG.language_config.get_value("definjected_dir", "DefInjected")
    if language_dir_override:
        subdir = Path(language_dir_override) / def_name
    else:
        subdir = CONFIG.language_config.get_language_subdir(mod_dir, language, "definjected")
        if not subdir.exists():
            subdir = _get_language_subdir_path(mod_dir, language, "definjected")
    if not subdir.exists():
        logger.warning("DefInjected 目录不存在: %s", subdir)
        return 0
    processor = XMLProcessor()
    updated_count = 0
    xml_files = list(Path(subdir).rglob("*.xml"))
    total_files = len(xml_files)
    if total_files == 0:
        return 0
    ui.print_info(f"正在更新 DefInjected 目录中的 {total_files} 个文件（按 Def 类型匹配）...")
    for i, xml_file in enumerate(xml_files, 1):
        try:
            rel = xml_file.relative_to(subdir)
            scope = rel.parts[0] if rel.parts else (xml_file.stem or "")
            translations = definjected_by_scope.get(scope, {})
            if not translations:
                continue
            normalized: Dict[str, str] = {}
            for key, value in translations.items():
                k = key.replace("\\", "/").replace("/", ".") if "/" in key or "\\" in key else key
                normalized[k] = value
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                continue
            if update_translations(
                processor,
                tree,
                normalized,
                generate_key_func=_definjected_key_func,
                merge=True,
                include_attributes=True,
                only_fill_empty=only_fill_empty,
            ):
                processor.save_xml(tree, str(xml_file))
                updated_count += 1
            ui.print_progress_bar(i, total_files, prefix="更新文件")
        except (FileNotFoundError, PermissionError, OSError, ValueError, TypeError) as e:
            logger.debug("跳过 %s: %s", xml_file, e)
    ui.print_info("")
    return updated_count


def _update_xml_in_subdir(
    mod_dir: str,
    language: str,
    subdir_type: str,
    translations: Dict[str, str],
    merge: bool = True,
    only_fill_empty: bool = False,
    language_dir_override: Optional[str] = None,
) -> int:
    """仅在指定子目录(Keyed/DefInjected)内更新翻译"""
    if not translations:
        return 0
    if language_dir_override:
        subdir = Path(language_dir_override) / subdir_type.lower()
    else:
        subdir = CONFIG.language_config.get_language_subdir(
            mod_dir, language, subdir_type
        )
        if not subdir.exists():
            subdir = _get_language_subdir_path(mod_dir, language, subdir_type)
    # 使用配置的目录名（如 DefInjected）以便正确解析路径
    if language_dir_override and subdir_type.lower() == "definjected":
        def_name = CONFIG.language_config.get_value("definjected_dir", "DefInjected")
        subdir = Path(language_dir_override) / def_name
    elif language_dir_override and subdir_type.lower() == "keyed":
        keyed_name = CONFIG.language_config.get_value("keyed_dir", "Keyed")
        subdir = Path(language_dir_override) / keyed_name
    if not subdir.exists():
        logger.warning("语言子目录不存在: %s", subdir)
        return 0
    processor = XMLProcessor()
    updated_count = 0
    generate_key_func = (
        _definjected_key_func if subdir_type.lower() == "definjected" else None
    )

    # 规格化 DefInjected 键：统一为点号格式（DefName.field 或 DefName.field.0），与三种导出格式一致
    if subdir_type.lower() == "definjected":
        normalized: Dict[str, str] = {}
        for key, value in translations.items():
            k = key.replace("\\", "/").replace("/", ".") if "/" in key or "\\" in key else key
            normalized[k] = value
        translations = normalized

    # 获取所有XML文件列表
    xml_files = list(Path(subdir).rglob("*.xml"))
    total_files = len(xml_files)

    if total_files == 0:
        return 0

    # 显示进度条
    ui.print_info(f"正在更新 {subdir_type} 目录中的 {total_files} 个文件...")

    for i, xml_file in enumerate(xml_files, 1):
        try:
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                continue
            if update_translations(
                processor,
                tree,
                translations,
                generate_key_func=generate_key_func,
                merge=merge,
                include_attributes=True,
                only_fill_empty=only_fill_empty,
            ):
                processor.save_xml(tree, str(xml_file))
                updated_count += 1

            # 显示进度条
            ui.print_progress_bar(i, total_files, prefix="更新文件")

        except FileNotFoundError:
            logger.error("XML文件不存在: %s", xml_file)
        except PermissionError:
            logger.error("无权限访问XML文件: %s", xml_file)
        except (OSError, ValueError, TypeError) as e:
            logger.error("处理XML文件失败: %s: %s", xml_file, e)

    # 完成进度条
    ui.print_info("")  # 换行
    return updated_count


def update_translations(
    processor: XMLProcessor,
    tree: Any,
    translations: Dict[str, str],
    generate_key_func: Optional[Callable] = None,
    merge: bool = True,
    include_attributes: bool = True,
    only_fill_empty: bool = False,
) -> bool:
    """
    更新 XML 中的翻译。当 only_fill_empty=True 时也会处理无文本节点，仅填充空项。
    用于 DefInjected 时，nested / flat_with_li / flat_all 任意格式均可作为目标，按统一 key 写入。

    Args:
        processor (XMLProcessor): XML处理器实例
        tree (Any): XML 树对象
        translations (Dict[str, str]): 翻译字典
        generate_key_func (Optional[Callable]): 生成键的函数（DefInjected 用）
        merge (bool): 是否合并更新
        include_attributes (bool): 是否更新属性
        only_fill_empty (bool): 仅当当前为空时写入（用于旧翻译迁移）

    Returns:
        bool: 是否更新成功
    """
    from utils.utils import sanitize_xml

    modified = False
    root = tree.getroot() if processor.use_lxml else tree
    parent_map = (
        {c: p for p in root.iter() for c in p} if not processor.use_lxml else None
    )

    def get_key(elem):
        return (
            generate_key_func(elem, root, parent_map)
            if generate_key_func
            else processor._get_element_key(elem)
        )

    elements = root.xpath(".//*") if processor.use_lxml else root.iter()

    for elem in elements:
        # 更新文本内容（含无文本节点，便于 only_fill_empty 填充）
        key = get_key(elem)
        if not key:
            continue
        # 精确匹配
        value = translations.get(key)
        # DefInjected 迁移：支持旧 flat_all / flat_with_li / nested 与任意新格式互导
        if value is None and generate_key_func is not None:
            tag = getattr(elem, "tag", None)
            tag_local = _definjected_tag_local(tag) if isinstance(tag, str) else ""
            # 1) 新模板是 <li> 时：旧 flat_all 可能为 .0、.1，用前缀匹配
            if tag_local == "li":
                prefix = key + "."
                candidates = [k for k in translations if k.startswith(prefix)]
                if len(candidates) == 1:
                    value = translations[candidates[0]]
                elif len(candidates) > 1:
                    value = translations.get(prefix + "RMBLabel") or translations.get(candidates[0])
            # 2) 按后缀匹配：旧翻译 key 可能带不同前缀（如不同 Def 文件夹结构），用路径后缀唯一匹配
            if value is None and "." in key:
                suffix = key.split(".", 1)[-1]
                candidates = [k for k in translations if k == suffix or k.endswith("." + suffix)]
                if len(candidates) == 1:
                    value = translations[candidates[0]]
                elif len(candidates) > 1:
                    def_name = key.split(".")[0]
                    for c in candidates:
                        if c.startswith(def_name + "."):
                            value = translations[c]
                            break
                    if value is None:
                        value = translations.get(candidates[0])
        if value is not None:
            current = (elem.text or "").strip()
            # 迁移时：若当前内容像英文占位（如 creation(tag=...)->...），仍用旧翻译覆盖
            if only_fill_empty and current and not _looks_like_en_placeholder(current):
                pass
            elif only_fill_empty:
                elem.text = sanitize_xml(value)
                modified = True
            elif merge and current != value:
                elem.text = sanitize_xml(value)
                modified = True
            elif not merge:
                elem.text = sanitize_xml(value)
                modified = True

        # 更新属性
        if include_attributes:
            for attr_name, attr_value in elem.attrib.items():
                if isinstance(attr_value, str) and attr_value.strip():
                    attr_key = f"{get_key(elem)}.{attr_name}"
                    if attr_key not in translations:
                        continue
                    current_attr = (attr_value or "").strip()
                    if only_fill_empty and current_attr and not _looks_like_en_placeholder(current_attr):
                        pass
                    elif only_fill_empty:
                        elem.set(attr_name, sanitize_xml(translations[attr_key]))
                        modified = True
                    elif merge and current_attr != translations[attr_key]:
                        elem.set(attr_name, sanitize_xml(translations[attr_key]))
                        modified = True
                    elif not merge:
                        elem.set(attr_name, sanitize_xml(translations[attr_key]))
                        modified = True

    return modified


def _verify_import_results(mod_dir: str, language: str) -> bool:
    """验证导入结果"""
    template_dir = CONFIG.language_config.get_language_dir(mod_dir, language)
    if not template_dir.exists():
        logger.error("导入后模板目录不存在")
        return False
    # 检查是否有翻译文件
    has_keyed = (
        any(
            (
                CONFIG.language_config.get_language_subdir(
                    mod_dir, language, "keyed"
                ).rglob("*.xml")
            )
        )
        if CONFIG.language_config.get_language_subdir(
            mod_dir, language, "keyed"
        ).exists()
        else False
    )
    has_definjected = (
        any(
            (
                CONFIG.language_config.get_language_subdir(
                    mod_dir, language, "definjected"
                ).rglob("*.xml")
            )
        )
        if CONFIG.language_config.get_language_subdir(
            mod_dir, language, "definjected"
        ).exists()
        else False
    )
    if not has_keyed and not has_definjected:
        logger.warning("导入后未找到翻译文件")
        return False
    logger.info("导入结果验证通过")
    return True
