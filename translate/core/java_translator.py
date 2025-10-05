"""
简化的Java翻译工具包装器
只记录当前翻译到第几行，恢复时从这一行继续
"""

import os
import subprocess
import signal
import threading
import shutil
import re
import csv
from utils.logging_config import get_logger
from utils.ui_style import ui

# 移除旧配置系统依赖
from typing import Optional, Dict, Any
from pathlib import Path
from glob import glob


def update_progress(current: int, total: int, status: str = ""):
    """更新进度条显示"""
    ui.print_progress_bar(current, total, width=40, prefix="翻译进度", suffix=status)

    if current == total:
        print()  # 换行
        ui.print_success("翻译完成！")


def count_csv_lines(csv_path: str) -> int:
    """统计CSV文件行数（不包括标题行）"""
    try:
        import csv

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            lines = list(reader)
            # 减去标题行，只统计数据行
            return max(0, len(lines) - 1)
    except Exception:
        return 0


class JavaTranslator:
    """简化的Java翻译工具包装器"""

    def __init__(self, jar_path: Optional[str] = None):
        """
        初始化Java翻译器

        Args:
            jar_path (Optional[str]): JAR文件路径，如果为None则自动查找
        """
        self.logger = get_logger(f"{__name__}.JavaTranslator")
        self.jar_path = jar_path or self._find_jar_path()
        self._validate_jar()

        # 中断和继续相关属性
        self.current_process: Optional[subprocess.Popen] = None
        self.is_interrupted = False
        self.interrupt_lock = threading.Lock()

        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _find_jar_path(self) -> str:
        """自动查找JAR文件路径，优先with-dependencies，没有则用普通JAR"""
        search_dirs = [
            Path(__file__).parent
            / "java_translate"
            / "RimWorldBatchTranslate"
            / "target",  # 从translate/core/找到java_translate/
        ]
        jar_candidates = []
        for d in search_dirs:
            if d.exists():
                jar_candidates += glob(str(d / "*with-dependencies.jar"))
        if not jar_candidates:
            # 没有with-dependencies，查找普通JAR
            for d in search_dirs:
                if d.exists():
                    jar_candidates += glob(str(d / "*.jar"))
        if jar_candidates:
            return jar_candidates[0]
        # 尝试自动编译
        try:
            self.logger.info("未找到JAR文件，尝试自动编译...")
            ui.print_info("🔨 未找到JAR文件，正在自动编译Java项目...")
            return self._auto_build_jar()
        except Exception as e:
            self.logger.error(f"自动编译失败: {e}")
            raise FileNotFoundError(
                f"未找到Java翻译工具JAR文件，自动编译也失败了：\n"
                f"错误: {e}\n"
                f"请手动构建Java项目：\n"
                f"cd java_translate/RimWorldBatchTranslate && mvn package\n"
                f"查找路径：{[str(d / '*with-dependencies.jar') for d in search_dirs] + [str(d / '*.jar') for d in search_dirs]}"
            )

    def _auto_build_jar(self) -> str:
        """自动编译Java项目"""
        try:
            # 确定Java项目路径
            java_project_path = (
                Path(__file__).parent / "java_translate" / "RimWorldBatchTranslate"
            )

            if not java_project_path.exists():
                raise FileNotFoundError(f"Java项目路径不存在: {java_project_path}")

            # 检查pom.xml是否存在
            pom_file = java_project_path / "pom.xml"
            if not pom_file.exists():
                raise FileNotFoundError(f"pom.xml文件不存在: {pom_file}")

            # 检查Maven是否可用
            mvn_commands = ["mvn", "mvn.cmd", "mvn.bat"]
            mvn_cmd = None

            for cmd in mvn_commands:
                try:
                    subprocess.run([cmd, "-version"], capture_output=True, check=True)
                    mvn_cmd = cmd
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

            if mvn_cmd is None:
                raise RuntimeError("Maven未安装或不在PATH中，请先安装Maven")

            self.logger.info(f"开始编译Java项目: {java_project_path}")
            ui.print_info(f"📁 项目路径: {java_project_path}")

            # 执行编译
            result = subprocess.run(
                [mvn_cmd, "clean", "package", "-q"],  # -q 静默模式，减少输出
                cwd=java_project_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
            )

            if result.returncode == 0:
                self.logger.info("Java项目编译成功")
                ui.print_success("✅ Java项目编译成功")

                # 重新查找JAR文件
                return self._find_jar_path_after_build()
            else:
                error_msg = f"Maven编译失败 (返回码: {result.returncode})"
                if result.stderr:
                    error_msg += f"\n错误信息: {result.stderr}"
                if result.stdout:
                    error_msg += f"\n输出信息: {result.stdout}"
                raise RuntimeError(error_msg)

        except subprocess.TimeoutExpired:
            raise RuntimeError("编译超时（5分钟），请检查项目配置或手动编译")
        except Exception as e:
            raise RuntimeError(f"自动编译失败: {str(e)}")

    def _find_jar_path_after_build(self) -> str:
        """编译后重新查找JAR文件"""
        target_dir = (
            Path(__file__).parent
            / "java_translate"
            / "RimWorldBatchTranslate"
            / "target"
        )

        if not target_dir.exists():
            raise FileNotFoundError(f"编译后target目录不存在: {target_dir}")

        # 查找with-dependencies JAR
        jar_candidates = glob(str(target_dir / "*with-dependencies.jar"))
        if jar_candidates:
            return jar_candidates[0]

        # 查找普通JAR
        jar_candidates = glob(str(target_dir / "*.jar"))
        if jar_candidates:
            return jar_candidates[0]

        raise FileNotFoundError(f"编译后未找到JAR文件: {target_dir}")

    def _protect_placeholders(self, text: str) -> tuple[str, list[str]]:
        """
        保护文本中的占位符，避免被翻译

        Args:
            text: 要保护的文本

        Returns:
            tuple: (保护后的文本, 占位符列表)
        """
        if not text or not isinstance(text, str):
            return text, []

        # 定义保护模式（与Java代码保持一致）
        patterns = [
            r"\\n",  # \n 换行符
            r"\[[^\]]+\]",  # [xxx]
            r"\{\d+\}",  # {0}, {1}
            r"%[sdif]",  # %s, %d, %i, %f
            r"</?[^>]+>",  # <color> 或 <br>
            r"[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)",  # 函数调用
            r"->\[[^\]]+\]",  # ->[结果]
            r"\bpawn\b",  # pawn 游戏术语
        ]

        protected_text = text
        placeholders = []
        idx = 1

        # 首先标准化换行符
        protected_text = protected_text.replace("\r\n", "\\n").replace("\n", "\\n")

        for pattern in patterns:
            matches = list(re.finditer(pattern, protected_text))
            for match in reversed(matches):  # 从后往前替换，避免位置偏移
                placeholder_text = match.group()
                # 跳过已经保护的ALIMT标签
                if "ALIMT" in placeholder_text:
                    continue

                placeholders.append(placeholder_text)
                placeholder = f"(PH_{idx})"
                alimt_tag = f"<ALIMT >{placeholder}</ALIMT>"

                start, end = match.span()
                protected_text = (
                    protected_text[:start] + alimt_tag + protected_text[end:]
                )
                idx += 1

        return protected_text, placeholders

    def _restore_placeholders(self, text: str, placeholders: list[str]) -> str:
        """
        恢复占位符

        Args:
            text: 包含占位符的文本
            placeholders: 原始占位符列表

        Returns:
            str: 恢复后的文本
        """
        if not placeholders:
            return text

        restored_text = text
        for i, placeholder in enumerate(placeholders, 1):
            ph_pattern = f"<ALIMT >\\(PH_{i}\\)</ALIMT>"
            restored_text = re.sub(ph_pattern, placeholder, restored_text)

        return restored_text

    def translate_csv_with_python_protection(
        self,
        input_csv: str,
        output_csv: str,
        access_key_id: str,
        access_key_secret: str,
        model_id: int = 27345,
        enable_interrupt: bool = True,
        resume_line: Optional[int] = None,
    ) -> bool:
        """
        使用Python层占位符保护的CSV翻译

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径
            access_key_id: 阿里云AccessKeyId
            access_key_secret: 阿里云AccessKeySecret
            model_id: 翻译模型ID
            enable_interrupt: 是否启用中断功能
            resume_line: 恢复行号

        Returns:
            bool: 翻译是否成功
        """
        try:
            # 创建临时文件用于占位符保护
            temp_csv = str(Path(input_csv).with_suffix(".temp_protected.csv"))

            # 步骤1：保护占位符
            self.logger.info("开始保护占位符...")
            ui.print_info("🔒 保护占位符...")

            protected_count = 0
            total_count = 0

            with open(input_csv, "r", encoding="utf-8") as infile, open(
                temp_csv, "w", encoding="utf-8", newline=""
            ) as outfile:

                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in reader:
                    total_count += 1

                    # 保护text列
                    if "text" in row and row["text"]:
                        original_text = row["text"]
                        protected_text, placeholders = self._protect_placeholders(
                            original_text
                        )
                        if placeholders:
                            row["text"] = protected_text
                            protected_count += 1
                            self.logger.debug(
                                f"保护了 {len(placeholders)} 个占位符: {placeholders}"
                            )

                    # 保护translated列（如果存在）
                    if "translated" in row and row["translated"]:
                        original_translated = row["translated"]
                        protected_translated, placeholders = self._protect_placeholders(
                            original_translated
                        )
                        if placeholders:
                            row["translated"] = protected_translated
                            protected_count += 1

                    writer.writerow(row)

            ui.print_success(
                f"✅ 占位符保护完成: {protected_count}/{total_count} 条记录"
            )

            # 步骤2：调用Java翻译器（简化版，不需要占位符保护）
            self.logger.info("开始Java翻译...")
            success = self._call_java_translator_directly(
                temp_csv,
                output_csv,
                access_key_id,
                access_key_secret,
                model_id,
                enable_interrupt,
                resume_line,
            )

            # 步骤3：恢复占位符
            if success:
                self.logger.info("开始恢复占位符...")
                ui.print_info("🔄 恢复占位符...")

                final_csv = str(Path(output_csv).with_suffix(".final.csv"))
                restored_count = 0

                with open(output_csv, "r", encoding="utf-8") as infile, open(
                    final_csv, "w", encoding="utf-8", newline=""
                ) as outfile:

                    reader = csv.DictReader(infile)
                    fieldnames = reader.fieldnames
                    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                    writer.writeheader()

                    for row in reader:
                        # 恢复text列
                        if "text" in row and row["text"]:
                            original_text = row["text"]
                            # 这里需要从原始CSV获取占位符信息
                            # 简化处理：直接恢复常见的占位符模式
                            restored_text = self._restore_common_placeholders(
                                original_text
                            )
                            if restored_text != original_text:
                                row["text"] = restored_text
                                restored_count += 1

                        # 恢复translated列
                        if "translated" in row and row["translated"]:
                            original_translated = row["translated"]
                            restored_translated = self._restore_common_placeholders(
                                original_translated
                            )
                            if restored_translated != original_translated:
                                row["translated"] = restored_translated
                                restored_count += 1

                        writer.writerow(row)

                # 替换原输出文件
                Path(output_csv).unlink()
                Path(final_csv).rename(output_csv)

                ui.print_success(f"✅ 占位符恢复完成: {restored_count} 条记录")

            # 清理临时文件
            if Path(temp_csv).exists():
                Path(temp_csv).unlink()

            return success

        except Exception as e:
            self.logger.error(f"Python层占位符保护翻译失败: {e}")
            ui.print_error(f"❌ 翻译失败: {e}")
            return False

    def _restore_common_placeholders(self, text: str) -> str:
        """
        恢复常见的占位符模式

        Args:
            text: 包含占位符的文本

        Returns:
            str: 恢复后的文本
        """
        if not text:
            return text

        # 恢复ALIMT标签中的占位符
        # 这里简化处理，实际应该根据原始占位符列表恢复
        restored_text = text

        # 恢复换行符
        restored_text = restored_text.replace("\\n", "\n")

        return restored_text

    def _call_java_translator_directly(
        self,
        input_csv: str,
        output_csv: str,
        access_key_id: str,
        access_key_secret: str,
        model_id: int = 27345,
        enable_interrupt: bool = True,
        resume_line: Optional[int] = None,
    ) -> bool:
        """
        直接调用Java翻译器（不进行占位符保护）

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径
            access_key_id: 阿里云AccessKeyId
            access_key_secret: 阿里云AccessKeySecret
            model_id: 翻译模型ID
            enable_interrupt: 是否启用中断功能
            resume_line: 恢复行号

        Returns:
            bool: 翻译是否成功
        """
        try:
            # 重置中断状态
            with self.interrupt_lock:
                self.is_interrupted = False

            # 验证输入文件
            if not os.path.exists(input_csv):
                raise FileNotFoundError(f"输入CSV文件不存在: {input_csv}")

            # 统计总行数用于进度条
            total_lines = count_csv_lines(input_csv)
            if total_lines == 0:
                ui.print_error("CSV文件为空或无法读取")
                return False

            ui.print_info(f"开始Java翻译，总计 {total_lines} 行...")
            if enable_interrupt:
                ui.print_tip("按 Ctrl+C 可以安全中断翻译")
            ui.print_separator()

            # 准备输入数据（包含起始行参数）
            if resume_line is not None:
                start_line = resume_line
            else:
                start_line = 0

            input_data = f"{input_csv}\n{output_csv}\n{access_key_id}\n{access_key_secret}\n{model_id}\n{start_line}\n"

            # 调用Java程序
            self.logger.debug(
                f"开始Java翻译: {input_csv} -> {output_csv} (从第{start_line}行开始)"
            )
            proc = subprocess.Popen(
                ["java", "-jar", self.jar_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            # 保存进程引用
            self.current_process = proc

            assert proc.stdin is not None
            proc.stdin.write(input_data)
            proc.stdin.flush()
            proc.stdin.close()

            # 解析Java输出并显示进度条
            current_line = start_line

            for line in proc.stdout:
                # 检查中断状态
                with self.interrupt_lock:
                    if self.is_interrupted:
                        self.logger.debug("翻译被中断")
                        return False

                line = line.strip()
                if line:
                    # 检查是否是进度相关的输出
                    if "翻译完成" in line:
                        current_line += 1
                        update_progress(current_line, total_lines, "翻译中...")
                        self.logger.debug(
                            "更新翻译进度: %d/%d", current_line, total_lines
                        )
                    elif "跳过占位符" in line:
                        current_line += 1
                        update_progress(current_line, total_lines, "跳过中...")
                        self.logger.debug(
                            "更新翻译进度: %d/%d", current_line, total_lines
                        )
                    elif "翻译失败，使用原文" in line:
                        current_line += 1
                        update_progress(current_line, total_lines, "失败处理...")
                        self.logger.debug(
                            "更新翻译进度: %d/%d", current_line, total_lines
                        )
                    elif "开始翻译" in line and "总计" in line:
                        continue
                    elif "✅" in line:
                        continue
                    elif "[警告]" in line:
                        ui.print_warning(line)
                        continue
                    else:
                        continue

            # 等待进程结束
            return_code = proc.wait()

            # 清除进程引用
            self.current_process = None

            if return_code == 0:
                self.logger.debug("Java翻译工具执行成功")
                return True
            else:
                # 检查是否是用户中断
                if return_code == 130:  # SIGINT (Ctrl+C)
                    self.logger.debug("用户中断翻译")
                    print()  # 换行
                    ui.print_separator()
                    ui.print_warning("翻译被用户中断")
                    return None  # 用户中断，不是失败
                else:
                    self.logger.error(f"Java翻译工具执行失败，返回码: {return_code}")
                    print()  # 换行
                    ui.print_separator()
                    ui.print_error(f"翻译失败，返回码: {return_code}")
                    return False

        except subprocess.TimeoutExpired:
            self.logger.error("Java翻译工具执行超时")
            ui.print_error("翻译超时")
            return False
        except Exception as e:
            self.logger.error(f"调用Java翻译工具时发生错误: {e}")
            ui.print_error(f"翻译错误: {e}")
            return False
        finally:
            # 清理进程引用
            self.current_process = None

    def translate_csv_simple(
        self,
        input_csv: str,
        output_csv: str,
        access_key_id: str,
        access_key_secret: str,
        model_id: int = 27345,
        enable_interrupt: bool = True,
        resume_line: Optional[int] = None,
    ) -> bool:
        """
        简化的CSV翻译（不包含占位符保护，假设输入已经保护过）

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径
            access_key_id: 阿里云AccessKeyId
            access_key_secret: 阿里云AccessKeySecret
            model_id: 翻译模型ID
            enable_interrupt: 是否启用中断功能
            resume_line: 恢复行号

        Returns:
            bool: 翻译是否成功
        """
        # 直接调用Java翻译器，不进行占位符保护
        return self._call_java_translator_directly(
            input_csv,
            output_csv,
            access_key_id,
            access_key_secret,
            model_id,
            enable_interrupt,
            resume_line,
        )

    def _validate_jar(self) -> None:
        """验证JAR文件是否存在且可执行"""
        if not os.path.exists(self.jar_path):
            raise FileNotFoundError(f"JAR文件不存在: {self.jar_path}")

        # 检查Java是否可用
        try:
            subprocess.run(["java", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Java未安装或不在PATH中")

    def translate_csv(
        self,
        input_csv: str,
        output_csv: str,
        access_key_id: str,
        access_key_secret: str,
        model_id: int = 27345,
        enable_interrupt: bool = True,
        resume_line: Optional[int] = None,
    ) -> bool:
        """
        翻译CSV文件（使用Python层占位符保护）

        Args:
            input_csv (str): 输入CSV文件路径
            output_csv (str): 输出CSV文件路径
            access_key_id (str): 阿里云AccessKeyId
            access_key_secret (str): 阿里云AccessKeySecret
            model_id (int): 翻译模型ID，默认27345
            enable_interrupt (bool): 是否启用中断功能

        Returns:
            bool: 翻译是否成功
        """
        # 使用Python层占位符保护的翻译方法
        return self.translate_csv_with_python_protection(
            input_csv,
            output_csv,
            access_key_id,
            access_key_secret,
            model_id,
            enable_interrupt,
            resume_line,
        )

    def _signal_handler(self, signum, frame):
        """信号处理器，用于处理中断信号"""
        with self.interrupt_lock:
            if not self.is_interrupted:
                self.is_interrupted = True
                self.logger.debug("收到中断信号，正在安全停止翻译...")
                # 不在这里打印，避免重复提示

                if self.current_process:
                    try:
                        self.current_process.terminate()
                        # 等待进程结束，最多等待5秒
                        try:
                            self.current_process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            self.current_process.kill()
                            self.current_process.wait()
                    except Exception as e:
                        self.logger.error("停止Java进程时发生错误: %s", e)

    def interrupt_translation(self) -> None:
        """
        中断当前翻译任务
        """
        with self.interrupt_lock:
            self.is_interrupted = True
            self.logger.debug("用户请求中断翻译")

    def can_resume_translation(self, input_csv: str) -> Optional[str]:
        """
        检查是否可以恢复翻译（基于文件对比）

        Args:
            input_csv (str): 输入CSV文件路径

        Returns:
            Optional[str]: 可恢复的输出文件路径，如果没有则返回None
        """
        # 自动生成输出文件路径
        output_csv = self._generate_output_path(input_csv)

        # 检查是否可以恢复
        if self._can_resume_from_files(input_csv, output_csv):
            return output_csv

        return None

    def _generate_output_path(self, input_csv: str) -> str:
        """
        自动生成输出文件路径

        Args:
            input_csv (str): 输入CSV文件路径

        Returns:
            str: 输出CSV文件路径
        """
        input_path = Path(input_csv)
        # 在文件名后添加 _zh
        output_name = input_path.stem + "_zh" + input_path.suffix
        return str(input_path.parent / output_name)

    def _can_resume_from_files(self, input_csv: str, output_csv: str) -> bool:
        """
        通过对比CSV文件检查是否可以恢复翻译

        Args:
            input_csv (str): 输入CSV文件路径
            output_csv (str): 输出CSV文件路径

        Returns:
            bool: 是否可以恢复
        """
        try:
            import csv
            import os

            # 检查文件是否存在
            if not os.path.exists(input_csv) or not os.path.exists(output_csv):
                return False

            # 读取输入文件行数
            with open(input_csv, "r", encoding="utf-8") as f:
                input_reader = csv.reader(f)
                input_lines = list(input_reader)
                input_data_lines = len(input_lines) - 1  # 减去标题行

            # 读取输出文件行数
            with open(output_csv, "r", encoding="utf-8") as f:
                output_reader = csv.reader(f)
                output_lines = list(output_reader)
                output_data_lines = len(output_lines) - 1  # 减去标题行

            # 如果输出文件行数小于输入文件，说明可以恢复
            # 但至少要有一行数据（不包括标题行）
            return 0 < output_data_lines < input_data_lines

        except Exception as e:
            self.logger.debug("检查文件恢复状态失败: %s", e)
            return False

    def get_resume_line_from_files(self, input_csv: str, output_csv: str) -> int:
        """
        通过对比CSV文件获取恢复起始行号

        Args:
            input_csv (str): 输入CSV文件路径
            output_csv (str): 输出CSV文件路径

        Returns:
            int: 恢复起始行号
        """
        try:
            import csv

            # 读取输出文件行数
            with open(output_csv, "r", encoding="utf-8") as f:
                output_reader = csv.reader(f)
                output_lines = list(output_reader)
                output_data_lines = len(output_lines) - 1  # 减去标题行

            # 返回已翻译的行数（从0开始计数）
            return max(0, output_data_lines)

        except Exception as e:
            self.logger.debug("获取恢复行号失败: %s", e)
            return 0

    def resume_translation(self, input_csv: str, output_csv: str) -> bool:
        """
        恢复翻译任务（基于文件对比）

        Args:
            input_csv (str): 输入CSV文件路径
            output_csv (str): 输出CSV文件路径

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
            api_manager = config_manager.api_manager
            primary_api = api_manager.get_primary_api()

            if primary_api and primary_api.is_enabled():
                # 根据API类型构建配置
                if primary_api.api_type == "aliyun":
                    cfg = {
                        "aliyun_access_key_id": primary_api.get_value(
                            "access_key_id", ""
                        ),
                        "aliyun_access_key_secret": primary_api.get_value(
                            "access_key_secret", ""
                        ),
                        "aliyun_region_id": primary_api.get_value(
                            "region", "cn-hangzhou"
                        ),
                        "model_id": primary_api.get_value("model_id", 27345),
                        "sleep_sec": primary_api.get_value("sleep_sec", 0.5),
                        "enable_interrupt": primary_api.get_value(
                            "enable_interrupt", True
                        ),
                    }
                else:
                    cfg = {}
            else:
                cfg = {}
        except Exception as e:
            self.logger.warning(f"从新配置系统获取配置失败: {e}")
            cfg = {}

        # 直接使用原始文件进行恢复翻译
        success = self.translate_csv(
            input_csv,
            output_csv,
            cfg.get("aliyun_access_key_id", ""),
            cfg.get("aliyun_access_key_secret", ""),
            cfg.get("model_id", 27345),
            True,  # 启用中断功能
            resume_line,  # 传递通过文件对比确定的恢复行号
        )

        if success:
            ui.print_success(f"恢复翻译完成！结果已保存到: {output_csv}")
            return True
        else:
            self.logger.debug("恢复翻译被中断或未完成")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        获取翻译器状态

        Returns:
            Dict[str, Any]: 状态信息
        """
        java_path = shutil.which("java")
        jar_path = None
        try:
            jar_path = self._find_jar_path()
        except Exception:
            pass
        return {
            "java_available": java_path is not None,
            "jar_exists": jar_path is not None,
            "jar_path": jar_path,
        }
