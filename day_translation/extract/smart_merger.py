from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
import logging
import xml.etree.ElementTree as ET
from day_translation.utils.utils import XMLProcessor
from day_translation.extract.xml_utils import save_xml, sanitize_xcomment
from day_translation.utils.config import get_config
import datetime

class SmartMerger:
    """
    智能合并器 - 负责5.1合并逻辑，将新提取的翻译与现有DefInjected文件进行智能合并
    """
    def __init__(self):
        self.processor = XMLProcessor()

    def perform_smart_merge(self, output_dir: str, new_translations: List[Tuple[str, str, str, str]]) -> Dict[str, Any]:
        output_path = Path(output_dir)
        definjected_dir = output_path / "DefInjected"
        if not definjected_dir.exists():
            logging.info("输出目录没有DefInjected，直接生成新文件")
            return self.create_new_files_with_translations(output_dir, new_translations)
        existing_files = self.read_existing_definjected_files(str(definjected_dir))
        structure_type = self.analyze_file_structure(existing_files)
        logging.info("检测到输出目录结构类型: %s", structure_type)
        merge_results = self.merge_with_existing_files(existing_files, new_translations, structure_type)
        self.save_merged_files(merge_results, str(definjected_dir))
        return self.calculate_merge_statistics(merge_results)

    def read_existing_definjected_files(self, definjected_dir: str) -> Dict[str, Dict]:
        existing_files = {}
        for xml_file in Path(definjected_dir).rglob("*.xml"):
            try:
                tree = self.processor.parse_xml(str(xml_file))
                if tree is None:
                    continue
                root = tree.getroot() if hasattr(tree, 'getroot') else tree
                file_data = {
                    'path': str(xml_file),
                    'relative_path': str(xml_file.relative_to(Path(definjected_dir))),
                    'translations': {},
                    'tree': tree,
                    'root': root
                }
                self.extract_translations_with_comments(root, file_data)
                existing_files[str(xml_file)] = file_data
                logging.debug("读取现有文件: %s, 包含 %s 条翻译", xml_file, len(file_data['translations']))
            except Exception as e:
                logging.warning("读取文件失败 %s: %s", xml_file, e)
        logging.info("读取现有DefInjected文件: %s 个文件", len(existing_files))
        return existing_files

    def analyze_file_structure(self, existing_files: Dict[str, Dict]) -> str:
        if not existing_files:
            return 'defs_by_type'
        file_paths = [data['relative_path'] for data in existing_files.values()]
        type_pattern_count = 0
        file_pattern_count = 0
        original_pattern_count = 0
        for path in file_paths:
            parts = Path(path).parts
            if len(parts) >= 2:
                folder_name = parts[0]
                file_name = parts[1]
                if folder_name.endswith('Def') or folder_name.endswith('Defs'):
                    type_pattern_count += 1
                elif '/' in path and not folder_name.endswith('Def'):
                    file_pattern_count += 1
                else:
                    original_pattern_count += 1
        if type_pattern_count > file_pattern_count and type_pattern_count > original_pattern_count:
            return 'defs_by_type'
        elif file_pattern_count > type_pattern_count and file_pattern_count > original_pattern_count:
            return 'defs_by_file_structure'
        else:
            return 'original_structure'

    def merge_with_existing_files(self, existing_files: Dict[str, Dict], new_translations: List[Tuple[str, str, str, str]], structure_type: str) -> Dict[str, Dict]:
        merge_results = {}
        for file_path, file_data in existing_files.items():
            merge_results[file_path] = {
                'path': file_data['path'],
                'relative_path': file_data['relative_path'],
                'translations': dict(file_data['translations']),
                'tree': file_data['tree'],
                'root': file_data['root'],
                'modified': False,
                'stats': {'unchanged': 0, 'updated': 0, 'added': 0}
            }
        for okey, otest, group, file_info in new_translations:
            target_file_path = self.find_target_file_for_translation(
                okey, otest, group, file_info, existing_files, structure_type
            )
            if target_file_path and target_file_path in merge_results:
                file_data = merge_results[target_file_path]
                self.merge_translation_into_file(file_data, okey, otest)
            else:
                new_file_path = self.create_new_file_for_translation(
                    okey, otest, group, file_info, structure_type, merge_results
                )
                if new_file_path:
                    self.merge_translation_into_file(merge_results[new_file_path], okey, otest, is_new_file=True)
        return merge_results

    def find_target_file_for_translation(self, okey: str, otest: str, group: str, file_info: str, existing_files: Dict[str, Dict], structure_type: str) -> Optional[str]:
        for file_path, file_data in existing_files.items():
            if okey in file_data['translations']:
                return file_path
        if structure_type == 'defs_by_type':
            def_type = self.extract_def_type_from_key(okey, group, file_info)
            for file_path, file_data in existing_files.items():
                if def_type.lower() in file_data['relative_path'].lower():
                    return file_path
        elif structure_type == 'defs_by_file_structure':
            if file_info:
                file_stem = Path(file_info).stem if isinstance(file_info, str) else ""
                for file_path, file_data in existing_files.items():
                    if file_stem.lower() in file_data['relative_path'].lower():
                        return file_path
        return None

    def merge_translation_into_file(self, file_data: Dict, okey: str, otest: str, is_new_file: bool = False):
        if okey in file_data['translations']:
            existing = file_data['translations'][okey]
            etest = existing['etest']
            eEN = existing['eEN']
            if otest == eEN:
                file_data['stats']['unchanged'] += 1
                logging.debug("翻译无变化: %s", okey)
            else:
                # 插入历史注释
                history_comment = ET.Comment(sanitize_xcomment(f"HISTORY: 原翻译内容：{etest}，替换于{datetime.date.today()}"))
                en_comment = ET.Comment(sanitize_xcomment(f"EN: {otest}"))
                idx = list(file_data['root']).index(existing['element'])
                file_data['root'].insert(idx, history_comment)
                file_data['root'].insert(idx + 1, en_comment)
                # 替换内容
                existing['etest'] = f"(需翻译){otest}"
                existing['eEN'] = otest
                existing['element'].text = f"(需翻译){otest}"
                file_data['modified'] = True
                file_data['stats']['updated'] += 1
                logging.info("更新翻译: %s -> %s", okey, otest)
        else:
            new_element = ET.SubElement(file_data['root'], okey)
            new_element.text = f"(需翻译){otest}"
            comment = ET.Comment(sanitize_xcomment(f"EN: {otest}"))
            file_data['root'].insert(list(file_data['root']).index(new_element), comment)
            file_data['translations'][okey] = {
                'etest': f"(需翻译){otest}",
                'eEN': otest,
                'element': new_element
            }
            file_data['modified'] = True
            file_data['stats']['added'] += 1
            logging.info("新增翻译: %s -> %s", okey, otest)

    def create_new_file_for_translation(self, okey: str, otest: str, group: str, file_info: str, structure_type: str, merge_results: Dict[str, Dict]) -> Optional[str]:
        if structure_type == 'defs_by_type':
            def_type = self.extract_def_type_from_key(okey, group, file_info)
            relative_path = f"{def_type}/{def_type}.xml"
        elif structure_type == 'defs_by_file_structure':
            if file_info:
                file_stem = Path(file_info).stem if isinstance(file_info, str) else "Unknown"
                relative_path = f"{file_stem}/{file_stem}.xml"
            else:
                relative_path = "Unknown/Unknown.xml"
        else:
            relative_path = "_Additional.xml"
        file_path = f"NEW_FILE:{relative_path}"
        root = ET.Element("LanguageData")
        tree = ET.ElementTree(root)
        merge_results[file_path] = {
            'path': file_path,
            'relative_path': relative_path,
            'translations': {},
            'tree': tree,
            'root': root,
            'modified': True,
            'stats': {'unchanged': 0, 'updated': 0, 'added': 0}
        }
        logging.info("创建新文件: %s", relative_path)
        return file_path

    def extract_def_type_from_key(self, okey: str, group: str, file_info: str) -> str:
        if '/' in okey:
            def_type_part = okey.split('/', 1)[0]
            if '.' in def_type_part:
                return def_type_part.split('.')[-1]
            return def_type_part
        if group and group != 'DefInjected':
            return group
        if file_info:
            file_stem = Path(file_info).stem if isinstance(file_info, str) else ""
            if file_stem.endswith('Defs') or file_stem.endswith('Def'):
                return file_stem
        return 'UnknownDef'

    def save_merged_files(self, merge_results: Dict[str, Dict], definjected_dir: str):
        saved_count = 0
        for file_path, file_data in merge_results.items():
            if not file_data['modified']:
                continue
            try:
                if file_path.startswith('NEW_FILE:'):
                    actual_path = Path(definjected_dir) / file_data['relative_path']
                    actual_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path = str(actual_path)
                else:
                    target_path = file_data['path']
                save_xml(file_data['tree'], target_path, pretty_print=True)
                saved_count += 1
                stats = file_data['stats']
                logging.info("保存文件: %s (更新:%s, 新增:%s, 不变:%s)", file_data['relative_path'], stats['updated'], stats['added'], stats['unchanged'])
            except Exception as e:
                logging.error("保存文件失败 %s: %s", file_data['relative_path'], e)
        print(f"   ✅ 保存了 {saved_count} 个文件")
        logging.info("保存合并文件完成: %s 个文件", saved_count)

    def calculate_merge_statistics(self, merge_results: Dict[str, Dict]) -> Dict[str, Any]:
        total_unchanged = sum(data['stats']['unchanged'] for data in merge_results.values())
        total_updated = sum(data['stats']['updated'] for data in merge_results.values())
        total_added = sum(data['stats']['added'] for data in merge_results.values())
        modified_files = sum(1 for data in merge_results.values() if data['modified'])
        stats = {
            'summary': {
                'total_unchanged': total_unchanged,
                'total_updated': total_updated,
                'total_added': total_added,
                'modified_files': modified_files,
                'total_files': len(merge_results)
            }
        }
        print(f"   📊 合并统计：不变 {total_unchanged} 条，更新 {total_updated} 条，新增 {total_added} 条")
        print(f"   📁 文件统计：修改 {modified_files} 个文件，总计 {len(merge_results)} 个文件")
        return stats

    def create_new_files_with_translations(self, output_dir: str, new_translations: List[Tuple[str, str, str, str]]) -> Dict[str, Any]:
        print(f"   📁 输出目录没有现有文件，直接创建新文件结构...")
        from .template_manager import TemplateManager
        # 使用默认的defs_by_type结构
        tm = TemplateManager(output_dir)
        tm._generate_templates_to_output_dir_with_structure(
            new_translations, output_dir, template_structure='defs_by_type'
        )
        return {
            'summary': {
                'total_unchanged': 0,
                'total_updated': 0,
                'total_added': len(new_translations),
                'modified_files': 0,
                'total_files': 0
            }
        }

    # 未使用
    def extract_translations_with_comments(self, root, file_data: Dict) -> None:
        try:
            if self.processor.use_lxml:
                self.extract_with_lxml(root, file_data)
            else:
                self.extract_with_etree(file_data['path'], root, file_data)
        except Exception as e:
            logging.warning("注释提取失败，使用基础解析: %s", e)
            self.extract_basic_translations(root, file_data)

    # 未使用
    def extract_with_lxml(self, root, file_data: Dict) -> None:
        try:
            import lxml.etree as etree
            current_comment = None
            for item in root:
                if hasattr(item, 'tag') and callable(getattr(item, 'tag', None)):
                    if item.tag is etree.Comment:
                        comment_text = item.text or ""
                        if comment_text.strip().startswith("EN: "):
                            current_comment = comment_text.strip()[4:].strip()
                elif hasattr(item, 'tag') and isinstance(item.tag, str) and not item.tag.startswith('{'):
                    ekey = item.tag
                    etest = item.text or ""
                    eEN = current_comment or ""
                    file_data['translations'][ekey] = {
                        'etest': etest,
                        'eEN': eEN,
                        'element': item
                    }
                    current_comment = None
        except ImportError:
            self.extract_with_etree(file_data['path'], root, file_data)

    # 未使用
    def extract_with_etree(self, file_path: str, root, file_data: Dict) -> None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            import re
            pattern = r'<!--\s*EN:\s*(.*?)\s*-->\s*<([^>]+)>(.*?)</\\2>'
            matches = re.findall(pattern, content, re.DOTALL)
            comment_map = {}
            for en_text, key, translation in matches:
                comment_map[key] = en_text.strip()
            for elem in root:
                if hasattr(elem, 'tag') and isinstance(elem.tag, str) and not elem.tag.startswith('{'):
                    ekey = elem.tag
                    etest = elem.text or ""
                    eEN = comment_map.get(ekey, "")
                    file_data['translations'][ekey] = {
                        'etest': etest,
                        'eEN': eEN,
                        'element': elem
                    }
        except Exception as e:
            logging.warning("文件内容解析失败: %s", e)
            self.extract_basic_translations(root, file_data)

    # 未使用
    def extract_basic_translations(self, root, file_data: Dict) -> None:
        for elem in root:
            if hasattr(elem, 'tag') and isinstance(elem.tag, str) and not elem.tag.startswith('{'):
                ekey = elem.tag
                etest = elem.text or ""
                eEN = ""
                file_data['translations'][ekey] = {
                    'etest': etest,
                    'eEN': eEN,
                    'element': elem
                }

def _perform_smart_merge(output_dir: str, translations: List[Tuple[str, str, str, str]], smart_merger: 'SmartMerger') -> Optional[Dict]:
    """
    执行智能合并操作
    Args:
        output_dir (str): 输出目录
        translations (List[Tuple[str, str, str, str]]): 提取的翻译数据，格式为 (key, text, group, file_info)
        smart_merger (SmartMerger): 智能合并器实例
    Returns:
        Optional[Dict]: 合并结果，如果没有需要合并的文件则返回None
    """
    try:
        output_path = Path(output_dir)
        file_mappings = []
        # 处理DefInjected文件
        definjected_dir = output_path / "DefInjected"
        if definjected_dir.exists():
            for xml_file in definjected_dir.rglob("*.xml"):
                if xml_file.is_file():
                    file_translations = _extract_file_translations(xml_file, translations)
                    if file_translations:
                        file_mappings.append((str(xml_file), file_translations))
        # 处理Keyed文件
        keyed_dir = output_path / "Keyed"
        if keyed_dir.exists():
            for xml_file in keyed_dir.glob("*.xml"):
                if xml_file.is_file():
                    file_translations = _extract_file_translations(xml_file, translations)
                    if file_translations:
                        file_mappings.append((str(xml_file), file_translations))
        if not file_mappings:
            return None
        results = smart_merger.merge_multiple_files(file_mappings)
        smart_merger.print_batch_summary(results)
        return results
    except Exception as e:
        logging.error(f"智能合并失败: {e}")
        return None

def _extract_file_translations(xml_file: Path, translations: List[Tuple[str, str, str, str]]) -> Dict[str, str]:
    """
    从翻译数据中提取对应文件的翻译内容
    Args:
        xml_file (Path): XML文件路径
        translations (List[Tuple[str, str, str, str]]): 翻译数据列表，格式为 (key, text, group, file_info)
    Returns:
        Dict[str, str]: 该文件的翻译内容 {key: text}
    """
    file_translations = {}
    xml_file_name = xml_file.name
    for key, text, group, file_info in translations:
        if file_info and (file_info.endswith(xml_file_name) or xml_file_name in file_info):
            file_translations[key] = text
    return file_translations