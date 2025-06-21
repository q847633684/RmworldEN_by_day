"""
Day Translation 2 - 现代化核心功能测试

测试核心翻译处理功能的实际API。
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from core.translation_facade import TranslationFacade
from models.result_models import OperationResult, OperationStatus


@pytest.mark.core
class TestTranslationFacade:
    """测试翻译门面核心功能"""

    @pytest.fixture
    def facade(self, temp_dir):
        """创建翻译门面实例"""
        return TranslationFacade(mod_dir=str(temp_dir))

    def test_facade_initialization(self, facade):
        """测试门面初始化"""
        assert facade is not None
        assert hasattr(facade, "template_manager")
        assert hasattr(facade, "config")

    def test_facade_with_valid_mod_dir(self, temp_dir):
        """测试有效模组目录的门面创建"""
        # 创建简单的模组结构
        languages_dir = temp_dir / "Languages"
        languages_dir.mkdir()

        english_dir = languages_dir / "English"
        english_dir.mkdir()

        facade = TranslationFacade(mod_dir=str(temp_dir))
        assert facade is not None

    def test_facade_with_invalid_mod_dir(self):
        """测试无效模组目录的处理"""
        # 使用不存在的目录，应该抛出ConfigError
        with pytest.raises(Exception):  # 可能抛出ConfigError或ImportError
            facade = TranslationFacade(mod_dir="/nonexistent/path")  # 应该能创建，但可能有警告


@pytest.mark.core
class TestTemplateManager:
    """测试模板管理器功能"""

    def test_template_manager_import(self):
        """测试模板管理器导入"""
        from core.template_manager import TemplateManager

        # 使用临时目录作为mod_dir
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TemplateManager(mod_dir=temp_dir)
            assert manager is not None

    def test_template_manager_basic_functionality(self, temp_dir):
        """测试模板管理器基础功能"""
        from core.template_manager import TemplateManager

        manager = TemplateManager(mod_dir=str(temp_dir))
        assert manager.mod_dir == Path(temp_dir)

        # 测试基本方法存在
        assert hasattr(manager, "extract_and_generate_templates")
        assert hasattr(manager, "import_translations")


@pytest.mark.core
class TestExtractors:
    """测试提取器功能"""

    def test_extractors_import(self):
        """测试提取器模块导入"""
        from core.extractors import extract_all_translations

        assert callable(extract_all_translations)

    def test_extract_basic_functionality(self, temp_dir):
        """测试基础提取功能"""
        from core.extractors import extract_all_translations

        # 创建完整的测试结构（包括Keyed子目录）
        keyed_dir = temp_dir / "Languages" / "English" / "Keyed"
        keyed_dir.mkdir(parents=True)

        # 创建DefInjected目录
        definjected_dir = temp_dir / "Languages" / "English" / "DefInjected"
        definjected_dir.mkdir(parents=True)

        # 调用提取功能（应该返回结果，即使是空的）
        result = extract_all_translations(str(temp_dir), "English")

        # 验证返回了某种结果
        assert result is not None
        assert isinstance(result, list)


@pytest.mark.core
class TestGenerators:
    """测试生成器功能"""

    def test_generators_import(self):
        """测试生成器模块导入"""
        from core.generators import TemplateGenerator

        assert TemplateGenerator is not None

    def test_template_generator_creation(self):
        """测试模板生成器创建"""
        from core.generators import TemplateGenerator

        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            generator = TemplateGenerator(mod_dir=temp_dir, language="ChineseSimplified")
            assert generator is not None
            assert generator.language == "ChineseSimplified"


@pytest.mark.core
class TestExporters:
    """测试导出器功能"""

    def test_exporters_import(self):
        """测试导出器模块导入"""
        from core.exporters import export_keyed, AdvancedExporter

        assert callable(export_keyed)
        assert AdvancedExporter is not None

    def test_advanced_exporter_creation(self):
        """测试高级导出器创建"""
        from core.exporters import AdvancedExporter

        exporter = AdvancedExporter()
        assert exporter is not None

    def test_csv_exporter_import(self):
        """测试CSV导出器导入"""
        from core.exporters.csv_exporter import export_to_csv

        # 验证可以导入CSV导出函数
        assert callable(export_to_csv)


@pytest.mark.core
@pytest.mark.integration
class TestCoreIntegration:
    """测试核心模块集成"""

    def test_full_workflow_simulation(self, temp_dir, sample_translation_data):
        """测试完整工作流程模拟"""
        # 这是一个简化的集成测试
        from core.translation_facade import TranslationFacade

        # 创建基本目录结构
        languages_dir = temp_dir / "Languages" / "English"
        languages_dir.mkdir(parents=True)

        keyed_dir = languages_dir / "Keyed"
        keyed_dir.mkdir()

        # 创建简单的XML文件
        xml_file = keyed_dir / "test.xml"
        xml_file.write_text(
            """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
    <TestKey>Test Value</TestKey>
</LanguageData>""",
            encoding="utf-8",
        )

        # 创建门面并测试基本功能
        facade = TranslationFacade(mod_dir=str(temp_dir))

        # 验证门面能够正常初始化
        assert facade is not None
        assert facade.template_manager is not None
