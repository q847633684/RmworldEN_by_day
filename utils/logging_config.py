"""
统一日志配置模块

提供整个项目的统一日志配置，包括：
- 统一的日志格式
- 分级日志处理
- 性能优化
- 调试支持
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class DelayedFileHandler(logging.handlers.RotatingFileHandler):
    """延迟创建文件的文件处理器，只有在有内容写入时才创建文件"""

    def __init__(
        self, filename, mode="a", maxBytes=0, backupCount=0, encoding=None, delay=False
    ):
        # 设置delay=True，这样文件只有在第一次写入时才会被创建
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay=True)
        self._file_created = False

    def emit(self, record):
        """只有在有实际内容时才创建文件"""
        if not self._file_created:
            # 检查文件是否已经存在且不为空
            if self.baseFilename and Path(self.baseFilename).exists():
                file_size = Path(self.baseFilename).stat().st_size
                if file_size > 0:
                    self._file_created = True
            else:
                # 文件不存在，延迟创建
                pass

        # 调用父类的emit方法
        super().emit(record)

        # 标记文件已创建
        if not self._file_created:
            self._file_created = True


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
        "RESET": "\033[0m",  # 重置
    }

    def format(self, record):
        # 添加颜色
        if sys.stdout.isatty():  # 只在终端中显示颜色
            color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"

        return super().format(record)


class LoggingConfig:
    """日志配置管理器"""

    _initialized = False
    _log_dir = None

    @classmethod
    def setup_logging(
        cls,
        level: str = "DEBUG",
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        log_dir: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ) -> None:
        """
        设置全局日志配置

        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_file_logging: 是否记录到文件
            enable_console_logging: 是否输出到控制台
            log_dir: 日志目录，默认为项目根目录下的logs
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的日志文件数量
        """
        if cls._initialized:
            return

        # 设置日志级别
        numeric_level = getattr(logging, level.upper(), logging.INFO)

        # 创建根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # 清除现有的处理器
        root_logger.handlers.clear()

        # 设置日志格式
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 控制台处理器
        if enable_console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)

            # 使用彩色格式化器
            colored_formatter = ColoredFormatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(colored_formatter)
            root_logger.addHandler(console_handler)

        # 文件处理器
        if enable_file_logging:
            if log_dir is None:
                log_dir = Path(__file__).parent.parent / "logs"
            else:
                log_dir = Path(log_dir)

            # 确保日志目录存在
            log_dir.mkdir(exist_ok=True)
            cls._log_dir = log_dir

            # 创建日志文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"day_translation_{timestamp}.log"

            # 使用轮转文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            # 错误日志单独记录 - 使用延迟创建
            error_log_file = log_dir / f"day_translation_error_{timestamp}.log"
            error_handler = DelayedFileHandler(
                error_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)

        cls._initialized = True

        # 记录初始化信息
        logger = logging.getLogger(__name__)
        logger.info("日志系统初始化完成")
        logger.info("日志级别: %s", level)
        logger.info("控制台输出: %s", enable_console_logging)
        logger.info("文件记录: %s", enable_file_logging)
        if enable_file_logging:
            logger.info("日志目录: %s", cls._log_dir)

        # 自动清理旧日志文件
        cls._cleanup_old_logs()

    @classmethod
    def is_initialized(cls) -> bool:
        """
        检查日志系统是否已初始化

        Returns:
            bool: 如果已初始化返回True，否则返回False
        """
        return cls._initialized

    @classmethod
    def reset_logging(
        cls, level: str = "DEBUG", enable_console_logging: bool = True
    ) -> None:
        """
        重新设置日志配置（用于测试或调试）

        Args:
            level: 日志级别
            enable_console_logging: 是否输出到控制台
        """
        # 重置初始化状态
        cls._initialized = False

        # 重新设置日志
        cls.setup_logging(
            level=level,
            enable_file_logging=True,
            enable_console_logging=enable_console_logging,
        )

    @classmethod
    def reload_from_user_config(cls) -> None:
        """
        从用户配置重新加载日志设置

        当用户在配置界面修改日志设置后，可以调用此方法应用新设置
        """
        try:
            from user_config import UserConfigManager

            config_manager = UserConfigManager()
            log_config = config_manager.log_config

            # 重置初始化状态
            cls._initialized = False

            # 从用户配置重新设置
            cls.setup_logging(
                level=log_config.get_value("log_level", "INFO"),
                enable_file_logging=log_config.get_value("log_to_file", True),
                enable_console_logging=log_config.get_value("log_to_console", False),
                max_file_size=log_config.get_value("log_file_size", 10) * 1024 * 1024,
                backup_count=log_config.get_value("log_backup_count", 5),
            )

            logger = logging.getLogger(__name__)
            logger.info("日志配置已从用户设置重新加载")

        except Exception as e:
            # 如果重新加载失败，使用默认配置
            cls.reset_logging()
            logger = logging.getLogger(__name__)
            logger.error(f"从用户配置重新加载日志设置失败: {e}")
            logger.info("已回退到默认日志配置")

    @classmethod
    def _cleanup_old_logs(cls, days_to_keep: int = 7) -> None:
        """
        清理指定天数前的日志文件

        Args:
            days_to_keep: 保留最近几天的日志文件，默认7天
        """
        if cls._log_dir is None or not cls._log_dir.exists():
            return

        try:
            from datetime import timedelta

            # 计算截止时间
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)

            # 查找所有日志文件（包括错误日志）
            log_files = list(cls._log_dir.glob("day_translation*.log"))

            deleted_count = 0
            total_size_before = 0
            total_size_after = 0

            for log_file in log_files:
                try:
                    # 获取文件修改时间和大小
                    file_stat = log_file.stat()
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                    file_size = file_stat.st_size

                    total_size_before += file_size

                    # 如果文件超过指定天数，则删除
                    if file_mtime < cutoff_time:
                        log_file.unlink()
                        deleted_count += 1
                    else:
                        total_size_after += file_size

                except (OSError, IOError):
                    # 忽略删除失败的文件，避免影响程序运行
                    pass

            # 计算节省的空间
            space_saved = total_size_before - total_size_after
            space_saved_mb = space_saved / (1024 * 1024)

            # 输出清理结果（避免 emoji 在 Windows gbk 下报错）
            try:
                if deleted_count > 0:
                    print(
                        f"🗑️ 日志清理完成：删除了 {deleted_count} 个旧日志文件，节省 {space_saved_mb:.2f} MB 空间"
                    )
                else:
                    print(f"📁 日志目录检查完成：当前保留 {len(log_files)} 个日志文件")
            except UnicodeEncodeError:
                if deleted_count > 0:
                    print(f"[日志清理] 删除了 {deleted_count} 个旧日志，节省 {space_saved_mb:.2f} MB")
                else:
                    print(f"[日志] 保留 {len(log_files)} 个日志文件")

        except (OSError, IOError, PermissionError) as e:
            try:
                print(f"⚠️ 日志清理过程中出现错误: {e}")
            except UnicodeEncodeError:
                print(f"[!] 日志清理错误: {e}")

    @classmethod
    def cleanup_old_logs(cls, days_to_keep: int = 7) -> None:
        """
        清理指定天数前的日志文件（公共方法）

        Args:
            days_to_keep: 保留最近几天的日志文件，默认7天
        """
        cls._cleanup_old_logs(days_to_keep)

    @classmethod
    def cleanup_all_logs(cls) -> None:
        """
        清理所有日志文件（谨慎使用）
        """
        if cls._log_dir is None or not cls._log_dir.exists():
            try:
                print("📁 日志目录不存在，无需清理")
            except UnicodeEncodeError:
                print("[日志] 目录不存在，无需清理")
            return

        try:
            # 查找所有日志文件
            log_files = list(cls._log_dir.glob("day_translation*.log"))

            if not log_files:
                try:
                    print("📁 没有找到日志文件")
                except UnicodeEncodeError:
                    print("[日志] 没有找到日志文件")
                return

            # 计算总大小
            total_size = sum(log_file.stat().st_size for log_file in log_files)
            total_size_mb = total_size / (1024 * 1024)

            # 删除所有日志文件
            deleted_count = 0
            for log_file in log_files:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except (OSError, IOError):
                    pass

            try:
                print(
                    f"🗑️ 已清理所有日志文件：删除了 {deleted_count} 个文件，释放 {total_size_mb:.2f} MB 空间"
                )
            except UnicodeEncodeError:
                print(f"[日志清理] 删除了 {deleted_count} 个文件，释放 {total_size_mb:.2f} MB 空间")

        except (OSError, IOError, PermissionError) as e:
            try:
                print(f"⚠️ 清理所有日志时出现错误: {e}")
            except UnicodeEncodeError:
                print(f"[!] 清理日志错误: {e}")

    @classmethod
    def get_log_info(cls) -> dict:
        """
        获取日志目录信息

        Returns:
            dict: 包含日志文件信息的字典
        """
        if cls._log_dir is None or not cls._log_dir.exists():
            return {"error": "日志目录不存在"}

        try:
            log_files = list(cls._log_dir.glob("day_translation*.log"))

            if not log_files:
                return {"message": "没有找到日志文件", "files": []}

            file_info = []
            total_size = 0

            for log_file in sorted(
                log_files, key=lambda x: x.stat().st_mtime, reverse=True
            ):
                file_stat = log_file.stat()
                file_size = file_stat.st_size
                file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                total_size += file_size

                file_info.append(
                    {
                        "name": log_file.name,
                        "size_mb": file_size / (1024 * 1024),
                        "modified": file_mtime.strftime("%Y-%m-%d %H:%M:%S"),
                        "path": str(log_file),
                    }
                )

            return {
                "total_files": len(log_files),
                "total_size_mb": total_size / (1024 * 1024),
                "files": file_info,
            }

        except (OSError, IOError, PermissionError) as e:
            return {"error": f"获取日志信息时出现错误: {e}"}


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器

    Args:
        name: 日志器名称，通常是模块名

    Returns:
        配置好的日志器
    """
    return logging.getLogger(name)


def log_function_call(func_name: str, **kwargs):
    """
    记录函数调用的装饰器辅助函数

    Args:
        func_name: 函数名称
        **kwargs: 函数参数
    """
    logger = get_logger("function_calls")
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug("调用函数: %s(%s)", func_name, params)


def log_performance(func_name: str, duration: float, **kwargs):
    """
    记录性能信息

    Args:
        func_name: 函数名称
        duration: 执行时间（秒）
        **kwargs: 额外信息
    """
    logger = get_logger("performance")
    extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info("性能统计: %s 耗时 %.3f秒 %s", func_name, duration, extra_info)


def log_user_action(action: str, **kwargs):
    """
    记录用户操作

    Args:
        action: 操作名称
        **kwargs: 操作参数
    """
    logger = get_logger("user_actions")
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug("用户操作: %s - %s", action, params)


def log_data_processing(operation: str, count: int, **kwargs):
    """
    记录数据处理操作

    Args:
        operation: 操作名称
        count: 处理数量
        **kwargs: 额外信息
    """
    logger = get_logger("data_processing")
    extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug("数据处理: %s - 处理了 %d 条记录 %s", operation, count, extra_info)


def log_error_with_context(exception: Exception, context: str = "", **kwargs):
    """
    记录带上下文的错误信息

    Args:
        exception: 异常对象
        context: 错误上下文
        **kwargs: 额外信息
    """
    logger = get_logger("errors")
    extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.error(
        "错误发生: %s - %s - %s", context, str(exception), extra_info, exc_info=True
    )


# 便捷的日志记录函数
def debug(msg: str, *args, **kwargs):
    """记录调试信息"""
    logger = get_logger("debug")
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """记录信息"""
    logger = get_logger("info")
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """记录警告"""
    logger = get_logger("warning")
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """记录错误"""
    logger = get_logger("error")
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """记录严重错误"""
    logger = get_logger("critical")
    logger.critical(msg, *args, **kwargs)


# 自动初始化
if not LoggingConfig.is_initialized():
    # 优先从用户配置读取，然后是环境变量，最后是默认值
    log_level = "INFO"
    enable_file_logging = True
    enable_console_logging = False
    max_file_size = 10 * 1024 * 1024  # 10MB
    backup_count = 5

    try:
        # 尝试从用户配置系统读取
        from user_config import UserConfigManager

        config_manager = UserConfigManager()
        log_config = config_manager.log_config

        log_level = log_config.get_value("log_level", "INFO")
        enable_file_logging = log_config.get_value("log_to_file", True)
        enable_console_logging = log_config.get_value("log_to_console", False)
        max_file_size = (
            log_config.get_value("log_file_size", 10) * 1024 * 1024
        )  # MB to bytes
        backup_count = log_config.get_value("log_backup_count", 5)

    except ImportError:
        # 如果用户配置系统不可用，使用环境变量
        log_level = os.getenv("DAY_TRANSLATION_LOG_LEVEL", "INFO")
        enable_file_logging = (
            os.getenv("DAY_TRANSLATION_LOG_TO_FILE", "true").lower() == "true"
        )
        enable_console_logging = (
            os.getenv("DAY_TRANSLATION_LOG_TO_CONSOLE", "false").lower() == "true"
        )

    LoggingConfig.setup_logging(
        level=log_level,
        enable_file_logging=enable_file_logging,
        enable_console_logging=enable_console_logging,
        max_file_size=max_file_size,
        backup_count=backup_count,
    )
