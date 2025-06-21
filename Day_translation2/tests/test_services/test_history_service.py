"""
测试服务层 - 历史记录服务

测试新架构的历史记录管理功能，不考虑向后兼容
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from config.data_models import GeneralConfig, UnifiedConfig, UserConfig
from services.history_service import HistoryService, history_service


@pytest.fixture
def test_config():
    """测试用的配置对象"""
    user_config = UserConfig(
        general=GeneralConfig(remember_paths=True), remembered_paths={}, path_history={}
    )
    return UnifiedConfig(user=user_config)


@pytest.fixture
def history_service_instance():
    """历史记录服务实例"""
    return HistoryService(default_max_history=5)


@pytest.mark.service
class TestHistoryService:
    """历史记录服务测试类"""

    def test_add_to_history_new_type(self, history_service_instance, test_config):
        """测试添加新类型的历史记录"""
        service = history_service_instance
        path_type = "test_path"
        path = "/test/path/1"

        service.add_to_history(path_type, path, test_config)

        # 验证历史记录被创建
        assert path_type in test_config.user.path_history
        history = test_config.user.path_history[path_type]
        assert history["paths"] == [path]
        assert history["last_used"] == path
        assert history["max_length"] == 5

    def test_add_to_history_existing_path(self, history_service_instance, test_config):
        """测试添加已存在的路径（应该移到最前面）"""
        service = history_service_instance
        path_type = "test_path"
        paths = ["/test/path/1", "/test/path/2", "/test/path/3"]

        # 添加多个路径
        for path in paths:
            service.add_to_history(path_type, path, test_config)

        # 再次添加第一个路径
        service.add_to_history(path_type, paths[0], test_config)

        # 验证第一个路径被移到最前面
        history = service.get_history(path_type, test_config)
        assert history[0] == paths[0]
        assert len(history) == 3

    def test_history_length_limit(self, history_service_instance, test_config):
        """测试历史记录长度限制"""
        service = history_service_instance
        path_type = "test_path"

        # 添加超过限制的路径
        for i in range(10):
            service.add_to_history(path_type, f"/test/path/{i}", test_config)

        # 验证长度被限制
        history = service.get_history(path_type, test_config)
        assert len(history) == 5  # 默认最大长度
        assert history[0] == "/test/path/9"  # 最新的在前面

    def test_get_last_used_path(self, history_service_instance, test_config):
        """测试获取最后使用的路径"""
        service = history_service_instance
        path_type = "test_path"
        last_path = "/test/path/last"

        # 添加历史记录
        service.add_to_history(path_type, "/test/path/1", test_config)
        service.add_to_history(path_type, last_path, test_config)

        # 验证最后使用的路径
        result = service.get_last_used_path(path_type, test_config)
        assert result == last_path

    def test_remember_path(self, history_service_instance, test_config):
        """测试记住路径功能"""
        service = history_service_instance
        path_type = "test_path"
        path = "/test/remembered/path"

        service.remember_path(path_type, path, test_config)

        # 验证路径被记住
        result = service.get_remembered_path(path_type, test_config)
        assert result == path

    def test_clear_history(self, history_service_instance, test_config):
        """测试清空历史记录"""
        service = history_service_instance
        path_type = "test_path"

        # 添加一些历史记录
        service.add_to_history(path_type, "/test/path/1", test_config)
        service.add_to_history(path_type, "/test/path/2", test_config)

        # 清空历史记录
        service.clear_history(path_type, test_config)

        # 验证历史记录被清空
        history = service.get_history(path_type, test_config)
        assert len(history) == 0

    def test_get_history_stats(self, history_service_instance, test_config):
        """测试获取历史记录统计"""
        service = history_service_instance

        # 添加不同类型的历史记录
        service.add_to_history("type1", "/path/1", test_config)
        service.add_to_history("type1", "/path/2", test_config)
        service.add_to_history("type2", "/path/3", test_config)

        stats = service.get_history_stats(test_config)

        # 验证统计信息
        assert "type1" in stats
        assert "type2" in stats
        assert stats["type1"]["count"] == 2
        assert stats["type2"]["count"] == 1
        assert stats["type1"]["has_last_used"] is True

    def test_validate_and_clean_history(
        self, history_service_instance, test_config, tmp_path
    ):
        """测试验证和清理历史记录"""
        service = history_service_instance
        path_type = "test_path"

        # 创建一些测试路径
        existing_path = tmp_path / "existing_file.txt"
        existing_path.write_text("test")
        nonexistent_path = tmp_path / "nonexistent_file.txt"

        # 添加历史记录
        service.add_to_history(path_type, str(existing_path), test_config)  # 存在
        service.add_to_history(path_type, str(nonexistent_path), test_config)  # 不存在

        # 验证和清理
        service.validate_and_clean_history(test_config)

        # 验证只保留存在的路径
        history = service.get_history(path_type, test_config)
        assert len(history) == 1
        assert history[0] == str(existing_path)

    def test_empty_config_handling(self, history_service_instance):
        """测试空配置的处理"""
        # 创建最小配置
        minimal_config = UnifiedConfig(user=UserConfig())
        service = history_service_instance

        # 这些操作不应该抛出异常
        history = service.get_history("nonexistent", minimal_config)
        assert history == []

        last_used = service.get_last_used_path("nonexistent", minimal_config)
        assert last_used is None


@pytest.mark.service
class TestHistoryServiceSingleton:
    """测试历史记录服务单例"""

    def test_singleton_instance(self):
        """测试单例实例存在"""
        assert history_service is not None
        assert isinstance(history_service, HistoryService)

    def test_singleton_consistency(self):
        """测试单例一致性"""
        from services.history_service import history_service as service1
        from services.history_service import history_service as service2

        assert service1 is service2


@pytest.mark.integration
class TestHistoryServiceIntegration:
    """历史记录服务集成测试"""

    def test_full_workflow(self, test_config):
        """测试完整的工作流程"""
        service = history_service

        # 模拟用户工作流程
        # 1. 记住常用路径
        service.remember_path("mod_folder", "/games/rimworld/mods", test_config)

        # 2. 添加历史记录
        service.add_to_history("mod_folder", "/games/rimworld/mods/mod1", test_config)
        service.add_to_history("mod_folder", "/games/rimworld/mods/mod2", test_config)
        service.add_to_history(
            "source_file", "/work/translations/file1.csv", test_config
        )

        # 3. 验证状态
        remembered = service.get_remembered_path("mod_folder", test_config)
        assert remembered == "/games/rimworld/mods"

        history = service.get_history("mod_folder", test_config)
        assert len(history) == 2
        assert history[0] == "/games/rimworld/mods/mod2"  # 最新的在前

        stats = service.get_history_stats(test_config)
        assert len(stats) == 2  # 两种类型

        # 4. 清理测试
        service.clear_all_history(test_config)
        stats_after = service.get_history_stats(test_config)
        assert len(stats_after) == 0
