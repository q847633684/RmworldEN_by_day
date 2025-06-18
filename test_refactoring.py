#!/usr/bin/env python3
"""
测试重构后的user_preferences模块，验证路径管理功能集成
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "day_translation" / "utils"))

import user_preferences
UserPreferencesManager = user_preferences.UserPreferencesManager
PathValidationResult = user_preferences.PathValidationResult

def test_path_validation():
    """测试路径验证功能"""
    print("=== 测试路径验证功能 ===")
    
    # 创建临时目录和文件
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.csv")
        Path(test_file).touch()
        
        # 初始化管理器
        prefs_manager = UserPreferencesManager()
        
        # 测试目录验证
        result = prefs_manager.validate_path(temp_dir, "dir")
        print(f"目录验证 - 有效: {result.is_valid}, 路径: {result.normalized_path}")
        assert result.is_valid, f"目录验证失败: {result.error_message}"
        
        # 测试CSV文件验证
        result = prefs_manager.validate_path(test_file, "csv")
        print(f"CSV文件验证 - 有效: {result.is_valid}, 路径: {result.normalized_path}")
        assert result.is_valid, f"CSV文件验证失败: {result.error_message}"
        
        # 测试不存在的文件
        result = prefs_manager.validate_path("不存在的文件.csv", "csv")
        print(f"不存在文件验证 - 有效: {result.is_valid}, 错误: {result.error_message}")
        assert not result.is_valid, "不存在的文件不应该通过验证"
        
    print("✅ 路径验证功能测试通过\n")

def test_path_history():
    """测试路径历史记录功能"""
    print("=== 测试路径历史记录功能 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 使用临时目录作为配置目录
        prefs_manager = UserPreferencesManager(config_dir=temp_dir)
        
        # 添加路径到历史记录
        test_paths = [
            os.path.join(temp_dir, "path1"),
            os.path.join(temp_dir, "path2"),
            os.path.join(temp_dir, "path3")
        ]
        
        for path in test_paths:
            prefs_manager.add_to_history("test_type", path)
        
        # 检查历史记录
        history = prefs_manager.get_path_history("test_type")
        print(f"历史记录长度: {len(history)}")
        print(f"历史记录: {history}")
        
        assert len(history) == 3, f"历史记录长度错误: {len(history)}"
        assert history[0] == test_paths[-1], f"最新路径不在首位: {history[0]}"
        
        # 检查最后使用的路径
        last_used = prefs_manager.get_last_used_path("test_type")
        print(f"最后使用的路径: {last_used}")
        assert last_used == test_paths[-1], f"最后使用路径错误: {last_used}"
        
    print("✅ 路径历史记录功能测试通过\n")

def test_preferences_integration():
    """测试偏好设置集成"""
    print("=== 测试偏好设置集成 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        prefs_manager = UserPreferencesManager(config_dir=temp_dir)
        
        # 测试偏好设置
        prefs = prefs_manager.get_preferences()
        print(f"默认提取模式: {prefs.extraction.merge_mode}")
        print(f"默认结构选择: {prefs.extraction.structure_choice}")
        print(f"自动模式: {prefs.general.auto_mode}")
        
        # 修改偏好设置
        prefs.extraction.merge_mode = "backup"
        prefs.general.auto_mode = True
        prefs_manager.save_preferences()
        
        # 重新加载验证
        prefs_manager.load_preferences()
        new_prefs = prefs_manager.get_preferences()
        
        assert new_prefs.extraction.merge_mode == "backup", "偏好设置保存失败"
        assert new_prefs.general.auto_mode == True, "自动模式设置失败"
        
        print("偏好设置保存和加载正常")
        
    print("✅ 偏好设置集成测试通过\n")

def main():
    """运行所有测试"""
    print("开始测试重构后的user_preferences模块...")
    
    try:
        test_path_validation()
        test_path_history()
        test_preferences_integration()
        
        print("🎉 所有测试通过！重构成功整合了路径管理功能。")
        print("✅ PathManager 的功能已成功集成到 UserPreferencesManager")
        print("✅ 消除了功能重复，简化了架构")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
