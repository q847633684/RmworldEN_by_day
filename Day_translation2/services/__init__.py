"""
Day Translation 2 - 服务层

提供独立的业务服务，支持核心业务逻辑。
包括机器翻译、批量处理、验证、语料生成等服务。
"""

try:
    # 尝试相对导入（包内使用）
    from .batch_processor import BatchProcessor
    from .corpus_generator import generate_parallel_corpus
    from .translation_service import translate_csv
    from .validation_service import TranslationValidator, validate_csv_file
except ImportError:
    # 备用绝对导入（独立运行时）
    from batch_processor import BatchProcessor
    from corpus_generator import generate_parallel_corpus
    from translation_service import translate_csv
    from validation_service import TranslationValidator, validate_csv_file

__all__ = [
    "translate_csv",
    "BatchProcessor",
    "TranslationValidator",
    "validate_csv_file",
    "generate_parallel_corpus",
]
