import logging
import os
import sys
import csv
import time
from typing import List, Tuple, Optional
from pathlib import Path
from . import extractors, importers, parallel_corpus, machine_translate
from ..utils.config import TranslationConfig
from .exporters import export_keyed_to_csv, cleanup_backstories_dir
from ..utils.utils import update_history_list, get_history_list

CONFIG = TranslationConfig()

def setup_logging() -> None:
    """初始化日志配置，避免重复添加 handler"""
    root_logger = logging.getLogger()
    # 检查是否已经配置过
    if root_logger.handlers:
        return
    
    logging.basicConfig(
        filename=CONFIG.log_file,
        level=logging.DEBUG if CONFIG.debug_mode else logging.INFO,
        format=CONFIG.log_format,
        encoding="utf-8",
        errors="replace"
    )
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(CONFIG.log_format))
    root_logger.addHandler(console)

class TranslationFacade:
    """翻译操作的门面类，封装高层次逻辑"""
    def __init__(self, mod_dir: str, export_dir: str, language: str = CONFIG.default_language):
        self.mod_dir = str(Path(mod_dir).resolve())
        self.export_dir = str(Path(export_dir).resolve())
        self.language = language
        self.source_language = CONFIG.source_language
        self.csv_path = str(Path(self.export_dir) / CONFIG.output_csv)

    def extract_all(self) -> List[Tuple[str, str, str, str]]:
        """提取所有翻译数据，避免重复扫描"""
        logging.info(f"提取翻译: mod_dir={self.mod_dir}, export_dir={self.export_dir}")
        
        # 先提取 DefInjected/Defs 相关内容
        extractors.extract_translate(
            mod_dir=self.mod_dir,
            export_dir=self.export_dir,
            language=self.language,
            source_language=self.source_language
        )
        
        # 再提取 Keyed 内容
        extractors.extract_key(
            mod_dir=self.mod_dir,
            export_dir=self.export_dir,
            language=self.language,
            source_language=self.source_language
        )
        
        # 清理背景故事目录
        cleanup_backstories_dir(
            mod_dir=self.mod_dir,
            export_dir=self.export_dir,
            language=self.language
        )
        
        # 获取所有可翻译字段（包括 DefInjected）
        translations = extractors.preview_translatable_fields(
            mod_dir=self.mod_dir,
            preview=CONFIG.preview_translatable_fields
        )
        
        # 导出 Keyed 到 CSV（重写模式）
        keyed_dir = str(Path(self.export_dir) / "Languages" / self.language / CONFIG.keyed_dir)
        export_keyed_to_csv(keyed_dir, self.csv_path)
        
        # 导出 DefInjected 到 CSV（追加模式）
        definjected_dir = str(Path(self.export_dir) / "Languages" / self.language / CONFIG.def_injected_dir)
        # 检查 DefInjured 兼容性
        if not os.path.exists(definjected_dir):
            definjured_dir = str(Path(self.export_dir) / "Languages" / self.language / "DefInjured")
            if os.path.exists(definjured_dir):
                definjected_dir = definjured_dir
        
        if os.path.exists(definjected_dir):
            from .exporters import export_definjected_to_csv
            export_definjected_to_csv(definjected_dir, self.csv_path)
        
        # 如果提取的翻译数据和 CSV 中的不一致，以实际文件为准
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                csv_rows = list(reader)
            print(f"📈 实际 CSV 记录: {len(csv_rows)} 条")
        except:
            csv_rows = []
        
        return translations

    def import_translations(self, csv_file: str, merge: bool) -> None:
        """导入翻译"""
        logging.info(f"导入翻译: csv_file={csv_file}, merge={merge}")
        importers.import_translations(
            csv_path=csv_file,
            mod_dir=self.mod_dir,
            language=self.language,
            merge=merge
        )

    def generate_corpus(self, mode: str) -> int:
        """生成平行语料集"""
        return parallel_corpus.generate_parallel_corpus(mode, self.mod_dir)

def get_user_input_with_history(prompt: str, history_key: str, validate_path: bool = False) -> str:
    """获取用户输入，支持历史记录选择"""
    history = get_history_list(history_key)
    
    if history:
        print(f"\n最近使用的{prompt.split('：')[0]}：")
        for idx, path in enumerate(history[:5], 1):
            print(f"  {idx}. {path}")
        print(f"\n{prompt}（输入数字选择历史记录，或直接输入新路径）")
    else:
        print(f"\n{prompt}")
    
    user_input = input("> ").strip()
    
    # 处理数字选择
    if user_input.isdigit() and history:
        try:
            idx = int(user_input) - 1
            if 0 <= idx < len(history):
                selected_path = history[idx]
                print(f"已选择: {selected_path}")
                if validate_path and not os.path.exists(selected_path):
                    print(f"警告：路径不存在 {selected_path}")
                    return ""
                return selected_path
        except (ValueError, IndexError):
            pass
    
    if validate_path and user_input and not os.path.exists(user_input):
        print(f"错误：路径不存在 {user_input}")
        return ""
    
    return user_input

def run_mode_1(facade: TranslationFacade) -> None:
    """运行模式 1：提取翻译到 CSV"""
    try:
        start_time = time.time()
        print("开始提取翻译...")
        
        output_dir = Path(facade.export_dir)
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
            print(f"创建导出目录: {output_dir}")
        
        if not os.access(facade.export_dir, os.W_OK):
            raise PermissionError(f"导出目录 {facade.export_dir} 无写入权限")
        
        # 检查模组结构
        mod_path = Path(facade.mod_dir)
        print(f"正在检查模组结构: {mod_path.name}")
        
        # 检查各种可能的目录结构
        defs_path = mod_path / "Defs"
        en_languages_path = mod_path / "Languages" / "English"
        zh_languages_path = mod_path / "Languages" / "ChineseSimplified"
        
        print(f"📁 Defs 目录: {'✅ 存在' if defs_path.exists() else '❌ 不存在'}")
        print(f"📁 英文语言目录: {'✅ 存在' if en_languages_path.exists() else '❌ 不存在'}")
        print(f"📁 中文语言目录: {'✅ 存在' if zh_languages_path.exists() else '❌ 不存在'}")
        
        if en_languages_path.exists():
            en_keyed = en_languages_path / "Keyed"
            en_definjected = en_languages_path / "DefInjected"
            print(f"  └─ 英文 Keyed: {'✅' if en_keyed.exists() else '❌'}")
            print(f"  └─ 英文 DefInjected: {'✅' if en_definjected.exists() else '❌'}")
        
        if zh_languages_path.exists():
            zh_keyed = zh_languages_path / "Keyed"
            zh_definjected = zh_languages_path / "DefInjected"
            print(f"  └─ 中文 Keyed: {'✅' if zh_keyed.exists() else '❌'}")
            print(f"  └─ 中文 DefInjected: {'✅' if zh_definjected.exists() else '❌'}")
        
        # 如果没有英文源文件，给出建议
        if not defs_path.exists() and not en_languages_path.exists():
            print("\n⚠️ 警告：此模组缺少英文源文件")
            print("💡 建议：")
            print("  1. 检查模组路径是否正确")
            print("  2. 此模组可能已经是汉化版本，无需再次翻译")
            print("  3. 如需要，可以从中文版本反向提取")
            
            # 询问是否继续
            continue_choice = input("\n是否继续处理？(y/n，回车默认 n): ").strip().lower()
            if continue_choice != 'y':
                print("已取消操作")
                return
        
        translations = facade.extract_all()
        rows = [(full_path, text, tag) for full_path, text, tag, _ in translations]
        
        print(f"正在写入 CSV 文件，共 {len(rows)} 条记录...")
        with open(facade.csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag"])
            writer.writerows(rows)
        
        elapsed = time.time() - start_time
        logging.info(f"共导出 {len(rows)} 条到 {facade.csv_path}，耗时 {elapsed:.2f} 秒")
        update_history_list("extracted_csv_history", facade.csv_path)
        
        # 更详细的结果统计
        if len(rows) > 0:
            print(f"✅ 提取完成！导出到 {facade.csv_path}")
            print(f"📊 统计：{len(rows)} 条记录，耗时 {elapsed:.2f} 秒")
            
            # 统计各类型记录数量
            keyed_count = sum(1 for row in rows if not '.' in row[0] or row[0].count('.') <= 1)
            definjected_count = len(rows) - keyed_count
            
            print(f"  📋 Keyed 记录: {keyed_count} 条")
            print(f"  🔧 DefInjected 记录: {definjected_count} 条")
            
            # 显示前几条记录作为预览
            print("\n📝 前几条记录预览：")
            with open(facade.csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:6]  # 读取前5行（包括标题行）
                for i, line in enumerate(lines):
                    if i == 0:
                        print(f"  标题: {line.strip()}")
                    else:
                        print(f"  {i}: {line.strip()[:80]}{'...' if len(line.strip()) > 80 else ''}")
            
            # 检查是否有 XML 解析错误
            if "XML 解析失败" in str(sys.stdout):
                print("\n⚠️ 注意：部分 XML 文件解析失败，可能需要手动修复")
                print("💡 常见问题：")
                print("  1. XML 中包含未转义的特殊字符（如 & < >）")
                print("  2. XML 标签不匹配或格式错误")
                print("  3. 文件编码问题")
        else:
            print(f"⚠️ 未提取到任何翻译内容")
            print("💡 可能原因：")
            print("  1. 模组没有可翻译的文本")
            print("  2. 模组结构不标准")
            print("  3. 文件路径有误")
            print("  4. 所有 XML 文件都有解析错误")

    except (PermissionError, csv.Error, OSError) as e:
        logging.error(f"模式 1 错误: {e}")
        print(f"❌ 错误: {e}，请检查 {CONFIG.log_file}")

def run_mode_2(facade: TranslationFacade) -> None:
    """运行模式 2：机器翻译 CSV"""
    try:
        if not os.path.exists(facade.csv_path):
            print(f"CSV 文件不存在: {facade.csv_path}，请先运行模式 1")
            return
        
        # 支持历史记录的 API 密钥输入
        saved_keys = get_history_list("api_keys")
        if saved_keys:
            print("是否使用上次保存的 API 密钥？(y/n，回车默认 y)：", end="")
            use_saved = input().strip().lower()
            if use_saved != "n" and saved_keys:
                access_key_id, access_secret = saved_keys[0].split("|", 1)
                print("使用已保存的 API 密钥")
            else:
                access_key_id = input("请输入阿里云 AccessKey ID：").strip()
                access_secret = input("请输入阿里云 AccessKey Secret：").strip()
                if access_key_id and access_secret:
                    api_key_pair = f"{access_key_id}|{access_secret}"
                    update_history_list("api_keys", api_key_pair)
        else:
            access_key_id = input("请输入阿里云 AccessKey ID：").strip()
            access_secret = input("请输入阿里云 AccessKey Secret：").strip()
            if access_key_id and access_secret:
                api_key_pair = f"{access_key_id}|{access_secret}"
                update_history_list("api_keys", api_key_pair)
        
        if not access_key_id or not access_secret:
            print("AccessKey 不能为空")
            return
        
        # 支持速率控制配置
        print("请输入翻译间隔（秒，回车默认 0.5）：", end="")
        sleep_input = input().strip()
        try:
            sleep_sec = float(sleep_input) if sleep_input else 0.5
        except ValueError:
            sleep_sec = 0.5
        
        output_path = str(Path(facade.export_dir) / "translated_zh.csv")
        machine_translate.translate_csv(
            input_path=facade.csv_path,
            output_path=output_path,
            access_key_id=access_key_id,
            access_secret=access_secret,
            sleep_sec=sleep_sec
        )
        update_history_list("translated_csv_history", output_path)
        print(f"机器翻译完成！保存到: {output_path}")
    except Exception as e:
        logging.error(f"模式 2 错误: {e}")
        print(f"错误: {e}，请检查 {CONFIG.log_file}")

def run_mode_3(facade: TranslationFacade) -> None:
    """运行模式 3：导入翻译"""
    try:
        csv_file = get_user_input_with_history(
            "请输入翻译后的 CSV 文件路径：", 
            "translated_csv_history", 
            validate_path=True
        )
        if not csv_file:
            return
        
        # 显示导入模式选择
        print("请选择导入模式：")
        print("1. 覆盖模式（清空现有内容，重新导入）")
        print("2. 合并模式（保留现有内容，CSV 优先）")
        print("3. 就地替换模式（仅替换已有键值，保持格式）")
        
        mode_choice = input("请选择模式（1/2/3，回车默认1）：").strip()
        
        if mode_choice == "3":
            # 就地替换模式
            print("使用就地替换模式，是否保留注释和格式？(y/n，回车默认 y)：", end="")
            keep_format = input().strip().lower() != "n"
            
            from ..utils.inplace_update_xml_lxml import inplace_update_all_xml as lxml_update
            from ..utils.inplace_update_xml_etree import inplace_update_all_xml as etree_update
            
            try:
                if keep_format:
                    lxml_update(csv_file, facade.mod_dir)
                    print("就地替换完成（lxml，保留格式）")
                else:
                    etree_update(csv_file, facade.mod_dir)
                    print("就地替换完成（ElementTree）")
            except ImportError:
                print("lxml 未安装，使用 ElementTree 方式")
                etree_update(csv_file, facade.mod_dir)
                print("就地替换完成（ElementTree）")
        else:
            # 覆盖或合并模式
            merge = mode_choice == "2"
            facade.import_translations(csv_file, merge)
            mode_name = "合并" if merge else "覆盖"
            print(f"导入完成（{mode_name}模式）！")
        
        update_history_list("translated_csv_history", csv_file)
        
    except Exception as e:
        logging.error(f"模式 3 错误: {e}")
        print(f"错误: {e}，请检查 {CONFIG.log_file}")

def check_dependencies() -> bool:
    """检查依赖项"""
    missing_deps = []
    try:
        import lxml
        print("✅ lxml 可用 - 支持保留格式的 XML 处理")
    except ImportError:
        print("⚠️ lxml 未安装 - 将使用标准库 XML 处理")
    
    try:
        import aiofiles
        print("✅ aiofiles 可用 - 支持异步文件处理")
    except ImportError:
        print("⚠️ aiofiles 未安装 - 将使用同步文件处理")
    
    try:
        from aliyunsdkcore.client import AcsClient
        print("✅ 阿里云 SDK 可用 - 支持机器翻译")
    except ImportError:
        print("⚠️ 阿里云 SDK 未安装 - 机器翻译功能不可用")
        missing_deps.append("aliyun-python-sdk-core aliyun-python-sdk-alimt")
    
    if missing_deps:
        print(f"\n💡 建议安装: pip install {' '.join(missing_deps)}")
    
    return True

def run_batch_mode() -> None:
    """批量处理模式"""
    print("\n=== 批量处理模式 ===")
    print("支持批量处理多个模组目录")
    
    mod_dirs = []
    while True:
        mod_dir = input(f"请输入第 {len(mod_dirs) + 1} 个模组目录（回车结束）：").strip()
        if not mod_dir:
            break
        if not os.path.exists(mod_dir):
            print(f"目录不存在: {mod_dir}")
            continue
        mod_dirs.append(mod_dir)
        print(f"已添加: {mod_dir}")
    
    if not mod_dirs:
        print("未添加任何目录")
        return
    
    export_base = input("请输入批量导出的基础目录：").strip()
    if not export_base:
        export_base = "batch_output"
    
    print(f"\n开始批量处理 {len(mod_dirs)} 个模组...")
    for i, mod_dir in enumerate(mod_dirs, 1):
        try:
            mod_name = Path(mod_dir).name
            export_dir = str(Path(export_base) / mod_name)
            print(f"\n[{i}/{len(mod_dirs)}] 处理: {mod_name}")
            
            facade = TranslationFacade(mod_dir, export_dir)
            run_mode_1(facade)
            
        except Exception as e:
            print(f"❌ 处理失败: {mod_name} - {e}")
            logging.error(f"批量处理失败: {mod_dir} - {e}")
    
    print(f"\n✅ 批量处理完成！结果保存在: {export_base}")

def main() -> None:
    """主程序入口"""
    setup_logging()
    logging.info("程序启动")
    
    print("=== RimWorld 模组翻译工具 ===")
    print("正在检查运行环境...")
    
    if not check_dependencies():
        input("按回车键退出...")
        return
    
    while True:
        print("\n=== RimWorld 模组翻译工具 ===")
        print("1. 从 Defs 和 Keyed 提取翻译到 CSV")
        print("2. 机器翻译 CSV（需阿里云 API）")
        print("3. 从翻译后的 CSV 导入到 DefInjected 和 Keyed")
        print("4. 生成中英平行语料集")
        print("5. 检查平行语料集格式")
        print("6. 批量处理模式")
        print("0. 退出")
        
        try:
            choice = input("请选择操作（0-6）：").strip()
            
            if choice == "0":
                logging.info("程序退出")
                print("感谢使用，再见！")
                break
                
            if choice not in {"1", "2", "3", "4", "5", "6"}:
                print("无效选项，请重试")
                continue
            
            if choice == "6":
                run_batch_mode()
                continue
            
            # 获取模组目录（支持历史记录）
            mod_dir = get_user_input_with_history(
                "请输入模组根目录路径：", 
                "mod_dir_history", 
                validate_path=True
            )
            if not mod_dir:
                continue
            
            # 获取导出目录（除了模式4和5）
            export_dir = None
            if choice in {"1", "2", "3"}:
                export_dir = get_user_input_with_history(
                    "请输入导出目录路径（建议绝对路径）：", 
                    "export_dir_history", 
                    validate_path=False
                )
                if not export_dir:
                    export_dir = str(Path(mod_dir).parent / "translation_output")
                    print(f"使用默认导出目录: {export_dir}")
            
            # 更新历史记录
            update_history_list("mod_dir_history", mod_dir)
            if export_dir:
                update_history_list("export_dir_history", export_dir)
            
            facade = TranslationFacade(mod_dir, export_dir or mod_dir)
            
            if choice == "1":
                run_mode_1(facade)
            elif choice == "2":
                run_mode_2(facade)
            elif choice == "3":
                run_mode_3(facade)
            elif choice == "4":
                mode = input("请选择语料集生成模式（1=从 XML 提取注释，2=从 DefInjected 和 Keyed 提取，1/2）：").strip()
                if mode not in {"1", "2"}:
                    print("无效模式")
                    continue
                count = facade.generate_corpus(mode)
                print(f"生成语料集完成，共 {count} 条")
            elif choice == "5":
                errors = parallel_corpus.check_parallel_tsv()
                print(f"检查完成，发现 {errors} 个问题")
                
        except KeyboardInterrupt:
            print("\n\n操作被用户中断")
            logging.info("用户中断操作")
        except Exception as e:
            logging.error(f"未处理错误: {e}")
            print(f"发生错误: {e}，请检查日志文件 {CONFIG.log_file}")
        
        input("\n按回车键返回主菜单...")

if __name__ == "__main__":
    main()