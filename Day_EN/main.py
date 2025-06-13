import logging
from Day_EN.extractors import extract_key, extract_definjected_from_defs, extract_translate, cleanup_backstories, preview_translatable_fields
from Day_EN.config import PREVIEW_TRANSLATABLE_FIELDS
import os
import json

def main() -> None:
    # 历史路径和AccessKey记忆文件
    history_path = os.path.join(os.path.expanduser("~"), ".day_en_history.json")
    def load_history():
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    def save_history(data):
        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    history = load_history()
    # 路径历史管理：严格只保留四类
    # 1. mod_root_dir_history：模组根目录路径（提取/导出/导入用）
    # 2. export_dir_history：导出目标文件夹路径（提取/翻译模板路径用）
    # 3. extracted_csv_history：生成翻译模板的CSV路径（提取/机器翻译/导入用）
    # 4. translated_csv_history：生成带翻译列的CSV路径（机器翻译/导入用）
    def update_history_list(key, value, max_items=3):
        arr = history.get(key, [])
        if not isinstance(arr, list):
            arr = []
        if value in arr:
            arr.remove(value)
        arr.insert(0, value)
        arr = arr[:max_items]
        history[key] = arr
        save_history(history)
    def get_history_list(key):
        arr = history.get(key, [])
        if not isinstance(arr, list):
            arr = []
        return arr

    while True:
        print("=== RimWorld 模组翻译工具 ===")
        print("请选择操作模式：")
        print("1. 从模组提取英文，生成 extracted_translations.csv 和翻译模板")
        print("2. 机器翻译/人工翻译 extracted_translations.csv，生成带翻译列的 CSV")
        print("3. 导入已翻译的 CSV，批量写入 Languages/ChineseSimplified/DefInjected、Keyed")
        print("4. 生成中英平行语料集 (parallel_corpus.tsv)")
        print("5. 检查中英平行语料集 (parallel_corpus.tsv)")
        print("0. 退出")
        mode = input("> ").strip()
        # 只在模式1、4、5需要模组根目录，2/3严格不询问模组根目录
        if mode in ["1", "4", "5"]:
            mod_history = get_history_list("mod_root_dir_history")
            print("最近使用的模组根目录：")
            for idx, p in enumerate(mod_history):
                print(f"  {idx+1}. {p}")
            print(f"请输入模组根目录路径（例如：C:/RimWorld/Mods/MyMod，留空则为第一个历史，输入序号可快速选择，若无历史则为当前目录）：")
            mod_root_dir = input("> ").strip()
            if mod_root_dir.isdigit() and 1 <= int(mod_root_dir) <= len(mod_history):
                mod_root_dir = mod_history[int(mod_root_dir)-1]
            elif not mod_root_dir:
                mod_root_dir = mod_history[0] if mod_history else os.getcwd()
            mod_root_dir = os.path.abspath(mod_root_dir)
        else:
            mod_root_dir = None
        if mode == "1":
            # 自动检测Mods结构
            def auto_detect_export_dir(mod_root_dir):
                langs = ["ChineseSimplified", "Chinese", "English"]
                for lang in langs:
                    lang_dir = os.path.join(mod_root_dir, "Languages", lang)
                    if os.path.isdir(lang_dir):
                        return os.path.join(mod_root_dir, "output")
                return os.path.join(mod_root_dir, "output")
            if not os.path.exists(mod_root_dir):
                print("错误：模组路径不存在！")
                logging.error(f"模组路径不存在：{mod_root_dir}")
                input("按回车返回主菜单...")
                continue
            update_history_list("mod_root_dir_history", mod_root_dir)
            export_history = get_history_list("export_dir_history")
            print("最近使用的导出目标文件夹（即翻译模板的导出目录）：")
            for idx, p in enumerate(export_history):
                print(f"  {idx+1}. {p}")
            auto_export = auto_detect_export_dir(mod_root_dir)
            print(f"请输入导出目标文件夹路径（即翻译模板将要导出的文件夹，如 D:/output，留空则为第一个历史，输入序号可快速选择，若无历史则自动检测:{auto_export}）：")
            export_dir = input("> ").strip()
            if export_dir.isdigit() and 1 <= int(export_dir) <= len(export_history):
                export_dir = export_history[int(export_dir)-1]
            elif not export_dir:
                export_dir = export_history[0] if export_history else auto_export
            export_dir = os.path.abspath(export_dir)
            if not os.path.exists(export_dir):
                try:
                    os.makedirs(export_dir)
                    print(f"已创建导出目录：{export_dir}")
                except Exception as e:
                    print(f"无法创建导出目录：{e}")
                    logging.error(f"无法创建导出目录：{export_dir}，错误：{e}")
                    input("按回车返回主菜单...")
                    continue
            update_history_list("export_dir_history", export_dir)  # 记录导出目标文件夹（翻译模板的路径）
            save_history(history)
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
                # 添加提取csv历史（翻译模板的路径）
                update_history_list("extracted_csv_history", csv_path)  # 写入生成翻译模板的CSV路径
                print("翻译提取完成！请在导出目标文件夹中查找 extracted_translations.csv。")
                logging.info("翻译提取完成")
            except Exception as e:
                print(f"提取错误：{e}")
                logging.error(f"提取错误：{e}")
            input("按回车返回主菜单...")
        if mode == "0":
            print("已退出。")
            break
        elif mode == "2":
            # 机器翻译CSV（阿里云API，自动英译中）
            from Day_EN.machine_translate import translate_csv
            # 提取csv历史（翻译模板的路径）
            extracted_csv_history = get_history_list("extracted_csv_history")  # 读取生成翻译模板的CSV路径
            print("提取翻译模板的CSV文件：")
            for idx, p in enumerate(extracted_csv_history):
                print(f"  {idx+1}. {p}")
            print("请输入要进行机器/人工翻译的 extracted_translations.csv 路径（留空则为第一个历史，输入序号可快速选择）：")
            input_path = input("> ").strip()
            if input_path.isdigit() and 1 <= int(input_path) <= len(extracted_csv_history):
                input_path = extracted_csv_history[int(input_path)-1]
            elif not input_path:
                input_path = extracted_csv_history[0] if extracted_csv_history else "extracted_translations.csv"

            print("请输入翻译后生成的带翻译列 CSV 路径（留空则为第一个历史，输入序号可快速选择，若无历史则默认为 translated_zh.csv）：")
            translated_history = get_history_list("translated_csv_history")  # 读取生成带翻译列的CSV路径
            output_path = input("> ").strip()
            if output_path.isdigit() and 1 <= int(output_path) <= len(translated_history):
                output_path = translated_history[int(output_path)-1]
            elif not output_path:
                if translated_history:
                    output_path = translated_history[0]
                else:
                    # 若没有带翻译列CSV历史，则用生成翻译模板的CSV路径（extracted_csv_history）同目录下的 translated_zh.csv
                    extracted_csv_history = get_history_list("extracted_csv_history")
                    if extracted_csv_history:
                        output_path = os.path.join(os.path.dirname(extracted_csv_history[0]), "translated_zh.csv")
                    else:
                        output_path = "translated_zh.csv"
            # AccessKey历史
            ak_id = history.get("access_key_id", "")
            ak_secret = history.get("access_secret", "")
            print(f"请输入阿里云AccessKey ID（留空则用上次:{ak_id}）：")
            access_key_id = input("> ").strip() or ak_id
            print(f"请输入阿里云AccessKey Secret（留空则用上次:{ak_secret[:4]}***）：")
            access_secret = input("> ").strip() or ak_secret
            print("请输入Region ID（默认cn-hangzhou，直接回车可用默认）：")
            region_id = input("> ").strip() or 'cn-hangzhou'
            # 记忆AccessKey
            if access_key_id:
                history["access_key_id"] = access_key_id
            if access_secret:
                history["access_secret"] = access_secret
            save_history(history)
            try:
                translate_csv(input_path, output_path, access_key_id, access_secret, region_id)
                print(f"翻译完成，结果已保存到 {output_path}")
                # 添加翻译好的csv历史
                update_history_list("translated_csv_history", output_path)  # 记录生成带翻译列的CSV路径
            except Exception as e:
                print(f"机器翻译出错：{e}")
            input("按回车返回主菜单...")
            continue
        elif mode == "3":
            # 路径历史管理：导入流程只涉及导出目标文件夹（即翻译模板的路径）
            export_dir_history = get_history_list("export_dir_history")
            print("最近使用的导出目标文件夹（即翻译模板的路径）：")
            for idx, p in enumerate(export_dir_history):
                print(f"  {idx+1}. {p}")
            print("请输入导出目标文件夹路径（即翻译模板的路径，留空则为第一个历史，输入序号可快速选择，若无历史则为当前目录）：")
            export_dir = input("> ").strip()
            if export_dir.isdigit() and 1 <= int(export_dir) <= len(export_dir_history):
                export_dir = export_dir_history[int(export_dir)-1]
            elif not export_dir:
                export_dir = export_dir_history[0] if export_dir_history else os.getcwd()
            export_dir = os.path.abspath(export_dir)
            if not os.path.exists(export_dir):
                print("错误：导出目标文件夹不存在！")
                logging.error(f"导出目标文件夹不存在：{export_dir}")
                input("按回车返回主菜单...")
                continue
            update_history_list("export_dir_history", export_dir)
            mod_root_dir = export_dir  # # 兼容导入逻辑，导入流程中“模组根目录”即为“导出目标文件夹”
            translated_csv_history = get_history_list("translated_csv_history")
            print("最近使用的带翻译列的CSV文件：")
            for idx, p in enumerate(translated_csv_history):
                print(f"  {idx+1}. {p}")
            print("请输入带翻译列的CSV文件路径（留空则为第一个历史，输入序号可快速选择，若无历史则默认为 translated_zh.csv）：")
            csv_path = input("> ").strip()
            if csv_path.isdigit() and 1 <= int(csv_path) <= len(translated_csv_history):
                csv_path = translated_csv_history[int(csv_path)-1]
            elif not csv_path:
                if translated_csv_history:
                    csv_path = translated_csv_history[0]
                else:
                    # 若没有带翻译列CSV历史，则用生成翻译模板的CSV路径（extracted_csv_history）同目录下的 translated_zh.csv
                    extracted_csv_history = get_history_list("extracted_csv_history")
                    if extracted_csv_history:
                        csv_path = os.path.join(os.path.dirname(extracted_csv_history[0]), "translated_zh.csv")
                    else:
                        csv_path = "translated_zh.csv"
            if not os.path.isabs(csv_path):
                csv_path = os.path.join(mod_root_dir, csv_path)
            if not os.path.exists(csv_path):
                print(f"错误：CSV 文件不存在：{csv_path}")
                logging.error(f"CSV 文件不存在：{csv_path}")
                input("按回车返回主菜单...")
                continue
            update_history_list("translated_csv_history", csv_path)
            from Day_EN.importer import import_translations
            try:
                import_translations(csv_path, mod_root_dir)
                print("批量汉化完成！请检查 Languages 目录。")
                logging.info("批量汉化完成")
            except Exception as e:
                print(f"批量汉化错误：{e}")
                logging.error(f"批量汉化错误：{e}")
            input("按回车返回主菜单...")
            continue

        elif mode == "4":
            # 生成中英平行语料集（模块化调用）
            from Day_EN.parallel_corpus import generate_parallel_corpus
            print("请选择提取方式：")
            print("1. 提取带 EN: 注释的中文翻译文件")
            print("2. 提取 Keyed/DefInjected 目录下的中英文对")
            mode2 = input("输入 1 或 2 并回车：").strip()
            if mode2 == '1':
                dir_tip = "请输入要递归查找的目录（可留空，留空则从当前目录开始）："
            elif mode2 == '2':
                dir_tip = "请输入mod根目录（可留空，留空则从当前目录开始）："
            else:
                print("无效选择，已退出。")
                input("按回车返回主菜单...")
                continue
            user_dir = input(dir_tip).strip() or '.'
            count = generate_parallel_corpus(mode2, user_dir, output_csv="extracted_translations.csv", output_tsv="extracted_translations.tsv")
            print(f'已生成 extracted_translations.csv 和 extracted_translations.tsv，共{count}条中英对。')
            input("按回车返回主菜单...")
            continue

        elif mode == "5":
            # 检查中英平行语料集（模块化调用）
            from Day_EN.parallel_corpus import check_parallel_tsv
            check_parallel_tsv('extracted_translations.tsv')
            input("按回车返回主菜单...")
            continue


        

if __name__ == "__main__":
    main()