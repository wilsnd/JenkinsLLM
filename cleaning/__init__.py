from .cleaner import preprocess, process_file, process_file_worker
from .content_validation import load_english_words, is_valid_encoding, is_good, quality_check
from .web_cleaner import clean_web_content, remove_web_boilerplate
from .deduplicator import ContentDeduplicator
from .config import get_cleaning_config
from .patterns import (COMBINED_REMOVAL_PATTERN, CLEANUP_PATTERNS, WORD_PATTERN, SENTENCE_PATTERN)

__version__ = "1.0.0"

__all__ = [
    "preprocess",
    "process_file",
    "process_file_worker",
    "load_english_words",
    "is_valid_encoding",
    "is_good",
    "quality_check",
    "clean_web_content",
    "remove_web_boilerplate",
    "ContentDeduplicator",
    "COMBINED_REMOVAL_PATTERN",
    "CLEANUP_PATTERNS",
    "WORD_PATTERN",
    "SENTENCE_PATTERN",
    "get_cleaning_config"
]

def get_version():
    return __version__