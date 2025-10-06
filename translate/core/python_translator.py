import csv
from utils.logging_config import get_logger
from utils.ui_style import ui
import os
import re
import time
from typing import List, Dict, Optional, Any
from pathlib import Path
from tqdm import tqdm
from .resume_base import ResumeBase

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
    支持 protected_text 字段优先翻译

    Args:
        input_path (str): 输入 CSV 文件路径
        output_path (str, optional): 输出 CSV 文件路径，默认为 None
        **kwargs: 可选参数（如 access_key_id, access_key_secret, region_id, sleep_sec）

    Raises:
        FileNotFoundError: 如果输入文件不存在
        KeyError: 如果 CSV 缺少 'text' 或 'protected_text' 列
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
            fieldnames = reader.fieldnames

            # 检查是否有text或protected_text字段
            if "text" not in fieldnames and "protected_text" not in fieldnames:
                ui.print_error(
                    f"❌ CSV 文件缺少 'text' 或 'protected_text' 列: {input_path}"
                )
                return

            # 确定使用哪个字段进行翻译
            use_protected_text = "protected_text" in fieldnames
            translation_field = "protected_text" if use_protected_text else "text"

            if use_protected_text:
                ui.print_info("🔒 检测到 protected_text 字段，将优先翻译保护后的内容")
            else:
                ui.print_info("📝 使用 text 字段进行翻译")

            total_rows = sum(1 for _ in reader)
            f.seek(0)
            reader = csv.DictReader(f)
            next(reader)  # 跳过表头

            ui.print_info(f"开始翻译 {total_rows} 条记录...")

            for line_num, row in enumerate(
                tqdm(reader, total=total_rows, desc="翻译进度", unit="行"), 2
            ):
                text = row[translation_field].strip()
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


class PythonTranslator(ResumeBase):
    """Python翻译器类，提供恢复功能"""

    def __init__(self):
        self.logger = get_logger(__name__)

    def resume_translation(self, input_csv: str, output_csv: str, protected_text: str) -> bool:
        """
        恢复翻译任务（基于文件对比）

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径

        Returns:
            bool: 是否成功恢复
        """
        # 通过文件对比获取实际的恢复行号
        resume_line = self.get_resume_line_from_files(input_csv, output_csv)

        ui.print_info(f"从第 {resume_line} 行开始恢复翻译")

        # 从新配置系统获取必要的参数
        try:
            from user_config import UserConfigManager

            config_manager = UserConfigManager()
            primary_api = config_manager.get_primary_api()

            if primary_api:
                kwargs = {
                    "access_key_id": primary_api.get_value("access_key_id", ""),
                    "access_key_secret": primary_api.get_value("access_key_secret", ""),
                    "region_id": primary_api.get_value("region", "cn-hangzhou"),
                    "sleep_sec": primary_api.get_value("sleep_sec", 0.5),
                }
            else:
                kwargs = {}

        except (ImportError, AttributeError, KeyError, ValueError):
            kwargs = {}

        # 调用原有的翻译函数，但需要修改以支持恢复
        return self._translate_csv_with_resume(
            input_csv, output_csv, resume_line, protected_text, **kwargs
        )

    def get_status(self) -> Dict[str, Any]:
        """获取Python翻译器状态"""
        try:
            # 检查阿里云SDK是否可用
            sdk_available = (
                AcsClient is not None and TranslateGeneralRequest is not None
            )

            return {
                "available": sdk_available,
                "sdk_available": sdk_available,
                "reason": "SDK不可用" if not sdk_available else "正常",
            }
        except Exception as e:
            return {"available": False, "sdk_available": False, "reason": str(e)}

    def _translate_csv_with_resume(
        self, input_path: str, output_path: str, resume_line: int, **kwargs
    ) -> bool:
        """带恢复功能的CSV翻译"""
        try:
            # 获取 API 密钥
            access_key_id = kwargs.get("access_key_id") or os.getenv(
                "ALIYUN_ACCESS_KEY_ID"
            )
            access_key_secret = kwargs.get("access_key_secret") or os.getenv(
                "ALIYUN_ACCESS_SECRET"
            )

            if not access_key_id or not access_key_secret:
                ui.print_error("❌ 缺少阿里云 API 密钥")
                return False

            region_id = kwargs.get("region_id", "cn-hangzhou")
            sleep_sec = kwargs.get("sleep_sec", 0.5)

            # 读取输入文件
            rows: List[Dict[str, str]] = []
            with open(input_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for i, row in enumerate(reader, 1):
                    if i >= resume_line:  # 从恢复行开始
                        rows.append(row)

            if not rows:
                ui.print_info("没有需要翻译的内容")
                return True

            # 翻译
            translated_rows = []
            for row in tqdm(rows, desc="翻译进度"):
                # 优先使用protected_text字段
                text_to_translate = row.get("protected_text", row.get("text", ""))

                if text_to_translate.strip():
                    try:
                        translated_text = translate_text(
                            text_to_translate,
                            access_key_id,
                            access_key_secret,
                            region_id,
                        )
                        row["translated"] = translated_text
                    except Exception as e:
                        ui.print_warning(f"翻译失败: {e}")
                        row["translated"] = text_to_translate
                else:
                    row["translated"] = ""

                translated_rows.append(row)
                time.sleep(sleep_sec)

            # 读取已有的输出文件内容（如果有的话）
            existing_rows = []
            if os.path.exists(output_path):
                with open(output_path, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    existing_rows = list(reader)

            # 合并结果
            all_rows = existing_rows + translated_rows

            # 写入输出文件
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                if fieldnames:
                    writer = csv.DictWriter(f, fieldnames=fieldnames + ["translated"])
                    writer.writeheader()
                    writer.writerows(all_rows)

            ui.print_success(f"✅ 翻译完成: {output_path}")
            return True

        except Exception as e:
            ui.print_error(f"❌ 恢复翻译失败: {e}")
            return False
