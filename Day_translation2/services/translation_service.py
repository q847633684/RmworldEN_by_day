"""
Day Translation 2 - 机器翻译服务

提供CSV文件的机器翻译功能，支持阿里云翻译API。
遵循提示文件标准：PEP 8规范、具体异常处理、用户友好错误信息。
"""

import csv
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 使用绝对导入
from config import get_config
from models.exceptions import ImportError as TranslationImportError
from models.exceptions import ProcessingError, ValidationError
from models.result_models import OperationResult, OperationStatus, OperationType


def translate_csv(
    input_csv: str,
    output_csv: str,
    access_key: str,
    secret_key: str,
    source_language: str = "en",
    target_language: str = "zh",
) -> OperationResult:
    """
    翻译CSV文件中的文本内容

    Args:
        input_csv: 输入CSV文件路径
        output_csv: 输出CSV文件路径
        access_key: 阿里云Access Key ID
        secret_key: 阿里云Access Key Secret
        source_language: 源语言代码
        target_language: 目标语言代码

    Returns:
        翻译操作结果

    Raises:
        ValidationError: 当参数无效时
        TranslationImportError: 当文件操作失败时
        ProcessingError: 当翻译过程出现错误时
    """
    # 参数验证
    if not all([input_csv, output_csv, access_key, secret_key]):
        raise ValidationError(
            "所有参数都不能为空",
            field_name="required_params",
            expected_type="非空字符串",
        )

    if not Path(input_csv).is_file():
        raise TranslationImportError(
            f"输入CSV文件不存在: {input_csv}", file_path=input_csv
        )

    try:
        # 创建翻译客户端
        translator = _create_translation_client(access_key, secret_key)

        # 读取CSV数据
        translations = _load_csv_data(input_csv)

        # 执行翻译
        translated_data = _translate_data(
            translator, translations, source_language, target_language
        )

        # 保存结果
        _save_translated_csv(translated_data, output_csv)

        return OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.TRANSLATION,
            message=f"机器翻译完成，已保存到 {output_csv}",
            processed_count=len(translations),
            success_count=len(translated_data),
        )

    except Exception as e:
        if isinstance(e, (ValidationError, TranslationImportError, ProcessingError)):
            raise
        raise ProcessingError(
            f"机器翻译失败: {str(e)}", operation="translate_csv", stage="翻译处理"
        )


def _create_translation_client(access_key: str, secret_key: str):
    """创建阿里云翻译客户端"""
    try:
        from alibabacloud_alimt20181012.client import Client as AliMtClient
        from alibabacloud_tea_openapi import models as open_api_models

        config = open_api_models.Config(
            access_key_id=access_key,
            access_key_secret=secret_key,
            endpoint="mt.cn-hangzhou.aliyuncs.com",
        )

        return AliMtClient(config)

    except ImportError:
        raise ProcessingError(
            "缺少阿里云SDK依赖包，请安装: pip install alibabacloud-alimt20181012",
            operation="_create_translation_client",
            stage="依赖检查",
        )
    except Exception as e:
        raise ProcessingError(
            f"创建翻译客户端失败: {str(e)}",
            operation="_create_translation_client",
            stage="客户端初始化",
        )


def _load_csv_data(csv_path: str) -> List[Dict[str, str]]:
    """从CSV文件加载数据"""
    try:
        data = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # 验证必要的列
            if "key" not in reader.fieldnames or "text" not in reader.fieldnames:
                raise TranslationImportError(
                    f"CSV文件缺少必要的列（key, text）: {csv_path}", file_path=csv_path
                )

            for row in reader:
                if row["key"] and row["text"]:
                    data.append(row)

        return data

    except Exception as e:
        if isinstance(e, TranslationImportError):
            raise
        raise TranslationImportError(f"读取CSV文件失败: {str(e)}", file_path=csv_path)


def _translate_data(
    translator, data: List[Dict[str, str]], source_lang: str, target_lang: str
) -> List[Dict[str, str]]:
    """翻译数据"""
    try:
        from alibabacloud_alimt20181012 import models as alimt_models

        translated_data = []

        # 使用进度条显示翻译进度
        with tqdm(total=len(data), desc="翻译进度", unit="条") as pbar:
            for item in data:
                try:
                    # 创建翻译请求
                    request = alimt_models.TranslateGeneralRequest(
                        format_type="text",
                        source_language=source_lang,
                        target_language=target_lang,
                        source_text=item["text"],
                        scene="general",
                    )

                    # 执行翻译
                    response = translator.translate_general(request)

                    if response.body.code == 200:
                        # 翻译成功
                        translated_item = item.copy()
                        translated_item["translated"] = response.body.data.translated
                        translated_data.append(translated_item)
                    else:
                        # 翻译失败，保留原文
                        logging.warning(
                            f"翻译失败: {item['key']}, 错误码: {response.body.code}"
                        )
                        translated_item = item.copy()
                        translated_item["translated"] = item["text"]  # 保留原文
                        translated_data.append(translated_item)

                    # 添加延迟避免API限制
                    time.sleep(0.1)

                except Exception as e:
                    logging.error(f"翻译请求异常: {item['key']}, 错误: {e}")
                    # 保留原文
                    translated_item = item.copy()
                    translated_item["translated"] = item["text"]
                    translated_data.append(translated_item)

                finally:
                    pbar.update(1)

        return translated_data

    except Exception as e:
        raise ProcessingError(
            f"翻译数据处理失败: {str(e)}", operation="_translate_data", stage="翻译执行"
        )


def _save_translated_csv(data: List[Dict[str, str]], output_path: str) -> None:
    """保存翻译后的数据到CSV文件"""
    try:
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

    except Exception as e:
        raise ProcessingError(
            f"保存翻译结果失败: {str(e)}",
            operation="_save_translated_csv",
            stage="文件保存",
            affected_items=[output_path],
        )
