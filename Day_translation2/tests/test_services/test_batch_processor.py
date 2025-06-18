"""
Day Translation 2 - 批量处理服务测试

测试批量处理服务的多线程处理、进度显示和错误处理功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import threading
import time

from ...services.batch_processor import BatchProcessor, process_multiple_mods
from ...models.result_models import OperationResult, OperationStatus, OperationType
from ...models.exceptions import ProcessingError, ValidationError


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
    
    def test_processor_initialization(self, processor):
        """测试处理器初始化"""
        assert processor.max_workers == 2
        assert processor.progress_callback is None
        assert hasattr(processor, 'executor')
    
    def test_processor_with_progress_callback(self):
        """测试带进度回调的处理器"""
        callback = Mock()
        processor = BatchProcessor(max_workers=1, progress_callback=callback)
        assert processor.progress_callback == callback
    
    @patch('Day_translation2.core.translation_facade.TranslationFacade')
    def test_process_single_mod_success(self, mock_facade, processor, temp_dir):
        """测试单个模组处理成功"""
        # 模拟翻译门面
        mock_facade_instance = Mock()
        mock_facade.return_value = mock_facade_instance
        mock_facade_instance.extract_templates_and_generate_csv.return_value = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="提取完成",
            processed_count=10,
            success_count=10
        )
        
        # 执行测试
        result = processor.process_single_mod(
            mod_directory=str(temp_dir),
            output_csv=str(temp_dir / "output.csv")
        )
        
        # 验证结果
        assert result.is_success
        assert result.processed_count == 10
        mock_facade_instance.extract_templates_and_generate_csv.assert_called_once()
    
    def test_process_single_mod_invalid_directory(self, processor):
        """测试无效目录的单个模组处理"""
        with pytest.raises(ValidationError) as exc_info:
            processor.process_single_mod(
                mod_directory="/nonexistent/directory",
                output_csv="/test/output.csv"
            )
        
        assert "目录不存在" in str(exc_info.value)
    
    @patch('Day_translation2.core.translation_facade.TranslationFacade')
    def test_process_multiple_mods_success(self, mock_facade, processor, mock_mod_directories, temp_dir):
        """测试多个模组批量处理成功"""
        # 模拟翻译门面
        mock_facade_instance = Mock()
        mock_facade.return_value = mock_facade_instance
        mock_facade_instance.extract_templates_and_generate_csv.return_value = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="提取完成",
            processed_count=5,
            success_count=5
        )
        
        # 执行测试
        results = processor.process_multiple_mods(
            mod_directories=mock_mod_directories,
            output_directory=str(temp_dir / "output")
        )
        
        # 验证结果
        assert len(results) == 3
        for result in results:
            assert result.is_success
            assert result.processed_count == 5
    
    def test_process_multiple_mods_with_progress(self, processor, mock_mod_directories, temp_dir):
        """测试带进度回调的批量处理"""
        progress_callback = Mock()
        processor.progress_callback = progress_callback
        
        with patch('Day_translation2.core.translation_facade.TranslationFacade') as mock_facade:
            mock_facade_instance = Mock()
            mock_facade.return_value = mock_facade_instance
            mock_facade_instance.extract_templates_and_generate_csv.return_value = OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXTRACTION,
                message="提取完成",
                processed_count=1,
                success_count=1
            )
            
            # 执行测试
            results = processor.process_multiple_mods(
                mod_directories=mock_mod_directories,
                output_directory=str(temp_dir / "output")
            )
            
            # 验证进度回调被调用
            assert progress_callback.call_count >= 3  # 每个模组至少调用一次
    
    def test_process_multiple_mods_partial_failure(self, processor, mock_mod_directories, temp_dir):
        """测试部分失败的批量处理"""
        with patch('Day_translation2.core.translation_facade.TranslationFacade') as mock_facade:
            mock_facade_instance = Mock()
            mock_facade.return_value = mock_facade_instance
            
            # 模拟第二个模组失败
            def side_effect(*args, **kwargs):
                if "mod_1" in args[0]:  # 第二个模组
                    return OperationResult(
                        status=OperationStatus.ERROR,
                        operation_type=OperationType.EXTRACTION,
                        message="处理失败",
                        error_count=1
                    )
                else:
                    return OperationResult(
                        status=OperationStatus.SUCCESS,
                        operation_type=OperationType.EXTRACTION,
                        message="提取完成",
                        processed_count=5,
                        success_count=5
                    )
            
            mock_facade_instance.extract_templates_and_generate_csv.side_effect = side_effect
            
            # 执行测试
            results = processor.process_multiple_mods(
                mod_directories=mock_mod_directories,
                output_directory=str(temp_dir / "output")
            )
            
            # 验证结果
            assert len(results) == 3
            success_count = sum(1 for r in results if r.is_success)
            error_count = sum(1 for r in results if not r.is_success)
            assert success_count == 2
            assert error_count == 1
    
    def test_thread_safety(self, processor, mock_mod_directories, temp_dir):
        """测试多线程安全性"""
        results = []
        exceptions = []
        
        def worker():
            try:
                with patch('Day_translation2.core.translation_facade.TranslationFacade') as mock_facade:
                    mock_facade_instance = Mock()
                    mock_facade.return_value = mock_facade_instance
                    mock_facade_instance.extract_templates_and_generate_csv.return_value = OperationResult(
                        status=OperationStatus.SUCCESS,
                        operation_type=OperationType.EXTRACTION,
                        message="提取完成",
                        processed_count=1,
                        success_count=1
                    )
                    
                    result = processor.process_single_mod(
                        mod_directory=mock_mod_directories[0],
                        output_csv=str(temp_dir / f"output_{threading.current_thread().ident}.csv")
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
        for result in results:
            assert result.is_success


class TestBatchProcessorUtilities:
    """测试批量处理工具函数"""
    
    @patch('Day_translation2.services.batch_processor.BatchProcessor')
    def test_process_multiple_mods_function(self, mock_batch_processor, temp_dir):
        """测试批量处理函数"""
        # 模拟批量处理器
        mock_processor = Mock()
        mock_batch_processor.return_value = mock_processor
        mock_processor.process_multiple_mods.return_value = [
            OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXTRACTION,
                message="模组1处理完成",
                processed_count=10,
                success_count=10
            ),
            OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXTRACTION,
                message="模组2处理完成",
                processed_count=8,
                success_count=8
            )
        ]
        
        # 执行测试
        result = process_multiple_mods(
            mod_directories=["/mod1", "/mod2"],
            output_directory=str(temp_dir),
            max_workers=2
        )
        
        # 验证结果
        assert result.is_success
        assert result.operation_type == OperationType.EXTRACTION
        assert "2个模组" in result.message
        assert result.processed_count == 18  # 10 + 8
        assert result.success_count == 18
    
    def test_process_multiple_mods_empty_list(self):
        """测试空模组列表处理"""
        with pytest.raises(ValidationError) as exc_info:
            process_multiple_mods(
                mod_directories=[],
                output_directory="/test/output"
            )
        
        assert "模组目录列表不能为空" in str(exc_info.value)
    
    def test_process_multiple_mods_invalid_parameters(self):
        """测试无效参数的批量处理"""
        with pytest.raises(ValidationError):
            process_multiple_mods(
                mod_directories=None,
                output_directory="/test/output"
            )
        
        with pytest.raises(ValidationError):
            process_multiple_mods(
                mod_directories=["/mod1"],
                output_directory=""
            )
