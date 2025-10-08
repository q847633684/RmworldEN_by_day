# 用户配置系统 2.0

一个完整、可扩展的用户配置管理系统，支持多种翻译API和丰富的配置选项。

## 🚀 主要特性

### ✨ 可扩展API配置
- **多API支持**: 阿里云、百度、腾讯、谷歌、自定义API
- **插件化架构**: 轻松添加新的API提供商
- **智能管理**: 多API支持
- **连接测试**: 内置API连接测试功能
- **配置验证**: 自动验证配置的正确性

### 🎛️ 完整配置管理
- **路径配置**: 管理默认路径和历史记录
- **语言配置**: 设置语言目录和文件名
- **日志配置**: 自定义日志级别和输出方式
- **界面配置**: 主题、语言、交互选项

### 🔧 高级功能
- **配置验证**: 实时验证配置有效性
- **备份恢复**: 配置备份和恢复功能
- **导入导出**: 配置的导入和导出
- **用户界面**: 友好的命令行配置界面

## 📁 系统架构

```
user_config/
├── core/           # 核心配置类
│   ├── base_config.py      # 配置基类
│   ├── user_config.py      # 用户配置管理器
│   └── config_validator.py # 配置验证器
├── api/            # API配置模块
│   ├── base_api.py         # API配置基类
│   ├── aliyun_api.py       # 阿里云API配置
│   ├── baidu_api.py        # 百度API配置
│   ├── tencent_api.py      # 腾讯API配置
│   ├── google_api.py       # 谷歌API配置
│   ├── custom_api.py       # 自定义API配置
│   └── api_manager.py      # API管理器
└── ui/             # 配置界面
    ├── main_config_ui.py   # 主配置界面
    └── api_config_ui.py    # API配置界面
```

## 🎯 快速开始

### 通过主菜单访问

新的配置系统已经集成到主程序中，通过以下方式访问：

1. **运行主程序**: `python main.py`
2. **选择配置管理**: 在主菜单中选择"配置管理"选项
3. **直接进入新配置系统**: 系统会自动启动新的配置界面

### 编程方式使用

```python
from user_config import UserConfigManager
from user_config.ui import MainConfigUI

# 创建配置管理器
config_manager = UserConfigManager()

# 启动配置界面
config_ui = MainConfigUI(config_manager)
config_ui.show_main_menu()
```

### API配置示例

```python
# 配置阿里云API
aliyun_api = config_manager.api_manager.get_api("aliyun")
aliyun_api.set_value("access_key_id", "your_access_key_id")
aliyun_api.set_value("access_key_secret", "your_access_key_secret")
aliyun_api.set_value("region", "cn-hangzhou")
aliyun_api.set_enabled(True)

# 测试连接
success, message = aliyun_api.test_connection()
print(f"连接测试: {message}")

# 保存配置
config_manager.save_config()
```

### 配置验证

```python
from user_config.core.config_validator import ConfigValidator

validator = ConfigValidator()
results = validator.validate_all_configs(config_manager)

for config_name, result in results.items():
    if result.is_valid:
        print(f"✅ {config_name}: 验证通过")
    else:
        print(f"❌ {config_name}: 验证失败")
        for error in result.errors:
            print(f"  - {error}")
```

## 🔌 扩展新API

### 1. 创建API配置类

```python
from user_config.api.base_api import BaseAPIConfig

class MyAPIConfig(BaseAPIConfig):
    def __init__(self):
        super().__init__("我的API", "myapi")
        
        # 设置默认值
        self._defaults.update({
            "api_key": "",
            "endpoint": "https://api.example.com"
        })
        
        # 设置必需字段
        self._required_fields.update({"api_key"})
        
        # 设置字段类型
        self._field_types.update({
            "api_key": str,
            "endpoint": str
        })
    
    def get_schema(self):
        return {
            "api_key": {
                "type": "password",
                "label": "API密钥",
                "required": True
            },
            "endpoint": {
                "type": "text", 
                "label": "API端点",
                "default": "https://api.example.com"
            }
        }
    
    def test_connection(self):
        # 实现连接测试逻辑
        return True, "连接成功"
    
    def get_auth_params(self):
        return {"api_key": self.get_value("api_key")}
    
    def get_request_params(self):
        return {"endpoint": self.get_value("endpoint")}
```

### 2. 注册到API管理器

```python
# 在 api_manager.py 中添加
from .myapi import MyAPIConfig

class APIManager:
    def __init__(self):
        self.apis = {
            # ... 现有API
            "myapi": MyAPIConfig(),
        }
```

## 📋 配置文件格式

配置文件保存在 `~/.day_translation/user_config.json`:

```json
{
  "version": "2.0.0",
  "api": {
    "apis": {
      "aliyun": {
        "enabled": true,
        "priority": 0,
        "access_key_id": "your_key",
        "access_key_secret": "your_secret",
        "region": "cn-hangzhou"
      }
    }
  },
  "path": {
    "remember_paths": true,
    "auto_detect_paths": true
  },
  "language": {
    "CN_language": "ChineseSimplified",
    "EN_language": "English"
  },
  "log": {
    "log_level": "INFO",
    "log_to_file": true
  },
  "ui": {
    "theme": "default",
    "language": "zh_CN"
  }
}
```

## 🛠️ API参考

### UserConfigManager

主要的配置管理器类。

#### 方法

- `get_config_modules()`: 获取所有配置模块
- `save_config()`: 保存配置到文件
- `load_config()`: 从文件加载配置
- `backup_config()`: 备份配置
- `restore_config(path)`: 恢复配置
- `reset_to_defaults()`: 重置为默认值
- `validate_all_configs()`: 验证所有配置

### APIManager

API配置管理器。

#### 方法

- `get_api(api_type)`: 获取指定API配置
- `get_enabled_apis()`: 获取已启用的API列表
- `get_primary_api()`: 获取主要API
- `test_api(api_type)`: 测试API连接
- `enable_api(api_type)`: 启用API
- `disable_api(api_type)`: 禁用API

## 🔍 故障排除

### 常见问题

1. **配置文件损坏**
   ```python
   # 重置配置
   config_manager.reset_to_defaults()
   config_manager.save_config()
   ```

2. **API连接失败**
   ```python
   # 验证配置
   success, message = api.test_connection()
   if not success:
       print(f"连接失败: {message}")
   ```

3. **配置验证失败**
   ```python
   # 查看详细错误
   result = validator.validate_config_schema(config_data, schema)
   for error in result.errors:
       print(f"错误: {error}")
   ```

## 📝 更新日志

### v2.0.0
- 全新的可扩展配置系统
- 支持多种翻译API
- 完整的配置验证
- 用户友好的界面
- 配置备份和恢复功能

## 🤝 贡献

欢迎提交问题和功能请求！

## 📄 许可证

MIT License
