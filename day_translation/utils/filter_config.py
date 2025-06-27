import re
import logging
import os
import json
from typing import Set, List, Dict, Any, Optional, Union, Callable
from pathlib import Path

class UnifiedFilterRules:
    """统一的过滤规则管理器"""
    
    # 扩展默认字段
    DEFAULT_FIELDS = {
        # 基础字段
        'label', 'description', 'labelShort', 'descriptionShort',
        'title', 'text', 'message', 'tooltip', 'baseDesc',
        'skillDescription', 'backstoryDesc', 'jobString',
        'gerundLabel', 'verb', 'deathMessage', 'summary',
        'note', 'flavor', 'quote', 'caption',
        # RimWorld 特有字段（参考 Day_EN）
        'RMBLabel', 'rulesStrings', 'labelNoun', 'gerund', 
        'reportString', 'skillLabel', 'pawnLabel', 'titleShort',
        # 新增字段
        'reportStringOverride', 'overrideReportString',
        'overrideTooltip', 'overrideLabel', 'overrideDescription',
        'overrideLabelShort', 'overrideDescriptionShort',
        'overrideTitle', 'overrideText', 'overrideMessage',
        'overrideTooltip', 'overrideBaseDesc', 'overrideSkillDescription',
        'overrideBackstoryDesc', 'overrideJobString', 'overrideGerundLabel',
        'overrideVerb', 'overrideDeathMessage', 'overrideSummary',
        'overrideNote', 'overrideFlavor', 'overrideQuote', 'overrideCaption',
        # 特殊字段
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
        # 新增字段
        'order', 'weight', 'value', 'amount', 'quantity',
        'duration', 'cooldown', 'range', 'radius', 'angle',
        'speed', 'force', 'power', 'energy', 'health',
        'armor', 'shield', 'resistance', 'penetration',
        'accuracy', 'evasion', 'critChance', 'critDamage',
        'dodgeChance', 'blockChance', 'parryChance',
        # 特殊字段
        'guid', 'uuid', 'timestamp', 'date', 'time',
        'checksum', 'signature', 'token', 'secret',
        'password', 'salt', 'hash', 'encryption',
        'compression', 'encoding', 'format', 'type',
        'category', 'tag', 'group', 'class', 'style'
    }
    
    # 改进非文本模式
    NON_TEXT_PATTERNS = [
        # 数字模式
        r'^\d+$',  # 整数
        r'^-?\d+\.\d+$',  # 浮点数
        r'^[0-9a-fA-F]+$',  # 十六进制
        r'^[+-]?(\d+\.?\d*|\.\d+)$',  # 科学计数法
        r'^\d+[kKmMgGtT]?$',  # 带单位的数字
        # 空白模式
        r'^\s*$',  # 纯空白
        r'^[\s\-_]+$',  # 分隔符
        # 布尔值
        r'^true$|^false$',  # 布尔值
        r'^yes$|^no$',  # 是/否
        r'^on$|^off$',  # 开/关
        # 路径模式
        r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$',  # 文件名
        r'^[A-Za-z0-9_-]+/[A-Za-z0-9_-]+$',  # 路径
        r'^[A-Za-z0-9_-]+\\[A-Za-z0-9_-]+$',  # Windows路径
        # URL模式
        r'https?://[^\s<>"]+|www\.[^\s<>"]+',  # URL
        r'^[A-Za-z0-9_-]+\.(com|org|net|edu|gov|io|co|uk|cn|jp|ru|de|fr|it|es|nl|be|ch|at|dk|se|no|fi|pl|cz|hu|ro|bg|gr|tr|il|sa|ae|in|br|mx|ar|cl|co|pe|ve|za|au|nz|sg|my|id|ph|vn|th|kr|tw|hk|mo)$',  # 域名
        # 文件模式
        r'^[A-Za-z0-9_-]+\.(xml|json|txt|csv|ini|cfg|conf|config|yaml|yml|toml|md|markdown|rst|log|dat|bin|exe|dll|so|dylib|py|pyc|pyo|pyd|java|class|jar|war|ear|zip|rar|7z|tar|gz|bz2|xz|iso|img|vhd|vmdk|ova|ovf|qcow2|raw|vdi|vbox|vmx|vhd|vhdx|vmdk|vmsd|vmsn|vmss|vmtm|vmx|vmxf|nvram|vmem|vswp|vmtx|vmtm|vmsd|vmsn|vmss|vmtm|vmx|vmxf|nvram|vmem|vswp|vmtx)$',  # 文件扩展名
        # 特殊模式
        r'^[A-Za-z0-9_-]+#[A-Za-z0-9_-]+$',  # 带#的标识符
        r'^[A-Za-z0-9_-]+@[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$',  # 邮箱
        r'^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+$',  # 带:的标识符
        r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$',  # 带.的标识符
        r'^[A-Za-z0-9_-]+\-[A-Za-z0-9_-]+\-[A-Za-z0-9_-]+$',  # 带-的标识符
        r'^[A-Za-z0-9_-]+\_[A-Za-z0-9_-]+\_[A-Za-z0-9_-]+$'  # 带_的标识符
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
            "fields": {f for f in DEFAULT_FIELDS if f.startswith('override')}
        },
        "custom": {
            "name": "自定义字段",
            "description": "用户自定义字段",
            "fields": {f for f in DEFAULT_FIELDS if f.startswith('custom')}
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
                 parent_rules: Optional['UnifiedFilterRules'] = None):
        """
        初始化过滤规则
        
        Args:
            default_fields (Optional[Set[str]]): 默认字段集合
            ignore_fields (Optional[Set[str]]): 忽略字段集合
            non_text_patterns (Optional[List[str]]): 非文本模式列表
            parent_rules (Optional[UnifiedFilterRules]): 父规则集
        """
        self.parent_rules = parent_rules
        self.default_fields = default_fields or self.DEFAULT_FIELDS
        self.ignore_fields = ignore_fields or self.IGNORE_FIELDS
        self.non_text_patterns = non_text_patterns or self.NON_TEXT_PATTERNS
        self.field_types = {}  # 字段类型映射
        self.field_groups = {}  # 字段分组映射
        self.field_priorities = {}  # 字段优先级映射
        self.conditional_rules = {}  # 条件规则映射
        self._validate_rules()
        self._initialize_field_types()
        self._initialize_field_groups()
        self._initialize_field_priorities()
        
    def _initialize_field_types(self) -> None:
        """初始化字段类型"""
        # 设置默认字段类型 - 添加安全检查
        try:
            default_fields = self.default_fields
            if hasattr(default_fields, '__iter__') and not isinstance(default_fields, str):
                for field in default_fields:
                    if isinstance(field, str):
                        self.field_types[field] = "translatable"
            else:
                logging.warning("default_fields 不可迭代: %s", type(default_fields))
        except Exception as e:
            logging.error("初始化默认字段类型时出错: %s", e)
            
        try:
            ignore_fields = self.ignore_fields  
            if hasattr(ignore_fields, '__iter__') and not isinstance(ignore_fields, str):
                for field in ignore_fields:
                    if isinstance(field, str):
                        self.field_types[field] = "ignored"
            else:
                logging.warning("ignore_fields 不可迭代: %s", type(ignore_fields))
        except Exception as e:
            logging.error("初始化忽略字段类型时出错: %s", e)
            
    def _initialize_field_groups(self) -> None:
        """初始化字段分组"""
        for group_id, group_info in self.FIELD_GROUPS.items():
            self.field_groups[group_id] = {
                "name": group_info["name"],
                "description": group_info["description"],
                "fields": set(group_info["fields"])
            }
            
    def _initialize_field_priorities(self) -> None:
        """初始化字段优先级"""
        # 设置默认优先级 - 添加安全检查
        try:
            default_fields = self.default_fields
            if hasattr(default_fields, '__iter__') and not isinstance(default_fields, str):
                for field in default_fields:
                    if isinstance(field, str):
                        self.field_priorities[field] = self.PRIORITY_LEVELS["normal"]
        except Exception as e:
            logging.error("初始化默认字段优先级时出错: %s", e)
            
        try:
            ignore_fields = self.ignore_fields
            if hasattr(ignore_fields, '__iter__') and not isinstance(ignore_fields, str):
                for field in ignore_fields:
                    if isinstance(field, str):
                        self.field_priorities[field] = self.PRIORITY_LEVELS["lowest"]
        except Exception as e:
            logging.error("初始化忽略字段优先级时出错: %s", e)
            
    def _validate_rules(self) -> None:
        """验证规则的有效性"""
        if not isinstance(self.default_fields, set):
            raise ValueError("default_fields 必须是集合类型")
        if not isinstance(self.ignore_fields, set):
            raise ValueError("ignore_fields 必须是集合类型")
        if not isinstance(self.non_text_patterns, list):
            raise ValueError("non_text_patterns 必须是列表类型")
            
        # 验证字段名
        for field in self.default_fields | self.ignore_fields:
            if not isinstance(field, str):
                raise ValueError(f"字段名必须是字符串类型: {field}")
            if not field.strip():
                raise ValueError("字段名不能为空")
            if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', field):
                raise ValueError(f"无效的字段名格式: {field}")
                
        # 验证正则表达式
        for pattern in self.non_text_patterns:
            if not isinstance(pattern, str):
                raise ValueError(f"正则表达式必须是字符串类型: {pattern}")
            if not pattern.strip():
                raise ValueError("正则表达式不能为空")
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f"无效的正则表达式: {pattern}, 错误: {e}")
                
        # 检查字段冲突
        conflicts = self.default_fields & self.ignore_fields
        if conflicts:
            raise ValueError(f"字段冲突: {conflicts}")
            
        # 验证父规则
        if self.parent_rules and not isinstance(self.parent_rules, UnifiedFilterRules):
            raise ValueError("parent_rules 必须是 UnifiedFilterRules 类型")
            
    def get_field_type(self, field: str) -> str:
        """
        获取字段类型
        
        Args:
            field (str): 字段名
            
        Returns:
            str: 字段类型
        """
        if field in self.field_types:
            return self.field_types[field]
        if self.parent_rules:
            return self.parent_rules.get_field_type(field)
        return "unknown"
        
    def set_field_type(self, field: str, field_type: str) -> None:
        """
        设置字段类型
        
        Args:
            field (str): 字段名
            field_type (str): 字段类型
        """
        if field_type not in self.FIELD_TYPES:
            raise ValueError(f"无效的字段类型: {field_type}")
        self.field_types[field] = field_type
        self._validate_rules()
        
    def get_field_group(self, field: str) -> Optional[str]:
        """
        获取字段所属分组
        
        Args:
            field (str): 字段名
            
        Returns:
            Optional[str]: 分组ID
        """
        for group_id, group_info in self.field_groups.items():
            if field in group_info["fields"]:
                return group_id
        if self.parent_rules:
            return self.parent_rules.get_field_group(field)
        return None
        
    def add_to_group(self, field: str, group_id: str) -> None:
        """
        将字段添加到分组
        
        Args:
            field (str): 字段名
            group_id (str): 分组ID
        """
        if group_id not in self.FIELD_GROUPS:
            raise ValueError(f"无效的分组ID: {group_id}")
        if group_id not in self.field_groups:
            self.field_groups[group_id] = {
                "name": self.FIELD_GROUPS[group_id]["name"],
                "description": self.FIELD_GROUPS[group_id]["description"],
                "fields": set()
            }
        self.field_groups[group_id]["fields"].add(field)
        
    def remove_from_group(self, field: str, group_id: str) -> None:
        """
        从分组中移除字段
        
        Args:
            field (str): 字段名
            group_id (str): 分组ID
        """
        if group_id in self.field_groups:
            self.field_groups[group_id]["fields"].discard(field)
            
    def get_field_priority(self, field: str) -> int:
        """
        获取字段优先级
        
        Args:
            field (str): 字段名
            
        Returns:
            int: 优先级值
        """
        if field in self.field_priorities:
            return self.field_priorities[field]
        if self.parent_rules:
            return self.parent_rules.get_field_priority(field)
        return self.PRIORITY_LEVELS["normal"]
        
    def set_field_priority(self, field: str, priority: Union[str, int]) -> None:
        """
        设置字段优先级
        
        Args:
            field (str): 字段名
            priority (Union[str, int]): 优先级（字符串或数值）
        """
        if isinstance(priority, str):
            if priority not in self.PRIORITY_LEVELS:
                raise ValueError(f"无效的优先级: {priority}")
            priority = self.PRIORITY_LEVELS[priority]
        elif not isinstance(priority, int) or priority < 0 or priority > 100:
            raise ValueError("优先级必须是 0-100 之间的整数")
        self.field_priorities[field] = priority
        
    def add_conditional_rule(self, field: str, condition: Callable[[str], bool]) -> None:
        """
        添加条件规则
        
        Args:
            field (str): 字段名
            condition (Callable[[str], bool]): 条件函数
        """
        self.conditional_rules[field] = condition
        
    def remove_conditional_rule(self, field: str) -> None:
        """
        移除条件规则
        
        Args:
            field (str): 字段名
        """
        self.conditional_rules.pop(field, None)
        
    def validate_text(self, text: str, field: str) -> bool:
        """
        验证文本是否需要翻译
        
        Args:
            text (str): 文本内容
            field (str): 字段名
            
        Returns:
            bool: 是否需要翻译
        """
        if not text or not isinstance(text, str):
            return False
            
        # 检查字段类型
        field_type = self.get_field_type(field)
        if field_type == "ignored":
            return False
        if field_type == "conditional":
            condition = self.conditional_rules.get(field)
            if condition and not condition(text):
                return False
                
        # 检查字段优先级
        priority = self.get_field_priority(field)
        if priority == self.PRIORITY_LEVELS["lowest"]:
            return False
            
        # 检查非文本模式
        for pattern in self.non_text_patterns:
            if re.match(pattern, text):
                return False
                
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """
        将规则转换为字典
        
        Returns:
            Dict[str, Any]: 规则字典
        """
        return {
            'version': '1.1.0',
            'default_fields': list(self.default_fields),
            'ignore_fields': list(self.ignore_fields),
            'non_text_patterns': self.non_text_patterns,
            'field_types': self.field_types,
            'field_groups': {
                group_id: {
                    'name': info['name'],
                    'description': info['description'],
                    'fields': list(info['fields'])
                }
                for group_id, info in self.field_groups.items()
            },
            'field_priorities': self.field_priorities,
            'conditional_rules': {
                field: condition.__name__ if hasattr(condition, '__name__') else str(condition)
                for field, condition in self.conditional_rules.items()
            }
        }
        
    def save_to_file(self, file_path: str, format: str = 'json') -> None:
        """
        保存规则到文件
        
        Args:
            file_path (str): 文件路径
            format (str): 文件格式（'json' 或 'yaml'）
        """
        try:
            data = self.to_dict()
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            elif format.lower() == 'yaml':
                import yaml
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(data, f, allow_unicode=True)
            else:
                raise ValueError(f"不支持的文件格式: {format}")
            logging.info("规则已保存到: %s", file_path)
        except Exception as e:
            logging.error("保存规则失败: %s", e)
            raise

    @classmethod
    def load_from_file(cls, file_path: str, format: str = 'json') -> 'UnifiedFilterRules':
        """
        从文件加载规则
        
        Args:
            file_path (str): 文件路径
            format (str): 文件格式（'json' 或 'yaml'）
            
        Returns:
            UnifiedFilterRules: 规则对象
        """
        try:
            if format.lower() == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif format.lower() == 'yaml':
                import yaml
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的文件格式: {format}")
                
            rules = cls(
                default_fields=set(data.get('default_fields', [])),
                ignore_fields=set(data.get('ignore_fields', [])),
                non_text_patterns=data.get('non_text_patterns', [])
            )
            
            # 加载字段类型
            rules.field_types = data.get('field_types', {})
            
            # 加载字段分组
            rules.field_groups = {
                group_id: {
                    'name': info['name'],
                    'description': info['description'],
                    'fields': set(info['fields'])
                }
                for group_id, info in data.get('field_groups', {}).items()
            }
            
            # 加载字段优先级
            rules.field_priorities = data.get('field_priorities', {})
            
            # 加载条件规则（注意：条件函数需要重新定义）
            rules.conditional_rules = {}
            
            return rules
        except Exception as e:
            logging.error("加载规则失败: %s", e)
            return cls()
            
    def merge(self, other: 'UnifiedFilterRules', priority: str = 'normal') -> 'UnifiedFilterRules':
        """
        合并两个规则集
        
        Args:
            other (UnifiedFilterRules): 要合并的规则集
            priority (str): 合并优先级
            
        Returns:
            UnifiedFilterRules: 合并后的规则集
        """
        if not isinstance(other, UnifiedFilterRules):
            raise ValueError("other 必须是 UnifiedFilterRules 类型")
            
        # 根据优先级合并字段
        priority_value = self.PRIORITY_LEVELS.get(priority, self.PRIORITY_LEVELS["normal"])
        default_fields = set()
        ignore_fields = set()
        
        # 合并默认字段
        for field in self.default_fields | other.default_fields:
            self_priority = self.get_field_priority(field)
            other_priority = other.get_field_priority(field)
            if self_priority >= priority_value and self_priority >= other_priority:
                default_fields.add(field)
            elif other_priority >= priority_value and other_priority > self_priority:
                default_fields.add(field)
                
        # 合并忽略字段
        for field in self.ignore_fields | other.ignore_fields:
            self_priority = self.get_field_priority(field)
            other_priority = other.get_field_priority(field)
            if self_priority >= priority_value and self_priority >= other_priority:
                ignore_fields.add(field)
            elif other_priority >= priority_value and other_priority > self_priority:
                ignore_fields.add(field)
                
        # 合并非文本模式
        non_text_patterns = list(set(self.non_text_patterns + other.non_text_patterns))
        
        # 创建新的规则集
        merged_rules = UnifiedFilterRules(
            default_fields=default_fields,
            ignore_fields=ignore_fields,
            non_text_patterns=non_text_patterns
        )
        
        # 合并字段类型
        merged_rules.field_types = {**self.field_types, **other.field_types}
        
        # 合并字段分组
        merged_rules.field_groups = {
            group_id: {
                'name': info['name'],
                'description': info['description'],
                'fields': set(info['fields'])
            }
            for group_id, info in {**self.field_groups, **other.field_groups}.items()
        }
        
        # 合并字段优先级
        merged_rules.field_priorities = {**self.field_priorities, **other.field_priorities}
        
        # 合并条件规则
        merged_rules.conditional_rules = {**self.conditional_rules, **other.conditional_rules}
        
        return merged_rules
        
    def get_stats(self) -> Dict[str, Any]:
        """
        获取规则统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            'default_fields': len(self.default_fields),
            'ignore_fields': len(self.ignore_fields),
            'non_text_patterns': len(self.non_text_patterns),
            'field_types': {
                type_name: len([f for f, t in self.field_types.items() if t == type_name])
                for type_name in self.FIELD_TYPES
            },
            'field_groups': {
                group_id: len(info['fields'])
                for group_id, info in self.field_groups.items()
            },
            'field_priorities': {
                level: len([f for f, p in self.field_priorities.items() if p == value])
                for level, value in self.PRIORITY_LEVELS.items()
            },
            'conditional_rules': len(self.conditional_rules)
        }
        
        if self.parent_rules:
            stats['parent_rules'] = self.parent_rules.get_stats()
            
        return stats
        
    def __str__(self) -> str:
        """返回规则的字符串表示"""
        stats = self.get_stats()
        return f"UnifiedFilterRules(默认字段: {stats['default_fields']}, 忽略字段: {stats['ignore_fields']}, 非文本模式: {stats['non_text_patterns']})"
        
    def __repr__(self) -> str:
        """返回规则的详细表示"""
        return f"UnifiedFilterRules(\n  default_fields={self.default_fields},\n  ignore_fields={self.ignore_fields},\n  non_text_patterns={self.non_text_patterns},\n  field_types={self.field_types},\n  field_groups={self.field_groups},\n  field_priorities={self.field_priorities},\n  conditional_rules={self.conditional_rules}\n)"
        
    def inherit_from(self, parent_rules: 'UnifiedFilterRules', inherit_types: bool = True,
                    inherit_groups: bool = True, inherit_priorities: bool = True,
                    inherit_conditionals: bool = True) -> None:
        """
        从父规则继承规则
        
        Args:
            parent_rules (UnifiedFilterRules): 父规则集
            inherit_types (bool): 是否继承字段类型
            inherit_groups (bool): 是否继承字段分组
            inherit_priorities (bool): 是否继承字段优先级
            inherit_conditionals (bool): 是否继承条件规则
        """
        if not isinstance(parent_rules, UnifiedFilterRules):
            raise ValueError("parent_rules 必须是 UnifiedFilterRules 类型")
            
        self.parent_rules = parent_rules
        
        if inherit_types:
            for field, field_type in parent_rules.field_types.items():
                if field not in self.field_types:
                    self.field_types[field] = field_type
                    
        if inherit_groups:
            for group_id, group_info in parent_rules.field_groups.items():
                if group_id not in self.field_groups:
                    self.field_groups[group_id] = {
                        "name": group_info["name"],
                        "description": group_info["description"],
                        "fields": set(group_info["fields"])
                    }
                else:
                    self.field_groups[group_id]["fields"].update(group_info["fields"])
                    
        if inherit_priorities:
            for field, priority in parent_rules.field_priorities.items():
                if field not in self.field_priorities:
                    self.field_priorities[field] = priority
                    
        if inherit_conditionals:
            for field, condition in parent_rules.conditional_rules.items():
                if field not in self.conditional_rules:
                    self.conditional_rules[field] = condition
                    
        self._validate_rules()
        
    def validate_field(self, field: str, value: Any) -> bool:
        """
        验证字段值
        
        Args:
            field (str): 字段名
            value (Any): 字段值
            
        Returns:
            bool: 是否有效
        """
        field_type = self.get_field_type(field)
        
        # 检查字段类型
        if field_type == "ignored":
            return True
            
        if not isinstance(value, str):
            return False
            
        # 检查条件规则
        if field_type == "conditional":
            condition = self.conditional_rules.get(field)
            if condition and not condition(value):
                return False
                
        # 检查非文本模式
        if field_type == "translatable":
            for pattern in self.non_text_patterns:
                if re.match(pattern, value):
                    return False
                    
        # 检查格式化字符串
        if field_type == "format":
            try:
                value.format()  # 尝试格式化
            except (KeyError, IndexError, ValueError):
                return False
                
        # 检查引用类型
        if field_type == "reference":
            if not re.match(r'^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)*$', value):
                return False
                
        # 检查复数形式
        if field_type == "plural":
            if not re.match(r'^[^{}]*{[^{}]*}[^{}]*$', value):
                return False
                
        # 检查性别相关
        if field_type == "gender":
            if not re.match(r'^[^{}]*{[^{}]*}[^{}]*$', value):
                return False
                
        # 检查上下文相关
        if field_type == "context":
            if not re.match(r'^[^{}]*{[^{}]*}[^{}]*$', value):
                return False
                
        return True
        
    def validate_ruleset(self) -> Dict[str, List[str]]:
        """
        验证规则集的有效性
        
        Returns:
            Dict[str, List[str]]: 验证结果
        """
        results = {
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # 检查字段类型
        for field, field_type in self.field_types.items():
            if field_type not in self.FIELD_TYPES:
                results["errors"].append(f"无效的字段类型: {field} -> {field_type}")
                
        # 检查字段分组
        for group_id, group_info in self.field_groups.items():
            if group_id not in self.FIELD_GROUPS:
                results["warnings"].append(f"未知的分组ID: {group_id}")
            for field in group_info["fields"]:
                if field not in self.field_types:
                    results["warnings"].append(f"分组中的未知字段: {group_id} -> {field}")
                    
        # 检查字段优先级
        for field, priority in self.field_priorities.items():
            if not isinstance(priority, int) or priority < 0 or priority > 100:
                results["errors"].append(f"无效的优先级值: {field} -> {priority}")
                
        # 检查条件规则
        for field, condition in self.conditional_rules.items():
            if not callable(condition):
                results["errors"].append(f"无效的条件规则: {field}")
            elif field not in self.field_types:
                results["warnings"].append(f"条件规则的未知字段: {field}")
                
        # 检查正则表达式
        for pattern in self.non_text_patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                results["errors"].append(f"无效的正则表达式: {pattern} -> {e}")
                
        # 检查字段冲突
        conflicts = self.default_fields & self.ignore_fields
        if conflicts:
            results["errors"].append(f"字段冲突: {conflicts}")
            
        # 检查父规则
        if self.parent_rules:
            parent_results = self.parent_rules.validate_ruleset()
            results["errors"].extend(parent_results["errors"])
            results["warnings"].extend(parent_results["warnings"])
            results["info"].extend(parent_results["info"])
            
        # 添加统计信息
        stats = self.get_stats()
        results["info"].append(f"规则集统计: {stats}")
        
        return results
        
    def export_rules(self, format: str = 'json', include_stats: bool = True) -> str:
        """
        导出规则为字符串
        
        Args:
            format (str): 导出格式（'json' 或 'yaml'）
            include_stats (bool): 是否包含统计信息
            
        Returns:
            str: 导出的规则字符串
        """
        data = self.to_dict()
        if include_stats:
            data['stats'] = self.get_stats()
            
        if format.lower() == 'json':
            return json.dumps(data, indent=4, ensure_ascii=False)
        elif format.lower() == 'yaml':
            import yaml
            return yaml.safe_dump(data, allow_unicode=True)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
            
    def import_rules(self, rules_str: str, format: str = 'json') -> None:
        """
        从字符串导入规则
        
        Args:
            rules_str (str): 规则字符串
            format (str): 导入格式（'json' 或 'yaml'）
        """
        try:
            if format.lower() == 'json':
                data = json.loads(rules_str)
            elif format.lower() == 'yaml':
                import yaml
                data = yaml.safe_load(rules_str)
            else:
                raise ValueError(f"不支持的导入格式: {format}")
                
            # 更新规则
            if 'default_fields' in data:
                self.default_fields = set(data['default_fields'])
            if 'ignore_fields' in data:
                self.ignore_fields = set(data['ignore_fields'])
            if 'non_text_patterns' in data:
                self.non_text_patterns = data['non_text_patterns']
            if 'field_types' in data:
                self.field_types = data['field_types']
            if 'field_groups' in data:
                self.field_groups = {
                    group_id: {
                        'name': info['name'],
                        'description': info['description'],
                        'fields': set(info['fields'])
                    }
                    for group_id, info in data['field_groups'].items()
                }
            if 'field_priorities' in data:
                self.field_priorities = data['field_priorities']
            if 'conditional_rules' in data:
                # 注意：条件规则需要重新定义
                self.conditional_rules = {}
                
            self._validate_rules()
        except Exception as e:
            logging.error("导入规则失败: %s", e)
            raise

    @classmethod
    def get_rules(cls) -> Dict[str, Any]:
        """
        返回当前过滤规则的字典表示，兼容旧代码调用。
        """
        return {
            "default_fields": getattr(cls, "DEFAULT_FIELDS", []),
            "ignore_fields": getattr(cls, "IGNORE_FIELDS", []),
            "non_text_patterns": getattr(cls, "NON_TEXT_PATTERNS", [])
        }