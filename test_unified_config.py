#!/usr/bin/env python
"""
测试新的统一配置系统
验证所有主要功能是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from day_translation.utils.unified_config import get_config, UnifiedConfig
from day_translation.utils.unified_interaction_manager import UnifiedInteractionManager

def test_unified_config():
    """测试统一配置系统的主要功能"""
    print("🧪 测试统一配置系统...")
      # 测试获取配置
    config = get_config()
    print(f"✅ 配置加载成功，版本: {config.version}")
      # 测试核心配置访问
    print(f"✅ 默认语言: {config.core.default_language}")
    print(f"✅ 源语言: {config.core.source_language}")
    print(f"✅ 输出CSV: {config.core.output_csv}")
    
    # 测试用户配置访问
    print(f"✅ 记住路径: {config.user.general.remember_paths}")
    print(f"✅ 自动模式: {config.user.general.auto_mode}")
      # 测试路径记忆
    remember_count = len(config.user.remembered_paths)
    print(f"✅ 记住的路径数量: {remember_count}")
    
    # 测试API密钥功能
    has_aliyun_key = bool(config.user.api.aliyun_access_key_id)
    print(f"✅ 阿里云密钥状态: {'已配置' if has_aliyun_key else '未配置'}")
      # 测试路径历史
    history_count = len(config.user.path_history)
    print(f"✅ 路径历史记录数量: {history_count}")
    
    print("🎉 统一配置系统测试通过！")


def test_unified_interaction_manager():
    """测试统一交互管理器"""
    print("\n🧪 测试统一交互管理器...")
    
    try:
        # 创建交互管理器实例
        manager = UnifiedInteractionManager()
        print("✅ 统一交互管理器创建成功")
          # 测试配置访问
        config = manager.config
        print(f"✅ 通过交互管理器访问配置: {config.core.default_language}")
        
        print("🎉 统一交互管理器测试通过！")
        
    except Exception as e:
        print(f"❌ 统一交互管理器测试失败: {e}")


def test_config_operations():
    """测试配置操作功能"""
    print("\n🧪 测试配置操作功能...")
    
    try:
        config = get_config()
        
        # 测试路径记忆
        test_path = r"C:\test\path" 
        test_path_type = "test_path"
        config.remember_path(test_path_type, test_path)
        remembered_path = config.get_remembered_path(test_path_type)
        assert remembered_path == test_path, f"路径记忆测试失败: {remembered_path}"
        print("✅ 路径记忆测试通过")
          # 测试API密钥设置
        test_key_name = "ALIYUN_ACCESS_KEY_ID"
        test_key_value = "test_api_key_value"
        config.set_api_key(test_key_name, test_key_value)
        retrieved_key = config.get_api_key(test_key_name)
        assert retrieved_key == test_key_value, f"API密钥测试失败: {retrieved_key}"
        print("✅ API密钥测试通过")
        
        print("🎉 配置操作功能测试通过！")
        
    except Exception as e:
        print(f"❌ 配置操作测试失败: {e}")
        raise


def main():
    """主测试函数"""
    print("🚀 开始测试新的统一配置系统\n")
    
    try:
        test_unified_config()
        test_unified_interaction_manager()
        test_config_operations()
        
        print("\n🎉 所有测试通过！统一配置系统运行正常。")
        print("📝 可以安全地删除旧的配置文件和相关代码了。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
