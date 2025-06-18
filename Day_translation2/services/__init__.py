"""
Day Translation 2 - 服务层

提供独立的业务服务，支持核心业务逻辑。
包括机器翻译、批量处理、验证、语料生成等服务。
"""

from .machine_translate import (
    MachineTranslateService,
    translate_text,
    translate_batch
)
from .batch_processor import (
    BatchProcessorService, 
    process_multiple_mods
)
from .validation_service import (
    ValidationService,
    validate_translation_data
)
from .corpus_generator import (
    CorpusGeneratorService,
    generate_parallel_corpus
)

__all__ = [
    "MachineTranslateService",
    "translate_text",
    "translate_batch", 
    "BatchProcessorService",
    "process_multiple_mods",
    "ValidationService", 
    "validate_translation_data",
    "CorpusGeneratorService",
    "generate_parallel_corpus"
]
