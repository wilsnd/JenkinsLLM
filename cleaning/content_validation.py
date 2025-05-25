from patterns import WORD_PATTERN, SENTENCE_PATTERN, PRINTABLE_PATTERN, LATIN_ALPHA


def load_english_words():
    """Load English words from english_words.txt"""
    with open('../data/english_words.txt', 'r') as f:
        words = {line.strip().lower() for line in f if line.strip()}
    print(f"Loaded {len(words)} English words")
    return words


def is_valid_encoding(text, config=None):
    """Encoding Validation"""
    if config is None:
        from config import get_cleaning_config
        config = get_cleaning_config()

    if not text:
        return False

    if isinstance(text, str):
        text_bytes = text.encode('utf-8', errors='ignore')
    else:
        text_bytes = text

    # Count printable characters
    printable_count = len(PRINTABLE_PATTERN.findall(text_bytes))
    total_chars = len(text_bytes)

    # Must be at least 95% printable characters
    printable_ratio = printable_count / total_chars
    return printable_ratio > config["printable_ratio_threshold"]


def is_good(text, english_words, config=None):
    """Stage 1 cleaning"""
    if config is None:
        from config import get_cleaning_config
        config = get_cleaning_config()

    # Check length
    text_len = len(text)
    if not (config["min_text_length"] < text_len < config["max_text_length"]):
        return False

    # Encoding Validation
    if not is_valid_encoding(text, config):
        return False

    if isinstance(text, str):
        text_bytes = text.encode('utf-8', errors='ignore')
        text_lower = text.lower()
    else:
        text_bytes = text
        text_lower = text.decode('utf-8', errors='ignore').lower()

    # Check based on latin character
    latin_chars = sum(1 for char in text if char in LATIN_ALPHA)
    total_alpha = sum(1 for char in text if char.isalpha())
    if total_alpha > 0 and (latin_chars / total_alpha) < config["latin_char_threshold"]:
        return False

    # Limit search
    search_text = text[:min(2000, text_len)].lower()
    words = WORD_PATTERN.findall(search_text)[:100]

    if not words:
        return False

    # Check if English words
    english_count = sum(1 for word in words if word in english_words)

    if english_count < len(words) * config["english_threshold"]:
        return False

    lines = text.split('\n')
    unique_ratio = len(set(lines)) / len(lines)
    return unique_ratio > config["unique_lines_threshold"]


def quality_check(text, config=None):
    """Stage 2 cleaning"""
    if config is None:
        from config import get_cleaning_config
        config = get_cleaning_config()

    if len(text) < config["min_text_length"]:
        return False

    # Split text
    lines = text.split('\n')
    lines_len = len(lines)
    stripped_lines = []
    content_lines = 0

    for line in lines:
        stripped = line.strip()
        if stripped:
            stripped_lines.append(stripped)
            # Count content lines in same loop
            if len(stripped) > 40 and ' ' in stripped and not stripped.isupper():
                content_lines += 1

    stripped_len = len(stripped_lines)

    # Check line diversity
    if len(stripped_lines) >= 5:
        if len(set(stripped_lines)) / len(stripped_lines) <= 0.5:
            return False  # Exit early

    # Check content ratio
    if lines_len > 0 and (content_lines / lines_len) <= config["content_ratio_threshold"]:
        return False

    # Check word diversity
    words = text.lower().split()
    if len(words) >= 50:
        if len(set(words)) / len(words) <= config["word_diversity_threshold"]:
            return False

    # Sentence check
    sentences = SENTENCE_PATTERN.split(text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) >= 3:
        total_words = sum(len(s.split()) for s in sentences)
        avg_words = total_words / len(sentences)
        return config["avg_words_min"] < avg_words < config["avg_words_max"]

    return True