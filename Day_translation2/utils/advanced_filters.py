"""
Day Translation 2 - 高级过滤规则管理器

从day_translation迁移的统一过滤规则管理器，提供企业级的文本过滤功能。
遵循提示文件标准：PEP 8规范、具体异常处理、游戏UI术语统一。

特性:
- 全面的RimWorld字段支持
- 智能非文本内容识别  
- 灵活的规则系统
- 数据持久化支持
"""

import re
import logging
import os
import json
from typing import Set, List, Dict, Any, Optional, Union, Callable
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    # 尝试相对导入 (包内使用)
    from ..models.exceptions import ValidationError, ConfigError
    from ..models.config_models import FilterConfig
except ImportError:
    # 回退到绝对导入 (直接运行时)
    from models.exceptions import ValidationError, ConfigError
    from models.config_models import FilterConfig


class AdvancedFilterRules:
    """高级过滤规则管理器 - Day_translation2版本"""
    
    # 扩展默认字段 - RimWorld专用
    DEFAULT_FIELDS = {
        # 基础字段
        'label', 'description', 'labelShort', 'descriptionShort',
        'title', 'text', 'message', 'tooltip', 'baseDesc',
        'skillDescription', 'backstoryDesc', 'jobString',
        'gerundLabel', 'verb', 'deathMessage', 'summary',
        'note', 'flavor', 'quote', 'caption',
        # RimWorld 特有字段
        'RMBLabel', 'rulesStrings', 'labelNoun', 'gerund', 
        'reportString', 'skillLabel', 'pawnLabel', 'titleShort',
        # 覆盖字段
        'reportStringOverride', 'overrideReportString',
        'overrideTooltip', 'overrideLabel', 'overrideDescription',
        'overrideLabelShort', 'overrideDescriptionShort',
        'overrideTitle', 'overrideText', 'overrideMessage',
        'overrideBaseDesc', 'overrideSkillDescription',
        'overrideBackstoryDesc', 'overrideJobString', 'overrideGerundLabel',
        'overrideVerb', 'overrideDeathMessage', 'overrideSummary',
        'overrideNote', 'overrideFlavor', 'overrideQuote', 'overrideCaption',
        # 自定义字段
        'customLabel', 'customDescription', 'customTooltip',
        'customMessage', 'customText', 'customTitle',
        'customBaseDesc', 'customSkillDescription', 'customBackstoryDesc',
        'customJobString', 'customGerundLabel', 'customVerb',
        'customDeathMessage', 'customSummary', 'customNote',
        'customFlavor', 'customQuote', 'customCaption'
    }
    
    # 扩展忽略字段
    IGNORE_FIELDS = {
        # 基础字段
        'defName', 'id', 'cost', 'damage', 'x', 'y', 'z',
        'width', 'height', 'priority', 'count', 'index',
        'version', 'url', 'path', 'file', 'hash', 'key',
        # 数值字段
        'order', 'weight', 'value', 'amount', 'quantity',
        'duration', 'cooldown', 'range', 'radius', 'angle',
        'speed', 'force', 'power', 'energy', 'health',
        'armor', 'shield', 'resistance', 'penetration',
        'accuracy', 'evasion', 'critChance', 'critDamage',
        'dodgeChance', 'blockChance', 'parryChance',
        # 技术字段
        'guid', 'uuid', 'timestamp', 'date', 'time',
        'checksum', 'signature', 'token', 'secret',
        'password', 'salt', 'encryption', 'compression',
        'encoding', 'format', 'type', 'category', 'tag',
        'group', 'class', 'style'
    }
    
    # 非文本模式 - 智能识别
    NON_TEXT_PATTERNS = [
        # 数字模式
        r'^\d+$',  # 整数
        r'^-?\d+\.\d+$',  # 浮点数
        r'^[0-9a-fA-F]+$',  # 十六进制
        r'^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$',  # 科学计数法
        r'^\d+[kKmMgGtT]?$',  # 带单位的数字
        # 空白模式
        r'^\s*$',  # 纯空白
        r'^[\s\-_]+$',  # 分隔符
        # 布尔值
        r'^(true|false)$',  # 布尔值
        r'^(yes|no)$',  # 是/否
        r'^(on|off)$',  # 开/关
        # 路径模式
        r'^[A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-]+$',  # 文件名
        r'^[A-Za-z0-9_\-/\\\.]+[/\\][A-Za-z0-9_\-\.]+$',  # 路径
        # URL模式
        r'https?://[^\s<>"]+',  # HTTP URL
        r'www\.[^\s<>"]+',  # www链接
        # 标识符模式
        r'^[A-Za-z0-9_\-]+#[A-Za-z0-9_\-]+$',  # 带#的标识符
        r'^[A-Za-z0-9_\-]+@[A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-]+$',  # 邮箱格式
        r'^[A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+$',  # 带:的标识符
    ]
    
    # 字段类型定义
    FIELD_TYPES = {
        "translatable": "需要翻译的字段",
        "ignored": "忽略的字段",
        "conditional": "条件性翻译的字段",
        "reference": "引用类型的字段",
        "format": "格式化字符串字段",
        "plural": "复数形式字段",
        "gender": "性别相关字段",
        "context": "上下文相关字段"
    }
    
    # 字段分组定义
    FIELD_GROUPS = {
        "basic": {
            "name": "基础字段",
            "description": "基本的文本字段",
            "fields": {'label', 'description', 'text', 'message'}
        },
        "ui": {
            "name": "界面字段", 
            "description": "用户界面相关字段",
            "fields": {'tooltip', 'title', 'caption', 'button', 'menu'}
        },
        "game": {
            "name": "游戏字段",
            "description": "游戏内容相关字段", 
            "fields": {'skillDescription', 'backstoryDesc', 'jobString', 'deathMessage'}
        },
        "override": {
            "name": "覆盖字段",
            "description": "覆盖默认值的字段",
            "fields": set()  # 在初始化时动态填充
        },
        "custom": {
            "name": "自定义字段",
            "description": "用户自定义字段",
            "fields": set()  # 在初始化时动态填充
        }
    }
    
    # 规则优先级定义
    PRIORITY_LEVELS = {
        "highest": 100,  # 最高优先级
        "high": 75,      # 高优先级
        "normal": 50,    # 普通优先级
        "low": 25,       # 低优先级
        "lowest": 0      # 最低优先级
    }
    
    def __init__(self, default_fields: Optional[Set[str]] = None,
                 ignore_fields: Optional[Set[str]] = None,
                 non_text_patterns: Optional[List[str]] = None,
                 parent_rules: Optional['AdvancedFilterRules'] = None):
        """
        初始化高级过滤规则
        
        Args:
            default_fields: 默认翻译字段集合
            ignore_fields: 忽略字段集合
            non_text_patterns: 非文本模式列表
            parent_rules: 父规则集
            
        Raises:
            ValidationError: 当规则验证失败时
        """
        try:
            self.parent_rules = parent_rules
            self.default_fields = default_fields or self.DEFAULT_FIELDS.copy()
            self.ignore_fields = ignore_fields or self.IGNORE_FIELDS.copy()
            self.non_text_patterns = non_text_patterns or self.NON_TEXT_PATTERNS.copy()
            
            # 初始化规则映射
            self.field_types: Dict[str, str] = {}
            self.field_groups: Dict[str, Dict[str, Any]] = {}
            self.field_priorities: Dict[str, int] = {}
            self.conditional_rules: Dict[str, Callable[[str], bool]] = {}
            
            # 验证和初始化
            self._validate_rules()
            self._initialize_field_groups()
            self._initialize_field_types()
            self._initialize_field_priorities()
            
            logging.debug(f"高级过滤规则初始化完成: {len(self.default_fields)} 个默认字段")
            
        except Exception as e:
            raise ValidationError(f"过滤规则初始化失败: {str(e)}")
    
    def _validate_rules(self) -> None:
        """验证规则的有效性"""
        if not isinstance(self.default_fields, set):
            raise ValidationError("default_fields 必须是集合类型")
        if not isinstance(self.ignore_fields, set):
            raise ValidationError("ignore_fields 必须是集合类型")
        if not isinstance(self.non_text_patterns, list):
            raise ValidationError("non_text_patterns 必须是列表类型")
            
        # 验证字段名
        for field in self.default_fields | self.ignore_fields:
            if not isinstance(field, str) or not field.strip():
                raise ValidationError(f"无效的字段名: {field}")
            if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', field):
                logging.warning(f"字段名格式可能有问题: {field}")
                
        # 验证正则表达式
        for pattern in self.non_text_patterns:
            if not isinstance(pattern, str) or not pattern.strip():
                raise ValidationError(f"无效的正则表达式: {pattern}")
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValidationError(f"正则表达式编译失败: {pattern}, 错误: {e}")
                
        # 检查字段冲突
        conflicts = self.default_fields & self.ignore_fields
        if conflicts:
            logging.warning(f"发现字段冲突: {conflicts}")
    
    def _initialize_field_groups(self) -> None:
        """初始化字段分组"""
        self.field_groups = {}
        for group_id, group_info in self.FIELD_GROUPS.items():
            self.field_groups[group_id] = {
                "name": group_info["name"],
                "description": group_info["description"],
                "fields": set(group_info["fields"])
            }
        
        # 动态填充override和custom分组
        override_fields = {f for f in self.default_fields if f.startswith('override')}
        custom_fields = {f for f in self.default_fields if f.startswith('custom')}
        
        self.field_groups["override"]["fields"] = override_fields
        self.field_groups["custom"]["fields"] = custom_fields
    
    def _initialize_field_types(self) -> None:
        """初始化字段类型"""
        # 设置默认字段类型
        for field in self.default_fields:
            if isinstance(field, str):
                self.field_types[field] = "translatable"
                
        # 设置忽略字段类型
        for field in self.ignore_fields:
            if isinstance(field, str):
                self.field_types[field] = "ignored"
    
    def _initialize_field_priorities(self) -> None:
        """初始化字段优先级"""
        # 设置默认优先级
        for field in self.default_fields:
            self.field_priorities[field] = self.PRIORITY_LEVELS["normal"]
            
        # 忽略字段设置最低优先级  
        for field in self.ignore_fields:
            self.field_priorities[field] = self.PRIORITY_LEVELS["lowest"]
    
    def should_translate_field(self, field_name: str, field_value: str = "") -> bool:
        """
        检查字段是否应该翻译
        
        Args:
            field_name: 字段名
            field_value: 字段值（用于条件判断）
            
        Returns:
            bool: 是否应该翻译
        """
        # 检查字段类型
        field_type = self.get_field_type(field_name)
        if field_type == "ignored":
            return False
            
        # 检查条件规则
        if field_type == "conditional":
            condition = self.conditional_rules.get(field_name)
            if condition and not condition(field_value):
                return False
                
        # 检查优先级
        priority = self.get_field_priority(field_name)
        if priority == self.PRIORITY_LEVELS["lowest"]:
            return False
            
        # 检查非文本模式
        if field_value and self.is_non_text_content(field_value):
            return False
            
        return field_name in self.default_fields
    
    def is_non_text_content(self, content: str) -> bool:
        """
        检查内容是否为非文本内容
        
        Args:
            content: 待检查的内容
            
        Returns:
            bool: 是否为非文本内容
        """
        if not content or not isinstance(content, str):
            return True
            
        content = content.strip()
        if not content:
            return True
            
        # 检查非文本模式
        for pattern in self.non_text_patterns:
            try:
                if re.match(pattern, content, re.IGNORECASE):
                    return True
            except re.error:
                continue
                
        return False
    
    def get_field_type(self, field: str) -> str:
        """获取字段类型"""
        if field in self.field_types:
            return self.field_types[field]
        if self.parent_rules:
            return self.parent_rules.get_field_type(field)
        return "unknown"
    
    def get_field_priority(self, field: str) -> int:
        """获取字段优先级"""
        if field in self.field_priorities:
            return self.field_priorities[field]
        if self.parent_rules:
            return self.parent_rules.get_field_priority(field)
        return self.PRIORITY_LEVELS["normal"]
    
    def add_field(self, field: str, field_type: str = "translatable", 
                  priority: str = "normal") -> None:
        """
        添加新字段
        
        Args:
            field: 字段名
            field_type: 字段类型
            priority: 优先级
        """
        if field_type == "translatable":
            self.default_fields.add(field)
        elif field_type == "ignored":
            self.ignore_fields.add(field)
            
        self.field_types[field] = field_type
        self.field_priorities[field] = self.PRIORITY_LEVELS.get(priority, 50)
    
    def remove_field(self, field: str) -> None:
        """移除字段"""
        self.default_fields.discard(field)
        self.ignore_fields.discard(field)
        self.field_types.pop(field, None)
        self.field_priorities.pop(field, None)
        self.conditional_rules.pop(field, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取规则统计信息"""
        return {
            'default_fields_count': len(self.default_fields),
            'ignore_fields_count': len(self.ignore_fields),
            'non_text_patterns_count': len(self.non_text_patterns),
            'field_types_count': len(self.field_types),
            'field_groups_count': len(self.field_groups),
            'field_priorities_count': len(self.field_priorities),
            'conditional_rules_count': len(self.conditional_rules),
            'field_type_distribution': {
                field_type: len([f for f, t in self.field_types.items() if t == field_type])
                for field_type in self.FIELD_TYPES
            }
        }
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """
        获取过滤器统计信息
        
        Returns:
            Dict[str, Any]: 包含统计信息的字典
        """
        return {
            "default_fields_count": len(self.default_fields),
            "ignore_fields_count": len(self.ignore_fields), 
            "non_text_patterns_count": len(self.non_text_patterns),
            "total_rules": len(self.default_fields) + len(self.ignore_fields) + len(self.non_text_patterns)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'version': '2.0.0',
            'default_fields': sorted(list(self.default_fields)),
            'ignore_fields': sorted(list(self.ignore_fields)),
            'non_text_patterns': self.non_text_patterns,
            'field_types': self.field_types,
            'field_groups': {
                group_id: {
                    'name': info['name'],
                    'description': info['description'],
                    'fields': sorted(list(info['fields']))
                }
                for group_id, info in self.field_groups.items()
            },
            'field_priorities': self.field_priorities,
            'stats': self.get_stats()
        }
    
    def save_to_file(self, file_path: str, format: str = 'json') -> None:
        """
        保存规则到文件
        
        Args:
            file_path: 文件路径
            format: 文件格式（'json' 或 'yaml'）
        """
        try:
            data = self.to_dict()
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            elif format.lower() == 'yaml' and yaml:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
            else:
                raise ConfigError(f"不支持的文件格式: {format}")
                
            logging.info(f"过滤规则已保存到: {file_path}")
            
        except Exception as e:
            raise ConfigError(f"保存过滤规则失败: {str(e)}")
    
    @classmethod
    def load_from_file(cls, file_path: str, format: str = 'json') -> 'AdvancedFilterRules':
        """
        从文件加载规则
        
        Args:
            file_path: 文件路径
            format: 文件格式
            
        Returns:
            AdvancedFilterRules: 规则对象
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if format.lower() == 'json':
                    data = json.load(f)
                elif format.lower() == 'yaml' and yaml:
                    data = yaml.safe_load(f)
                else:
                    raise ConfigError(f"不支持的文件格式: {format}")
            
            rules = cls(
                default_fields=set(data.get('default_fields', [])),
                ignore_fields=set(data.get('ignore_fields', [])),
                non_text_patterns=data.get('non_text_patterns', [])
            )
            
            # 加载扩展信息
            rules.field_types.update(data.get('field_types', {}))
            rules.field_priorities.update(data.get('field_priorities', {}))
            
            logging.info(f"过滤规则从 {file_path} 加载成功")
            return rules
            
        except Exception as e:
            raise ConfigError(f"加载过滤规则失败: {str(e)}")
    
    def __str__(self) -> str:
        """返回规则的字符串表示"""
        stats = self.get_stats()
        return (f"AdvancedFilterRules("
                f"默认字段: {stats['default_fields_count']}, "
                f"忽略字段: {stats['ignore_fields_count']}, "
                f"模式: {stats['non_text_patterns_count']})")
    def should_translate_keyed(self, text: str, key: str = "") -> bool:
        """
        检查Keyed翻译项是否应该被翻译
        
        对于Keyed翻译，不限制字段类型，因为Keyed使用自定义标签名
        只进行基础的文本有效性检查
        
        Args:
            text: 文本内容
            key: 翻译键名
            
        Returns:
            bool: 是否应该翻译
        """
        # 基础检查 - 对于Keyed翻译比较宽松
        if not text or not isinstance(text, str):
            return False
        
        text = text.strip()
        if not text:
            return False
        
        # 从key中提取字段名（仅用于ignore_fields检查）
        field_name = self._extract_field_name(key)
        
        # 检查是否在忽略字段中
        if field_name in self.ignore_fields:
            return False
        
        # 检查是否为纯数字（除非很短的数字可能是版本号等）
        if text.isdigit() and len(text) > 3:
            return False
        
        # 检查非文本模式（较宽松）
        import re
        for pattern in self.non_text_patterns:
            if re.match(pattern, text):
                return False
        
        # Keyed翻译不限制default_fields，允许所有其他文本
        return True
    
    def should_translate_def_field(self, text: str, field: str, def_type: str = "") -> bool:
        """
        检查DefInjected字段是否应该被翻译
        
        对于DefInjected翻译，需要检查字段是否在默认字段列表中
        
        Args:
            text: 文本内容
            field: 字段名
            def_type: 定义类型（如ThingDef, PawnKindDef等）
            
        Returns:
            bool: 是否应该翻译
        """
        # 基础检查
        if not self._is_valid_text(text):
            return False
        
        # 提取字段名
        field_name = self._extract_field_name(field)
        
        # 检查是否在忽略字段中
        if field_name in self.ignore_fields:
            return False
        
        # DefInjected需要检查是否在默认字段中
        if self.default_fields and field_name not in self.default_fields:
            return False
        
        return True
    
    def should_translate_corpus(self, source_text: str, target_text: str = "") -> bool:
        """
        检查平行语料是否应该被翻译
        
        Args:
            source_text: 源文本
            target_text: 目标文本
            
        Returns:
            bool: 是否应该翻译
        """
        # 基础检查
        if not self._is_valid_text(source_text):
            return False
        
        # 语料库翻译的特殊逻辑
        # 检查是否已有翻译
        if target_text and target_text.strip():
            # 已有翻译，可能需要更新
            return True
        
        return True
    
    def _extract_field_name(self, key: str) -> str:
        """
        从key路径中智能提取字段名
        
        模仿原ContentFilter的逻辑：从后往前找到第一个非数字的部分
        
        Args:
            key: 键名路径，如 "ThingDef.0.label" 或 "UI_Confirm"
            
        Returns:
            str: 提取的字段名
        """
        if not key:
            return ""
        
        parts = key.split('.')
        
        # 从后往前遍历，找到第一个非数字的部分
        for i in range(len(parts) - 1, -1, -1):
            if not parts[i].isdigit():
                return parts[i]
        
        # 如果都是数字，返回最后一部分
        return parts[-1] if parts else key
    
    def _is_valid_text(self, text: str) -> bool:
        """
        检查文本是否有效（非空、非纯数字等）
        
        Args:
            text: 待检查的文本
            
        Returns:
            bool: 文本是否有效
        """
        if not text or not isinstance(text, str):
            return False
        
        text = text.strip()
        if not text:
            return False
        
        # 检查是否为纯数字
        if text.isdigit():
            return False
        
        # 检查是否为数字表达式
        import re
        if re.match(r'^[0-9\.\-\+\s]+$', text):
            return False
        
        # 检查非文本模式
        for pattern in self.non_text_patterns:
            if re.match(pattern, text):
                return False
        
        return True

# 兼容性函数，支持旧代码调用
def get_unified_filter_rules() -> AdvancedFilterRules:
    """获取统一过滤规则实例（兼容性函数）"""
    return AdvancedFilterRules()


# 导出主要接口
__all__ = [
    'AdvancedFilterRules',
    'get_unified_filter_rules'
]
