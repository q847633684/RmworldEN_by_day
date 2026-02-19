"""
统一错误处理工具

提供 report_handler_error，供各 handler 在 except 中调用，
统一完成：打印错误、记录日志、debug_mode 时打印 traceback。
"""
from typing import Any, Optional
from utils.logging_config import log_error_with_context
from utils.ui_style import ui


def report_handler_error(
    e: Exception,
    message: str = "操作失败",
    mod_dir: Optional[str] = None,
    **log_context: Any
) -> None:
    """
    统一上报 handler 异常：打印错误、记录日志、debug 时打印 traceback

    Args:
        e: 异常对象
        message: 错误描述
        mod_dir: 模组目录（可选）
        **log_context: 传给 log_error_with_context 的额外上下文
    """
    ui.print_error(f"❌ {message}: {e}")
    ctx = dict(log_context)
    if mod_dir is not None:
        ctx["mod_dir"] = mod_dir
    log_error_with_context(e, message, **ctx)
    _maybe_print_traceback()


def _maybe_print_traceback() -> None:
    """若启用 debug_mode 则打印 traceback"""
    try:
        from user_config import UserConfigManager
        if UserConfigManager.get_instance().system_config.get_value("debug_mode", False):
            import traceback
            traceback.print_exc()
    except Exception:
        pass
