import csv
from utils.logging_config import get_logger
from utils.ui_style import ui
import os
import re
import time
from typing import List, Dict
from pathlib import Path
from tqdm import tqdm

logger = get_logger(__name__)

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkalimt.request.v20181012 import TranslateGeneralRequest
except ImportError:
    logger.warning(
        "阿里云 SDK 未安装，机器翻译功能不可用。请运行：pip install aliyun-python-sdk-core aliyun-python-sdk-alimt"
    )
    AcsClient = None
    TranslateGeneralRequest = None


def translate_text(
    text: str,
    access_key_id: str,
    access_key_secret: str,
    region_id: str = "cn-hangzhou",
) -> str:
    """
    使用阿里云翻译 API 翻译文本，保留 [xxx] 占位符

    Args:
        text (str): 待翻译文本
        access_key_id (str): 阿里云访问密钥 ID
        access_key_secret (str): 阿里云访问密钥 Secret
        region_id (str): 阿里云区域 ID，默认为 'cn-hangzhou'

    Returns:
        str: 翻译后的文本

    Raises:
        RuntimeError: 如果阿里云 SDK 未安装
        Exception: 如果翻译 API 调用失败
    """
    ui.print_info(f"翻译文本: {text[:50]}...")
    if AcsClient is None or TranslateGeneralRequest is None:
        ui.print_error("阿里云 SDK 未安装")
        raise RuntimeError("阿里云 SDK 未安装，无法进行机器翻译")

    # 检查是否只包含占位符
    if re.fullmatch(r"(\s*\[[^\]]+\]\s*)+", text):
        ui.print_info(f"文本仅含占位符，跳过翻译: {text}")
        return text

    try:
        # 处理ALIMT标签：保护不需要翻译的内容
        alimt_pattern = r"<ALIMT >(.*?)</ALIMT>"
        alimt_matches = {}
        idx = 1

        def replace_alimt(match):
            nonlocal idx
            placeholder = f"(ALIMT_PH_{idx})"
            alimt_matches[placeholder] = match.group(1)
            idx += 1
            return placeholder

        # 替换ALIMT标签为占位符
        protected_text = re.sub(alimt_pattern, replace_alimt, text, flags=re.DOTALL)

        # 分割文本，保留占位符
        parts = re.split(r"(\[[^\]]+\])", protected_text)
        translated_parts = []

        client = AcsClient(access_key_id, access_key_secret, region_id)

        for part in parts:
            if re.fullmatch(r"\[[^\]]+\]", part):
                # 占位符，直接保留
                translated_parts.append(part)
                ui.print_info(f"保留占位符: {part}")
            elif part.strip():
                # 需要翻译的文本
                request = TranslateGeneralRequest()
                request.set_accept_format("json")
                request.set_SourceLanguage("en")
                request.set_TargetLanguage("zh")
                request.set_SourceText(part)
                response = client.do_action_with_exception(request)
                import json

                result = json.loads(response)
                translated_text = result.get("Data", {}).get("Translated", part)
                translated_parts.append(translated_text)
                ui.print_info(f"翻译部分: {part[:30]}... -> {translated_text[:30]}...")
            else:
                # 空白部分
                translated_parts.append(part)

        translated = "".join(translated_parts)

        # 恢复ALIMT标签内容
        for placeholder, original_content in alimt_matches.items():
            translated = translated.replace(placeholder, original_content)
            ui.print_info(f"恢复ALIMT内容: {placeholder} -> {original_content[:30]}...")

        ui.print_success(f"翻译完成: {text[:30]}... -> {translated[:30]}...")
        return translated

    except (ConnectionError, TimeoutError, ValueError, RuntimeError) as e:
        ui.print_error(f"翻译失败: {text[:50]}..., 错误: {e}")
        return text


def translate_csv(input_path: str, output_path: str = None, **kwargs) -> None:
    """
    翻译 CSV 文件，生成包含翻译列的输出文件

    Args:
        input_path (str): 输入 CSV 文件路径
        output_path (str, optional): 输出 CSV 文件路径，默认为 None
        **kwargs: 可选参数（如 access_key_id, access_key_secret, region_id, sleep_sec）

    Raises:
        FileNotFoundError: 如果输入文件不存在
        KeyError: 如果 CSV 缺少 'text' 列
    """
    if output_path is None:
        input_file = Path(input_path)
        output_path = str(
            input_file.parent / f"{input_file.stem}_translated{input_file.suffix}"
        )

    # 获取 API 密钥
    access_key_id = kwargs.get("access_key_id") or os.getenv("ALIYUN_ACCESS_KEY_ID")
    access_key_secret = kwargs.get("access_key_secret") or os.getenv(
        "ALIYUN_ACCESS_SECRET"
    )

    if not access_key_id or not access_key_secret:
        ui.print_error("❌ 缺少阿里云 API 密钥，请设置环境变量或传入参数")
        ui.print_info("设置方法：")
        ui.print_info("  export ALIYUN_ACCESS_KEY_ID='your_key'")
        ui.print_info("  export ALIYUN_ACCESS_SECRET='your_secret'")
        return

    region_id = kwargs.get("region_id", "cn-hangzhou")
    sleep_sec = kwargs.get("sleep_sec", 0.5)

    ui.print_info(
        f"翻译 CSV: input={input_path}, output={output_path}, region_id={region_id}"
    )

    if not os.path.exists(input_path):
        ui.print_error(f"❌ 文件不存在: {input_path}")
        return

    try:
        rows: List[Dict[str, str]] = []

        with open(input_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "text" not in reader.fieldnames:
                ui.print_error(f"❌ CSV 文件缺少 'text' 列: {input_path}")
                return

            total_rows = sum(1 for _ in reader)
            f.seek(0)
            reader = csv.DictReader(f)
            next(reader)  # 跳过表头

            ui.print_info(f"开始翻译 {total_rows} 条记录...")

            for line_num, row in enumerate(
                tqdm(reader, total=total_rows, desc="翻译进度", unit="行"), 2
            ):
                text = row["text"].strip()
                ui.print_info(f"处理第 {line_num} 行: {text[:50]}...")
                if not text:
                    row["translated"] = ""
                elif re.fullmatch(r"(\s*\[[^\]]+\]\s*)+", text):
                    row["translated"] = text
                    ui.print_info(f"第 {line_num} 行仅含占位符，跳过")
                else:
                    try:
                        translated = translate_text(
                            text, access_key_id, access_key_secret, region_id
                        )
                        row["translated"] = translated
                        if translated and translated.strip():
                            ui.print_success(
                                f"✅ 第{line_num}行: {text[:30]}... => {translated[:30]}..."
                            )
                        else:
                            ui.print_warning(
                                f"⚠️ 第{line_num}行翻译为空: {text[:50]}..."
                            )
                            ui.print_warning(
                                f"第{line_num}行翻译失败。原文：{text[:50]}..."
                            )
                    except (
                        ConnectionError,
                        TimeoutError,
                        ValueError,
                        RuntimeError,
                    ):
                        ui.print_error(f"❌ 第{line_num}行翻译失败: {text[:50]}...")
                        row["translated"] = text

                rows.append(row)
                time.sleep(sleep_sec)

        output_dir = os.path.dirname(output_path) or "."
        os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            if rows:
                fieldnames = rows[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        ui.print_success(f"🎉 翻译完成，保存到: {output_path}")

    except (OSError, IOError, csv.Error, ValueError, RuntimeError) as e:
        ui.print_error(f"❌ 翻译失败: {e}")
