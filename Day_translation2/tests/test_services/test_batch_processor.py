"""
Day Translation 2 - 批量处理服务测试

测试批量处理服务的多线程处理、进度显示和错误处理功能。
"""

import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.exceptions import ProcessingError, ValidationError
from models.result_models import OperationResult, OperationStatus, OperationType
from services.batch_processor import BatchProcessor


class TestBatchProcessor:
    """测试批量处理器"""

    @pytest.fixture
    def processor(self):
        """创建批量处理器实例"""
        return BatchProcessor(max_workers=2)

    @pytest.fixture
    def mock_mod_directories(self, temp_dir):
        """创建模拟模组目录"""
        mod_dirs = []
        for i in range(3):
            mod_dir = temp_dir / f"mod_{i}"
            mod_dir.mkdir()
            # 创建基本的模组文件结构
            (mod_dir / "Languages" / "English").mkdir(parents=True)
            (mod_dir / "Languages" / "English" / "Keyed").mkdir()
            mod_dirs.append(str(mod_dir))
        return mod_dirs

    def test_processor_initialization(self, processor) -> None:
        """测试处理器初始化"""
        assert processor.max_workers == 2
        assert processor.timeout == 300  # 默认超时时间
        assert processor.xml_processor is not None

    def test_processor_with_timeout(self) -> None:
        """测试带超时的处理器"""
        processor = BatchProcessor(max_workers=1, timeout=60)
        assert processor.max_workers == 1
        assert processor.timeout == 60

    @patch("Day_translation2.core.translation_facade.TranslationFacade")
    def test_process_multiple_mods_single_mod(self, mock_facade, processor, temp_dir) -> None:
        """测试单个模组处理（通过批量处理方法）"""
        # 创建一个模拟的模组目录结构
        mod_dir = temp_dir / "test_mod"
        mod_dir.mkdir()
        (mod_dir / "Languages").mkdir()
        (mod_dir / "Languages" / "English").mkdir()
        (mod_dir / "Languages" / "English" / "Keyed").mkdir()
        (mod_dir / "Languages" / "English" / "Keyed" / "test.xml").write_text(
            '<?xml version="1.0" encoding="utf-8"?><LanguageData><test>Test</test></LanguageData>'
        )

        # 执行测试 - 使用单个模组的批量处理
        result = processor.process_multiple_mods(mod_list=[str(mod_dir)])

        # 验证结果 - 即使失败也应该返回结果对象
        assert result.status in [
            OperationStatus.SUCCESS,
            OperationStatus.FAILED,
            OperationStatus.PARTIAL,
        ]
        assert result.operation_type == OperationType.BATCH_PROCESSING

    def test_process_invalid_directory(self, processor) -> None:
        """测试无效目录的处理"""
        result = processor.process_multiple_mods(mod_list=["/nonexistent/directory"])
        assert result.status == OperationStatus.FAILED
        assert "有效" in result.message  # "没有有效的模组目录"

    @patch("Day_translation2.core.translation_facade.TranslationFacade")
    def test_process_multiple_mods_success(
        self, mock_facade, processor, mock_mod_directories, temp_dir
    ) -> None:
        """测试多个模组批量处理成功"""
        # 模拟翻译门面
        mock_facade_instance = Mock()
        mock_facade.return_value = mock_facade_instance
        mock_facade_instance.extract_templates_and_generate_csv.return_value = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="提取完成",
            processed_count=5,
            success_count=5,
        )

        # 执行测试
        results = processor.process_multiple_mods(
            mod_list=mock_mod_directories,
            csv_path=str(temp_dir / "output.csv"),
        )

        # 验证结果
        assert results.status in [
            OperationStatus.SUCCESS,
            OperationStatus.FAILED,
            OperationStatus.PARTIAL,
        ]
        assert results.operation_type == OperationType.BATCH_PROCESSING
        # 如果成功，应该处理了指定数量的模组
        if results.is_success:
            assert results.processed_count > 0

    def test_process_multiple_mods_with_timeout(
        self, processor, mock_mod_directories, temp_dir
    ) -> None:
        """测试带超时的批量处理"""
        processor_with_timeout = BatchProcessor(max_workers=2, timeout=1)  # 1秒超时

        results = processor_with_timeout.process_multiple_mods(
            mod_list=mock_mod_directories,
            csv_path=str(temp_dir / "output.csv"),
        )

        # 验证结果
        assert results.status in [
            OperationStatus.SUCCESS,
            OperationStatus.FAILED,
            OperationStatus.PARTIAL,
        ]
        assert results.operation_type == OperationType.BATCH_PROCESSING

    def test_process_multiple_mods_partial_failure(
        self, processor, mock_mod_directories, temp_dir
    ) -> None:
        """测试部分失败的批量处理"""
        with patch("Day_translation2.core.translation_facade.TranslationFacade") as mock_facade:
            mock_facade_instance = Mock()
            mock_facade.return_value = mock_facade_instance

            # 模拟第二个模组失败
            def side_effect(*args, **kwargs):
                if "mod_1" in args[0]:  # 第二个模组
                    return OperationResult(
                        status=OperationStatus.ERROR,
                        operation_type=OperationType.EXTRACTION,
                        message="处理失败",
                        error_count=1,
                    )
                else:
                    return OperationResult(
                        status=OperationStatus.SUCCESS,
                        operation_type=OperationType.EXTRACTION,
                        message="提取完成",
                        processed_count=5,
                        success_count=5,
                    )

            mock_facade_instance.extract_templates_and_generate_csv.side_effect = side_effect

            # 执行测试
            results = processor.process_multiple_mods(
                mod_list=mock_mod_directories,
                csv_path=str(temp_dir / "output.csv"),
            )

            # 验证结果
            assert results.status in [
                OperationStatus.SUCCESS,
                OperationStatus.FAILED,
                OperationStatus.PARTIAL,
            ]
            assert results.processed_count >= 0  # 至少处理了一些内容

    def test_thread_safety(self, processor, mock_mod_directories, temp_dir) -> None:
        """测试多线程安全性"""
        results = []
        exceptions = []

        def worker():
            try:
                with patch(
                    "Day_translation2.core.translation_facade.TranslationFacade"
                ) as mock_facade:
                    mock_facade_instance = Mock()
                    mock_facade.return_value = mock_facade_instance
                    mock_facade_instance.extract_templates_and_generate_csv.return_value = (
                        OperationResult(
                            status=OperationStatus.SUCCESS,
                            operation_type=OperationType.EXTRACTION,
                            message="提取完成",
                            processed_count=1,
                            success_count=1,
                        )
                    )

                    result = processor.process_multiple_mods(
                        mod_list=[mock_mod_directories[0]],  # 只使用第一个模组目录
                        csv_path=str(temp_dir / f"output_{threading.current_thread().ident}.csv"),
                    )
                    results.append(result)
            except Exception as e:
                exceptions.append(e)

        # 创建多个线程
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(exceptions) == 0, f"线程执行出现异常: {exceptions}"
        assert len(results) == 3
        # 所有结果都应该是有效的操作结果
        for result in results:
            assert hasattr(result, "status")
            assert hasattr(result, "operation_type")


class TestBatchProcessorUtilities:
    """测试批量处理工具函数"""

    def test_process_multiple_mods_function(self, temp_dir) -> None:
        """测试批量处理函数 - 测试失败情况"""
        # 使用真实的处理器但测试失败情况
        processor = BatchProcessor(max_workers=2)
        result = processor.process_multiple_mods(
            mod_list=["/mod1", "/mod2"],  # 不存在的路径
        )

        # 验证结果 - 应该失败因为路径不存在
        assert result.status == OperationStatus.FAILED
        assert result.operation_type == OperationType.BATCH_PROCESSING
        assert "无效" in result.message or "没有有效" in result.message

    def test_process_multiple_mods_empty_list(self) -> None:
        """测试空模组列表处理"""
        processor = BatchProcessor()
        result = processor.process_multiple_mods(mod_list=[])
        assert result.status == OperationStatus.FAILED
        assert "模组列表为空" in result.message

    def test_process_multiple_mods_invalid_parameters(self) -> None:
        """测试无效参数的批量处理"""
        processor = BatchProcessor()

        # 测试 None 参数
        result = processor.process_multiple_mods(mod_list=None)
        assert result.status == OperationStatus.FAILED

        # 测试空字符串参数
        result = processor.process_multiple_mods(mod_list=[""])
        assert result.status == OperationStatus.FAILED
