"""
Day Translation 2 - 批量处理服务

提供多模组的并发处理功能，支持批量配置生成和XML更新。
遵循提示文件标准：PEP 8规范、具体异常处理、用户友好错误信息。
"""

import logging
import os
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as ConcurrentTimeoutError
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from colorama import Fore, Style
from tqdm import tqdm

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.importers import import_translations, load_translations_from_csv
from models.exceptions import ConfigError
from models.exceptions import ImportError as TranslationImportError
from models.exceptions import ProcessingError
from models.result_models import OperationResult, OperationStatus, OperationType

# 使用绝对导入
from services.config_service import config_service
from utils.xml_processor import AdvancedXMLProcessor


@dataclass
class ModProcessResult:
    """模组处理结果数据类"""

    mod_dir: str
    success: bool
    error: Optional[str] = None
    config_generated: bool = False
    xml_updated: bool = False
    files_processed: int = 0
    files_updated: int = 0
    processing_time: float = 0.0


class BatchProcessor:
    """批量处理服务，支持多模组并发处理"""

    def __init__(self, max_workers: int = 10, timeout: int = 300):
        """
        初始化批量处理器

        Args:
            max_workers: 最大并发线程数
            timeout: 单个模组处理超时时间（秒）

        Raises:
            ConfigError: 配置无效时
        """
        if max_workers <= 0:
            raise ConfigError("max_workers必须大于0")
        if timeout <= 0:
            raise ConfigError("timeout必须大于0")

        self.max_workers = max_workers
        self.timeout = timeout
        self.xml_processor = AdvancedXMLProcessor()
        self._results: Dict[str, ModProcessResult] = {}

        try:
            self.config = config_service.get_unified_config()
        except Exception as e:
            raise ConfigError(f"初始化配置失败: {str(e)}")

        logging.debug(f"初始化批量处理器: max_workers={max_workers}, timeout={timeout}")

    def process_multiple_mods(
        self,
        mod_list: List[str],
        csv_path: Optional[str] = None,
        language: Optional[str] = None,
    ) -> OperationResult:
        """
        批量处理多个模组

        Args:
            mod_list: 模组目录列表
            csv_path: 翻译CSV文件路径（可选）
            language: 目标语言（可选，默认使用配置中的语言）

        Returns:
            OperationResult: 批量处理结果
        """
        if not mod_list:
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.BATCH_PROCESSING,
                message="模组列表为空",
                errors=["未提供任何模组目录"],
            )

        target_language = language or self.config.core.default_language

        logging.info(f"开始批量处理 {len(mod_list)} 个模组")
        print(f"{Fore.BLUE}开始处理 {len(mod_list)} 个模组...{Style.RESET_ALL}")

        try:
            # 验证输入
            valid_mods = self._validate_mod_list(mod_list)
            if not valid_mods:
                return OperationResult(
                    status=OperationStatus.FAILED,
                    operation_type=OperationType.BATCH_PROCESSING,
                    message="没有有效的模组目录",
                    errors=["所有模组目录都无效"],
                )

            # 验证CSV文件
            if csv_path and not self._validate_csv_file(csv_path):
                return OperationResult(
                    status=OperationStatus.FAILED,
                    operation_type=OperationType.BATCH_PROCESSING,
                    message="CSV文件无效",
                    errors=[f"CSV文件不存在或无法访问: {csv_path}"],
                )

            # 并发处理模组
            self._process_mods_concurrently(valid_mods, csv_path, target_language)

            # 生成处理结果
            return self._generate_processing_result()

        except Exception as e:
            error_msg = f"批量处理失败: {str(e)}"
            logging.error(error_msg)
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.BATCH_PROCESSING,
                message=error_msg,
                errors=[str(e)],
            )

    def _validate_mod_list(self, mod_list: List[str]) -> List[str]:
        """验证模组目录列表"""
        valid_mods = []
        for mod_dir in mod_list:
            try:
                mod_path = Path(mod_dir).resolve()
                if not mod_path.is_dir():
                    print(f"{Fore.RED}❌ 无效的模组目录: {mod_dir}{Style.RESET_ALL}")
                    continue
                valid_mods.append(str(mod_path))
            except Exception as e:
                print(f"{Fore.RED}❌ 模组目录验证失败: {mod_dir}, 错误: {e}{Style.RESET_ALL}")
                logging.warning(f"模组目录验证失败: {mod_dir}, 错误: {e}")
                continue
        return valid_mods

    def _validate_csv_file(self, csv_path: str) -> bool:
        """验证CSV文件"""
        try:
            csv_path = str(Path(csv_path).resolve())
            if not os.path.isfile(csv_path):
                print(f"{Fore.RED}❌ CSV文件不存在: {csv_path}{Style.RESET_ALL}")
                return False
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ CSV文件验证失败: {csv_path}, 错误: {e}{Style.RESET_ALL}")
            logging.error(f"CSV文件验证失败: {csv_path}, 错误: {e}")
            return False

    def _process_mods_concurrently(
        self, mod_list: List[str], csv_path: Optional[str], language: str
    ) -> None:
        """并发处理模组"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures: Dict[str, Future] = {}

            # 提交所有任务
            for mod_dir in mod_list:
                future = executor.submit(self._process_single_mod, mod_dir, csv_path, language)
                futures[mod_dir] = future

            # 显示进度并收集结果
            with tqdm(total=len(futures), desc="处理模组", unit="模组") as p_bar:
                for mod_dir, future in futures.items():
                    try:
                        result = future.result(timeout=self.timeout)
                        self._results[mod_dir] = result

                        status = (
                            f"{Fore.GREEN}✓{Style.RESET_ALL}"
                            if result.success
                            else f"{Fore.RED}✗{Style.RESET_ALL}"
                        )
                        p_bar.set_postfix_str(f"{status} {Path(mod_dir).name}")

                    except ConcurrentTimeoutError:
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
                        print(f"{Fore.RED}❌ 模组处理失败: {mod_dir}, 错误: {e}{Style.RESET_ALL}")
                        logging.error(f"模组处理失败: {mod_dir}, 错误: {e}")

                    finally:
                        p_bar.update(1)

        # 显示处理摘要
        self._show_processing_summary()

    def _process_single_mod(
        self, mod_dir: str, csv_path: Optional[str], language: str
    ) -> ModProcessResult:
        """
        处理单个模组

        Args:
            mod_dir: 模组目录
            csv_path: CSV文件路径
            language: 目标语言

        Returns:
            ModProcessResult: 处理结果
        """
        start_time = time.time()
        result = ModProcessResult(mod_dir=mod_dir, success=True)

        try:
            logging.debug(f"处理模组: {mod_dir}, csv_path={csv_path}")  # 生成配置文件
            try:
                config_path = os.path.join(mod_dir, "translation_config.json")
                from services.config_service import config_service

                config_service.export_config(self.config, config_path)
                result.config_generated = True
                logging.debug(f"配置文件已生成: {config_path}")
            except Exception as e:
                logging.warning(f"生成配置失败: {mod_dir}, 错误: {e}")
                result.error = f"配置生成失败: {e}"

            # 更新XML文件
            if csv_path:
                try:
                    files_processed, files_updated = self._update_mod_xml(
                        mod_dir, csv_path, language
                    )
                    result.xml_updated = True
                    result.files_processed = files_processed
                    result.files_updated = files_updated
                    logging.debug(
                        f"XML更新完成: {mod_dir}, 处理{files_processed}个文件，更新{files_updated}个"
                    )
                except Exception as e:
                    logging.error(f"更新XML失败: {mod_dir}, 错误: {e}")
                    result.error = f"XML更新失败: {e}"
                    result.success = False

            result.processing_time = time.time() - start_time
            return result

        except Exception as e:
            logging.error(f"模组处理失败: {mod_dir}, 错误: {e}")
            result.success = False
            result.error = str(e)
            result.processing_time = time.time() - start_time
            return result

    def _update_mod_xml(self, mod_dir: str, csv_path: str, language: str) -> Tuple[int, int]:
        """
        更新模组的XML文件

        Args:
            mod_dir: 模组目录
            csv_path: CSV文件路径
            language: 目标语言

        Returns:
            Tuple[int, int]: (处理的文件数, 更新的文件数)

        Raises:
            ProcessingError: XML处理失败时
        """
        try:
            # 加载翻译数据
            translations = load_translations_from_csv(csv_path)
            if not translations:
                raise ProcessingError(f"未能从CSV文件加载翻译数据: {csv_path}")

            # 获取语言目录路径
            lang_path = self._get_language_folder_path(language, mod_dir)
            if not os.path.exists(lang_path):
                raise ProcessingError(f"语言目录不存在: {lang_path}")

            files_processed = 0
            files_updated = 0

            # 处理DefInjected和Keyed目录
            for dir_name in [
                self.config.core.definjected_dir,
                self.config.core.keyed_dir,
            ]:
                dir_path = os.path.join(lang_path, dir_name)
                if not os.path.exists(dir_path):
                    logging.debug(f"目录不存在，跳过: {dir_path}")
                    continue

                # 递归处理XML文件
                for xml_file in Path(dir_path).rglob("*.xml"):
                    files_processed += 1
                    try:
                        if self._update_single_xml_file(str(xml_file), translations):
                            files_updated += 1
                    except Exception as e:
                        logging.error(f"处理XML文件失败: {xml_file}, 错误: {e}")
                        continue

            return files_processed, files_updated

        except Exception as e:
            raise ProcessingError(f"更新模组XML失败: {str(e)}")

    def _update_single_xml_file(self, xml_file_path: str, translations: Dict[str, str]) -> bool:
        """
        更新单个XML文件

        Args:
            xml_file_path: XML文件路径
            translations: 翻译字典

        Returns:
            bool: 是否成功更新
        """
        try:
            tree = self.xml_processor.parse_xml(xml_file_path)
            if not tree:
                logging.warning(f"无法解析XML文件: {xml_file_path}")
                return False

            # 更新翻译
            updated = self.xml_processor.update_translations(tree, translations)

            if updated:
                self.xml_processor.save_xml(tree, xml_file_path)
                logging.debug(f"XML文件已更新: {xml_file_path}")
                return True
            else:
                logging.debug(f"XML文件无需更新: {xml_file_path}")
                return False

        except Exception as e:
            logging.error(f"更新XML文件失败: {xml_file_path}, 错误: {e}")
            return False

    def _get_language_folder_path(self, language: str, mod_dir: str) -> str:
        """获取语言文件夹路径"""
        return os.path.join(mod_dir, "Languages", language)

    def _generate_processing_result(self) -> OperationResult:
        """生成批量处理结果"""
        if not self._results:
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.BATCH_PROCESSING,
                message="未处理任何模组",
            )

        total_mods = len(self._results)
        successful_mods = sum(1 for r in self._results.values() if r.success)
        failed_mods = total_mods - successful_mods

        total_files_processed = sum(r.files_processed for r in self._results.values())
        total_files_updated = sum(r.files_updated for r in self._results.values())

        # 确定整体状态
        if failed_mods == 0:
            status = OperationStatus.SUCCESS
            message = f"批量处理成功: {successful_mods}/{total_mods} 个模组"
        elif successful_mods == 0:
            status = OperationStatus.FAILED
            message = f"批量处理失败: 所有 {total_mods} 个模组都失败"
        else:
            status = OperationStatus.PARTIAL
            message = f"批量处理部分成功: {successful_mods}/{total_mods} 个模组"

        result = OperationResult(
            status=status,
            operation_type=OperationType.BATCH_PROCESSING,
            message=message,
            processed_count=total_mods,
            success_count=successful_mods,
        )

        # 添加详细信息
        result.details.update(
            {
                "total_mods": total_mods,
                "successful_mods": successful_mods,
                "failed_mods": failed_mods,
                "total_files_processed": total_files_processed,
                "total_files_updated": total_files_updated,
                "processing_results": self._results,
            }
        )

        # 添加错误信息
        failed_results = {mod: res for mod, res in self._results.items() if not res.success}
        if failed_results:
            result.errors = [
                f"{Path(mod).name}: {res.error}" for mod, res in failed_results.items()
            ]

        return result

    def _show_processing_summary(self) -> None:
        """显示处理结果摘要"""
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

    def get_processing_results(self) -> Dict[str, ModProcessResult]:
        """获取处理结果"""
        return self._results.copy()

    def clear_results(self) -> None:
        """清空处理结果"""
        self._results.clear()
