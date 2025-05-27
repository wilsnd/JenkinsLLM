try:
    from .patterns import COMBINED_REMOVAL_PATTERN, CLEANUP_PATTERNS
except ImportError:
    from patterns import COMBINED_REMOVAL_PATTERN, CLEANUP_PATTERNS

def clean_web_content(text):
    """Additional web data cleaning"""
    if len(text) < 100:
        return text

    # Cleaning
    text = COMBINED_REMOVAL_PATTERN.sub(' ', text)
    for pattern, replacement in CLEANUP_PATTERNS:
        text = pattern.sub(replacement, text)

    return text


def remove_web_boilerplate(text):
    """Remove the top and bottom section"""
    text = clean_web_content(text)

    # Split text
    lines = text.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]

    # Filter out very short lines
    if len(non_empty_lines) > 10:
        start = len(non_empty_lines) // 7  # 15%
        end = len(non_empty_lines) - len(non_empty_lines) // 7  # 85%
        non_empty_lines = non_empty_lines[start:end]

    return '\n'.join(non_empty_lines)