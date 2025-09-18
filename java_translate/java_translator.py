"""
Java翻译工具包装器
提供Python接口调用Java翻译工具
"""

import os
import subprocess
import logging
import csv
import re
from pathlib import Path
from typing import Optional, Dict, Any
from utils.config import get_config
from glob import glob
import shutil


CONFIG = get_config()


def update_progress(current: int, total: int, status: str = ""):
    """更新进度条显示"""
    percentage = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current / total)

    # 使用更美观的字符
    bar = "[" + "█" * filled_length + "░" * (bar_length - filled_length) + "] "
    progress_text = f"{bar}{percentage:.1f}% ({current}/{total}) {status}"

    # 清除当前行并显示进度条
    print(f"\r{' ' * 80}\r{progress_text}", end="", flush=True)

    if current == total:
        print()  # 换行
        print("🎉 翻译完成！")


def count_csv_lines(csv_path: str) -> int:
    """统计CSV文件行数"""
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            return sum(1 for row in reader)
    except Exception:
        return 0


class JavaTranslator:
    """Java翻译工具包装器"""

    def __init__(self, jar_path: Optional[str] = None):
        """
        初始化Java翻译器

        Args:
            jar_path (Optional[str]): JAR文件路径，如果为None则自动查找
        """
        self.jar_path = jar_path or self._find_jar_path()
        self._validate_jar()

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
    ) -> bool:
        """
        翻译CSV文件

        Args:
            input_csv (str): 输入CSV文件路径
            output_csv (str): 输出CSV文件路径
            access_key_id (str): 阿里云AccessKeyId
            access_key_secret (str): 阿里云AccessKeySecret
            model_id (int): 翻译模型ID，默认27345

        Returns:
            bool: 翻译是否成功
        """
        try:
            # 验证输入文件
            if not os.path.exists(input_csv):
                raise FileNotFoundError(f"输入CSV文件不存在: {input_csv}")

            # 统计总行数用于进度条
            total_lines = count_csv_lines(input_csv)
            if total_lines == 0:
                print("❌ CSV文件为空或无法读取")
                return False

            print(f"🚀 开始翻译，总计 {total_lines} 行...")
            print("=" * 60)

            # 准备输入数据
            input_data = (
                f"{input_csv}\n{output_csv}\n{access_key_id}\n{access_key_secret}\n"
            )

            # 调用Java程序
            logging.info(f"开始调用Java翻译工具: {self.jar_path}")
            logging.info(f"输入文件: {input_csv}")
            logging.info(f"输出文件: {output_csv}")

            proc = subprocess.Popen(
                ["java", "-jar", self.jar_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )
            assert proc.stdin is not None
            proc.stdin.write(input_data)
            proc.stdin.flush()
            proc.stdin.close()

            # 解析Java输出并显示进度条
            processed_lines = 0
            for line in proc.stdout:
                line = line.strip()
                if line:
                    # 检查是否是进度相关的输出
                    if "翻译完成" in line or "跳过" in line or "翻译失败" in line:
                        processed_lines += 1
                        update_progress(processed_lines, total_lines, "处理中...")
                    elif "开始翻译" in line and "总计" in line:
                        # Java输出的开始信息，忽略
                        continue
                    elif "✅" in line:
                        # Java输出的完成信息，忽略
                        continue
                    else:
                        # 其他输出直接显示
                        print(f"\n{line}")

            proc.wait()

            if proc.returncode == 0:
                logging.info("Java翻译工具执行成功")
                print("=" * 60)
                print(f"✅ 翻译完成！输出文件: {output_csv}")
                return True
            else:
                logging.error(f"Java翻译工具执行失败，返回码: {proc.returncode}")
                print("=" * 60)
                print(f"❌ 翻译失败，返回码: {proc.returncode}")
                return False

        except subprocess.TimeoutExpired:
            logging.error("Java翻译工具执行超时")
            print("❌ 翻译超时")
            return False
        except Exception as e:
            logging.error(f"调用Java翻译工具时发生错误: {e}")
            print(f"❌ 翻译错误: {e}")
            return False

    def translate_csv_interactive(self, input_csv: str, output_csv: str) -> bool:
        """
        交互式翻译CSV文件（用户手动输入阿里云密钥）

        Args:
            input_csv (str): 输入CSV文件路径
            output_csv (str): 输出CSV文件路径

        Returns:
            bool: 翻译是否成功
        """
        print(f"📝 准备翻译文件: {input_csv} -> {output_csv}")
        print("=" * 60)

        # 获取阿里云密钥
        access_key_id = input("🔑 请输入阿里云 AccessKeyId: ").strip()
        access_key_secret = input("🔐 请输入阿里云 AccessKeySecret: ").strip()

        if not access_key_id or not access_key_secret:
            print("❌ 阿里云密钥不能为空")
            return False

        return self.translate_csv(
            input_csv, output_csv, access_key_id, access_key_secret
        )

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

    def _check_java_available(self) -> bool:
        """检查Java是否可用"""
        try:
            subprocess.run(["java", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def translate_csv_with_java(
    input_csv: str, output_csv: str, access_key_id: str, access_key_secret: str
) -> bool:
    """
    使用Java工具翻译CSV文件的便捷函数

    Args:
        input_csv (str): 输入CSV文件路径
        output_csv (str): 输出CSV文件路径
        access_key_id (str): 阿里云AccessKeyId
        access_key_secret (str): 阿里云AccessKeySecret

    Returns:
        bool: 翻译是否成功
    """
    try:
        translator = JavaTranslator()
        return translator.translate_csv(
            input_csv, output_csv, access_key_id, access_key_secret
        )
    except Exception as e:
        logging.error(f"Java翻译失败: {e}")
        print(f"❌ Java翻译失败: {e}")
        return False
