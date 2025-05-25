from patterns import COMBINED_REMOVAL_PATTERN, CLEANUP_PATTERNS


def clean_web_content(text):
    """Additional web data cleaning"""
    if not text or len(text) < 100:
        return ""

    # Cleaning
    text = COMBINED_REMOVAL_PATTERN.sub(' ', text)
    for pattern, replacement in CLEANUP_PATTERNS:
        text = pattern.sub(replacement, text)

    return text


def remove_web_boilerplate(text):
    """Remove the top and bottom section"""
    text = clean_web_content(text)

    # Split text
    lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 60]

    # Filter out very short lines
    if len(lines) > 10:
        start = len(lines) // 7  # 15%
        end = len(lines) - len(lines) // 7  # 85%
        lines = lines[start:end]

    return '\n'.join(lines)