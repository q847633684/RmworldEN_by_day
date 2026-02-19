"""
翻译器工厂
负责创建和管理不同类型的翻译器实例
支持：阿里云(付费)、Google(免费, deep-translator)
Google 翻译时按占位符分段，只翻译非占位符部分，与阿里云逻辑一致。
"""

import csv
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Tuple, Dict
from utils.logging_config import get_logger
from tqdm import tqdm

# 翻译配置已迁移到新配置系统
from .core.java_translator import JavaTranslator
from .core.python_translator import translate_csv, PythonTranslator
from .core.placeholders import PlaceholderManager
from .core.resume_base import ResumeBase


class TranslatorFactory:
    """翻译器工厂类"""

    def __init__(self, config: dict):
        """
        初始化翻译器工厂

        Args:
            config: 翻译配置
        """
        self.logger = get_logger(f"{__name__}.TranslatorFactory")
        self.config = config

    def create_java_translator(self):
        """创建Java翻译器实例"""
        try:
            return JavaTranslatorAdapter(JavaTranslator(), self.config)
        except ImportError as e:
            self.logger.debug("Java翻译器导入失败: %s", e)
            raise RuntimeError("Java翻译器不可用") from e
        except Exception as e:
            self.logger.debug("创建Java翻译器失败: %s", e)
            raise RuntimeError(f"创建Java翻译器失败: {str(e)}") from e

    def create_python_translator(self):
        """创建Python翻译器实例"""
        try:
            return PythonTranslatorAdapter(PythonTranslator(), self.config)
        except ImportError as e:
            self.logger.debug("Python翻译器导入失败: %s", e)
            raise RuntimeError("Python翻译器不可用") from e
        except Exception as e:
            self.logger.debug("创建Python翻译器失败: %s", e)
            raise RuntimeError(f"创建Python翻译器失败: {str(e)}") from e

    def create_dictionary_translator(self, dictionary_type: str = "adult"):
        """创建词典翻译器实例"""
        try:
            return PlaceholderManagerAdapter(
                PlaceholderManager(dictionary_type), self.config
            )
        except ImportError as e:
            self.logger.debug("占位符管理器导入失败: %s", e)
            raise RuntimeError("占位符管理器不可用") from e
        except Exception as e:
            self.logger.debug("创建占位符管理器失败: %s", e)
            raise RuntimeError(f"创建占位符管理器失败: {str(e)}") from e

    def create_google_translator(self):
        """创建 Google 免费翻译器实例（deep-translator，无需 API 密钥）"""
        try:
            from .core.google_translator import GoogleTranslator
            return GoogleTranslatorAdapter(GoogleTranslator(), self.config)
        except ImportError as e:
            self.logger.debug("Google 翻译器导入失败: %s", e)
            raise RuntimeError("Google 翻译器不可用，请安装: pip install deep-translator") from e
        except Exception as e:
            self.logger.debug("创建 Google 翻译器失败: %s", e)
            raise RuntimeError(f"创建 Google 翻译器失败: {str(e)}") from e


class JavaTranslatorAdapter:
    """Java翻译器适配器"""

    def __init__(self, java_translator, config: dict):
        """
        初始化Java翻译器适配器

        Args:
            java_translator: Java翻译器实例
            config: 翻译配置
        """
        self.java_translator = java_translator
        self.config = config
        self.logger = get_logger(f"{__name__}.JavaTranslatorAdapter")

    def translate_csv(
        self, input_csv: str, output_csv: str, protected_text: str, **kwargs
    ) -> bool:
        """
        翻译CSV文件

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径
            **kwargs: 其他参数

        Returns:
            bool: 翻译是否成功
        """
        try:
            # 从配置或kwargs中获取API密钥
            access_key_id = kwargs.get("access_key_id") or self.config.get(
                "access_key_id"
            )
            access_key_secret = kwargs.get("access_key_secret") or self.config.get(
                "access_key_secret"
            )

            if not access_key_id or not access_key_secret:
                self.logger.error("缺少阿里云API密钥")
                return False

            # 调用Java翻译器
            success = self.java_translator.translate_csv(
                input_csv,
                output_csv,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                model_id=kwargs.get("model_id", self.config.get("model_id", 27345)),
                enable_interrupt=kwargs.get(
                    "enable_interrupt", self.config.get("enable_interrupt", True)
                ),
                resume_line=kwargs.get("resume_line"),
                protected_text=protected_text,
            )

            self.logger.info("Java翻译完成: %s -> %s", input_csv, output_csv)
            return success

        except Exception as e:
            self.logger.error("Java翻译失败: %s", e, exc_info=True)
            return False

    def can_resume_translation(self, input_csv: str, output_csv: str) -> Optional[str]:
        """检查是否可以恢复翻译"""
        try:
            return self.java_translator.can_resume_translation(input_csv, output_csv)
        except Exception as e:
            self.logger.debug("检查恢复状态失败: %s", e)
            return None

    def resume_translation(
        self, input_csv: str, output_csv: str, protected_text: str
    ) -> bool:
        """恢复翻译"""
        try:
            return self.java_translator.resume_translation(
                input_csv, output_csv, protected_text
            )
        except Exception as e:
            self.logger.error("恢复翻译失败: %s", e, exc_info=True)
            return False

    def get_status(self) -> dict:
        """获取翻译器状态"""
        try:
            return self.java_translator.get_status()
        except Exception as e:
            return {"available": False, "reason": str(e)}


class PythonTranslatorAdapter:
    """Python翻译器适配器"""

    def __init__(self, python_translator, config: dict):
        """
        初始化Python翻译器适配器

        Args:
            python_translator: Python翻译器实例
            config: 翻译配置
        """
        self.python_translator = python_translator
        self.config = config
        self.logger = get_logger(f"{__name__}.PythonTranslatorAdapter")

    def translate_csv(
        self, input_csv: str, output_csv: str, protected_text: str, **kwargs
    ) -> bool:
        """
        翻译CSV文件

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径
            protected_text: 保护文本
            **kwargs: 其他参数

        Returns:
            bool: 翻译是否成功
        """
        try:
            # 从配置或kwargs中获取API密钥
            access_key_id = kwargs.get("access_key_id") or self.config.get(
                "access_key_id"
            )
            access_key_secret = kwargs.get("access_key_secret") or self.config.get(
                "access_key_secret"
            )

            if not access_key_id or not access_key_secret:
                self.logger.error("缺少阿里云API密钥")
                return False

            # 调用Python翻译函数
            translate_csv(
                input_csv,
                output_csv,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                protected_text=protected_text,
                **kwargs,
            )

            self.logger.info("Python翻译完成: %s -> %s", input_csv, output_csv)
            return True

        except Exception as e:
            self.logger.error("Python翻译失败: %s", e, exc_info=True)
            return False

    def can_resume_translation(self, input_csv: str, output_csv: str) -> Optional[str]:
        """检查是否可以恢复翻译"""
        return self.python_translator.can_resume_translation(input_csv, output_csv)

    def resume_translation(
        self, input_csv: str, output_csv: str, protected_text: str
    ) -> bool:
        """恢复翻译"""
        return self.python_translator.resume_translation(
            input_csv, output_csv, protected_text
        )

    def get_status(self) -> dict:
        """获取翻译器状态"""
        return self.python_translator.get_status()


# 整句翻译时占位符的包裹格式：[[...]]，目标语言中通常不会被翻译（类似模板变量）
#
# Java (阿里云) 与 Google 的对比：
# - Java：发送前不做包裹，整段 protected_text 原样发给阿里云 API；仅对「整行纯 ALIMT 标签」跳过翻译并
#   removeAlimtTags（去掉 <ALIMT >/</ALIMT> 只保留内容）。占位符/成人词是否被 API 翻译取决于 API 行为。
# - Google：发送前先 _wrap_adult_words_for_google（成人词典词 + "->" 包成 [[word->]]，单独词包成 [[word]]），
#   再 _wrap_placeholders_for_whole_sentence（(PH_x)、[xxx]、{xxx}、<ALIMT >(PH_x)</ALIMT> 包成 [[...]]），
#   整句发给 Google 后 _unwrap_placeholders_after_translation 去掉 [[...]]。
_PLACEHOLDER_WRAP = "[["
_PLACEHOLDER_UNWRAP = "]]"
_PLACEHOLDER_PATTERN = re.compile(
    r"(<ALIMT\s*>\([^)]+\)</ALIMT>|\[[^\]]+\]|\{[^}]+\}|\(PH_\d+\))"
)

# 成人词典英文词列表（用于 Google 发送前包裹，避免翻译 bottomless-> 等游戏 key）
_ADULT_ENGLISH_WORDS_CACHE: Optional[list] = None


def _get_adult_english_words() -> list:
    """加载成人词典中的英文词列表（长词优先），供 Google 发送前包裹用。"""
    global _ADULT_ENGLISH_WORDS_CACHE
    if _ADULT_ENGLISH_WORDS_CACHE is not None:
        return _ADULT_ENGLISH_WORDS_CACHE
    try:
        import yaml
        config_path = Path(__file__).parent.parent / "user_config" / "config"
        dictionary_file = config_path / "adult_dictionary.yaml"
        if not dictionary_file.exists():
            _ADULT_ENGLISH_WORDS_CACHE = []
            return _ADULT_ENGLISH_WORDS_CACHE
        with open(dictionary_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        words = []
        for category_data in data.values():
            if not isinstance(category_data, dict):
                continue
            entries = category_data.get("entries") or []
            for entry in entries:
                if isinstance(entry, dict) and entry.get("english"):
                    words.append(entry["english"])
        words = sorted(set(words), key=len, reverse=True)  # 长词优先，避免部分匹配
        _ADULT_ENGLISH_WORDS_CACHE = words
        return words
    except Exception:
        _ADULT_ENGLISH_WORDS_CACHE = []
        return _ADULT_ENGLISH_WORDS_CACHE


def _wrap_adult_words_for_google(text: str) -> str:
    """将成人词典中的英文词用 [[...]] 包裹，发给 Google 时不翻译。key-> 整段（含箭头）包裹为 [[key->]]。"""
    words = _get_adult_english_words()
    if not words:
        return text
    result = text
    for word in words:
        # 先包裹 "word->" 整段（含箭头），如 bottomless-> -> [[bottomless->]]
        pattern_with_arrow = r"(?<![a-zA-Z])" + re.escape(word) + r"->"
        result = re.sub(
            pattern_with_arrow,
            _PLACEHOLDER_WRAP + word + "->" + _PLACEHOLDER_UNWRAP,
            result,
        )
        # 再包裹剩余单独出现的整词（如句中 anal）
        pattern_word = r"(?<![a-zA-Z])" + re.escape(word) + r"(?![a-zA-Z\-])"
        result = re.sub(pattern_word, _PLACEHOLDER_WRAP + word + _PLACEHOLDER_UNWRAP, result)
    return result


def _wrap_placeholders_for_whole_sentence(text: str) -> str:
    """将占位符包裹为 [[...]]，整句发给 Google 时通常不会被翻译。"""
    def repl(m):
        return _PLACEHOLDER_WRAP + m.group(0) + _PLACEHOLDER_UNWRAP
    return _PLACEHOLDER_PATTERN.sub(repl, text)


def _unwrap_placeholders_after_translation(text: str) -> str:
    """翻译后去掉 [[...]] 包裹，还原为占位符。"""
    # 非贪婪匹配 [[...]]，还原为内部内容（可多次以处理嵌套或连续）
    out = text
    while True:
        next_out = re.sub(
            re.escape(_PLACEHOLDER_WRAP) + r"(.*?)" + re.escape(_PLACEHOLDER_UNWRAP),
            r"\1",
            out,
            flags=re.DOTALL,
        )
        if next_out == out:
            break
        out = next_out
    return out


def _strip_alimt_after_translation(text: str) -> str:
    """翻译后去掉残留的 <ALIMT >...</ALIMT>，只保留内部内容，避免输出里出现 <ALIMT >[[阴道]]</ALIMT> 等。"""
    return re.sub(r"<ALIMT\s*>([^<]*)</ALIMT>", r"\1", text)


def _translate_text_preserve_placeholders(adapter_self, text: str) -> str:
    """
    整句发给 Google 翻译，占位符用 [[...]] 包裹，目标语言中通常不会被翻译。
    占位符包括：本项目的 (PH_1)、游戏中的 [xxx]、{0} 等；成人词典英文词（如 bottomless）也会包裹，避免被译成下着较少。
    """
    if not text or not text.strip():
        return text
    # 发送前先去掉残留的 <ALIMT >...</ALIMT>，只按 (PH_x)/[xxx] 等包裹，避免发给 Google 后再解包仍带 ALIMT
    normalized = _strip_alimt_after_translation(text)
    wrapped = _wrap_adult_words_for_google(normalized)
    wrapped = _wrap_placeholders_for_whole_sentence(wrapped)
    try:
        result = adapter_self.google_translator.translate_text(wrapped)
    except Exception as e:
        adapter_self.logger.debug("整句翻译失败，保留原文: %s", e)
        return text
    result = result or text
    result = _unwrap_placeholders_after_translation(result)
    result = _strip_alimt_after_translation(result)
    return result


class GoogleTranslatorAdapter(ResumeBase):
    """Google 免费翻译适配器（无需 API 密钥，使用 deep-translator）"""

    restores_placeholders_per_row = True  # 每翻译一行即恢复 (PH_1)->[saw]，不再依赖步骤4整表恢复

    def __init__(self, google_translator, config: dict):
        super().__init__()
        self.google_translator = google_translator
        self.config = config
        self.logger = get_logger(f"{__name__}.GoogleTranslatorAdapter")

    def translate_csv(  # pylint: disable=unused-argument
        self, input_csv: str, output_csv: str, protected_text: str = "", **kwargs
    ) -> bool:
        """翻译 CSV，使用 protected_text 或 text 列，写入 translated 列。支持断点续传。"""
        try:
            input_path = Path(input_csv)
            output_path = Path(output_csv)
            if not input_path.exists():
                self.logger.error("输入文件不存在: %s", input_csv)
                return False

            with open(input_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)

            if "translated" not in fieldnames:
                fieldnames.append("translated")
            translation_col = "protected_text" if "protected_text" in fieldnames else "text"
            if translation_col not in fieldnames:
                self.logger.error("CSV 缺少 %s 或 text 列", translation_col)
                return False

            start_row = 0
            if output_path.exists():
                start_row = self._count_csv_lines(str(output_path))
                if 0 < start_row < len(rows):
                    with open(output_path, encoding="utf-8") as f:
                        existing = list(csv.DictReader(f))
                    out_rows = existing
                    todo = rows[start_row:]
                else:
                    out_rows = []
                    todo = rows
            else:
                out_rows = []
                todo = rows

            output_path.parent.mkdir(parents=True, exist_ok=True)
            max_workers = int(self.config.get("max_workers", 5))
            chunk_size = max(1, int(self.config.get("chunk_size", 10)))
            sleep_sec = float(self.config.get("sleep_sec", 0.1))

            placeholder_map = kwargs.get("placeholder_map") or {}
            do_restore_per_row = bool(placeholder_map)
            pm = PlaceholderManager() if do_restore_per_row else None

            def translate_one(item):
                i, text = item
                if not text:
                    return i, ""
                try:
                    return i, _translate_text_preserve_placeholders(self, text)
                except Exception as e:
                    self.logger.warning("第 %d 行翻译失败: %s", start_row + i + 1, e)
                    return i, text

            pause_file = output_path.parent / "translate_pause.flag"
            if pause_file.exists():
                try:
                    pause_file.unlink()
                except OSError:
                    pass
            self._paused = False

            total_rows = len(rows)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                offset = 0
                # 全局进度：总行数 = 整表行数，初始值 = 已完成的（断点续传时）
                pbar = tqdm(
                    total=total_rows,
                    initial=start_row,
                    desc="Google 翻译进度",
                    unit="行",
                    dynamic_ncols=True,
                )
                try:
                    while offset < len(todo):
                        chunk = todo[offset : offset + chunk_size]
                        line_start = start_row + offset + 1
                        line_end = start_row + offset + len(chunk)
                        range_str = f"第 {line_start} 行" if line_start == line_end else f"第 {line_start}-{line_end} 行"
                        first_text = (chunk[0].get(translation_col) or "").strip()
                        preview = (first_text[:72] + "…") if len(first_text) > 72 else first_text
                        # 第二行显示当前行范围与内容；打印后光标移回第一行，否则 tqdm 的 \r 会在第二行刷新导致进度条不更新
                        if offset > 0:
                            print("\033[B\r\033[K", end="", flush=True)  # 下移到第二行并清除
                        else:
                            print(end="\n", flush=True)
                        print(f"  当前 {range_str} | {preview}", end="", flush=True)
                        print("\033[A", end="", flush=True)  # 光标回到第一行，让 pbar.update() 在首行刷新

                        texts = [(i, (row.get(translation_col) or "").strip()) for i, row in enumerate(chunk, start=offset)]
                        results = {}
                        for future in as_completed(executor.submit(translate_one, (i, t)) for i, t in texts):
                            idx, translated = future.result()
                            results[idx] = translated
                        for i, row in enumerate(chunk):
                            j = offset + i
                            raw = results.get(j, (row.get(translation_col) or "").strip())
                            if do_restore_per_row and pm and raw:
                                csv_key = row.get("key", f"row_{j + 1}")
                                raw = pm.restore_text(raw, csv_key, placeholder_map)
                            row["translated"] = raw
                            out_rows.append(row)
                        with open(output_path, "w", encoding="utf-8", newline="") as f:
                            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                            w.writeheader()
                            w.writerows(out_rows)
                        offset += len(chunk)
                        pbar.update(len(chunk))
                        # 每块结束后检查暂停：存在 translate_pause.flag 或用户 Ctrl+C 则停止并保存当前进度
                        if pause_file.exists():
                            try:
                                pause_file.unlink()
                            except OSError:
                                pass
                            self._paused = True
                            self.logger.info("用户暂停翻译，进度已保存至 %s", output_csv)
                            break
                        if sleep_sec > 0 and offset < len(todo):
                            time.sleep(sleep_sec)
                except KeyboardInterrupt:
                    self._paused = True
                    self.logger.info("用户中断翻译（Ctrl+C），进度已保存至 %s", output_csv)
                finally:
                    pbar.close()
                    print()  # 第二行“当前”可能未换行，此处补上

            if self._paused:
                return False
            self.logger.info("Google 翻译完成: %s -> %s", input_csv, output_csv)
            return True
        except Exception as e:
            self.logger.error("Google 翻译失败: %s", e, exc_info=True)
            return False

    def can_resume_translation(self, input_csv: str, output_csv: str) -> Optional[str]:
        if self._can_resume_from_files(input_csv, output_csv):
            return output_csv
        return None

    def resume_translation(
        self, input_csv: str, output_csv: str, protected_text: str
    ) -> bool:
        return self.translate_csv(input_csv, output_csv, protected_text=protected_text)

    def get_status(self) -> dict:
        try:
            from .core.google_translator import DeepTranslator
            return {
                "available": DeepTranslator is not None,
                "reason": "正常（免费，无需 API 密钥）" if DeepTranslator else "请安装: pip install deep-translator",
            }
        except Exception as e:
            return {"available": False, "reason": str(e)}


class PlaceholderManagerAdapter:
    """占位符管理器适配器"""

    def __init__(self, placeholder_manager, config: dict):
        """
        初始化占位符管理器适配器

        Args:
            placeholder_manager: 占位符管理器实例
            config: 翻译配置
        """
        self.placeholder_manager = placeholder_manager
        self.config = config
        self.logger = get_logger(f"{__name__}.PlaceholderManagerAdapter")

    def translate_csv(
        self, input_csv: str, mode: str = "protect", **kwargs
    ) -> Tuple[bool, dict, str]:
        """
        处理CSV文件中的占位符

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径
            mode: 处理模式 ("protect" 保护, "restore" 恢复)
            **kwargs: 其他参数

        Returns:
            bool 或 (bool, dict): 处理是否成功，保护模式时返回 (success, placeholder_map)
        """
        try:
            if mode == "protect":
                success, placeholder_map, protected_text = (
                    self.placeholder_manager.protect_csv_file(input_csv)
                )
                self.logger.info("占位符保护完成: %s (模式: %s)", input_csv, mode)
                return success, placeholder_map, protected_text
            elif mode == "restore":
                # 从kwargs中获取placeholder_map
                placeholder_map = kwargs.get("placeholder_map", {})
                success = self.placeholder_manager.restore_csv_file(
                    input_csv, placeholder_map
                )
                self.logger.info("占位符恢复完成: %s (模式: %s)", input_csv, mode)
                return success, placeholder_map, ""
            else:
                self.logger.error("不支持的模式: %s", mode)
                return False

        except Exception as e:
            self.logger.error("占位符处理失败: %s", e, exc_info=True)
            return False

    def protect_csv_file(self, input_csv: str):
        """保护CSV文件"""
        return self.placeholder_manager.protect_csv_file(input_csv)

    def restore_csv_file(self, input_csv: str, placeholder_map: dict):
        """恢复CSV文件"""
        return self.placeholder_manager.restore_csv_file(input_csv, placeholder_map)

    def protect_text(
        self,
        text: str,
        csv_key: str = "single_text",
        placeholder_map: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        """保护单个文本"""
        return self.placeholder_manager.protect_text(text, csv_key, placeholder_map)

    def restore_text(
        self,
        text: str,
        csv_key: str = "single_text",
        placeholder_map: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        """恢复单个文本"""
        return self.placeholder_manager.restore_text(text, csv_key, placeholder_map)

    def get_dictionary_stats(self) -> dict:
        """获取词典统计信息"""
        return {
            "total_entries": len(self.placeholder_manager.dictionary),
            "dictionary_type": self.placeholder_manager.dictionary_type,
        }

    def get_status(self) -> dict:
        """获取状态"""
        return {
            "available": True,
            "type": "placeholder_manager",
            "dictionary_type": self.placeholder_manager.dictionary_type,
            "dictionary_entries": len(self.placeholder_manager.dictionary),
        }
