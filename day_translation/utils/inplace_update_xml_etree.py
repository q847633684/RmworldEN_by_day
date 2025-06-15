import os
import logging
from pathlib import Path
from typing import Dict
import xml.etree.ElementTree as ET
from ..utils.config import TranslationConfig

CONFIG = TranslationConfig()

def inplace_update_all_xml(csv_path: str, mod_dir: str) -> None:
    """
    使用 ElementTree 更新所有 XML 文件中的翻译。

    Args:
        csv_path: 翻译 CSV 文件路径
        mod_dir: 模组根目录
    """
    logging.info(f"使用 ElementTree 更新 XML: csv_path={csv_path}, mod_dir={mod_dir}")
    translations: Dict[str, str] = {}
    try:
        import csv
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row["key"]
                # 处理复合键名
                if "/" in key and "." in key:
                    # 对于 DefType/DefName.field 格式，提取最后的字段名
                    key = key.split(".")[-1]
                translations[key] = row.get("translated", row["text"])
    except csv.Error as e:
        logging.error(f"CSV 解析失败: {csv_path}, 错误: {e}")
        return
    except OSError as e:
        logging.error(f"无法读取 CSV: {csv_path}, 错误: {e}")
        return

    def_injected_path = os.path.join(mod_dir, "Languages", CONFIG.default_language, CONFIG.def_injected_dir)
    if not os.path.exists(def_injected_path):
        def_injured_path = os.path.join(mod_dir, "Languages", CONFIG.default_language, "DefInjured")
        if os.path.exists(def_injured_path):
            def_injected_path = def_injured_path
        else:
            logging.error(f"未找到 DefInjected 或 DefInjured 目录: {def_injected_path}")
            return

    keyed_path = os.path.join(mod_dir, "Languages", CONFIG.default_language, CONFIG.keyed_dir)
    
    try:
        for xml_file in list(Path(def_injected_path).rglob("*.xml")) + list(Path(keyed_path).rglob("*.xml")):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                modified = False
                
                # 构建父节点映射
                parent_map = {child: parent for parent in root.iter() for child in parent}
                
                for elem in root.findall(".//*"):
                    if elem.text and elem.text.strip():
                        # 简化的键匹配：直接使用元素标签名
                        simple_key = elem.tag
                        
                        # 也尝试匹配完整路径
                        path_parts = []
                        current = elem
                        while current is not None and current != root:
                            if current.tag != "LanguageData":
                                path_parts.append(current.tag)
                            parent = parent_map.get(current)
                            current = parent
                        
                        path_parts.reverse()
                        full_key = ".".join(path_parts) if path_parts else simple_key
                        
                        # 尝试匹配键
                        for key_to_try in [simple_key, full_key, elem.tag]:
                            if key_to_try in translations:
                                elem.text = translations[key_to_try]
                                modified = True
                                break
                
                if modified:
                    tree.write(xml_file, encoding="utf-8", xml_declaration=True)
                    logging.info(f"更新文件: {xml_file}")
                    
            except ET.ParseError as e:
                logging.error(f"XML 解析失败: {xml_file}: {e}")
            except OSError as e:
                logging.error(f"无法处理 {xml_file}: {e}")
    except Exception as e:
        logging.error(f"更新 XML 失败: {e}")