import logging
import os
import sys
import csv
import time
from typing import List, Tuple, Optional, Dict, Set
from pathlib import Path
import xml.etree.ElementTree as ET


# 导入模块化组件
from .filters import ContentFilter
from . import extractors, importers, parallel_corpus, machine_translate
from ..utils.config import TranslationConfig
from .exporters import export_keyed_to_csv, cleanup_backstories_dir
from ..utils.utils import update_history_list, get_history_list, sanitize_xml
from ..utils.filter_config import save_config_template
from .generators import TemplateGenerator

CONFIG = TranslationConfig()

# 添加类型别名
TranslationData = Tuple[str, str, str, str]  # (key, text, tag, file_path)
TranslationDict = Dict[str, Dict[str, str]]  # {key: {text: str, tag: str}}

def setup_logging() -> None:
    """初始化日志配置，避免重复添加 handler"""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    
    # 确保日志目录存在
    log_dir = Path(CONFIG.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    try:
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
    except Exception as e:
        print(f"警告：日志初始化失败，使用基本配置: {e}")
        logging.basicConfig(level=logging.INFO)

class TranslationFacade:
    """翻译操作的门面类"""
    
    def __init__(self, mod_dir: str, export_dir: str, language: str = CONFIG.default_language):
        """初始化翻译门面"""
        self.mod_dir = str(Path(mod_dir).resolve())
        self.export_dir = str(Path(export_dir).resolve())
        self.language = language
        self.source_language = CONFIG.source_language
        self.csv_path = str(Path(self.export_dir) / CONFIG.output_csv)
        
        # 初始化组件
        self.filter_mode = "standard"
        self.template_location = "mod"
        self._init_components()
    
    def _init_components(self) -> None:
        """初始化各个组件"""
        config_file = None
        if self.filter_mode == "custom":
            config_file = os.path.join(self.mod_dir, "translation_config.json")
        
        self.content_filter = ContentFilter(self.filter_mode, config_file)
    
    def set_filter_mode(self, mode: str) -> None:
        """设置过滤模式"""
        if mode in ["standard", "custom"]:
            self.filter_mode = mode
            self._init_components()  # 重新初始化组件
        else:
            raise ValueError("mode 必须是 'standard' 或 'custom'")
    
    def set_template_location(self, location: str) -> None:
        """设置模板生成位置"""
        if location in ["mod", "export"]:
            self.template_location = location
        else:
            raise ValueError("location 必须是 'mod' 或 'export'")
    
    def extract_all(self) -> List[TranslationData]:
        """提取所有翻译数据"""
        logging.info(f"提取翻译: mod_dir={self.mod_dir}, export_dir={self.export_dir}")
        return self._extract_comprehensive_mode()
    
    def _extract_comprehensive_mode(self) -> List[TranslationData]:
        """全面模式提取"""
        print("🔧 开始全面提取...")
        
        all_translations = []
        processed_keys = set()
        
        try:
            # 1. 英文 Keyed 提取
            en_keyed_path = Path(self.mod_dir) / "Languages" / self.source_language / CONFIG.keyed_dir
            keyed_count = 0
            
            if en_keyed_path.exists():
                keyed_translations = extractors.extract_keyed_translations(str(en_keyed_path), self.content_filter)
                
                for key, text, tag, file_path in keyed_translations:
                    normalized_key = self._normalize_key(key)
                    if normalized_key not in processed_keys:
                        all_translations.append((key, text, tag, file_path))
                        processed_keys.add(normalized_key)
                        keyed_count += 1
                
                if keyed_translations:
                    self._generate_keyed_template_from_translations(keyed_translations)
            
            # 2. Defs 提取
            defs_translations = extractors.preview_translatable_fields(
                mod_dir=self.mod_dir,
                preview=CONFIG.preview_translatable_fields,
                facade=self
            )
            
            defs_count = 0
            for full_path, text, tag, file_path in defs_translations:
                normalized_key = self._normalize_key(full_path)
                if normalized_key not in processed_keys:
                    all_translations.append((full_path, text, tag, file_path))
                    processed_keys.add(normalized_key)
                    defs_count += 1
            
            if defs_translations:
                self._generate_definjected_template_from_translations(defs_translations)
            
            # 3. 中文补充
            zh_keyed_count = 0
            if not en_keyed_path.exists():
                zh_keyed_path = Path(self.mod_dir) / "Languages" / self.language / CONFIG.keyed_dir
                if zh_keyed_path.exists():
                    zh_keyed_translations = extractors.extract_keyed_translations(str(zh_keyed_path), self.content_filter)
                    for key, text, tag, file_path in zh_keyed_translations:
                        normalized_key = self._normalize_key(key)
                        if normalized_key not in processed_keys:
                            all_translations.append((key, text, tag, file_path))
                            processed_keys.add(normalized_key)
                            zh_keyed_count += 1
            
            print(f"📊 提取完成: Keyed {keyed_count + zh_keyed_count}, Defs {defs_count}, 总计 {len(all_translations)}")
            
            if all_translations:
                self._write_translations_to_csv(all_translations)
            
            return all_translations
            
        except Exception as e:
            logging.error(f"提取过程出错: {e}", exc_info=True)
            raise
    
    def _normalize_key(self, key: str) -> str:
        """标准化键名，用于去重比较"""
        if '/' in key:
            return key.split('/', 1)[1]
        return key
    
    def _write_translations_to_csv(self, translations: List[TranslationData]) -> None:
        """写入翻译到 CSV 文件"""
        with open(self.csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag"])
            
            for key, text, tag, _ in translations:
                writer.writerow([key, sanitize_xml(text), tag])
        
        logging.info(f"直接导出 {len(translations)} 条到 {self.csv_path}")
    
    def generate_config_template(self, config_file: str) -> None:
        generator = TemplateGenerator(self.mod_dir, self.language, self.template_location)
        generator.generate_config_template(config_file)
    
    # 其他方法保持简洁，主要调用相应模块
    def import_translations(self, csv_file: str, merge: bool) -> None:
        """导入翻译"""
        importers.import_translations(csv_file, self.mod_dir, self.language, merge)
    
    def generate_corpus(self, mode: str) -> int:
        """生成平行语料集"""
        return parallel_corpus.generate_parallel_corpus(mode, self.mod_dir)
    
    def _generate_keyed_template_from_translations(self, keyed_translations: List[TranslationData]) -> None:
        """从已过滤的翻译数据生成 Keyed 模板（避免重复过滤）"""
        print("📋 正在生成中文 Keyed 翻译模板...")
        
        # 🔧 修复：使用 generators 模块，避免重复 XML 处理逻辑
        from .generators import TemplateGenerator
        
        generator = TemplateGenerator(self.mod_dir, self.language, self.template_location)
        export_dir = self.export_dir if self.template_location == "export" else None
        
        generator.generate_keyed_template_from_data(keyed_translations, export_dir)
    
    def _generate_definjected_template_from_translations(self, defs_translations: List[TranslationData]) -> None:
        """从已过滤的翻译数据生成 DefInjected 模板（避免重复过滤）"""
        print("🔧 正在生成 DefInjected 翻译模板...")
        
        # 🔧 修复：使用 generators 模块，避免重复 XML 处理逻辑
        from .generators import TemplateGenerator
        
        generator = TemplateGenerator(self.mod_dir, self.language, self.template_location)
        export_dir = self.export_dir if self.template_location == "export" else None
        
        generator.generate_definjected_template_from_data(defs_translations, export_dir)
    
    # 🗑️ 删除重复的 XML 处理代码
    # 原来的 _generate_keyed_template_from_translations 和 _generate_definjected_template_from_translations
    # 包含大量重复的 XML 处理逻辑，现在委托给 generators 模块

# ...existing code... (其他工具函数保持不变)

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


def main_workflow_example():
    """完整工作流 - 简化版本"""
    print("🚀 Day Translation")
    
    mod_dir = get_user_input_with_history("模组目录：", "mod_dir_history", True)
    export_dir = get_user_input_with_history("导出目录：", "export_dir_history", False)
    
    if not mod_dir or not export_dir:
        print("❌ 路径无效")
        return
    
    facade = TranslationFacade(mod_dir, export_dir)
    
    print("n模式: 1-提取 2-机翻 3-导入 4-语料 5-完整流程")
    mode = input("选择: ").strip()
    
    if mode == "1":
        run_mode_1(facade)
    elif mode in ["2", "3", "4"]:
        run_mode_2_to_4(facade, mode)
    elif mode == "5":
        run_complete_workflow(facade)
    else:
        print("❌ 无效选择")

def run_mode_1(facade: TranslationFacade) -> None:
    """运行模式 1：提取翻译到 CSV """
    try:
        start_time = time.time()
        
        output_dir = Path(facade.export_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 简化过滤模式选择
        filter_choice = input("过滤模式: 1-标准(默认) 2-自定义 : ").strip()
        
        if filter_choice == "2":
            facade.set_filter_mode("custom")
            config_file = os.path.join(facade.mod_dir, "translation_config.json")
            if not os.path.exists(config_file):
                if input("生成配置模板? (y/n): ").lower() == 'y':
                    facade.generate_config_template(config_file)
                    print(f"配置文件生成: {config_file}")
                    return
        else:
            facade.set_filter_mode("standard")
        
        # 简化模板位置选择
        location_choice = input("模板位置: 1-模组内(默认) 2-导出目录: ").strip()
        facade.set_template_location("export" if location_choice == "2" else "mod")
        
        # 执行提取
        translations = facade.extract_all()
        
        elapsed = time.time() - start_time
        update_history_list("extracted_csv_history", facade.csv_path)
        
        if translations:
            print(f"✅ 完成: {len(translations)} 条, {elapsed:.1f}秒, {len(translations)/elapsed:.0f}条/秒")
            print(f"📄 文件: {facade.csv_path}")
        else:
            print("⚠️ 未提取到内容")
        
    except Exception as e:
        logging.error(f"提取错误: {e}")
        print(f"❌ 错误: {e}")

def run_mode_2_to_4(facade: TranslationFacade, mode: str) -> None:
    """运行模式 2-4: 统一处理"""
    if mode == "2":  # 机器翻译
        csv_file = get_user_input_with_history("CSV文件路径：", "csv_file_history", True)
        if csv_file:
            try:
                from . import machine_translate
                machine_translate.translate_csv(csv_file)
                print("✅ 机器翻译完成")
            except Exception as e:
                print(f"❌ 翻译失败: {e}")
    
    elif mode == "3":  # 导入翻译
        csv_file = get_user_input_with_history("翻译CSV路径：", "translated_csv_history", True)
        if csv_file:
            merge = input("合并模式? (y/n): ").lower() == 'y'
            try:
                facade.import_translations(csv_file, merge)
                print("✅ 导入完成")
            except Exception as e:
                print(f"❌ 导入失败: {e}")
    
    elif mode == "4":  # 平行语料
        corpus_mode = input("语料模式: 1-XML注释 2-对比文件: ").strip()
        try:
            count = facade.generate_corpus(corpus_mode)
            print(f"✅ 语料生成: {count} 条")
        except Exception as e:
            print(f"❌ 语料失败: {e}")

def run_complete_workflow(facade: TranslationFacade) -> None:
    """完整流程 - 简化版本"""
    try:
        # 提取
        translations = facade.extract_all()
        if not translations:
            print("❌ 无内容")
            return
        
        # 机翻（可选）
        if input("机器翻译? (y/n): ").lower() == 'y':
            from . import machine_translate
            machine_translate.translate_csv(facade.csv_path)
        
        # 等待编辑
        input(f"编辑 {facade.csv_path} 后按回车...")
        
        # 导入
        facade.import_translations(facade.csv_path, False)
        print("✅ 流程完成")
        
    except Exception as e:
        print(f"❌ 流程失败: {e}")

def main() -> None:
    """主入口函数"""
    try:
        setup_logging()
        main_workflow_example()
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断操作")
        logging.info("用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常退出: {e}")
        logging.error(f"程序异常退出: {e}", exc_info=True)
    finally:
        print("\n👋 感谢使用 Day Translation 框架！")

if __name__ == "__main__":
    main()