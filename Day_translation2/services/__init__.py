"""
Day Translation 2 - 服务层

提供独立的业务服务，支持核心业务逻辑。
包括机器翻译、批量处理、验证、语料生成等服务。
"""

from .batch_processor import BatchProcessorService, process_multiple_mods
from .corpus_generator import CorpusGeneratorService, generate_parallel_corpus
from .translation_service import (MachineTranslateService, translate_batch,
                                translate_text)
from .validation_service import ValidationService, validate_translation_data

__all__ = [
    "MachineTranslateService",
    "translate_text",
    "translate_batch",
    "BatchProcessorService",
    "process_multiple_mods",
    "ValidationService",
    "validate_translation_data",
    "CorpusGeneratorService",
    "generate_parallel_corpus",
]
