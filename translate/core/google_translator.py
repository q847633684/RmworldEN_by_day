"""
Google翻译工具
使用googletrans库进行免费翻译
"""

import csv
import time
import re
from typing import List, Dict, Optional, Any
from pathlib import Path
from tqdm import tqdm
from utils.logging_config import get_logger
from utils.ui_style import ui
from .resume_base import ResumeBase

logger = get_logger(__name__)

try:
    from deep_translator import GoogleTranslator as DeepTranslator
except ImportError:
    logger.warning(
        "deep-translator 库未安装，Google翻译功能不可用。请运行：pip install deep-translator"
    )
    DeepTranslator = None


def translate_text(
    text: str, target_lang: str = "zh-CN", source_lang: str = "auto"
) -> str:
    """
    使用Google翻译API翻译文本

    Args:
        text (str): 待翻译文本
        target_lang (str): 目标语言代码，默认为 'zh-CN'（简体中文）
        source_lang (str): 源语言代码，默认为 'auto'（自动检测）

    Returns:
        str: 翻译后的文本

    Raises:
        RuntimeError: 如果deep-translator库未安装
        Exception: 如果翻译API调用失败
    """
    if DeepTranslator is None:
        ui.print_error("deep-translator 库未安装")
        raise RuntimeError("deep-translator 库未安装，无法进行Google翻译")

    if not text or not text.strip():
        return text

    try:
        translator = DeepTranslator(source=source_lang, target=target_lang)
        result = translator.translate(text)

        if result and result.strip():
            return result
        else:
            logger.warning(f"Google翻译返回空结果: {text}")
            return text

    except Exception as e:
        logger.error(f"Google翻译失败: {text[:50]}... 错误: {str(e)}")
        # 如果翻译失败，返回原文
        return text


class GoogleTranslator(ResumeBase):
    """Google翻译工具包装器"""

    def __init__(self, target_lang: str = "zh-CN", source_lang: str = "auto"):
        """
        初始化Google翻译器

        Args:
            target_lang (str): 目标语言代码，默认为 'zh-CN'
            source_lang (str): 源语言代码，默认为 'auto'
        """
        super().__init__()
        self.target_lang = target_lang
        self.source_lang = source_lang
        self.translator = (
            DeepTranslator(source=source_lang, target=target_lang)
            if DeepTranslator
            else None
        )

    def translate_csv_file(
        self,
        input_file: str,
        output_file: str,
        text_column: str = "Text",
        key_column: str = "Key",
        resume: bool = True,
    ) -> bool:
        """
        翻译CSV文件

        Args:
            input_file (str): 输入CSV文件路径
            output_file (str): 输出CSV文件路径
            text_column (str): 包含待翻译文本的列名
            key_column (str): 用作唯一标识的列名
            resume (bool): 是否支持断点续传

        Returns:
            bool: 翻译是否成功
        """
        if not self.translator:
            ui.print_error("Google翻译器未初始化")
            return False

        input_path = Path(input_file)
        output_path = Path(output_file)

        if not input_path.exists():
            ui.print_error(f"输入文件不存在: {input_file}")
            return False

        # 创建输出目录
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 检查是否需要断点续传
        start_row = 0
        if resume and output_path.exists():
            start_row = self._get_resume_row(output_file, key_column)
            if start_row > 0:
                ui.print_info(f"从第 {start_row + 1} 行继续翻译")

        try:
            # 读取CSV文件
            with open(input_path, "r", encoding="utf-8") as infile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames

                if text_column not in fieldnames:
                    ui.print_error(f"CSV文件中未找到文本列: {text_column}")
                    return False

                rows = list(reader)
                total_rows = len(rows)

            if total_rows == 0:
                ui.print_warning("CSV文件为空")
                return True

            # 写入翻译结果
            with open(output_path, "w", encoding="utf-8", newline="") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

                for i, row in enumerate(tqdm(rows, desc="翻译进度")):
                    # 跳过已翻译的行
                    if i < start_row:
                        writer.writerow(row)
                        continue

                    # 获取待翻译文本
                    original_text = row.get(text_column, "").strip()

                    if not original_text:
                        # 空文本直接写入
                        writer.writerow(row)
                        continue

                    # 翻译文本
                    try:
                        translated_text = self.translate_text(original_text)
                        row[text_column] = translated_text

                        # 更新进度
                        ui.print_progress_bar(
                            i + 1,
                            total_rows,
                            width=40,
                            prefix="翻译进度",
                            suffix=f"第 {i + 1}/{total_rows} 行",
                        )

                    except Exception as e:
                        logger.error(f"翻译第 {i + 1} 行失败: {str(e)}")
                        ui.print_warning(f"第 {i + 1} 行翻译失败，保留原文")
                        # 翻译失败时保留原文
                        pass

                    # 写入行
                    writer.writerow(row)

                    # 保存进度
                    if resume:
                        self._save_progress(output_file, i + 1)

                    # 添加延迟避免请求过于频繁
                    time.sleep(0.1)

            ui.print_success(f"翻译完成！结果保存到: {output_file}")
            return True

        except Exception as e:
            logger.error(f"翻译CSV文件失败: {str(e)}")
            ui.print_error(f"翻译失败: {str(e)}")
            return False

    def translate_text(self, text: str) -> str:
        """
        翻译单个文本

        Args:
            text (str): 待翻译文本

        Returns:
            str: 翻译后的文本
        """
        return translate_text(text, self.target_lang, self.source_lang)

    def batch_translate(self, texts: List[str], batch_size: int = 10) -> List[str]:
        """
        批量翻译文本列表

        Args:
            texts (List[str]): 待翻译文本列表
            batch_size (int): 批处理大小

        Returns:
            List[str]: 翻译后的文本列表
        """
        if not self.translator:
            ui.print_error("Google翻译器未初始化")
            return texts

        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_results = []

            for text in batch:
                try:
                    translated = self.translate_text(text)
                    batch_results.append(translated)
                except Exception as e:
                    logger.error(f"批量翻译失败: {str(e)}")
                    batch_results.append(text)  # 失败时保留原文

            results.extend(batch_results)

            # 添加延迟避免请求过于频繁
            time.sleep(0.5)

        return results

    def get_supported_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表

        Returns:
            Dict[str, str]: 语言代码到语言名称的映射
        """
        if not self.translator:
            return {}

        try:
            # googletrans库支持的语言
            languages = {
                "af": "南非荷兰语",
                "sq": "阿尔巴尼亚语",
                "am": "阿姆哈拉语",
                "ar": "阿拉伯语",
                "hy": "亚美尼亚语",
                "az": "阿塞拜疆语",
                "eu": "巴斯克语",
                "be": "白俄罗斯语",
                "bn": "孟加拉语",
                "bs": "波斯尼亚语",
                "bg": "保加利亚语",
                "ca": "加泰罗尼亚语",
                "ceb": "宿务语",
                "ny": "齐切瓦语",
                "zh-CN": "中文（简体）",
                "zh-TW": "中文（繁体）",
                "co": "科西嘉语",
                "hr": "克罗地亚语",
                "cs": "捷克语",
                "da": "丹麦语",
                "nl": "荷兰语",
                "en": "英语",
                "eo": "世界语",
                "et": "爱沙尼亚语",
                "tl": "菲律宾语",
                "fi": "芬兰语",
                "fr": "法语",
                "fy": "弗里西语",
                "gl": "加利西亚语",
                "ka": "格鲁吉亚语",
                "de": "德语",
                "el": "希腊语",
                "gu": "古吉拉特语",
                "ht": "海地克里奥尔语",
                "ha": "豪萨语",
                "haw": "夏威夷语",
                "iw": "希伯来语",
                "hi": "印地语",
                "hmn": "苗语",
                "hu": "匈牙利语",
                "is": "冰岛语",
                "ig": "伊博语",
                "id": "印尼语",
                "ga": "爱尔兰语",
                "it": "意大利语",
                "ja": "日语",
                "jw": "爪哇语",
                "kn": "卡纳达语",
                "kk": "哈萨克语",
                "km": "高棉语",
                "ko": "韩语",
                "ku": "库尔德语",
                "ky": "吉尔吉斯语",
                "lo": "老挝语",
                "la": "拉丁语",
                "lv": "拉脱维亚语",
                "lt": "立陶宛语",
                "lb": "卢森堡语",
                "mk": "马其顿语",
                "mg": "马尔加什语",
                "ms": "马来语",
                "ml": "马拉雅拉姆语",
                "mt": "马耳他语",
                "mi": "毛利语",
                "mr": "马拉地语",
                "mn": "蒙古语",
                "my": "缅甸语",
                "ne": "尼泊尔语",
                "no": "挪威语",
                "ps": "普什图语",
                "fa": "波斯语",
                "pl": "波兰语",
                "pt": "葡萄牙语",
                "ma": "旁遮普语",
                "ro": "罗马尼亚语",
                "ru": "俄语",
                "sm": "萨摩亚语",
                "gd": "苏格兰盖尔语",
                "sr": "塞尔维亚语",
                "st": "塞索托语",
                "sn": "修纳语",
                "sd": "信德语",
                "si": "僧伽罗语",
                "sk": "斯洛伐克语",
                "sl": "斯洛文尼亚语",
                "so": "索马里语",
                "es": "西班牙语",
                "su": "巽他语",
                "sw": "斯瓦希里语",
                "sv": "瑞典语",
                "tg": "塔吉克语",
                "ta": "泰米尔语",
                "te": "泰卢固语",
                "th": "泰语",
                "tr": "土耳其语",
                "uk": "乌克兰语",
                "ur": "乌尔都语",
                "uz": "乌兹别克语",
                "vi": "越南语",
                "cy": "威尔士语",
                "xh": "科萨语",
                "yi": "意第绪语",
                "yo": "约鲁巴语",
                "zu": "祖鲁语",
            }
            return languages
        except Exception as e:
            logger.error(f"获取支持语言失败: {str(e)}")
            return {}

    def test_connection(self) -> bool:
        """
        测试Google翻译连接

        Returns:
            bool: 连接是否成功
        """
        if not self.translator:
            ui.print_error("Google翻译器未初始化")
            return False

        try:
            test_text = "Hello, world!"
            result = self.translate_text(test_text)

            if result and result != test_text:
                ui.print_success("Google翻译连接测试成功")
                return True
            else:
                ui.print_warning("Google翻译连接测试失败：返回结果异常")
                return False

        except Exception as e:
            logger.error(f"Google翻译连接测试失败: {str(e)}")
            ui.print_error(f"连接测试失败: {str(e)}")
            return False


def main():
    """测试Google翻译器"""
    translator = GoogleTranslator()

    # 测试连接
    if translator.test_connection():
        # 测试单个文本翻译
        test_text = "Hello, this is a test message."
        translated = translator.translate_text(test_text)
        print(f"原文: {test_text}")
        print(f"译文: {translated}")

        # 显示支持的语言
        languages = translator.get_supported_languages()
        print(f"\n支持的语言数量: {len(languages)}")
        print("部分支持的语言:")
        for code, name in list(languages.items())[:10]:
            print(f"  {code}: {name}")


if __name__ == "__main__":
    main()
