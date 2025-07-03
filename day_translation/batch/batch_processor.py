"""
批量处理器 - 处理多个模组的批量操作
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from colorama import Fore, Style

from day_translation.utils.config import get_config
from day_translation.utils.path_manager import PathManager
from concurrent.futures import ThreadPoolExecutor, Future
import time
from dataclasses import dataclass
from tqdm import tqdm
from day_translation.extract.template_manager import TemplateManager
from day_translation.utils.filters import ContentFilter

CONFIG = get_config()


@dataclass
class ModProcessResult:
    """模组处理结果"""

    mod_dir: str
    success: bool
    error: Optional[str] = None
    config_generated: bool = False
    xml_updated: bool = False
    files_processed: int = 0
    files_updated: int = 0
    processing_time: float = 0.0


class BatchProcessor:
    """批量处理多个模组的翻译任务"""

    def __init__(self, max_workers: int = 10, timeout: int = 300):
        """
        初始化 BatchProcessor

        Args:
            max_workers (int): 最大并发线程数，默认为 10
            timeout (int): 单个模组处理超时时间（秒），默认为 300
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.processor = XMLProcessor()
        self._results: Dict[str, ModProcessResult] = {}
        logging.debug(
            "初始化 BatchProcessor: max_workers=%s, timeout=%s", max_workers, timeout
        )

    def process_multiple_mods(
        self,
        mod_list: List[str],
        csv_path: str = None,
        language="en-us",
    ) -> Dict[str, ModProcessResult]:
        """
        批量处理多个模组，生成配置并更新 XML

        Args:
            mod_list (List[str]): 模组目录列表
            csv_path (str, optional): 翻译 CSV 文件路径，默认为 None
            language (str): 目标语言，默认为 CONFIG.default_language

        Returns:
            Dict[str, ModProcessResult]: 处理结果字典，键为模组目录
        """
        logging.info("批量处理 %s 个模组", len(mod_list))
        print(f"{Fore.BLUE}开始处理 {len(mod_list)} 个模组...{Style.RESET_ALL}")

        # 验证输入
        valid_mods = []
        for mod_dir in mod_list:
            try:
                mod_path = Path(mod_dir).resolve()
                if not mod_path.is_dir():
                    print(f"{Fore.RED}❌ 无效的模组目录: {mod_dir}{Style.RESET_ALL}")
                    continue
                valid_mods.append(str(mod_path))
            except Exception as e:
                print(
                    f"{Fore.RED}❌ 模组目录验证失败: {mod_dir}, 错误: {e}{Style.RESET_ALL}"
                )
                continue

        if not valid_mods:
            print(f"{Fore.RED}❌ 没有有效的模组目录{Style.RESET_ALL}")
            return {}

        # 验证CSV文件
        if csv_path:
            try:
                csv_path = str(Path(csv_path).resolve())
                if not os.path.isfile(csv_path):
                    print(f"{Fore.RED}❌ CSV文件不存在: {csv_path}{Style.RESET_ALL}")
                    return {}
            except Exception as e:
                print(
                    f"{Fore.RED}❌ CSV文件验证失败: {csv_path}, 错误: {e}{Style.RESET_ALL}"
                )
                return {}

        # 使用线程池处理模组
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures: Dict[str, Future] = {}
            for mod_dir in valid_mods:
                future = executor.submit(
                    self._process_single_mod, mod_dir, csv_path, language
                )
                futures[mod_dir] = future

            # 使用tqdm显示进度
            with tqdm(total=len(futures), desc="处理模组", unit="模组") as pbar:
                for mod_dir, future in futures.items():
                    try:
                        result = future.result(timeout=self.timeout)
                        self._results[mod_dir] = result
                        status = (
                            f"{Fore.GREEN}✓{Style.RESET_ALL}"
                            if result.success
                            else f"{Fore.RED}✗{Style.RESET_ALL}"
                        )
                        pbar.set_postfix_str(f"{status} {Path(mod_dir).name}")
                    except TimeoutError:
                        self._results[mod_dir] = ModProcessResult(
                            mod_dir=mod_dir,
                            success=False,
                            error=f"处理超时（{self.timeout}秒）",
                        )
                        print(f"{Fore.RED}❌ 模组处理超时: {mod_dir}{Style.RESET_ALL}")
                    except Exception as e:
                        self._results[mod_dir] = ModProcessResult(
                            mod_dir=mod_dir, success=False, error=str(e)
                        )
                        print(
                            f"{Fore.RED}❌ 模组处理失败: {mod_dir}, 错误: {e}{Style.RESET_ALL}"
                        )
                    finally:
                        pbar.update(1)

        # 显示处理结果统计
        self._show_processing_summary()
        return self._results

    def _process_single_mod(
        self, mod_dir: str, csv_path: str, language: str
    ) -> ModProcessResult:
        """
        处理单个模组，生成配置并更新 XML

        Args:
            mod_dir (str): 模组目录
            csv_path (str): 翻译 CSV 文件路径
            language (str): 目标语言

        Returns:
            ModProcessResult: 处理结果
        """
        start_time = time.time()
        result = ModProcessResult(mod_dir=mod_dir, success=True)

        try:
            logging.debug("处理模组: %s, csv_path=%s", mod_dir, csv_path)

            # 生成配置
            config_path = os.path.join(mod_dir, "translation_config.json")
            try:
                generate_default_config(config_path)
                result.config_generated = True
            except Exception as e:
                logging.warning("生成配置失败: %s, 错误: %s", mod_dir, e)
                result.error = f"配置生成失败: {e}"

            # 更新XML
            if csv_path:
                try:
                    files_processed, files_updated = self._update_mod_xml(
                        mod_dir, csv_path, language
                    )
                    result.xml_updated = True
                    result.files_processed = files_processed
                    result.files_updated = files_updated
                except Exception as e:
                    logging.error("更新XML失败: %s, 错误: %s", mod_dir, e)
                    result.error = f"XML更新失败: {e}"
                    result.success = False

            result.processing_time = time.time() - start_time
            return result

        except Exception as e:
            logging.error("模组处理失败: %s, 错误: %s", mod_dir, e)
            result.success = False
            result.error = str(e)
            result.processing_time = time.time() - start_time
            return result

    def _update_mod_xml(
        self, mod_dir: str, csv_path: str, language: str
    ) -> Tuple[int, int]:
        """
        更新模组的 XML 文件以应用翻译

        Args:
            mod_dir (str): 模组目录
            csv_path (str): 翻译 CSV 文件路径
            language (str): 目标语言

        Returns:
            Tuple[int, int]: (处理的文件数, 更新的文件数)
        """
        logging.debug("更新模组 XML: mod_dir=%s, csv_path=%s", mod_dir, csv_path)

        # 使用 TemplateManager 加载翻译
        template_manager = TemplateManager(mod_dir, language)
        translations = template_manager._load_translations_from_csv(csv_path)

        content_filter = ContentFilter(CONFIG)
        lang_path = get_language_folder_path(language, mod_dir)

        files_processed = 0
        files_updated = 0

        for dir_name in [CONFIG.def_injected_dir, CONFIG.keyed_dir]:
            dir_path = os.path.join(lang_path, dir_name)
            if not os.path.exists(dir_path):
                logging.debug("目录不存在，跳过: %s", dir_path)
                continue

            for xml_file in Path(dir_path).rglob("*.xml"):
                files_processed += 1
                try:
                    logging.debug("处理 XML 文件: %s", xml_file)
                    tree = self.processor.parse_xml(str(xml_file))
                    if tree and self.processor.update_translations(
                        tree, translations, generate_element_key
                    ):
                        self.processor.save_xml(tree, str(xml_file))
                        files_updated += 1
                        logging.debug("更新 XML 文件: %s", xml_file)
                except Exception as e:
                    logging.error("处理文件失败: %s, 错误: %s", xml_file, e)
                    continue

        return files_processed, files_updated

    def _show_processing_summary(self) -> None:
        """显示处理结果统计"""
        if not self._results:
            return

        total_mods = len(self._results)
        successful_mods = sum(1 for r in self._results.values() if r.success)
        failed_mods = total_mods - successful_mods

        total_files_processed = sum(r.files_processed for r in self._results.values())
        total_files_updated = sum(r.files_updated for r in self._results.values())
        total_time = sum(r.processing_time for r in self._results.values())

        print(f"\n{Fore.BLUE}=== 处理结果统计 ==={Style.RESET_ALL}")
        print(f"总模组数: {total_mods}")
        print(f"成功: {Fore.GREEN}{successful_mods}{Style.RESET_ALL}")
        print(f"失败: {Fore.RED}{failed_mods}{Style.RESET_ALL}")
        print(f"处理文件数: {total_files_processed}")
        print(f"更新文件数: {total_files_updated}")
        print(f"总处理时间: {total_time:.2f}秒")

        if failed_mods > 0:
            print(f"\n{Fore.RED}=== 失败详情 ==={Style.RESET_ALL}")
            for mod_dir, result in self._results.items():
                if not result.success:
                    print(f"{Path(mod_dir).name}: {result.error}")

        print(f"{Fore.BLUE}==================={Style.RESET_ALL}\n")
