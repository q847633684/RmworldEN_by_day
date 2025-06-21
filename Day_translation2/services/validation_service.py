"""
Day Translation 2 - 验证服务

提供翻译质量验证、术语一致性检查和格式规范验证功能。
遵循提示文件标准：PEP 8规范、具体异常处理、用户友好错误信息。
"""

import logging
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# 使用绝对导入
from services.config_service import config_service
from models.exceptions import ImportError as TranslationImportError
from models.exceptions import ProcessingError, ValidationError
from models.result_models import OperationResult, OperationStatus, OperationType

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@dataclass
class ValidationIssue:
    """
    验证问题数据类

    Attributes:
        issue_type: 问题类型
        severity: 严重程度 (error, warning, info)
        key: 相关的翻译key
        message: 问题描述
        suggestion: 修改建议
        file_path: 文件路径
    """

    issue_type: str
    severity: str
    key: str
    message: str
    suggestion: Optional[str] = None
    file_path: Optional[str] = None


@dataclass
class ValidationReport:
    """
    验证报告数据类

    Attributes:
        total_entries: 总翻译条目数
        issues: 发现的问题列表
        error_count: 错误数量
        warning_count: 警告数量
        quality_score: 质量评分 (0-100)
        terminology_consistency: 术语一致性评分
    """

    total_entries: int
    issues: List[ValidationIssue]
    error_count: int
    warning_count: int
    quality_score: float
    terminology_consistency: float


class TranslationValidator:
    """翻译验证器，负责验证翻译质量和一致性"""

    def __init__(self):
        """初始化验证器"""
        self.config = config_service.get_unified_config()
        self.terminology_dict = self._load_terminology_dict()

        # 验证规则配置
        self.validation_rules = {
            "check_empty_translations": True,
            "check_format_consistency": True,
            "check_terminology": True,
            "check_length_ratio": True,
            "check_special_chars": True,
            "max_length_ratio": 3.0,  # 翻译长度比例上限
            "min_length_ratio": 0.2,  # 翻译长度比例下限
        }

    def validate_translations(self, translations: List[Tuple[str, str, str]]) -> ValidationReport:
        """
        验证翻译列表

        Args:
            translations: 翻译数据列表 [(key, source_text, target_text), ...]

        Returns:
            验证报告

        Raises:
            ValidationError: 当输入数据无效时
            ProcessingError: 当验证过程出现错误时
        """
        if not translations:
            raise ValidationError(
                "翻译数据不能为空", field_name="translations", expected_type="非空列表"
            )

        try:
            logging.info(f"开始验证 {len(translations)} 条翻译")

            issues = []

            # 执行各项验证
            if self.validation_rules["check_empty_translations"]:
                issues.extend(self._check_empty_translations(translations))

            if self.validation_rules["check_format_consistency"]:
                issues.extend(self._check_format_consistency(translations))

            if self.validation_rules["check_terminology"]:
                issues.extend(self._check_terminology_consistency(translations))

            if self.validation_rules["check_length_ratio"]:
                issues.extend(self._check_length_ratio(translations))

            if self.validation_rules["check_special_chars"]:
                issues.extend(self._check_special_characters(translations))

            # 统计问题
            error_count = sum(1 for issue in issues if issue.severity == "error")
            warning_count = sum(1 for issue in issues if issue.severity == "warning")

            # 计算质量评分
            quality_score = self._calculate_quality_score(
                len(translations), error_count, warning_count
            )

            # 计算术语一致性评分
            terminology_score = self._calculate_terminology_score(translations, issues)

            return ValidationReport(
                total_entries=len(translations),
                issues=issues,
                error_count=error_count,
                warning_count=warning_count,
                quality_score=quality_score,
                terminology_consistency=terminology_score,
            )

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ProcessingError(
                f"验证翻译时发生错误: {str(e)}",
                operation="validate_translations",
                stage="翻译验证",
            )

    def _check_empty_translations(
        self, translations: List[Tuple[str, str, str]]
    ) -> List[ValidationIssue]:
        """检查空翻译"""
        issues = []

        for key, source_text, target_text in translations:
            if not source_text.strip():
                issues.append(
                    ValidationIssue(
                        issue_type="empty_source",
                        severity="error",
                        key=key,
                        message="源文本为空",
                        suggestion="检查源文件中的文本内容",
                    )
                )

            if not target_text.strip():
                issues.append(
                    ValidationIssue(
                        issue_type="empty_translation",
                        severity="error",
                        key=key,
                        message="翻译文本为空",
                        suggestion="添加翻译内容",
                    )
                )

            if source_text.strip() == target_text.strip():
                issues.append(
                    ValidationIssue(
                        issue_type="untranslated",
                        severity="warning",
                        key=key,
                        message="翻译与源文本相同，可能未翻译",
                        suggestion="检查是否需要翻译或保持原文",
                    )
                )

        return issues

    def _check_format_consistency(
        self, translations: List[Tuple[str, str, str]]
    ) -> List[ValidationIssue]:
        """检查格式一致性"""
        issues = []  # 检查占位符格式
        placeholder_patterns = [
            r"\{[^}]+\}",  # {placeholder}
            r"%[sd]",  # %s, %d
            r"\$[A-Za-z_][A-Za-z0-9_]*",  # $variable
        ]

        for key, source_text, target_text in translations:
            for pattern in placeholder_patterns:
                source_placeholders = set(re.findall(pattern, source_text))
                target_placeholders = set(re.findall(pattern, target_text))

                # 检查占位符数量是否匹配
                if len(source_placeholders) != len(target_placeholders):
                    issues.append(
                        ValidationIssue(
                            issue_type="placeholder_mismatch",
                            severity="error",
                            key=key,
                            message=f"占位符数量不匹配: 源文本{len(source_placeholders)}个，翻译{len(target_placeholders)}个",
                            suggestion="确保翻译中包含所有占位符",
                        )
                    )

                # 检查占位符内容是否匹配
                missing_placeholders = source_placeholders - target_placeholders
                if missing_placeholders:
                    issues.append(
                        ValidationIssue(
                            issue_type="missing_placeholder",
                            severity="error",
                            key=key,
                            message="缺少占位符: " + ", ".join(missing_placeholders),
                            suggestion="在翻译中添加: " + ", ".join(missing_placeholders),
                        )
                    )

        return issues

    def _check_terminology_consistency(
        self, translations: List[Tuple[str, str, str]]
    ) -> List[ValidationIssue]:
        """检查术语一致性"""
        issues = []

        # 收集术语使用情况
        term_usage: Dict[str, Counter] = defaultdict(Counter)

        for key, source_text, target_text in translations:
            # 检查预定义术语
            for source_term, expected_translations in self.terminology_dict.items():
                if source_term.lower() in source_text.lower():
                    # 查找实际使用的翻译
                    found_translation = None
                    for expected in expected_translations:
                        if expected.lower() in target_text.lower():
                            found_translation = expected
                            break

                    if found_translation:
                        term_usage[source_term][found_translation] += 1
                    else:
                        issues.append(
                            ValidationIssue(
                                issue_type="terminology_inconsistency",
                                severity="warning",
                                key=key,
                                message=f"术语 '{source_term}' 未使用标准翻译",
                                suggestion="建议使用: " + ", ".join(expected_translations),
                            )
                        )

        # 检查术语翻译一致性
        for source_term, translation_counts in term_usage.items():
            if len(translation_counts) > 1:
                most_common = translation_counts.most_common()
                if most_common[0][1] > most_common[1][1]:  # 有明显的主要翻译
                    issues.append(
                        ValidationIssue(
                            issue_type="terminology_variation",
                            severity="info",
                            key="",
                            message=f"术语 '{source_term}' 有多种翻译: {dict(translation_counts)}",
                            suggestion=f"建议统一使用: {most_common[0][0]}",
                        )
                    )

        return issues

    def _check_length_ratio(
        self, translations: List[Tuple[str, str, str]]
    ) -> List[ValidationIssue]:
        """检查翻译长度比例"""
        issues = []

        max_ratio = self.validation_rules["max_length_ratio"]
        min_ratio = self.validation_rules["min_length_ratio"]

        for key, source_text, target_text in translations:
            if len(source_text) == 0:
                continue

            length_ratio = len(target_text) / len(source_text)

            if length_ratio > max_ratio:
                issues.append(
                    ValidationIssue(
                        issue_type="translation_too_long",
                        severity="warning",
                        key=key,
                        message=f"翻译过长，长度比例: {length_ratio:.2f} (最大: {max_ratio})",
                        suggestion="检查翻译是否过于冗长",
                    )
                )
            elif length_ratio < min_ratio:
                issues.append(
                    ValidationIssue(
                        issue_type="translation_too_short",
                        severity="warning",
                        key=key,
                        message=f"翻译过短，长度比例: {length_ratio:.2f} (最小: {min_ratio})",
                        suggestion="检查翻译是否完整",
                    )
                )

        return issues

    def _check_special_characters(
        self, translations: List[Tuple[str, str, str]]
    ) -> List[ValidationIssue]:
        """检查特殊字符处理"""
        issues = []

        # 需要保留的特殊字符
        special_chars = ["<", ">", '"', "'", "\\n", "\\t", "&"]

        for key, source_text, target_text in translations:
            for char in special_chars:
                source_count = source_text.count(char)
                target_count = target_text.count(char)

                if source_count != target_count:
                    issues.append(
                        ValidationIssue(
                            issue_type="special_char_mismatch",
                            severity="warning",
                            key=key,
                            message=f"特殊字符 '{char}' 数量不匹配: 源{source_count}个，译{target_count}个",
                            suggestion="检查特殊字符是否正确处理",
                        )
                    )

        return issues

    def _calculate_quality_score(
        self, total_entries: int, error_count: int, warning_count: int
    ) -> float:
        """计算质量评分"""
        if total_entries == 0:
            return 0.0

        # 错误权重更高
        error_penalty = (error_count / total_entries) * 50
        warning_penalty = (warning_count / total_entries) * 20

        score = 100 - error_penalty - warning_penalty
        return max(0.0, min(100.0, score))

    def _calculate_terminology_score(
        self, translations: List[Tuple[str, str, str]], issues: List[ValidationIssue]
    ) -> float:
        """计算术语一致性评分"""
        terminology_issues = [
            issue
            for issue in issues
            if issue.issue_type in ["terminology_inconsistency", "terminology_variation"]
        ]

        if not translations:
            return 0.0

        if not terminology_issues:
            return 100.0

        issue_rate = len(terminology_issues) / len(translations)
        score = 100 - (issue_rate * 100)
        return max(0.0, min(100.0, score))

    def _load_terminology_dict(self) -> Dict[str, List[str]]:
        """加载术语词典"""
        # 游戏UI常用术语字典
        return {
            "Save": ["保存", "存档"],
            "Load": ["加载", "读取"],
            "New Game": ["新游戏"],
            "Continue": ["继续"],
            "Settings": ["设置", "选项"],
            "Options": ["选项", "设置"],
            "Exit": ["退出"],
            "Quit": ["退出"],
            "Health": ["生命值", "血量"],
            "Damage": ["伤害"],
            "Attack": ["攻击"],
            "Defense": ["防御"],
            "Speed": ["速度"],
            "Level": ["等级", "级别"],
            "Experience": ["经验", "经验值"],
            # "Skill": ["技能"],  # DUPLICATE: Removed to avoid F601
            "Inventory": ["背包", "物品栏"],
            "Equipment": ["装备"],
            "Weapon": ["武器"],
            "Armor": ["护甲", "盔甲"],
            "Item": ["物品", "道具"],
            "Quest": ["任务", "委托"],
            "Mission": ["任务", "使命"],
            "Map": ["地图"],
            "Character": ["角色", "人物"],
            "Player": ["玩家"],
            "Enemy": ["敌人"],
            "Boss": ["首领", "BOSS"],
            "Victory": ["胜利"],
            "Defeat": ["失败", "败北"],
            "Score": ["分数", "得分"],
            "Points": ["点数", "分数"],
            "Money": ["金钱", "货币"],
            "Gold": ["金币", "黄金"],
            "Silver": ["银币", "银子"],
            "Copper": ["铜币"],
            "Buy": ["购买"],
            "Sell": ["出售", "售卖"],
            "Trade": ["交易"],
            "Shop": ["商店"],
            "Merchant": ["商人"],
            "Crafting": ["制作", "合成"],
            "Recipe": ["配方", "食谱"],
            "Material": ["材料"],
            "Resource": ["资源"],
            "Building": ["建筑", "建造"],
            "Construction": ["建设", "建造"],
            "Research": ["研究"],
            "Technology": ["技术", "科技"],
            "Magic": ["魔法"],
            "Spell": ["法术", "咒语"],
            "Potion": ["药水", "药剂"],
            "Heal": ["治疗", "回复"],
            "Restore": ["恢复", "回复"],
            "Bu": ["增益", "强化"],
            "Debu": ["减益", "削弱"],
            "Status": ["状态"],
            "Effect": ["效果"],
            "Duration": ["持续时间"],
            "Cooldown": ["冷却时间"],
            "Range": ["范围", "射程"],
            "Area": ["区域", "范围"],
            "Target": ["目标"],
            "Random": ["随机"],
            "Chance": ["几率", "概率"],
            "Probability": ["概率", "几率"],
            "Difficulty": ["难度"],
            "Easy": ["简单", "容易"],
            "Normal": ["普通", "正常"],
            "Hard": ["困难", "艰难"],
            "Expert": ["专家", "高手"],
            "Master": ["大师"],
            "Beginner": ["初学者", "新手"],
            "Tutorial": ["教程", "教学"],
            "Help": ["帮助", "帮助"],
            "Manual": ["手册", "说明书"],
            "Guide": ["指南", "指导"],
            "Tip": ["提示", "小贴士"],
            "Warning": ["警告", "注意"],
            "Error": ["错误", "出错"],
            "Success": ["成功"],
            "Failure": ["失败"],
            "Complete": ["完成"],
            "Incomplete": ["未完成"],
            "Progress": ["进度", "进展"],
            "Percentage": ["百分比"],
            "Total": ["总计", "总数"],
            "Current": ["当前", "目前"],
            "Maximum": ["最大", "最大值"],
            "Minimum": ["最小", "最小值"],
            "Average": ["平均", "平均值"],
            "Time": ["时间"],
            "Date": ["日期"],
            "Hour": ["小时"],
            "Minute": ["分钟"],
            "Second": ["秒"],
            "Day": ["天", "日"],
            "Week": ["周", "星期"],
            "Month": ["月", "月份"],
            "Year": ["年"],
            "Season": ["季节"],
            "Weather": ["天气"],
            "Temperature": ["温度"],
            "Wind": ["风"],
            "Rain": ["雨"],
            "Snow": ["雪"],
            "Sun": ["太阳", "阳光"],
            "Moon": ["月亮"],
            "Star": ["星星", "恒星"],
            "Sky": ["天空"],
            "Cloud": ["云", "云朵"],
            "Water": ["水"],
            "Fire": ["火"],
            "Earth": ["土", "地球"],
            "Air": ["空气", "风"],
            "Nature": ["自然"],
            "Animal": ["动物"],
            "Plant": ["植物"],
            "Tree": ["树"],
            "Flower": ["花"],
            "Grass": ["草"],
            "Stone": ["石头"],
            "Rock": ["岩石"],
            "Mountain": ["山", "山脉"],
            "Hill": ["山丘"],
            "Valley": ["山谷"],
            "River": ["河", "河流"],
            "Lake": ["湖", "湖泊"],
            "Ocean": ["海洋"],
            "Sea": ["海"],
            "Beach": ["海滩"],
            "Desert": ["沙漠"],
            "Forest": ["森林"],
            "Jungle": ["丛林"],
            "Cave": ["洞穴"],
            "Dungeon": ["地牢"],
            "Castle": ["城堡"],
            "Tower": ["塔"],
            "House": ["房子", "房屋"],
            "Home": ["家", "家园"],
            "Village": ["村庄"],
            "Town": ["城镇"],
            "City": ["城市"],
            "Capital": ["首都", "资本"],
            "Country": ["国家", "乡村"],
            "Nation": ["国家", "民族"],
            "World": ["世界"],
            "Universe": ["宇宙"],
            "Space": ["空间", "太空"],
            "Planet": ["行星"],
            "Galaxy": ["银河系", "星系"],
            "Dimension": ["维度", "尺寸"],
            "Reality": ["现实"],
            "Dream": ["梦", "梦想"],
            "Fantasy": ["幻想"],
            "Adventure": ["冒险"],
            "Journey": ["旅程", "旅行"],
            "Exploration": ["探索"],
            "Discovery": ["发现"],
            "Mystery": ["神秘", "谜"],
            "Secret": ["秘密"],
            "Hidden": ["隐藏的"],
            "Lost": ["失落的", "丢失的"],
            "Found": ["找到的", "发现的"],
            "Ancient": ["古代的", "古老的"],
            "Modern": ["现代的"],
            "Future": ["未来"],
            "Past": ["过去"],
            "Present": ["现在", "礼物"],
            "History": ["历史"],
            "Legend": ["传说"],
            "Myth": ["神话"],
            "Story": ["故事"],
            "Tale": ["故事", "传说"],
            "Book": ["书", "书籍"],
            "Chapter": ["章节"],
            "Page": ["页", "页面"],
            "Word": ["单词", "词"],
            "Letter": ["字母", "信"],
            "Number": ["数字", "号码"],
            "Symbol": ["符号", "象征"],
            "Sign": ["标志", "符号"],
            "Mark": ["标记", "分数"],
            "Color": ["颜色"],
            "Red": ["红色"],
            "Blue": ["蓝色"],
            "Green": ["绿色"],
            "Yellow": ["黄色"],
            "Orange": ["橙色"],
            "Purple": ["紫色"],
            "Pink": ["粉色"],
            "Brown": ["棕色", "褐色"],
            "Black": ["黑色"],
            "White": ["白色"],
            "Gray": ["灰色"],
            "Grey": ["灰色"],
            "Size": ["大小", "尺寸"],
            "Big": ["大的"],
            "Small": ["小的"],
            "Large": ["大的"],
            "Huge": ["巨大的"],
            "Tiny": ["微小的"],
            "Long": ["长的"],
            "Short": ["短的"],
            "Wide": ["宽的"],
            "Narrow": ["窄的"],
            "Thick": ["厚的"],
            "Thin": ["薄的"],
            "Heavy": ["重的"],
            "Light": ["轻的", "光"],
            "Strong": ["强的", "强壮的"],
            "Weak": ["弱的"],
            "Fast": ["快的"],
            "Slow": ["慢的"],
            "High": ["高的"],
            "Low": ["低的"],
            "Hot": ["热的"],
            "Cold": ["冷的"],
            "Warm": ["温暖的"],
            "Cool": ["凉的", "酷的"],
            "Good": ["好的"],
            "Bad": ["坏的"],
            "Best": ["最好的"],
            "Worst": ["最坏的"],
            "Better": ["更好的"],
            "Worse": ["更坏的"],
            "New": ["新的"],
            "Old": ["老的", "旧的"],
            "Fresh": ["新鲜的"],
            "Stale": ["不新鲜的"],
            "Clean": ["干净的", "清洁"],
            "Dirty": ["脏的"],
            "Safe": ["安全的"],
            "Dangerous": ["危险的"],
            # DUPLICATE 'Easy': "Easy": ["容易的"],
            "Difficult": ["困难的"],
            "Simple": ["简单的"],
            "Complex": ["复杂的"],
            "Complicated": ["复杂的"],
            "Clear": ["清楚的", "清除"],
            "Unclear": ["不清楚的"],
            "Obvious": ["明显的"],
            # DUPLICATE 'Hidden': "Hidden": ["隐藏的"],
            "Visible": ["可见的"],
            "Invisible": ["不可见的"],
            "Open": ["打开", "开放的"],
            "Close": ["关闭", "接近"],
            "Closed": ["关闭的"],
            "Start": ["开始"],
            "Stop": ["停止"],
            "Begin": ["开始"],
            "End": ["结束"],
            "Finish": ["完成", "结束"],
            "Cancel": ["取消"],
            "Confirm": ["确认"],
            "Accept": ["接受"],
            "Reject": ["拒绝"],
            "Approve": ["批准"],
            "Deny": ["拒绝"],
            "Allow": ["允许"],
            "Forbid": ["禁止"],
            "Enable": ["启用"],
            "Disable": ["禁用"],
            "Activate": ["激活"],
            "Deactivate": ["停用"],
            "Turn On": ["打开"],
            "Turn O": ["关闭"],
            "Switch": ["切换", "开关"],
            "Change": ["改变", "更改"],
            "Modify": ["修改"],
            "Edit": ["编辑"],
            "Update": ["更新"],
            "Upgrade": ["升级"],
            "Downgrade": ["降级"],
            "Install": ["安装"],
            "Uninstall": ["卸载"],
            "Download": ["下载"],
            "Upload": ["上传"],
            "Import": ["导入"],
            "Export": ["导出"],
            "Copy": ["复制"],
            "Paste": ["粘贴"],
            "Cut": ["剪切"],
            "Delete": ["删除"],
            "Remove": ["移除"],
            "Add": ["添加"],
            "Insert": ["插入"],
            "Create": ["创建"],
            "Generate": ["生成"],
            "Build": ["建造", "构建"],
            "Destroy": ["摧毁"],
            "Break": ["打破", "破坏"],
            "Repair": ["修理"],
            "Fix": ["修复"],
            "Replace": ["替换"],
            "Substitute": ["替代"],
            "Move": ["移动"],
            "Drag": ["拖拽"],
            "Drop": ["放下", "掉落"],
            "Pick": ["选择", "捡起"],
            "Select": ["选择"],
            "Choose": ["选择"],
            "Decide": ["决定"],
            "Determine": ["确定"],
            "Find": ["找到", "查找"],
            "Search": ["搜索"],
            "Look": ["看", "寻找"],
            "See": ["看见"],
            "Watch": ["观看"],
            "View": ["查看", "视图"],
            "Show": ["显示", "展示"],
            "Hide": ["隐藏"],
            "Display": ["显示", "展示"],
            # DUPLICATE 'Present': "Present": ["展示", "现在的"],
            "Represent": ["代表"],
            "Demonstrate": ["演示"],
            "Explain": ["解释"],
            "Describe": ["描述"],
            "Define": ["定义"],
            "Identify": ["识别"],
            "Recognize": ["识别", "认出"],
            "Understand": ["理解"],
            "Know": ["知道"],
            "Learn": ["学习"],
            "Study": ["学习", "研究"],
            "Teach": ["教"],
            "Instruct": ["指导"],
            "Train": ["训练"],
            "Practice": ["练习"],
            "Exercise": ["练习", "锻炼"],
            "Work": ["工作"],
            "Job": ["工作", "职业"],
            "Task": ["任务"],
            "Duty": ["职责"],
            "Responsibility": ["责任"],
            "Role": ["角色", "作用"],
            "Function": ["功能", "函数"],
            "Purpose": ["目的"],
            "Goal": ["目标"],
            "Objective": ["目标", "客观的"],
            # DUPLICATE 'Target': "Target": ["目标"],
            "Aim": ["目标", "瞄准"],
            "Plan": ["计划"],
            "Strategy": ["策略"],
            "Tactic": ["战术"],
            "Method": ["方法"],
            "Way": ["方法", "路"],
            "Approach": ["方法", "接近"],
            "Technique": ["技术", "技巧"],
            "Skill": ["技能"],
            "Ability": ["能力"],
            "Capability": ["能力"],
            "Capacity": ["容量", "能力"],
            "Power": ["力量", "权力"],
            "Force": ["力量", "强制"],
            "Strength": ["力量", "强度"],
            "Energy": ["能量"],
            "Effort": ["努力"],
            "Try": ["尝试"],
            "Attempt": ["尝试"],
            "Test": ["测试"],
            "Experiment": ["实验"],
            "Trial": ["试验", "审判"],
            "Check": ["检查"],
            "Verify": ["验证"],
            "Validate": ["验证"],
            # DUPLICATE 'Confirm': "Confirm": ["确认"],
            "Prove": ["证明"],
            # DUPLICATE 'Demonstrate': "Demonstrate": ["证明", "演示"],
            "Evidence": ["证据"],
            "Proo": ["证明", "证据"],
            "Result": ["结果"],
            "Outcome": ["结果"],
            "Consequence": ["后果"],
            # DUPLICATE 'Effect': "Effect": ["效果", "影响"],
            "Impact": ["影响", "冲击"],
            "Influence": ["影响"],
            "Affect": ["影响"],
            # DUPLICATE 'Change': "Change": ["改变"],
            "Alter": ["改变"],
            "Transform": ["转换", "变换"],
            "Convert": ["转换"],
            "Translate": ["翻译"],
            "Interpret": ["解释", "翻译"],
            # DUPLICATE 'Understand': "Understand": ["理解"],
            "Comprehend": ["理解"],
            "Grasp": ["抓住", "理解"],
            "Realize": ["意识到", "实现"],
            # DUPLICATE 'Recognize': "Recognize": ["认识", "识别"],
            "Acknowledge": ["承认"],
            "Admit": ["承认"],
            "Confess": ["承认", "坦白"],
            "Declare": ["宣布", "声明"],
            "Announce": ["宣布"],
            "Proclaim": ["宣布"],
            "State": ["状态", "声明"],
            "Express": ["表达"],
            "Communicate": ["交流"],
            "Speak": ["说话"],
            "Talk": ["谈话"],
            "Say": ["说"],
            "Tell": ["告诉"],
            "Inform": ["通知"],
            "Notify": ["通知"],
            "Alert": ["警告", "警报"],
            "Warn": ["警告"],
            "Advise": ["建议"],
            "Suggest": ["建议"],
            "Recommend": ["推荐"],
            "Propose": ["提议"],
            "Offer": ["提供", "提议"],
            "Provide": ["提供"],
            "Supply": ["供应", "提供"],
            "Give": ["给"],
            "Grant": ["授予"],
            "Award": ["奖励", "授予"],
            # DUPLICATE 'Present': "Present": ["展示", "礼物"],
            "Gift": ["礼物"],
            "Reward": ["奖励"],
            "Prize": ["奖品"],
            "Bonus": ["奖金", "额外的"],
            "Extra": ["额外的"],
            "Additional": ["额外的"],
            "More": ["更多"],
            "Less": ["更少"],
            "Few": ["少数"],
            "Many": ["许多"],
            "Much": ["很多"],
            "Some": ["一些"],
            "Any": ["任何"],
            "All": ["所有"],
            "None": ["没有"],
            "Everything": ["一切"],
            "Nothing": ["什么都没有"],
            "Something": ["某事"],
            "Anything": ["任何事"],
            "Everyone": ["每个人"],
            "No one": ["没有人"],
            "Someone": ["某人"],
            "Anyone": ["任何人"],
            "Everybody": ["每个人"],
            "Nobody": ["没有人"],
            "Somebody": ["某人"],
            "Anybody": ["任何人"],
            "Everywhere": ["到处"],
            "Nowhere": ["无处"],
            "Somewhere": ["某处"],
            "Anywhere": ["任何地方"],
            "Here": ["这里"],
            "There": ["那里"],
            "Where": ["哪里"],
            "When": ["什么时候"],
            "Why": ["为什么"],
            "How": ["如何", "怎样"],
            "What": ["什么"],
            "Which": ["哪个"],
            "Who": ["谁"],
            "Whose": ["谁的"],
            "Whom": ["谁(宾格)"],
            "This": ["这个"],
            "That": ["那个"],
            "These": ["这些"],
            "Those": ["那些"],
            "Such": ["这样的"],
            "Same": ["相同的"],
            "Different": ["不同的"],
            "Similar": ["相似的"],
            "Like": ["像", "喜欢"],
            "Unlike": ["不像"],
            "Equal": ["相等的"],
            "Unequal": ["不相等的"],
            "Equivalent": ["等价的"],
            "Identical": ["相同的"],
            "Unique": ["独特的"],
            "Special": ["特殊的"],
            "Ordinary": ["普通的"],
            # DUPLICATE 'Normal': "Normal": ["正常的"],
            "Abnormal": ["异常的"],
            "Strange": ["奇怪的"],
            "Weird": ["奇怪的"],
            "Odd": ["奇怪的", "奇数的"],
            "Even": ["甚至", "偶数的"],
            "Usual": ["通常的"],
            "Unusual": ["不寻常的"],
            "Common": ["常见的", "共同的"],
            "Rare": ["稀有的"],
            "Frequent": ["频繁的"],
            "Occasional": ["偶尔的"],
            "Regular": ["规律的", "常规的"],
            "Irregular": ["不规律的"],
            "Constant": ["常数", "持续的"],
            "Variable": ["变量", "可变的"],
            "Fixed": ["固定的"],
            "Flexible": ["灵活的"],
            "Rigid": ["刚性的"],
            "Soft": ["软的"],
            # DUPLICATE 'Hard': "Hard": ["硬的", "困难的"],
            "Smooth": ["光滑的"],
            "Rough": ["粗糙的"],
            "Sharp": ["锋利的"],
            "Dull": ["钝的", "无聊的"],
            "Bright": ["明亮的"],
            "Dark": ["黑暗的"],
            # DUPLICATE 'Light': "Light": ["光", "轻的"],
            "Shadow": ["阴影"],
            "Shade": ["阴影", "遮蔽"],
            "Sunshine": ["阳光"],
            "Daylight": ["日光"],
            "Moonlight": ["月光"],
            "Starlight": ["星光"],
            "Dawn": ["黎明"],
            "Dusk": ["黄昏"],
            "Morning": ["早晨"],
            "Afternoon": ["下午"],
            "Evening": ["晚上"],
            "Night": ["夜晚"],
            "Midnight": ["午夜"],
            "Noon": ["中午"],
            "Today": ["今天"],
            "Yesterday": ["昨天"],
            "Tomorrow": ["明天"],
            "Now": ["现在"],
            "Then": ["然后", "那时"],
            "Soon": ["很快"],
            "Later": ["稍后"],
            "Earlier": ["更早"],
            "Before": ["之前"],
            "After": ["之后"],
            "During": ["期间"],
            "While": ["当...时候"],
            "Until": ["直到"],
            "Since": ["自从"],
            "Always": ["总是"],
            "Never": ["从不"],
            "Sometimes": ["有时"],
            "Often": ["经常"],
            "Usually": ["通常"],
            "Rarely": ["很少"],
            "Seldom": ["很少"],
            "Frequently": ["频繁地"],
            "Occasionally": ["偶尔"],
            "Already": ["已经"],
            "Yet": ["还", "然而"],
            "Still": ["仍然", "静止的"],
            "Just": ["刚刚", "仅仅"],
            "Only": ["只有", "仅仅"],
            "Also": ["也"],
            "Too": ["太", "也"],
            "Either": ["要么", "也"],
            "Neither": ["既不"],
            "Both": ["两者都"],
            # DUPLICATE 'Either': "Either": ["任一"],
            "Or": ["或者"],
            "And": ["和"],
            "But": ["但是"],
            "However": ["然而"],
            "Nevertheless": ["然而"],
            "Although": ["虽然"],
            "Though": ["虽然"],
            "Despite": ["尽管"],
            "In spite o": ["尽管"],
            "Because": ["因为"],
            # DUPLICATE 'Since': "Since": ["因为", "自从"],
            "As": ["因为", "作为"],
            "So": ["所以"],
            "Therefore": ["因此"],
            "Thus": ["因此"],
            "Hence": ["因此"],
            "Consequently": ["因此"],
            "As a result": ["结果"],
            "For example": ["例如"],
            "For instance": ["例如"],
            "Such as": ["比如"],
            # DUPLICATE 'Like': "Like": ["像", "喜欢"],
            "Including": ["包括"],
            "Except": ["除了"],
            "Besides": ["除了", "此外"],
            "In addition": ["此外"],
            "Moreover": ["而且"],
            "Furthermore": ["此外"],
            "Additionally": ["另外"],
            # DUPLICATE 'Also': "Also": ["也"],
            "Plus": ["加", "另外"],
            "Minus": ["减", "负的"],
            "Times": ["次", "乘"],
            "Divide": ["除"],
            "Equals": ["等于"],
            "More than": ["多于"],
            "Less than": ["少于"],
            "Greater than": ["大于"],
            "Smaller than": ["小于"],
            "At least": ["至少"],
            "At most": ["至多"],
            "About": ["关于", "大约"],
            "Approximately": ["大约"],
            "Nearly": ["几乎"],
            "Almost": ["几乎"],
            "Exactly": ["确切地"],
            "Precisely": ["精确地"],
            "Roughly": ["粗略地"],
            "Generally": ["一般地"],
            "Specifically": ["具体地"],
            "Particularly": ["特别地"],
            "Especially": ["尤其"],
            "Mainly": ["主要地"],
            "Mostly": ["大多数"],
            "Partly": ["部分地"],
            "Completely": ["完全地"],
            "Totally": ["完全地"],
            "Entirely": ["完全地"],
            "Fully": ["充分地"],
            "Partially": ["部分地"],
            "Slightly": ["轻微地"],
            "Somewhat": ["有点"],
            "Rather": ["相当"],
            "Quite": ["相当"],
            "Very": ["非常"],
            "Extremely": ["极其"],
            "Highly": ["高度地"],
            "Deeply": ["深深地"],
            "Greatly": ["极大地"],
            "Significantly": ["显著地"],
            "Considerably": ["相当地"],
            "Substantially": ["大幅地"],
            "Remarkably": ["显著地"],
            "Noticeably": ["明显地"],
            "Obviously": ["显然地"],
            "Clearly": ["清楚地"],
            "Evidently": ["明显地"],
            "Apparently": ["显然地"],
            "Seemingly": ["似乎"],
            "Possibly": ["可能地"],
            "Probably": ["可能地"],
            "Likely": ["可能地"],
            "Perhaps": ["也许"],
            "Maybe": ["也许"],
            "Certainly": ["当然"],
            "Definitely": ["肯定地"],
            "Absolutely": ["绝对地"],
            "Surely": ["当然"],
            "Undoubtedly": ["无疑地"],
            "Indeed": ["确实"],
            "Actually": ["实际上"],
            "Really": ["真的"],
            "Truly": ["真正地"],
            "Honestly": ["诚实地"],
            "Frankly": ["坦率地"],
            "Seriously": ["严肃地"],
            "Literally": ["字面上"],
            "Figuratively": ["比喻地"],
            "Metaphorically": ["隐喻地"],
            "Symbolically": ["象征性地"],
            "Traditionally": ["传统上"],
            "Historically": ["历史上"],
            "Originally": ["最初"],
            "Initially": ["最初"],
            "Finally": ["最后"],
            "Eventually": ["最终"],
            "Ultimately": ["最终"],
            "Basically": ["基本上"],
            "Essentially": ["本质上"],
            "Fundamentally": ["根本上"],
            "Primarily": ["主要地"],
            "Chiefly": ["主要地"],
            "Principally": ["主要地"],
            "Largely": ["很大程度上"],
            "Widely": ["广泛地"],
            "Broadly": ["广泛地"],
            "Extensively": ["广泛地"],
            "Thoroughly": ["彻底地"],
            "Carefully": ["仔细地"],
            "Cautiously": ["谨慎地"],
            "Safely": ["安全地"],
            "Securely": ["安全地"],
            "Properly": ["正确地"],
            "Correctly": ["正确地"],
            "Accurately": ["准确地"],
            # DUPLICATE 'Precisely': "Precisely": ["精确地"],
            # DUPLICATE 'Exactly': "Exactly": ["确切地"],
            "Perfectly": ["完美地"],
            "Ideally": ["理想地"],
            "Optimally": ["最佳地"],
            "Effectively": ["有效地"],
            "Efficiently": ["高效地"],
            "Successfully": ["成功地"],
            "Smoothly": ["顺利地"],
            "Easily": ["容易地"],
            "Simply": ["简单地"],
            "Quickly": ["快速地"],
            "Rapidly": ["迅速地"],
            "Slowly": ["缓慢地"],
            "Gradually": ["逐渐地"],
            "Suddenly": ["突然地"],
            "Immediately": ["立即地"],
            "Instantly": ["立即地"],
            "Directly": ["直接地"],
            "Indirectly": ["间接地"],
            "Automatically": ["自动地"],
            "Manually": ["手动地"],
            "Personally": ["个人地"],
            "Individually": ["个别地"],
            "Collectively": ["集体地"],
            "Together": ["一起"],
            "Separately": ["分别地"],
            "Apart": ["分开"],
            "Away": ["离开"],
            "Back": ["回来", "背部"],
            "Forward": ["向前"],
            "Backward": ["向后"],
            "Upward": ["向上"],
            "Downward": ["向下"],
            "Inward": ["向内"],
            "Outward": ["向外"],
            "Inside": ["里面"],
            "Outside": ["外面"],
            "Above": ["上面"],
            "Below": ["下面"],
            "Over": ["在...上"],
            "Under": ["在...下"],
            "Beneath": ["在...下面"],
            "Behind": ["在...后面"],
            "In front o": ["在...前面"],
            "Beside": ["在...旁边"],
            "Next to": ["在...旁边"],
            "Near": ["在...附近"],
            "Close to": ["接近"],
            "Far from": ["远离"],
            "Between": ["在...之间"],
            "Among": ["在...中间"],
            "Within": ["在...内"],
            "Without": ["没有"],
            "Against": ["反对"],
            "Towards": ["朝向"],
            "Through": ["通过"],
            "Across": ["穿过"],
            "Along": ["沿着"],
            "Around": ["围绕"],
            "Beyond": ["超越"],
            # DUPLICATE 'Past': "Past": ["经过", "过去"],
            "Into": ["进入"],
            "Out o": ["从...出来"],
            "Onto": ["到...上"],
            "O": ["离开", "关闭"],
            "Up": ["向上"],
            "Down": ["向下"],
            "In": ["在...里"],
            "Out": ["在...外"],
            "On": ["在...上"],
            "At": ["在"],
            "To": ["到"],
            "From": ["从"],
            "With": ["与", "用"],
            "By": ["被", "通过"],
            "For": ["为了"],
            "O": ["...的"],
            # DUPLICATE 'About': "About": ["关于"],
            # DUPLICATE 'Like': "Like": ["像"],
            # DUPLICATE 'As': "As": ["作为"],
            "Than": ["比"],
            "I": ["如果"],
            "Unless": ["除非"],
            "Whether": ["是否"],
            # DUPLICATE 'That': "That": ["那个"],
            # DUPLICATE 'Which': "Which": ["哪个"],
            # DUPLICATE 'Who': "Who": ["谁"],
            # DUPLICATE 'Whom': "Whom": ["谁"],
            # DUPLICATE 'Whose': "Whose": ["谁的"],
            # DUPLICATE 'Where': "Where": ["哪里"],
            # DUPLICATE 'When': "When": ["何时"],
            # DUPLICATE 'Why': "Why": ["为什么"],
            # DUPLICATE 'How': "How": ["如何"],
            # DUPLICATE 'What': "What": ["什么"],
        }


def validate_csv_file(csv_path: str) -> OperationResult:
    """
    验证CSV翻译文件

    Args:
        csv_path: CSV文件路径

    Returns:
        验证操作结果

    Raises:
        TranslationImportError: 当文件不存在时
        ProcessingError: 当验证过程出现错误时
    """
    if not Path(csv_path).is_file():
        raise TranslationImportError(f"CSV文件不存在: {csv_path}", file_path=csv_path)

    try:
        # 加载CSV数据
        translations = []
        with open(csv_path, "r", encoding="utf-8") as f:
            import csv

            reader = csv.DictReader(f)

            if "key" not in reader.fieldnames or "text" not in reader.fieldnames:
                raise ValidationError(
                    f"CSV文件缺少必要的列（key, text）: {csv_path}",
                    field_name="csv_columns",
                    actual_value=str(reader.fieldnames),
                )

            for row in reader:
                key = row.get("key", "")
                source = row.get("text", "")
                target = row.get("translated", row.get("translation", ""))

                if key and source:
                    translations.append((key, source, target))

        # 执行验证
        validator = TranslationValidator()
        report = validator.validate_translations(translations)

        # 生成验证报告文件
        report_path = csv_path.replace(".csv", "_validation_report.txt")
        _save_validation_report(report, report_path)

        return OperationResult(
            status=(
                OperationStatus.SUCCESS if report.error_count == 0 else OperationStatus.WARNING
            ),
            operation_type=OperationType.VALIDATION,
            message=f"验证完成: {report.error_count}个错误, {report.warning_count}个警告, 质量评分: {report.quality_score:.1f}",
            processed_count=report.total_entries,
            success_count=report.total_entries - report.error_count,
        )

    except Exception as e:
        if isinstance(e, (TranslationImportError, ValidationError)):
            raise
        raise ProcessingError(
            f"验证CSV文件失败: {str(e)}",
            operation="validate_csv_file",
            stage="文件验证",
        )


def _save_validation_report(report: ValidationReport, output_path: str) -> None:
    """保存验证报告"""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# 翻译验证报告\n\n")
            f.write(f"总翻译条目数: {report.total_entries}\n")
            f.write(f"错误数量: {report.error_count}\n")
            f.write(f"警告数量: {report.warning_count}\n")
            f.write(f"质量评分: {report.quality_score:.1f}/100\n")
            f.write(f"术语一致性: {report.terminology_consistency:.1f}/100\n\n")

            if report.issues:
                f.write("## 发现的问题\n\n")

                # 按严重程度分组
                errors = [issue for issue in report.issues if issue.severity == "error"]
                warnings = [issue for issue in report.issues if issue.severity == "warning"]
                infos = [issue for issue in report.issues if issue.severity == "info"]

                if errors:
                    f.write("### 错误 (必须修复)\n\n")
                    for issue in errors:
                        f.write(f"- **{issue.key}**: {issue.message}\n")
                        if issue.suggestion:
                            f.write(f"  建议: {issue.suggestion}\n")
                        f.write("\n")

                if warnings:
                    f.write("### 警告 (建议修复)\n\n")
                    for issue in warnings:
                        f.write(f"- **{issue.key}**: {issue.message}\n")
                        if issue.suggestion:
                            f.write(f"  建议: {issue.suggestion}\n")
                        f.write("\n")

                if infos:
                    f.write("### 信息 (供参考)\n\n")
                    for issue in infos:
                        f.write(f"- **{issue.key}**: {issue.message}\n")
                        if issue.suggestion:
                            f.write(f"  建议: {issue.suggestion}\n")
                        f.write("\n")
            else:
                f.write("## 验证结果\n\n")
                f.write("✅ 未发现问题，翻译质量良好。\n")

        logging.info(f"验证报告已保存到: {output_path}")

    except Exception as e:
        raise ProcessingError(
            f"保存验证报告失败: {str(e)}",
            operation="_save_validation_report",
            stage="报告保存",
            affected_items=[output_path],
        )
