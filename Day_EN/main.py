import logging
from Day_EN.extractors import extract_key, extract_definjected_from_defs, extract_translate, cleanup_backstories, preview_translatable_fields
from Day_EN.config import PREVIEW_TRANSLATABLE_FIELDS
import os

def main() -> None:
    print("=== RimWorld 模组翻译工具 ===")
    print("请选择操作模式：")
    print("1. 提取翻译（生成 CSV 和翻译模板）")
    print("2. 导入 CSV 自动批量汉化（写入 XML）")
    mode = input("> ").strip()
    if mode == "2":
        print("请输入模组根目录路径（如 C:/RimWorld/Mods/MyMod）：")
        mod_root_dir = input("> ").strip()
        if not os.path.exists(mod_root_dir):
            print("错误：模组路径不存在！")
            logging.error(f"模组路径不存在：{mod_root_dir}")
            return
        print("请输入翻译 CSV 文件路径（如 extracted_translations.csv）：")
        csv_path = input("> ").strip()
        if not os.path.exists(csv_path):
            print("错误：CSV 文件不存在！")
            logging.error(f"CSV 文件不存在：{csv_path}")
            return
        from Day_EN.importer import import_translations
        try:
            import_translations(csv_path, mod_root_dir)
            print("批量汉化完成！请检查 Languages 目录。")
            logging.info("批量汉化完成")
        except Exception as e:
            print(f"批量汉化错误：{e}")
            logging.error(f"批量汉化错误：{e}")
        return
    # 默认模式：提取翻译
    print("请输入模组根目录路径（例如：C:/RimWorld/Mods/MyMod）：")
    mod_root_dir = input("> ").strip()
    if not os.path.exists(mod_root_dir):
        print("错误：模组路径不存在！")
        logging.error(f"模组路径不存在：{mod_root_dir}")
        return
    print("请输入导出目标文件夹路径（如 D:/output 或留空则为当前目录）：")
    export_dir = input("> ").strip()
    if not export_dir:
        export_dir = os.getcwd()
    if not os.path.exists(export_dir):
        try:
            os.makedirs(export_dir)
            print(f"已创建导出目录：{export_dir}")
        except Exception as e:
            print(f"无法创建导出目录：{e}")
            logging.error(f"无法创建导出目录：{export_dir}，错误：{e}")
            return
    print("开始提取翻译...")
    try:
        extract_translate(mod_root_dir, export_dir)
        extract_key(mod_root_dir, export_dir)
        cleanup_backstories(mod_root_dir, export_dir)
        # 自动导出所有可翻译字段到 extracted_translations.csv（含 DefInjected 和 Keyed）
        csv_path = os.path.join(export_dir, "extracted_translations.csv")
        all_translations = preview_translatable_fields(mod_root_dir, preview=False)
        import csv
        # Keyed 导出
        keyed_dir = os.path.join(export_dir, "Languages", "English", "Keyed")
        keyed_rows = []
        if os.path.exists(keyed_dir):
            from pathlib import Path
            for xml_file in Path(keyed_dir).rglob("*.xml"):
                try:
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    for elem in root:
                        if elem.tag is ET.Comment:
                            continue
                        if elem.text and elem.text.strip():
                            keyed_rows.append((elem.tag, elem.text.strip(), elem.tag))
                except Exception as e:
                    logging.error(f"Keyed导出失败: {xml_file}: {e}")
        with open(csv_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag"])
            # DefInjected
            for full_path, text, tag, _ in all_translations:
                writer.writerow([full_path, text, tag])
            # Keyed
            for key, text, tag in keyed_rows:
                writer.writerow([key, text, tag])
        print(f"已自动导出所有可翻译字段到 {csv_path}")
        logging.info(f"已自动导出所有可翻译字段到 {csv_path}")
        print("翻译提取完成！请检查导出文件夹。")
        logging.info("翻译提取完成")
    except Exception as e:
        print(f"提取错误：{e}")
        logging.error(f"提取错误：{e}")

if __name__ == "__main__":
    main()
