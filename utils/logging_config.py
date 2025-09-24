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

            # 错误日志单独记录
            error_log_file = log_dir / f"day_translation_error_{timestamp}.log"
            error_handler = logging.handlers.RotatingFileHandler(
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
    def _cleanup_old_logs(cls, days_to_keep: int = 1) -> None:
        """
        清理指定天数前的日志文件

        Args:
            days_to_keep: 保留最近几天的日志文件，默认1天
        """
        if cls._log_dir is None or not cls._log_dir.exists():
            return

        try:
            from datetime import timedelta

            # 计算截止时间
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)

            # 查找所有日志文件
            log_files = list(cls._log_dir.glob("day_translation*.log"))

            deleted_count = 0
            for log_file in log_files:
                try:
                    # 获取文件修改时间
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

                    # 如果文件超过指定天数，则删除
                    if file_mtime < cutoff_time:
                        log_file.unlink()
                        deleted_count += 1

                except (OSError, IOError):
                    # 忽略删除失败的文件，避免影响程序运行
                    pass

            # 只在有删除操作时才输出信息
            if deleted_count > 0:
                print(f"🗑️ 自动清理完成，删除了 {deleted_count} 个旧日志文件")

        except (OSError, IOError, PermissionError):
            # 忽略清理过程中的错误，避免影响程序运行
            pass


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
    # 从环境变量读取配置
    log_level = os.getenv("DAY_TRANSLATION_LOG_LEVEL", "INFO")
    enable_file_logging_env = (
        os.getenv("DAY_TRANSLATION_LOG_TO_FILE", "true").lower() == "true"
    )
    enable_console_logging_env = (
        os.getenv("DAY_TRANSLATION_LOG_TO_CONSOLE", "false").lower() == "true"
    )

    LoggingConfig.setup_logging(
        level=log_level,
        enable_file_logging=enable_file_logging_env,
        enable_console_logging=enable_console_logging_env,
    )
