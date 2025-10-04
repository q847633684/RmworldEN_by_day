# 配置文件目录

本目录包含翻译系统的配置文件，已从项目根目录的 `config/` 迁移到 `user_config/config/`。

## 📁 文件说明

### `translation_fields.yaml`
- **用途**: 翻译字段配置
- **内容**: 定义需要翻译的字段、忽略的字段、非文本模式等
- **加载**: 由 `SystemConfig` 自动加载

### `adult_dictionary.yaml` 和 `game_dictionary.yaml`
- **用途**: 翻译词典配置
- **内容**: 常用词汇的翻译对照关系
- **用途**: 提供翻译参考和一致性检查

## 🔄 迁移说明

配置文件已从项目根目录的 `config/` 目录迁移到 `user_config/config/` 目录，以实现配置系统的统一管理。

### 迁移的好处

1. **统一管理**: 所有配置相关文件都在 `user_config/` 目录下
2. **模块化**: 配置系统更加模块化和独立
3. **易于维护**: 配置文件和配置代码在同一个目录结构下

### 代码更新

- `SystemConfig._load_translation_rules()` 方法已更新配置文件路径
- 从 `Path(__file__).parent.parent.parent / "config"` 改为 `Path(__file__).parent.parent / "config"`

## 📋 使用方法

配置文件会被 `SystemConfig` 自动加载，无需手动操作。如需修改配置：

1. 直接编辑 YAML 文件
2. 重启应用程序或重新加载配置
3. 配置会自动生效

## 🛠️ 开发说明

如需添加新的配置文件，请：

1. 将文件放在此目录下
2. 在相应的配置类中添加加载逻辑
3. 更新此 README 文件的说明
