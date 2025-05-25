import re

# Compile regex
COMBINED_REMOVAL_PATTERN = re.compile(r'''
    # HTML tags
    <[^>]+>|
    # JS/CSS blocks
    \{[^}]*\}|
    # Navigation elements
    \b(home|about|contact|login|register|sign\s+in|sign\s+up|menu|navigation|navbar|footer|header|sidebar)\b|
    # UI elements  
    \b(skip\s+to|jump\s+to|go\s+to|click\s+here|read\s+more|learn\s+more|subscribe|newsletter|follow\s+us)\b|
    # Social media
    \b(facebook|twitter|instagram|linkedin|youtube)\b|
    # Legal/copyright
    ©.*?\d{4}.*?(all\s+rights\s+reserved|copyright)|
    \b(privacy\s+policy|terms\s+of\s+service|cookie\s+policy|gdpr)\b|
    # Ads
    \b(advertisement|sponsored|affiliate|buy\s+now|order\s+now|free\s+trial|limited\s+time)\b|
    # Technical
    function\s*\([^)]*\)|var\s+\w+\s*=|document\.\w+|window\.\w+|console\.\w+
''', re.IGNORECASE | re.VERBOSE)

# Fast cleanup patterns
CLEANUP_PATTERNS = [
    (re.compile(r'[|•→←↑↓◦▪▫□■►◄]+'), ' '),
    (re.compile(r'\s*[-_=]{3,}\s*'), '\n'),
    (re.compile(r'\*{3,}'), '\n'),
    (re.compile(r'[ \t]+'), ' '),
    (re.compile(r'\n\s*\n\s*\n+'), '\n\n')
]

# Legacy patterns for compatibility
WORD_PATTERN = re.compile(r'\b[a-zA-Z]+\b')
SENTENCE_PATTERN = re.compile(r'[.!?]+')
PRINTABLE_PATTERN = re.compile(b'[\x20-\x7E\x09\x0A\x0D]')

# Lookup tables
LATIN_ALPHA = frozenset(chr(i) for i in range(256) if chr(i).isalpha())
PRINTABLE_CHARS = frozenset(chr(i) for i in range(32, 127)) | {'\t', '\n', '\r', ' '}