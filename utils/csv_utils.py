"""
CSV 读写封装 - 统一编码与 newline，与翻译 CSV 表头常量配合使用。
"""

from typing import Optional, TextIO

from utils.constants import CSV_ENCODING_READ, CSV_ENCODING_WRITE


def open_csv_reader(
    path: str,
    encoding: Optional[str] = None,
    newline: str = "",
) -> TextIO:
    """以读方式打开 CSV 文件，默认 utf-8-sig（兼容 BOM），newline=''。"""
    return open(
        path,
        "r",
        encoding=encoding or CSV_ENCODING_READ,
        newline=newline,
    )


def open_csv_writer(
    path: str,
    encoding: Optional[str] = None,
    newline: str = "",
) -> TextIO:
    """以写方式打开 CSV 文件，默认 utf-8，newline=''。"""
    return open(
        path,
        "w",
        encoding=encoding or CSV_ENCODING_WRITE,
        newline=newline,
    )
