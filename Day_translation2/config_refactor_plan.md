# config_models.py 职责分离拆分计划

## 🎯 拆分目标

将 `config_models.py` 拆分为职责单一的模块，实现"配置只做配置"的架构原则。

## 📁 拆分后的文件结构

```
config/
├── __init__.py                     # 统一导入接口
├── data_models.py                  # 🔸 纯数据模型（新）
├── config_manager.py               # 🔸 配置管理器（新）
└── legacy_config_models.py         # ⚠️ 重命名的原文件（待废弃）

services/
├── path_service.py                 # 🆕 路径验证服务
├── config_service.py               # 🆕 配置操作服务
└── history_service.py              # 🆕 历史记录服务

utils/
└── config_utils.py                 # 🆕 配置工具函数
```

## 🔸 模块职责划分

### 1. config/data_models.py - 纯数据模型
**职责**: 只包含数据结构定义，无任何业务逻辑

```python
@dataclass
class CoreConfig:
    """核心配置数据模型"""
    version: str
    default_language: str
    source_language: str
    debug_mode: bool

@dataclass
class UserConfig:
    """用户配置数据模型"""
    general: GeneralConfig
    extraction: ExtractionConfig
    api: APIConfig
    remembered_paths: Dict[str, str]
    path_history: Dict[str, Dict[str, Any]]

@dataclass
class UnifiedConfig:
    """统一配置数据容器"""
    core: CoreConfig
    user: UserConfig
    version: str
```

### 2. config/config_manager.py - 配置管理器
**职责**: 配置的加载、保存、重置等基本操作

```python
class ConfigManager:
    """配置管理器 - 只负责配置的CRUD操作"""

    def load_config(self, path: str) -> UnifiedConfig:
        """加载配置文件"""

    def save_config(self, config: UnifiedConfig, path: str) -> None:
        """保存配置文件"""

    def reset_config(self) -> UnifiedConfig:
        """重置为默认配置"""

    def validate_config(self, config: UnifiedConfig) -> bool:
        """验证配置完整性"""
```

### 3. services/path_service.py - 路径验证服务
**职责**: 路径验证、文件检查等与文件系统相关的业务逻辑

```python
class PathValidationService:
    """路径验证服务"""

    def validate_path(self, path: str, validator_type: str) -> PathValidationResult:
        """验证路径有效性"""

    def get_path_with_validation(self, config: PathConfig) -> Optional[str]:
        """获取并验证路径"""

    def check_file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
```

### 4. services/config_service.py - 配置操作服务
**职责**: 配置的高级操作，如导入导出、合并等

```python
class ConfigService:
    """配置操作服务"""

    def __init__(self, manager: ConfigManager):
        self.manager = manager

    def export_config(self, config: UnifiedConfig, export_path: str) -> bool:
        """导出配置到文件"""

    def import_config(self, import_path: str) -> UnifiedConfig:
        """从文件导入配置"""

    def merge_configs(self, base: UnifiedConfig, override: UnifiedConfig) -> UnifiedConfig:
        """合并配置"""
```

### 5. services/history_service.py - 历史记录服务
**职责**: 路径历史记录的管理

```python
class HistoryService:
    """历史记录服务"""

    def add_to_history(self, path_type: str, path: str, config: UnifiedConfig) -> None:
        """添加到历史记录"""

    def get_history(self, path_type: str, config: UnifiedConfig) -> List[str]:
        """获取历史记录"""

    def get_last_used_path(self, path_type: str, config: UnifiedConfig) -> Optional[str]:
        """获取最后使用的路径"""

    def remember_path(self, path_type: str, path: str, config: UnifiedConfig) -> None:
        """记住路径"""
```

## 🔄 迁移步骤

### Phase 1: 创建新模块 ✅ 准备执行
1. 创建 `config/data_models.py` - 迁移纯数据模型
2. 创建 `config/config_manager.py` - 迁移配置CRUD操作
3. 创建 `services/path_service.py` - 迁移路径验证逻辑
4. 创建 `services/config_service.py` - 迁移配置业务操作
5. 创建 `services/history_service.py` - 迁移历史记录管理

### Phase 2: 更新依赖
1. 更新 `config/__init__.py` 导入新模块
2. 更新 `interaction_manager.py` 使用新服务
3. 更新其他模块的导入

### Phase 3: 清理旧代码
1. 将 `config_models.py` 重命名为 `legacy_config_models.py`
2. 添加废弃警告
3. 验证所有功能正常
4. 删除旧文件

## 🎯 预期成果

1. **职责清晰**: 每个模块只负责一种类型的功能
2. **易于测试**: 纯数据模型和业务逻辑分离
3. **易于维护**: 配置变更不会影响业务逻辑
4. **符合SOLID原则**: 单一职责、依赖倒置
5. **类型安全**: 完整的类型注解和验证

## 🔗 模块依赖关系

```
interaction_manager.py
    ↓
services/config_service.py
    ↓
config/config_manager.py
    ↓
config/data_models.py

services/path_service.py → services/history_service.py
    ↓
config/data_models.py
```

这样的架构确保了配置模块只负责数据存储和基本操作，而所有业务逻辑都被移到了相应的服务层。
