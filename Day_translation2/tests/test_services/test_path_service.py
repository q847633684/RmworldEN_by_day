"""
测试服务层 - 路径验证服务

测试新架构的路径验证功能，不考虑向后兼容
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from config.data_models import PathValidationResult
from services.path_service import PathValidationService, path_validation_service


@pytest.fixture
def path_service():
    """路径验证服务实例"""
    return PathValidationService()


@pytest.fixture
def temp_files(tmp_path):
    """创建临时文件和目录用于测试"""
    # 创建测试目录结构
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # 创建测试文件
    test_file = test_dir / "test.txt"
    test_file.write_text("test content")

    csv_file = test_dir / "test.csv"
    csv_file.write_text("key,original,translated\ntest,hello,你好")

    json_file = test_dir / "test.json"
    json_file.write_text('{"test": "data"}')

    return {
        "dir": str(test_dir),
        "file": str(test_file),
        "csv": str(csv_file),
        "json": str(json_file),
        "nonexistent": str(tmp_path / "nonexistent"),
    }


@pytest.mark.service
class TestPathValidationService:
    """路径验证服务测试类"""

    def test_normalize_path(self, path_service):
        """测试路径规范化"""
        # 测试相对路径
        result = path_service.normalize_path("./test")
        assert result.is_valid
        assert Path(result.normalized_path).is_absolute()

        # 测试绝对路径
        abs_path = str(Path.cwd() / "test")
        result = path_service.normalize_path(abs_path)
        assert result.is_valid
        assert result.normalized_path == str(Path(abs_path).resolve())

    def test_validate_directory_existing(self, path_service, temp_files):
        """测试验证存在的目录"""
        result = path_service.validate_path(temp_files["dir"], "dir")

        assert result.is_valid
        assert result.path == temp_files["dir"]
        assert result.error_message is None

    def test_validate_directory_nonexistent(self, path_service, temp_files):
        """测试验证不存在的目录"""
        result = path_service.validate_path(temp_files["nonexistent"], "dir")

        assert not result.is_valid
        assert "不存在" in result.error_message
        assert result.suggestion is not None

    def test_validate_file_existing(self, path_service, temp_files):
        """测试验证存在的文件"""
        result = path_service.validate_path(temp_files["file"], "file")

        assert result.is_valid
        assert result.path == temp_files["file"]

    def test_validate_file_nonexistent(self, path_service, temp_files):
        """测试验证不存在的文件"""
        result = path_service.validate_path(temp_files["nonexistent"], "file")

        assert not result.is_valid
        assert "不存在" in result.error_message

    def test_validate_csv_file_valid(self, path_service, temp_files):
        """测试验证有效的CSV文件"""
        result = path_service.validate_path(temp_files["csv"], "csv")

        assert result.is_valid
        assert result.path == temp_files["csv"]

    def test_validate_csv_file_wrong_extension(self, path_service, temp_files):
        """测试验证错误扩展名的CSV文件"""
        result = path_service.validate_path(temp_files["file"], "csv")

        assert not result.is_valid
        assert "CSV格式" in result.error_message

    def test_validate_csv_file_create_new(self, path_service, tmp_path):
        """测试验证创建新CSV文件"""
        new_csv = tmp_path / "new_file.csv"
        result = path_service.validate_path(str(new_csv), "csv")

        # 应该允许创建新CSV文件
        assert result.is_valid

    def test_validate_json_file_valid(self, path_service, temp_files):
        """测试验证有效的JSON文件"""
        result = path_service.validate_path(temp_files["json"], "json")

        assert result.is_valid
        assert result.path == temp_files["json"]

    def test_validate_json_file_wrong_extension(self, path_service, temp_files):
        """测试验证错误扩展名的JSON文件"""
        result = path_service.validate_path(temp_files["file"], "json")

        assert not result.is_valid
        assert "JSON格式" in result.error_message

    def test_validate_directory_create(self, path_service, tmp_path):
        """测试验证创建目录"""
        new_dir = tmp_path / "parent" / "new_dir"
        # 确保父目录存在
        new_dir.parent.mkdir(exist_ok=True)

        result = path_service.validate_path(str(new_dir), "dir_create")

        assert result.is_valid

    def test_validate_directory_create_no_parent(self, path_service, tmp_path):
        """测试验证创建目录但父目录不存在"""
        new_dir = tmp_path / "nonexistent_parent" / "new_dir"

        result = path_service.validate_path(str(new_dir), "dir_create")

        assert not result.is_valid
        assert "父目录不存在" in result.error_message

    def test_validate_mod_directory(self, path_service, tmp_path):
        """测试验证模组目录"""
        # 创建有效的模组目录结构
        mod_dir = tmp_path / "TestMod"
        mod_dir.mkdir()

        # 创建About子目录和About.xml文件
        about_dir = mod_dir / "About"
        about_dir.mkdir()
        about_xml = about_dir / "About.xml"
        about_xml.write_text(
            '<?xml version="1.0" encoding="utf-8"?><ModMetaData></ModMetaData>'
        )

        result = path_service.validate_path(str(mod_dir), "mod")

        assert result.is_valid

    def test_validate_unknown_type(self, path_service, temp_files):
        """测试验证未知类型"""
        result = path_service.validate_path(temp_files["file"], "unknown_type")

        assert not result.is_valid
        assert "未知的验证器类型" in result.error_message

    @patch("os.access")
    def test_validate_permission_denied(self, mock_access, path_service, temp_files):
        """测试验证权限被拒绝的情况"""
        mock_access.return_value = False

        result = path_service.validate_path(temp_files["dir"], "dir")

        assert not result.is_valid
        assert "无法访问" in result.error_message

    def test_get_directory_info(self, path_service, temp_files):
        """测试获取目录信息"""
        info = path_service.get_directory_info(temp_files["dir"])

        assert "exists" in info
        assert "is_directory" in info
        assert "file_count" in info
        assert info["exists"] is True
        assert info["is_directory"] is True
        assert info["file_count"] >= 3  # 至少有我们创建的3个文件

    def test_get_directory_file_count(self, path_service, temp_files):
        """测试获取目录文件数量"""
        # 测试所有文件
        total_count = path_service.get_directory_file_count(temp_files["dir"])
        assert total_count >= 3

        # 测试特定扩展名
        csv_count = path_service.get_directory_file_count(temp_files["dir"], ".csv")
        assert csv_count == 1

        json_count = path_service.get_directory_file_count(temp_files["dir"], ".json")
        assert json_count == 1

    def test_error_handling(self, path_service):
        """测试错误处理"""
        # 测试无效路径字符
        invalid_paths = ["", None, 123]

        for invalid_path in invalid_paths:
            try:
                result = path_service.validate_path(invalid_path, "file")
                # 应该返回无效结果而不是抛出异常
                assert not result.is_valid
            except (TypeError, AttributeError):
                # 如果抛出异常也是可以接受的
                pass


@pytest.mark.service
class TestPathValidationServiceSingleton:
    """测试路径验证服务单例"""

    def test_singleton_instance(self):
        """测试单例实例存在"""
        assert path_validation_service is not None
        assert isinstance(path_validation_service, PathValidationService)

    def test_singleton_consistency(self):
        """测试单例一致性"""
        from services.path_service import path_validation_service as service1
        from services.path_service import path_validation_service as service2

        assert service1 is service2


@pytest.mark.integration
class TestPathValidationIntegration:
    """路径验证服务集成测试"""

    def test_real_world_scenarios(self, tmp_path):
        """测试真实世界场景"""
        service = path_validation_service

        # 场景1：验证游戏模组目录
        mod_dir = tmp_path / "RimWorld" / "Mods" / "MyMod"
        mod_dir.mkdir(parents=True)

        # 创建About目录和About.xml文件
        about_dir = mod_dir / "About"
        about_dir.mkdir()
        about_xml = about_dir / "About.xml"
        about_xml.write_text(
            '<?xml version="1.0" encoding="utf-8"?><ModMetaData></ModMetaData>'
        )

        result = service.validate_path(str(mod_dir), "mod")
        assert result.is_valid

        # 场景2：验证翻译文件
        translation_file = (
            mod_dir / "Languages" / "ChineseSimplified" / "DefInjected.csv"
        )
        translation_file.parent.mkdir(parents=True)
        translation_file.write_text("defName,original,translated\ntest,Hello,你好")

        result = service.validate_path(str(translation_file), "csv")
        assert result.is_valid

        # 场景3：验证配置文件
        config_file = tmp_path / "config.json"
        config_file.write_text('{"version": "1.0"}')

        result = service.validate_path(str(config_file), "json")
        assert result.is_valid

    @pytest.mark.slow
    def test_performance_many_files(self, tmp_path):
        """测试大量文件的性能"""
        service = path_validation_service

        # 创建包含大量文件的目录
        test_dir = tmp_path / "performance_test"
        test_dir.mkdir()

        # 创建100个测试文件
        for i in range(100):
            (test_dir / f"file_{i}.txt").write_text(f"content {i}")

        # 测试目录文件计数性能
        import time

        start_time = time.time()

        count = service.get_directory_file_count(str(test_dir))

        end_time = time.time()

        assert count == 100
        assert end_time - start_time < 1.0  # 应该在1秒内完成
