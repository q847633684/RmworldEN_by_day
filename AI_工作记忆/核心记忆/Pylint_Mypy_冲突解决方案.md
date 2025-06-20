# Day_translation2 - Pylint vs Mypy 冲突解决配置

## 配置策略：分层质量检查

### 基础层：Pylint (代码质量)
- 专注：代码风格、逻辑错误、最佳实践
- 配置：相对宽松，允许必要的技术债务
- 目标：团队协作和可维护性

### 严格层：Mypy (类型安全)
- 专注：类型安全、接口契约
- 配置：逐步严格化，生产环境必须
- 目标：运行时错误预防

### 实践解决方案

#### 1. type: ignore 标准化
```python
# ✅ 推荐：明确指定错误类型
from ..models import TranslationData  # type: ignore[attr-defined]

# ❌ 避免：通用忽略
from ..models import TranslationData  # type: ignore
```

#### 2. Optional参数标准化
```python
# ✅ Mypy友好
def func(param: Optional[str] = None) -> None:
    pass

# ❌ Mypy抱怨
def func(param: str = None) -> None:
    pass
```

#### 3. 返回类型注解优先级
```python
# ✅ 两者都满意
def process_data(self) -> None:
    """处理数据"""
    pass

# ❌ Mypy抱怨，Pylint可能允许
def process_data(self):
    """处理数据"""
    pass
```

#### 4. 工具使用顺序
1. **开发阶段**: 只运行Pylint，专注代码质量
2. **提交前**: 运行Mypy，修复类型错误
3. **CI/CD**: 两者都必须通过

#### 5. 渐进式类型检查
```ini
# mypy.ini 配置示例
[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True
warn_unused_ignores = False  # 降低与Pylint冲突
no_implicit_optional = True

# 按模块逐步严格化
[mypy-tests.*]
ignore_errors = True

[mypy-utils.*]
disallow_untyped_defs = False  # 逐步迁移

[mypy-core.*]
disallow_untyped_defs = True   # 核心模块严格
```

### 当前项目最佳实践
1. **继续使用quality_check.py** - 已经平衡了两者
2. **Flake8作为快速反馈** - 语法和基础问题
3. **Pylint用于代码审查** - 质量和风格
4. **Mypy用于类型安全** - 生产就绪验证

### 冲突解决原则
- **安全优先**: 类型安全问题听Mypy
- **可读性优先**: 代码风格问题听Pylint
- **实用主义**: 允许合理的type: ignore
- **渐进改进**: 不强求一次性完美
