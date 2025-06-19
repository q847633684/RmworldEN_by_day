"""
Day Translation 2 - 验证服务测试

测试翻译质量验证、术语一致性检查和格式规范验证功能。
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ...models.exceptions import ProcessingError, ValidationError
from ...models.result_models import (OperationResult, OperationStatus,
                                     OperationType)
from ...services.validation_service import (TranslationValidator,
                                            ValidationIssue, ValidationReport,
                                            validate_csv_file)


class TestValidationIssue:
    """测试验证问题数据类"""

    def test_validation_issue_creation(self):
        """测试验证问题创建"""
        issue = ValidationIssue(
            issue_type="empty_translation",
            severity="error",
            key="Test.Key",
            message="翻译为空",
            suggestion="添加翻译内容",
            file_path="test.xml",
        )

        assert issue.issue_type == "empty_translation"
        assert issue.severity == "error"
        assert issue.key == "Test.Key"
        assert issue.message == "翻译为空"
        assert issue.suggestion == "添加翻译内容"
        assert issue.file_path == "test.xml"


class TestValidationReport:
    """测试验证报告数据类"""

    def test_validation_report_creation(self):
        """测试验证报告创建"""
        issues = [
            ValidationIssue("error", "error", "key1", "错误1"),
            ValidationIssue("warning", "warning", "key2", "警告1"),
        ]

        report = ValidationReport(
            total_entries=100,
            issues=issues,
            error_count=1,
            warning_count=1,
            quality_score=85.5,
            terminology_consistency=90.0,
        )

        assert report.total_entries == 100
        assert len(report.issues) == 2
        assert report.error_count == 1
        assert report.warning_count == 1
        assert report.quality_score == 85.5
        assert report.terminology_consistency == 90.0


class TestTranslationValidator:
    """测试翻译验证器"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return TranslationValidator()

    @pytest.fixture
    def sample_translations(self):
        """提供测试翻译数据"""
        return [
            ("Keyed.Welcome", "Welcome to the game", "欢迎来到游戏"),
            ("Keyed.Start", "Start Game", "开始游戏"),
            ("Keyed.Settings", "Settings", "设置"),
            ("Keyed.Empty", "Not empty", ""),  # 空翻译
            ("Keyed.Same", "Same", "Same"),  # 相同文本
            ("Keyed.Placeholder", "Hello {name}", "你好 {name}"),  # 占位符
            (
                "Keyed.TooLong",
                "Short",
                "这是一个非常非常长的翻译文本，远远超过了原文的长度",
            ),  # 过长翻译
        ]

    def test_validator_initialization(self, validator):
        """测试验证器初始化"""
        assert validator.config is not None
        assert validator.content_filter is not None
        assert validator.terminology_dict is not None
        assert validator.validation_rules["check_empty_translations"] is True

    def test_validate_translations_success(self, validator):
        """测试翻译验证成功"""
        translations = [("Keyed.Welcome", "Welcome", "欢迎"), ("Keyed.Start", "Start", "开始")]

        report = validator.validate_translations(translations)

        assert isinstance(report, ValidationReport)
        assert report.total_entries == 2
        assert report.quality_score > 0

    def test_validate_translations_empty_input(self, validator):
        """测试空输入验证"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_translations([])

        assert "翻译数据不能为空" in str(exc_info.value)

    def test_check_empty_translations(self, validator):
        """测试空翻译检查"""
        translations = [
            ("Key1", "Source", ""),  # 空翻译
            ("Key2", "", "Target"),  # 空源文本
            ("Key3", "Same", "Same"),  # 相同文本
            ("Key4", "Normal", "正常翻译"),  # 正常翻译
        ]

        issues = validator._check_empty_translations(translations)

        # 应该发现3个问题
        assert len(issues) == 3

        # 检查问题类型
        issue_types = [issue.issue_type for issue in issues]
        assert "empty_translation" in issue_types
        assert "empty_source" in issue_types
        assert "untranslated" in issue_types

    def test_check_format_consistency(self, validator):
        """测试格式一致性检查"""
        translations = [
            ("Key1", "Hello {name}", "你好 {name}"),  # 正确的占位符
            ("Key2", "Hello {name}", "你好"),  # 缺少占位符
            ("Key3", "Value: %d", "值: %d"),  # 正确的格式符
            ("Key4", "Value: %d", "值"),  # 缺少格式符
        ]

        issues = validator._check_format_consistency(translations)

        # 应该发现2个占位符问题
        placeholder_issues = [i for i in issues if i.issue_type == "placeholder_mismatch"]
        missing_issues = [i for i in issues if i.issue_type == "missing_placeholder"]

        assert len(placeholder_issues) >= 1
        assert len(missing_issues) >= 1

    def test_check_terminology_consistency(self, validator):
        """测试术语一致性检查"""
        # 模拟术语字典
        validator.terminology_dict = {"Settings": ["设置", "选项"], "Save": ["保存", "存档"]}

        translations = [
            ("Key1", "Open Settings", "打开配置"),  # 未使用标准术语
            ("Key2", "Save Game", "保存游戏"),  # 使用标准术语
            ("Key3", "Settings Menu", "设置菜单"),  # 使用标准术语
        ]

        issues = validator._check_terminology_consistency(translations)

        # 应该发现术语不一致问题
        terminology_issues = [i for i in issues if i.issue_type == "terminology_inconsistency"]
        assert len(terminology_issues) >= 1

    def test_check_length_ratio(self, validator):
        """测试长度比例检查"""
        translations = [
            ("Key1", "Short", "短"),  # 正常比例
            ("Key2", "Short", "这是一个非常非常长的翻译"),  # 过长
            ("Key3", "Very long source text", "短"),  # 过短
        ]

        issues = validator._check_length_ratio(translations)

        # 应该发现长度问题
        too_long = [i for i in issues if i.issue_type == "translation_too_long"]
        too_short = [i for i in issues if i.issue_type == "translation_too_short"]

        assert len(too_long) >= 1
        assert len(too_short) >= 1

    def test_check_special_characters(self, validator):
        """测试特殊字符检查"""
        translations = [
            ("Key1", "Text with <tag>", "带有 <tag> 的文本"),  # 正确保留
            ("Key2", "Text with <tag>", "带有标签的文本"),  # 缺少特殊字符
            ("Key3", 'Text with "quotes"', '带有"引号"的文本'),  # 正确保留
        ]

        issues = validator._check_special_characters(translations)

        # 应该发现特殊字符不匹配问题
        char_issues = [i for i in issues if i.issue_type == "special_char_mismatch"]
        assert len(char_issues) >= 1

    def test_calculate_quality_score(self, validator):
        """测试质量评分计算"""
        # 测试满分情况
        score = validator._calculate_quality_score(100, 0, 0)
        assert score == 100.0

        # 测试有错误和警告的情况
        score = validator._calculate_quality_score(100, 10, 5)
        assert score < 100.0
        assert score >= 0.0

        # 测试空输入
        score = validator._calculate_quality_score(0, 0, 0)
        assert score == 0.0

    def test_calculate_terminology_score(self, validator):
        """测试术语一致性评分计算"""
        translations = [("Key1", "Test", "测试")]

        # 无术语问题
        score = validator._calculate_terminology_score(translations, [])
        assert score == 100.0

        # 有术语问题
        issues = [ValidationIssue("terminology_inconsistency", "warning", "Key1", "术语问题")]
        score = validator._calculate_terminology_score(translations, issues)
        assert score < 100.0


class TestValidationUtilities:
    """测试验证工具函数"""

    def test_validate_csv_file_success(self, temp_dir):
        """测试CSV文件验证成功"""
        # 创建测试CSV文件
        csv_file = temp_dir / "test.csv"
        csv_content = """key,text,translated
Keyed.Welcome,Welcome,欢迎
Keyed.Start,Start,开始"""
        csv_file.write_text(csv_content, encoding="utf-8")

        # 执行验证
        result = validate_csv_file(str(csv_file))

        # 验证结果
        assert result.is_success or result.status == OperationStatus.WARNING
        assert result.operation_type == OperationType.VALIDATION

    def test_validate_csv_file_missing_columns(self, temp_dir):
        """测试缺少必要列的CSV文件"""
        # 创建缺少列的CSV文件
        csv_file = temp_dir / "invalid.csv"
        csv_content = """wrong_key,wrong_text
Test1,测试1"""
        csv_file.write_text(csv_content, encoding="utf-8")

        # 执行验证
        with pytest.raises(ValidationError) as exc_info:
            validate_csv_file(str(csv_file))

        assert "缺少必要的列" in str(exc_info.value)

    def test_validate_csv_file_not_exists(self):
        """测试不存在的CSV文件"""
        with pytest.raises(ValidationError) as exc_info:
            validate_csv_file("/nonexistent/file.csv")

        assert "文件不存在" in str(exc_info.value)

    @patch("Day_translation2.services.validation_service._save_validation_report")
    def test_validation_report_generation(self, mock_save_report, temp_dir):
        """测试验证报告生成"""
        # 创建测试CSV文件
        csv_file = temp_dir / "test.csv"
        csv_content = """key,text,translated
Keyed.Welcome,Welcome,
Keyed.Start,Start,开始"""
        csv_file.write_text(csv_content, encoding="utf-8")

        # 执行验证
        result = validate_csv_file(str(csv_file))

        # 验证报告保存被调用
        mock_save_report.assert_called_once()

        # 检查结果包含错误信息
        assert "错误" in result.message or "警告" in result.message
