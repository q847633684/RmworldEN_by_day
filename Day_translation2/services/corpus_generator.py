"""
Day Translation 2 - 语料生成服务

生成英中对照平行语料，用于翻译质量分析和改进。
遵循提示文件标准：PEP 8规范、具体异常处理、用户友好错误信息。
"""

import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import get_config
from ..core.extractors import (extract_definjected_translations,
                               extract_keyed_translations)
from ..models.exceptions import ImportError as TranslationImportError
from ..models.exceptions import ProcessingError, ValidationError
from ..models.result_models import (OperationResult, OperationStatus,
                                    OperationType)


def generate_parallel_corpus(
    mod_dir: str,
    output_csv: str,
    source_language: str = "English",
    target_language: str = "ChineseSimplified",
) -> OperationResult:
    """
    生成英中对照平行语料

    Args:
        mod_dir: 模组目录路径
        output_csv: 输出CSV文件路径
        source_language: 源语言
        target_language: 目标语言

    Returns:
        语料生成操作结果

    Raises:
        ValidationError: 当参数无效时
        TranslationImportError: 当目录不存在时
        ProcessingError: 当生成过程出现错误时
    """
    # 参数验证
    if not mod_dir or not output_csv:
        raise ValidationError(
            "模组目录和输出文件路径不能为空",
            field_name="required_params",
            expected_type="非空字符串",
        )

    if not Path(mod_dir).is_dir():
        raise TranslationImportError(f"模组目录不存在: {mod_dir}", file_path=mod_dir)

    try:
        logging.info(f"开始生成平行语料: {mod_dir}")

        # 提取源语言翻译
        source_translations = _extract_language_translations(mod_dir, source_language)
        logging.info(f"提取到 {len(source_translations)} 条源语言翻译")

        # 提取目标语言翻译
        target_translations = _extract_language_translations(mod_dir, target_language)
        logging.info(f"提取到 {len(target_translations)} 条目标语言翻译")

        # 匹配对应翻译
        parallel_pairs = _match_translations(source_translations, target_translations)
        logging.info(f"匹配到 {len(parallel_pairs)} 条对照翻译")

        # 生成语料统计
        statistics = _generate_corpus_statistics(parallel_pairs)

        # 保存平行语料
        _save_parallel_corpus(parallel_pairs, output_csv, statistics)

        return OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXPORT,
            message=f"平行语料生成完成，共 {len(parallel_pairs)} 条对照翻译",
            processed_count=len(source_translations) + len(target_translations),
            success_count=len(parallel_pairs),
        )

    except Exception as e:
        if isinstance(e, (ValidationError, TranslationImportError, ProcessingError)):
            raise
        raise ProcessingError(
            f"生成平行语料失败: {str(e)}", operation="generate_parallel_corpus", stage="语料生成"
        )


def _extract_language_translations(mod_dir: str, language: str) -> Dict[str, str]:
    """提取指定语言的翻译数据"""
    try:
        translations = {}

        # 提取Keyed翻译
        keyed_data = extract_keyed_translations(mod_dir, language)
        for key, text, tag, file_path in keyed_data:
            translations[key] = text

        # 提取DefInjected翻译
        definjected_data = extract_definjected_translations(mod_dir, language)
        for key, text, tag, file_path in definjected_data:
            translations[key] = text

        return translations

    except Exception as e:
        raise ProcessingError(
            f"提取 {language} 翻译数据失败: {str(e)}",
            operation="_extract_language_translations",
            stage="数据提取",
        )


def _match_translations(
    source_dict: Dict[str, str], target_dict: Dict[str, str]
) -> List[Tuple[str, str, str]]:
    """匹配源语言和目标语言的对应翻译"""
    try:
        parallel_pairs = []

        # 找出共同的key
        common_keys = set(source_dict.keys()) & set(target_dict.keys())

        for key in common_keys:
            source_text = source_dict[key].strip()
            target_text = target_dict[key].strip()

            # 过滤空文本和无效翻译
            if source_text and target_text and source_text != target_text:
                parallel_pairs.append((key, source_text, target_text))

        return parallel_pairs

    except Exception as e:
        raise ProcessingError(
            f"匹配翻译对照失败: {str(e)}", operation="_match_translations", stage="翻译匹配"
        )


def _generate_corpus_statistics(parallel_pairs: List[Tuple[str, str, str]]) -> Dict[str, any]:
    """生成语料统计信息"""
    try:
        statistics = {
            "total_pairs": len(parallel_pairs),
            "source_chars": 0,
            "target_chars": 0,
            "avg_source_length": 0,
            "avg_target_length": 0,
            "key_types": defaultdict(int),
        }

        if not parallel_pairs:
            return statistics

        total_source_chars = 0
        total_target_chars = 0

        for key, source_text, target_text in parallel_pairs:
            source_chars = len(source_text)
            target_chars = len(target_text)

            total_source_chars += source_chars
            total_target_chars += target_chars

            # 统计key类型
            if "." in key:
                key_type = key.split(".")[0]
            else:
                key_type = "Keyed"
            statistics["key_types"][key_type] += 1

        statistics["source_chars"] = total_source_chars
        statistics["target_chars"] = total_target_chars
        statistics["avg_source_length"] = total_source_chars / len(parallel_pairs)
        statistics["avg_target_length"] = total_target_chars / len(parallel_pairs)

        return statistics

    except Exception as e:
        raise ProcessingError(
            f"生成语料统计失败: {str(e)}", operation="_generate_corpus_statistics", stage="统计生成"
        )


def _save_parallel_corpus(
    parallel_pairs: List[Tuple[str, str, str]], output_path: str, statistics: Dict[str, any]
) -> None:
    """保存平行语料到CSV文件"""
    try:
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)

            # 写入头部信息
            writer.writerow(["# 平行语料统计"])
            writer.writerow([f"# 总对数: {statistics['total_pairs']}"])
            writer.writerow([f"# 源语言字符数: {statistics['source_chars']}"])
            writer.writerow([f"# 目标语言字符数: {statistics['target_chars']}"])
            writer.writerow([f"# 平均源语言长度: {statistics['avg_source_length']:.1f}"])
            writer.writerow([f"# 平均目标语言长度: {statistics['avg_target_length']:.1f}"])
            writer.writerow([])

            # 写入列标题
            writer.writerow(["key", "source_text", "target_text", "source_length", "target_length"])

            # 写入语料数据
            for key, source_text, target_text in parallel_pairs:
                writer.writerow([key, source_text, target_text, len(source_text), len(target_text)])

        logging.info(f"平行语料已保存到: {output_path}")

    except Exception as e:
        raise ProcessingError(
            f"保存平行语料失败: {str(e)}",
            operation="_save_parallel_corpus",
            stage="文件保存",
            affected_items=[output_path],
        )


def analyze_corpus_quality(corpus_csv: str) -> Dict[str, any]:
    """
    分析语料质量

    Args:
        corpus_csv: 平行语料CSV文件路径

    Returns:
        质量分析结果字典

    Raises:
        TranslationImportError: 当文件不存在时
        ProcessingError: 当分析过程出现错误时
    """
    if not Path(corpus_csv).is_file():
        raise TranslationImportError(f"语料文件不存在: {corpus_csv}", file_path=corpus_csv)

    try:
        quality_metrics = {
            "total_pairs": 0,
            "length_ratio_avg": 0,
            "length_ratio_std": 0,
            "suspicious_pairs": [],
            "quality_score": 0,
        }

        pairs = []
        length_ratios = []

        with open(corpus_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                if row.get("key", "").startswith("#"):
                    continue

                key = row.get("key", "")
                source_text = row.get("source_text", "")
                target_text = row.get("target_text", "")

                if key and source_text and target_text:
                    pairs.append((key, source_text, target_text))

                    # 计算长度比例
                    length_ratio = (
                        len(target_text) / len(source_text) if len(source_text) > 0 else 0
                    )
                    length_ratios.append(length_ratio)

        if pairs:
            quality_metrics["total_pairs"] = len(pairs)
            quality_metrics["length_ratio_avg"] = sum(length_ratios) / len(length_ratios)

            # 计算标准差
            avg_ratio = quality_metrics["length_ratio_avg"]
            variance = sum((r - avg_ratio) ** 2 for r in length_ratios) / len(length_ratios)
            quality_metrics["length_ratio_std"] = variance**0.5

            # 找出可疑的翻译对
            for i, (key, source, target) in enumerate(pairs):
                ratio = length_ratios[i]
                if abs(ratio - avg_ratio) > 2 * quality_metrics["length_ratio_std"]:
                    quality_metrics["suspicious_pairs"].append(
                        {
                            "key": key,
                            "source": source[:50] + "..." if len(source) > 50 else source,
                            "target": target[:50] + "..." if len(target) > 50 else target,
                            "length_ratio": ratio,
                        }
                    )

            # 计算质量分数 (0-100)
            suspicious_rate = len(quality_metrics["suspicious_pairs"]) / len(pairs)
            quality_metrics["quality_score"] = max(0, 100 - suspicious_rate * 100)

        return quality_metrics

    except Exception as e:
        raise ProcessingError(
            f"分析语料质量失败: {str(e)}", operation="analyze_corpus_quality", stage="质量分析"
        )
