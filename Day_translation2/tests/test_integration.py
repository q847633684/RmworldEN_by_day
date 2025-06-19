"""
Day Translation 2 - 集成测试

验证主要功能模块是否正常工作。
"""

import os
import tempfile
from pathlib import Path

import pytest

from Day_translation2.core.translation_facade import TranslationFacade
from Day_translation2.models.exceptions import ConfigError, TranslationError
from Day_translation2.models.result_models import (OperationResult,
                                                   OperationStatus)
from Day_translation2.services.batch_processor import BatchProcessor


class TestIntegration:
    """集成测试类"""

    def test_translation_facade_initialization(self):
        """测试翻译门面初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建模拟的模组目录结构
            mod_dir = Path(temp_dir) / "TestMod"
            mod_dir.mkdir()
            (mod_dir / "Languages").mkdir()

            # 测试正常初始化
            facade = TranslationFacade(str(mod_dir))
            assert facade.mod_dir == str(mod_dir.resolve())
            assert facade.language == "ChineseSimplified"  # 默认语言

    def test_translation_facade_invalid_mod_dir(self):
        """测试无效模组目录的处理"""
        with pytest.raises(ConfigError):
            TranslationFacade("/nonexistent/path")

    def test_batch_processor_initialization(self):
        """测试批量处理器初始化"""
        processor = BatchProcessor(max_workers=5, timeout=60)
        assert processor.max_workers == 5
        assert processor.timeout == 60

    def test_batch_processor_invalid_params(self):
        """测试批量处理器无效参数"""
        with pytest.raises(ConfigError):
            BatchProcessor(max_workers=0)

        with pytest.raises(ConfigError):
            BatchProcessor(timeout=-1)

    def test_batch_processor_empty_mod_list(self):
        """测试空模组列表处理"""
        processor = BatchProcessor()
        result = processor.process_multiple_mods([])

        assert isinstance(result, OperationResult)
        assert result.status == OperationStatus.FAILED
        assert "模组列表为空" in result.message

    def test_models_import(self):
        """测试模型类导入"""
        from Day_translation2.models.exceptions import (ConfigError,
                                                        ImportError,
                                                        ProcessingError,
                                                        TranslationError)
        from Day_translation2.models.result_models import (OperationResult,
                                                           OperationStatus,
                                                           OperationType)

        # 验证异常类
        assert issubclass(TranslationError, Exception)
        assert issubclass(ConfigError, TranslationError)
        assert issubclass(ImportError, TranslationError)
        assert issubclass(ProcessingError, TranslationError)

        # 验证操作结果类
        result = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="测试成功",
        )
        assert result.status == OperationStatus.SUCCESS
        assert result.operation_type == OperationType.EXTRACTION
        assert result.message == "测试成功"

    def test_core_modules_import(self):
        """测试核心模块导入"""
        from Day_translation2.core.exporters import DataExporter
        from Day_translation2.core.extractors import DataExtractor
        from Day_translation2.core.importers import DataImporter
        from Day_translation2.core.translation_facade import TranslationFacade

        # 验证类存在
        assert DataExtractor is not None
        assert DataImporter is not None
        assert DataExporter is not None
        assert TranslationFacade is not None

    def test_services_import(self):
        """测试服务模块导入"""
        from Day_translation2.services.batch_processor import BatchProcessor
        from Day_translation2.services.corpus_generator import \
            generate_parallel_corpus
        from Day_translation2.services.translation_service import \
            MachineTranslateService

        # 验证类和函数存在
        assert BatchProcessor is not None
        assert MachineTranslateService is not None
        assert generate_parallel_corpus is not None

    def test_utils_import(self):
        """测试工具模块导入"""
        from Day_translation2.utils.filter_rules import AdvancedFilterRules
        from Day_translation2.utils.file_utils import ensure_directory_exists
        from Day_translation2.utils.xml_processor import XMLProcessor

        # 验证类和函数存在
        assert XMLProcessor is not None
        assert AdvancedFilterRules is not None
        assert ensure_directory_exists is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
