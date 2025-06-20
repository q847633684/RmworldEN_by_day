import csv
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, List

from colorama import Fore, Style
from tqdm import tqdm

try:
    from aliyunsdkalimt.request.v20181012 import TranslateGeneralRequest
    from aliyunsdkcore.client import AcsClient
except ImportError:
    logging.warning(
        "阿里云 SDK 未安装，机器翻译功能不可用。请运行：pip install aliyun-python-sdk-core aliyun-python-sdk-alimt"
    )
    AcsClient = None
    TranslateGeneralRequest = None


def translate_text(
    text: str, access_key_id: str, access_secret: str, region_id: str = "cn-hangzhou"
) -> str:
    """
    使用阿里云翻译 API 翻译文本，保留 [xxx] 占位符

    Args:
        text (str): 待翻译文本
        access_key_id (str): 阿里云访问密钥 ID
        access_secret (str): 阿里云访问密钥 Secret
        region_id (str): 阿里云区域 ID，默认为 'cn-hangzhou'

    Returns:
        str: 翻译后的文本

    Raises:
        RuntimeError: 如果阿里云 SDK 未安装
        Exception: 如果翻译 API 调用失败
    """
    print(f"{Fore.BLUE}翻译文本: {text[:50]}...{Style.RESET_ALL}")
    if AcsClient is None or TranslateGeneralRequest is None:
        print(f"{Fore.RED}阿里云 SDK 未安装{Style.RESET_ALL}")
        raise RuntimeError("阿里云 SDK 未安装，无法进行机器翻译")

    # 检查是否只包含占位符
    if re.fullmatch(r"(\s*\[[^\]]+\]\s*)+", text):
        print(f"{Fore.BLUE}文本仅含占位符，跳过翻译: {text}{Style.RESET_ALL}")
        return text

    try:
        # 分割文本，保留占位符
        parts = re.split(r"(\[[^\]]+\])", text)
        translated_parts = []

        client = AcsClient(access_key_id, access_secret, region_id)

        for part in parts:
            if re.fullmatch(r"\[[^\]]+\]", part):
                # 占位符，直接保留
                translated_parts.append(part)
                print(f"{Fore.BLUE}保留占位符: {part}{Style.RESET_ALL}")
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
                print(
                    f"{Fore.BLUE}翻译部分: {part[:30]}... -> {translated_text[:30]}...{Style.RESET_ALL}"
                )
            else:
                # 空白部分
                translated_parts.append(part)

        translated = "".join(translated_parts)
        print(
            f"{Fore.GREEN}翻译完成: {text[:30]}... -> {translated[:30]}...{Style.RESET_ALL}"
        )
        return translated

    except Exception as e:
        print(f"{Fore.RED}翻译失败: {text[:50]}..., 错误: {e}{Style.RESET_ALL}")
        return text


def translate_csv(input_path: str, output_path: str = None, **kwargs) -> None:
    """
    翻译 CSV 文件，生成包含翻译列的输出文件

    Args:
        input_path (str): 输入 CSV 文件路径
        output_path (str, optional): 输出 CSV 文件路径，默认为 None
        **kwargs: 可选参数（如 access_key_id, access_secret, region_id, sleep_sec）

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
    access_secret = kwargs.get("access_secret") or os.getenv("ALIYUN_ACCESS_SECRET")

    if not access_key_id or not access_secret:
        print(
            f"{Fore.RED}❌ 缺少阿里云 API 密钥，请设置环境变量或传入参数{Style.RESET_ALL}"
        )
        print("设置方法：")
        print("  export ALIYUN_ACCESS_KEY_ID='your_key'")
        print("  export ALIYUN_ACCESS_SECRET='your_secret'")
        return

    region_id = kwargs.get("region_id", "cn-hangzhou")
    sleep_sec = kwargs.get("sleep_sec", 0.5)

    print(
        f"{Fore.BLUE}翻译 CSV: input={input_path}, output={output_path}, region_id={region_id}"
    )

    if not os.path.exists(input_path):
        print(f"{Fore.RED}❌ 文件不存在: {input_path}{Style.RESET_ALL}")
        return

    try:
        rows: List[Dict[str, str]] = []

        with open(input_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "text" not in reader.fieldnames:
                print(
                    f"{Fore.RED}❌ CSV 文件缺少 'text' 列: {input_path}{Style.RESET_ALL}"
                )
                return

            total_rows = sum(1 for _ in reader)
            f.seek(0)
            reader = csv.DictReader(f)
            next(reader)  # 跳过表头

            print(f"{Fore.BLUE}开始翻译 {total_rows} 条记录...{Style.RESET_ALL}")

            for line_num, row in enumerate(
                tqdm(reader, total=total_rows, desc="翻译进度", unit="行"), 2
            ):
                text = row["text"].strip()
                print(
                    f"{Fore.BLUE}处理第 {line_num} 行: {text[:50]}...{Style.RESET_ALL}"
                )
                if not text:
                    row["translated"] = ""
                elif re.fullmatch(r"(\s*\[[^\]]+\]\s*)+", text):
                    row["translated"] = text
                    print(
                        f"{Fore.BLUE}第 {line_num} 行仅含占位符，跳过{Style.RESET_ALL}"
                    )
                else:
                    try:
                        translated = translate_text(
                            text, access_key_id, access_secret, region_id
                        )
                        row["translated"] = translated
                        if translated and translated.strip():
                            print(
                                f"{Fore.GREEN}✅ 第{line_num}行: {text[:30]}... => {translated[:30]}...{Style.RESET_ALL}"
                            )
                        else:
                            print(
                                f"{Fore.YELLOW}⚠️ 第{line_num}行翻译为空: {text[:50]}...{Style.RESET_ALL}"
                            )
                            print(
                                f"{Fore.YELLOW}第{line_num}行翻译失败。原文：{text[:50]}...{Style.RESET_ALL}"
                            )
                    except Exception as e:
                        print(
                            f"{Fore.RED}❌ 第{line_num}行翻译失败: {text[:50]}...{Style.RESET_ALL}"
                        )
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

        print(f"{Fore.GREEN}🎉 翻译完成，保存到: {output_path}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}❌ 翻译失败: {e}{Style.RESET_ALL}")
