"""
Day Translation 2 - 翻译门面类测试

测试TranslationFacade的核心功能和接口。
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.translation_facade import TranslationFacade
from models.exceptions import ProcessingError, ValidationError
from models.result_models import OperationResult, OperationStatus, OperationType


class TestTranslationFacade:
    """测试翻译门面类"""

    @pytest.fixture
    def facade(self):
        """创建翻译门面实例"""
        return TranslationFacade()

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock()
        config.core.source_language = "English"
        config.core.target_language = "ChineseSimplified"
        config.core.mod_directory = "/test/mod"
        config.core.output_directory = "/test/output"
        return config

    def test_facade_initialization(self, facade):
        """测试门面类初始化"""
        assert facade is not None
        assert hasattr(facade, "template_manager")
        assert hasattr(facade, "config")

    @patch("Day_translation2.core.template_manager.TemplateManager")
    def test_extract_templates_and_generate_csv_success(
        self, mock_template_manager, facade, temp_dir
    ):
        """测试模板提取和CSV生成成功"""
        # 模拟模板管理器
        mock_manager = Mock()
        mock_template_manager.return_value = mock_manager
        mock_manager.extract_and_generate_templates.return_value = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXTRACTION,
            message="提取完成",
            processed_count=100,
            success_count=100,
        )

        # 执行测试
        result = facade.extract_templates_and_generate_csv(
            mod_directory=str(temp_dir), output_csv=str(temp_dir / "output.csv")
        )

        # 验证结果
        assert result.is_success
        assert result.operation_type == OperationType.EXTRACTION
        assert "提取完成" in result.message

    def test_extract_templates_invalid_directory(self, facade):
        """测试无效目录的提取操作"""
        with pytest.raises(ValidationError) as exc_info:
            facade.extract_templates_and_generate_csv(
                mod_directory="/nonexistent/directory", output_csv="/test/output.csv"
            )

        assert "目录不存在" in str(exc_info.value)

    def test_extract_templates_empty_directory(self, facade, temp_dir):
        """测试空目录的提取操作"""
        result = facade.extract_templates_and_generate_csv(
            mod_directory=str(temp_dir), output_csv=str(temp_dir / "output.csv")
        )

        # 空目录应该返回成功但处理数量为0
        assert result.is_success
        assert result.processed_count == 0

    @patch("Day_translation2.core.template_manager.TemplateManager")
    def test_import_translations_to_templates_success(
        self, mock_template_manager, facade, temp_dir
    ):
        """测试翻译导入成功"""
        # 创建测试CSV文件
        csv_file = temp_dir / "translations.csv"
        csv_content = "key,text,translated\nTest.Key,Hello,你好"
        csv_file.write_text(csv_content, encoding="utf-8")

        # 模拟模板管理器
        mock_manager = Mock()
        mock_template_manager.return_value = mock_manager
        mock_manager.import_translations.return_value = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.IMPORT,
            message="导入完成",
            processed_count=1,
            success_count=1,
        )

        # 执行测试
        result = facade.import_translations_to_templates(
            csv_file=str(csv_file), templates_directory=str(temp_dir / "templates")
        )

        # 验证结果
        assert result.is_success
        assert result.operation_type == OperationType.IMPORT

    def test_import_translations_invalid_csv(self, facade):
        """测试无效CSV文件的导入操作"""
        with pytest.raises(ValidationError) as exc_info:
            facade.import_translations_to_templates(
                csv_file="/nonexistent/file.csv", templates_directory="/test/templates"
            )

        assert "文件不存在" in str(exc_info.value)

    @patch("Day_translation2.services.translation_service.translate_csv")
    def test_machine_translate_success(self, mock_translate, facade, temp_dir):
        """测试机器翻译成功"""
        # 创建测试CSV文件
        input_csv = temp_dir / "input.csv"
        output_csv = temp_dir / "output.csv"
        csv_content = "key,text\nTest.Key,Hello"
        input_csv.write_text(csv_content, encoding="utf-8")

        # 模拟翻译服务
        mock_translate.return_value = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.TRANSLATION,
            message="翻译完成",
            processed_count=1,
            success_count=1,
        )

        # 执行测试
        result = facade.machine_translate(
            input_csv=str(input_csv),
            output_csv=str(output_csv),
            access_key="test_key",
            secret_key="test_secret",
        )

        # 验证结果
        assert result.is_success
        assert result.operation_type == OperationType.TRANSLATION

    def test_machine_translate_empty_credentials(self, facade, temp_dir):
        """测试空凭据的机器翻译"""
        input_csv = temp_dir / "input.csv"
        output_csv = temp_dir / "output.csv"

        with pytest.raises(ValidationError) as exc_info:
            facade.machine_translate(
                input_csv=str(input_csv),
                output_csv=str(output_csv),
                access_key="",
                secret_key="",
            )

        assert "API密钥不能为空" in str(exc_info.value)

    @patch("Day_translation2.services.corpus_generator.generate_parallel_corpus")
    def test_generate_corpus_success(self, mock_generate, facade, temp_dir):
        """测试语料生成成功"""
        # 模拟语料生成服务
        mock_generate.return_value = OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXPORT,
            message="语料生成完成",
            processed_count=100,
            success_count=100,
        )

        # 执行测试
        result = facade.generate_corpus(
            mod_directory=str(temp_dir), output_csv=str(temp_dir / "corpus.csv")
        )

        # 验证结果
        assert result.is_success
        assert result.operation_type == OperationType.EXPORT
        assert "语料生成完成" in result.message

    def test_parameter_validation(self, facade):
        """测试参数验证功能"""
        # 测试空字符串参数
        with pytest.raises(ValidationError):
            facade.extract_templates_and_generate_csv("", "output.csv")

        # 测试None参数
        with pytest.raises(ValidationError):
            facade.extract_templates_and_generate_csv(None, "output.csv")

    @patch("Day_translation2.core.template_manager.TemplateManager")
    def test_error_handling_and_logging(self, mock_template_manager, facade, temp_dir):
        """测试错误处理和日志记录"""
        # 模拟模板管理器抛出异常
        mock_manager = Mock()
        mock_template_manager.return_value = mock_manager
        mock_manager.extract_and_generate_templates.side_effect = Exception("测试异常")

        # 执行测试，应该捕获异常并返回错误结果
        result = facade.extract_templates_and_generate_csv(
            mod_directory=str(temp_dir), output_csv=str(temp_dir / "output.csv")
        )

        # 验证错误结果
        assert not result.is_success
        assert result.status == OperationStatus.ERROR
        assert "测试异常" in result.message
