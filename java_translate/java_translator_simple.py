"""
简化的Java翻译工具包装器
只记录当前翻译到第几行，恢复时从这一行继续
"""

import os
import subprocess
import signal
import threading
import shutil
from utils.logging_config import get_logger
from typing import Optional, Dict, Any
from pathlib import Path
from glob import glob


def update_progress(current: int, total: int, status: str = ""):
    """更新进度条显示"""
    percentage = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current / total)

    # 使用更美观的字符
    bar = "[" + "█" * filled_length + "░" * (bar_length - filled_length) + "] "
    progress_text = f"{bar}{percentage:.1f}% ({current}/{total}) {status}"

    # 清除当前行并显示进度条，使用更长的清除长度
    print(f"\r{' ' * 120}\r{progress_text}", end="", flush=True)

    if current == total:
        print()  # 换行
        print("🎉 翻译完成！")


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
            Path(__file__).parent / "RimWorldBatchTranslate" / "target",  # 当前目录下
            Path(__file__).parent.parent
            / "RimWorldBatchTranslate"
            / "target",  # 上级目录（兼容旧路径）
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
        raise FileNotFoundError(
            "未找到Java翻译工具JAR文件。请先构建Java项目：\n"
            "cd java_translate/RimWorldBatchTranslate && mvn package\n"
            f"查找路径：{[str(d / '*with-dependencies.jar') for d in search_dirs] + [str(d / '*.jar') for d in search_dirs]}"
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
        翻译CSV文件（简化版）

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
                print("❌ CSV文件为空或无法读取")
                return False

            print(f"🚀 开始翻译，总计 {total_lines} 行...")
            if enable_interrupt:
                print("💡 提示: 按 Ctrl+C 可以安全中断翻译")
            print("=" * 60)

            # 准备输入数据（包含起始行参数）
            # 优先使用传入的resume_line参数
            if resume_line is not None:
                start_line = resume_line
            else:
                start_line = 0

            input_data = f"{input_csv}\n{output_csv}\n{access_key_id}\n{access_key_secret}\n{model_id}\n{start_line}\n"

            # 调用Java程序
            self.logger.debug(
                f"开始翻译: {input_csv} -> {output_csv} (从第{start_line}行开始)"
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
                        # 不在这里打印，避免重复提示

                        return False

                line = line.strip()
                if line:
                    # 检查是否是进度相关的输出
                    if "翻译完成" in line:
                        current_line += 1
                        update_progress(current_line, total_lines, "翻译中...")

                        # 记录日志但不换行
                        self.logger.debug(
                            "更新翻译进度: %d/%d", current_line, total_lines
                        )
                    elif "跳过占位符" in line:
                        current_line += 1
                        update_progress(current_line, total_lines, "跳过中...")

                        # 记录日志但不换行
                        self.logger.debug(
                            "更新翻译进度: %d/%d", current_line, total_lines
                        )
                    elif "翻译失败，使用原文" in line:
                        current_line += 1
                        update_progress(current_line, total_lines, "失败处理...")

                        # 记录日志但不换行
                        self.logger.debug(
                            "更新翻译进度: %d/%d", current_line, total_lines
                        )
                    elif "开始翻译" in line and "总计" in line:
                        # Java输出的开始信息，忽略
                        continue
                    elif "✅" in line:
                        # Java输出的完成信息，忽略
                        continue
                    elif "[警告]" in line:
                        # Java输出的警告信息，显示但不计入进度
                        print(f"\n⚠️ {line}")
                        continue
                    else:
                        # 其他输出忽略，避免干扰进度条
                        continue

            # 等待进程结束
            return_code = proc.wait()

            # 清除进程引用
            self.current_process = None

            if return_code == 0:
                self.logger.debug("Java翻译工具执行成功")
                print("=" * 60)
                print(f"✅ 翻译完成！输出文件: {output_csv}")

                return True
            else:
                # 检查是否是用户中断
                if return_code == 130:  # SIGINT (Ctrl+C)
                    self.logger.debug("用户中断翻译")
                    print()  # 换行
                    print("=" * 60)
                    print("⚠️ 翻译被用户中断")

                    return None  # 用户中断，不是失败
                else:
                    self.logger.error(f"Java翻译工具执行失败，返回码: {return_code}")
                    print()  # 换行
                    print("=" * 60)
                    print(f"❌ 翻译失败，返回码: {return_code}")

                    return False

        except subprocess.TimeoutExpired:
            self.logger.error("Java翻译工具执行超时")
            print("❌ 翻译超时")

            return False
        except Exception as e:
            self.logger.error(f"调用Java翻译工具时发生错误: {e}")
            print(f"❌ 翻译错误: {e}")

            return False
        finally:
            # 清理进程引用
            self.current_process = None

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
        from pathlib import Path

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

        print(f"📍 从第 {resume_line} 行开始恢复翻译")

        # 从用户配置中获取必要的参数
        from utils.config import get_user_config

        cfg = get_user_config() or {}

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
            print(f"✅ 恢复翻译完成！结果已保存到: {output_csv}")
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
