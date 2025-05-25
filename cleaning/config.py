# Config
DEFAULT_CONFIG = {
    "min_text_length": 500,
    "max_text_length": 20000,
    "english_threshold": 0.4,
    "content_ratio_threshold": 0.2,
    "printable_ratio_threshold": 0.95,
    "latin_char_threshold": 0.95,
    "unique_lines_threshold": 0.5,
    "word_diversity_threshold": 0.3,
    "avg_words_min": 5,
    "avg_words_max": 50,
    "batch_size": 500,
    "deduplication_enabled": True
}

def get_cleaning_config():
    return DEFAULT_CONFIG.copy()