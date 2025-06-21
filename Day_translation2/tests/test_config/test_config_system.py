"""
测试配置系统 - 现代化架构

测试新的配置架构，不考虑向后兼容
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from config.data_models import UnifiedConfig, CoreConfig, UserConfig, GeneralConfig
from config.config_manager import ConfigManager
from services.config_service import ConfigService


@pytest.fixture
def temp_config_file(tmp_path):
    """临时配置文件"""
    config_file = tmp_path / "test_config.json"
    return str(config_file)


@pytest.fixture
def sample_config_data():
    """示例配置数据"""
    return {
        "version": "2.0.0",
        "core": {
            "version": "2.0.0",
            "default_language": "zh_CN",
            "source_language": "en",
            "debug_mode": False,
        },
        "user": {
            "general": {"auto_mode": False, "remember_paths": True, "confirm_operations": True},
            "remembered_paths": {},
            "path_history": {},
        },
    }


@pytest.mark.config
class TestDataModels:
    """测试数据模型"""

    def test_core_config_creation(self):
        """测试核心配置创建"""
        config = CoreConfig(default_language="zh_CN", source_language="en", debug_mode=True)

        assert config.default_language == "zh_CN"
        assert config.source_language == "en"
        assert config.debug_mode is True

    def test_user_config_creation(self):
        """测试用户配置创建"""
        general = GeneralConfig(auto_mode=True, remember_paths=False)
        config = UserConfig(general=general)

        assert config.general.auto_mode is True
        assert config.general.remember_paths is False
        assert isinstance(config.remembered_paths, dict)
        assert isinstance(config.path_history, dict)

    def test_unified_config_creation(self):
        """测试统一配置创建"""
        config = UnifiedConfig()

        assert config.version == "2.0.0"
        assert isinstance(config.core, CoreConfig)
        assert isinstance(config.user, UserConfig)

    def test_config_serialization(self):
        """测试配置序列化"""
        config = UnifiedConfig()
        data = config.to_dict()

        assert "version" in data
        assert "core" in data
        assert "user" in data
        assert data["version"] == "2.0.0"

    def test_config_from_dict(self, sample_config_data):
        """测试从字典创建配置"""
        config = UnifiedConfig.from_dict(sample_config_data)

        assert config.version == "2.0.0"
        assert config.core.default_language == "zh_CN"
        assert config.user.general.remember_paths is True


@pytest.mark.config
class TestConfigManager:
    """测试配置管理器"""

    def test_create_default_config(self):
        """测试创建默认配置"""
        manager = ConfigManager()
        config = manager.create_default_config()

        assert isinstance(config, UnifiedConfig)
        assert config.version == "2.0.0"

    def test_save_and_load_config(self, temp_config_file, sample_config_data):
        """测试保存和加载配置"""
        manager = ConfigManager()

        # 创建配置对象
        config = UnifiedConfig.from_dict(sample_config_data)

        # 保存配置
        manager.save_config(config, temp_config_file)

        # 验证文件存在
        assert Path(temp_config_file).exists()

        # 加载配置
        loaded_config = manager.load_config(temp_config_file)

        # 验证配置内容
        assert loaded_config.version == config.version
        assert loaded_config.core.default_language == config.core.default_language
        assert loaded_config.user.general.remember_paths == config.user.general.remember_paths

    def test_load_nonexistent_config(self, temp_config_file):
        """测试加载不存在的配置文件"""
        manager = ConfigManager()

        # 加载不存在的文件应该返回默认配置
        config = manager.load_config(temp_config_file)

        assert isinstance(config, UnifiedConfig)
        assert config.version == "2.0.0"

    def test_validate_config_valid(self, sample_config_data):
        """测试验证有效配置"""
        manager = ConfigManager()
        config = UnifiedConfig.from_dict(sample_config_data)

        is_valid, errors = manager.validate_config(config)

        assert is_valid
        assert len(errors) == 0

    def test_validate_config_invalid(self):
        """测试验证无效配置"""
        manager = ConfigManager()

        # 创建无效配置（缺少必要字段）
        config = UnifiedConfig()
        config.core = None  # 这应该导致验证失败

        is_valid, errors = manager.validate_config(config)

        assert not is_valid
        assert len(errors) > 0

    def test_backup_and_restore(self, temp_config_file, sample_config_data):
        """测试备份和恢复配置"""
        manager = ConfigManager()
        config = UnifiedConfig.from_dict(sample_config_data)

        # 保存配置
        manager.save_config(config, temp_config_file)

        # 创建备份
        backup_file = manager.backup_config(temp_config_file)

        assert Path(backup_file).exists()

        # 修改原配置
        config.core.debug_mode = True
        manager.save_config(config, temp_config_file)

        # 恢复备份
        success = manager.restore_config(backup_file, temp_config_file)
        assert success

        # 验证配置已恢复
        restored_config = manager.load_config(temp_config_file)
        assert restored_config.core.debug_mode is False  # 应该是原来的值


@pytest.mark.config
class TestConfigService:
    """测试配置服务"""

    def test_service_initialization(self):
        """测试服务初始化"""
        manager = ConfigManager()
        service = ConfigService(manager)

        assert service.manager is manager

    def test_export_config(self, temp_config_file, sample_config_data):
        """测试导出配置"""
        manager = ConfigManager()
        service = ConfigService(manager)
        config = UnifiedConfig.from_dict(sample_config_data)

        export_file = temp_config_file.replace(".json", "_export.json")
        success = service.export_config(config, export_file)

        assert success
        assert Path(export_file).exists()

        # 验证导出的内容
        with open(export_file, "r", encoding="utf-8") as f:
            exported_data = json.load(f)

        assert exported_data["version"] == "2.0.0"

    def test_import_config(self, temp_config_file, sample_config_data):
        """测试导入配置"""
        manager = ConfigManager()
        service = ConfigService(manager)

        # 先保存一个配置作为导入源
        config = UnifiedConfig.from_dict(sample_config_data)
        manager.save_config(config, temp_config_file)

        # 导入配置
        imported_config = service.import_config(temp_config_file)

        assert imported_config is not None
        assert imported_config.version == "2.0.0"

    def test_merge_configs(self):
        """测试合并配置"""
        manager = ConfigManager()
        service = ConfigService(manager)

        # 创建基础配置
        base_config = UnifiedConfig()
        base_config.core.debug_mode = False
        base_config.user.general.auto_mode = False

        # 创建覆盖配置
        override_config = UnifiedConfig()
        override_config.core.debug_mode = True
        # auto_mode 保持默认值

        # 合并配置
        merged_config = service.merge_configs(base_config, override_config)

        # 验证合并结果
        assert merged_config.core.debug_mode is True  # 被覆盖
        assert merged_config.user.general.auto_mode is False  # 保持基础值

    def test_config_migration(self):
        """测试配置迁移"""
        manager = ConfigManager()
        service = ConfigService(manager)

        # 模拟旧版本配置
        old_config_data = {"version": "1.0.0", "settings": {"language": "zh_CN", "debug": False}}

        # 迁移配置
        migrated_config = service.migrate_config(old_config_data)

        assert migrated_config.version == "2.0.0"
        # 验证迁移逻辑正确


@pytest.mark.integration
class TestConfigIntegration:
    """配置系统集成测试"""

    def test_full_config_workflow(self, tmp_path):
        """测试完整的配置工作流程"""
        config_file = tmp_path / "workflow_test.json"

        # 1. 创建配置管理器和服务
        manager = ConfigManager()
        service = ConfigService(manager)

        # 2. 创建默认配置
        config = manager.create_default_config()

        # 3. 修改配置
        config.core.debug_mode = True
        config.user.general.remember_paths = False

        # 4. 保存配置
        manager.save_config(config, str(config_file))

        # 5. 加载配置
        loaded_config = manager.load_config(str(config_file))

        # 6. 验证配置
        is_valid, errors = manager.validate_config(loaded_config)
        assert is_valid

        # 7. 导出配置
        export_file = tmp_path / "exported.json"
        service.export_config(loaded_config, str(export_file))

        # 8. 导入配置
        imported_config = service.import_config(str(export_file))

        # 9. 验证整个流程
        assert imported_config.core.debug_mode is True
        assert imported_config.user.general.remember_paths is False

    def test_error_recovery(self, tmp_path):
        """测试错误恢复机制"""
        config_file = tmp_path / "error_test.json"
        manager = ConfigManager()

        # 创建损坏的配置文件
        with open(config_file, "w") as f:
            f.write('{"invalid": json')

        # 加载应该失败但返回默认配置
        config = manager.load_config(str(config_file))

        assert isinstance(config, UnifiedConfig)
        assert config.version == "2.0.0"

    @pytest.mark.slow
    def test_performance_large_config(self, tmp_path):
        """测试大配置文件的性能"""
        import time

        manager = ConfigManager()
        config = manager.create_default_config()

        # 创建大量历史记录
        for i in range(1000):
            path_type = f"type_{i % 10}"
            if path_type not in config.user.path_history:
                config.user.path_history[path_type] = {
                    "paths": [],
                    "max_length": 10,
                    "last_used": None,
                }
            config.user.path_history[path_type]["paths"].append(f"/path/{i}")

        config_file = tmp_path / "large_config.json"

        # 测试保存性能
        start_time = time.time()
        manager.save_config(config, str(config_file))
        save_time = time.time() - start_time

        # 测试加载性能
        start_time = time.time()
        loaded_config = manager.load_config(str(config_file))
        load_time = time.time() - start_time

        # 性能断言
        assert save_time < 1.0  # 保存应该在1秒内完成
        assert load_time < 1.0  # 加载应该在1秒内完成
        assert len(loaded_config.user.path_history) == 10
