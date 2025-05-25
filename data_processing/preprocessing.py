import gzip
import warcio
from tqdm import tqdm
import glob
import os
import re
from multiprocessing import Pool, cpu_count
import tempfile
import xxhash
from collections import deque

# Compile regex
WORD_PATTERN = re.compile(r'\b[a-zA-Z]+\b')
SENTENCE_PATTERN = re.compile(r'[.!?]+')
PRINTABLE_PATTERN = re.compile(b'[\x20-\x7E\x09\x0A\x0D]')
NAV_PATTERNS = [
    re.compile(r'\b(home|about|contact|login|register|sign in|sign up)\b', re.IGNORECASE),
    re.compile(r'\b(menu|navigation|navbar|footer|header|sidebar)\b', re.IGNORECASE),
    re.compile(r'\b(skip to|jump to|go to|click here|read more|learn more)\b', re.IGNORECASE),
    re.compile(r'\b(subscribe|newsletter|follow us|share|like|tweet)\b', re.IGNORECASE),
    re.compile(r'\b(facebook|twitter|x|instagram|linkedin|youtube)\b', re.IGNORECASE),
    re.compile(r'\b(search|categories|tags|archive|recent posts)\b', re.IGNORECASE)
]
UI_PATTERNS = [
    re.compile(r'toggle navigation', re.IGNORECASE),
    re.compile(r'show/hide menu', re.IGNORECASE),
    re.compile(r'expand/collapse', re.IGNORECASE),
    re.compile(r'previous\s+next', re.IGNORECASE),
    re.compile(r'page \d+ of \d+', re.IGNORECASE),
    re.compile(r'showing \d+ results', re.IGNORECASE),
    re.compile(r'sort by|filter by', re.IGNORECASE),
    re.compile(r'view all|see more|show all', re.IGNORECASE)
]
LEGAL_PATTERNS = [
    re.compile(r'©.*?\d{4}.*?(all rights reserved|copyright)', re.IGNORECASE),
    re.compile(r'privacy policy|terms of service|cookie policy', re.IGNORECASE),
    re.compile(r'gdpr|data protection|privacy notice', re.IGNORECASE),
    re.compile(r'powered by.*?(?=\n|\.|$)', re.IGNORECASE),
    re.compile(r'designed by.*?(?=\n|\.|$)', re.IGNORECASE),
    re.compile(r'copyright.*?\d{4}.*?(?=\n|\.|$)', re.IGNORECASE)
]
AD_PATTERNS = [
    re.compile(r'advertisement.*?(?=\n|\.|$)', re.IGNORECASE),
    re.compile(r'sponsored.*?(?=\n|\.|$)', re.IGNORECASE),
    re.compile(r'affiliate.*?(?=\n|\.|$)', re.IGNORECASE),
    re.compile(r'promotion.*?(?=\n|\.|$)', re.IGNORECASE),
    re.compile(r'\b(buy now|order now|get now|download now)\b', re.IGNORECASE),
    re.compile(r'\b(free trial|limited time|special offer|discount)\b', re.IGNORECASE)
]
TECH_PATTERNS = [
    re.compile(r'<[^>]+>'),  # HTML tags
    re.compile(r'\{[^}]*\}'),  # CSS/JavaScript
    re.compile(r'function\s*\([^)]*\)'),  # Function definitions
    re.compile(r'var\s+\w+\s*='),  # Variable declarations
    re.compile(r'document\.\w+'),  # JavaScript DOM
    re.compile(r'window\.\w+'),  # JavaScript window
    re.compile(r'console\.\w+'),  # Console commands
]
SPECIAL_CHARS = re.compile(r'[|•→←↑↓◦▪▫□■►◄]+')
DIVIDER_LINES = re.compile(r'\s*[-_=]{3,}\s*')
ASTERISK_DIVIDERS = re.compile(r'\*{3,}')
MULTIPLE_NEWLINES = re.compile(r'\n\s*\n\s*\n+')
MULTIPLE_SPACES = re.compile(r'[ \t]+')
TRIM_LINES = re.compile(r'^\s+|\s+$', re.MULTILINE)
FINAL_SPACING = re.compile(r'\n\s*\n\s*\n+')

# Lookup tables
LATIN_ALPHA = frozenset(chr(i) for i in range(256) if chr(i).isalpha())
PRINTABLE_CHARS = frozenset(chr(i) for i in range(32, 127)) | {'\t', '\n', '\r', ' '}


def load_english_words():
    """Load English words from english_words.txt"""
    with open('../data/english_words.txt', 'r') as f:
        words = {line.strip().lower() for line in f if line.strip()}
    print(f"Loaded {len(words)} English words")
    return words


def is_valid_encoding(text):
    """Encoding Validation"""
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
    return printable_ratio > 0.95


def is_good(text, english_words):
    """Stage 1 cleaning"""

    # Check length
    text_len = len(text)
    if not (500 < text_len < 20000):
        return False

    # Encoding Validation
    if not is_valid_encoding(text):
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
    if total_alpha > 0 and (latin_chars / total_alpha) < 0.95:
        return False

    # Limit search
    search_text = text[:min(2000, text_len)].lower()
    words = WORD_PATTERN.findall(search_text)[:100]

    if not words:
        return False

    # Check if English words
    english_count = sum(1 for word in words if word in english_words)

    if english_count < len(words) * 0.4:
        return False

    lines = text.split('\n')
    unique_ratio = len(set(lines)) / len(lines)
    return unique_ratio > 0.5


def quality_check(text):
    """Stage 2 cleaning"""
    if len(text) < 500:
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
    if lines_len > 0 and (content_lines / lines_len) <= 0.2:
        return False

    # Check word diversity
    words = text.lower().split()
    if len(words) >= 50:
        if len(set(words)) / len(words) <= 0.3:
            return False

    # Sentence check
    sentences = SENTENCE_PATTERN.split(text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) >= 3:
        total_words = sum(len(s.split()) for s in sentences)
        avg_words = total_words / len(sentences)
        return 5 < avg_words < 50

    return True


def clean_web_content(text):
    """Additional web data cleaning"""
    if not text or len(text) < 100:
        return ""

    # Remove HTML tags
    for pattern in TECH_PATTERNS:
        text = pattern.sub(' ', text)

    # Remove nav elements
    for pattern in NAV_PATTERNS:
        text = pattern.sub(' ', text)

    # Remove UI elements
    for pattern in UI_PATTERNS:
        text = pattern.sub(' ', text)

    # Remove Legal
    for pattern in LEGAL_PATTERNS:
        text = pattern.sub(' ', text)

    # Remove ads
    for pattern in AD_PATTERNS:
        text = pattern.sub(' ', text)

    # Remove specials chars
    text = SPECIAL_CHARS.sub(' ', text)
    text = DIVIDER_LINES.sub('\n', text)
    text = ASTERISK_DIVIDERS.sub('\n', text)

    # Clean up
    text = MULTIPLE_SPACES.sub(' ', text)
    text = TRIM_LINES.sub('', text)
    text = MULTIPLE_NEWLINES.sub('\n\n', text)

    return text

def remove_web_boilerplate(text):
    """Remove the top and bottom section"""
    text = clean_web_content(text)

    lines = text.split('\n')

    # Filter out very short lines
    content_lines = []
    for line in lines:
        stripped = line.strip()
        if len(stripped) > 15:  # Keep substantial content only
            content_lines.append(stripped)

    # Skip first and last section
    if len(content_lines) > 10:
        # Skip first 15% and last 15%
        start = int(len(content_lines) * 0.15)
        end = int(len(content_lines) * 0.85)
        content_lines = content_lines[start:end]

    return '\n'.join(content_lines)


def process_file(wet_file, out, english_words):
    """Process single WET file"""

    total = kept = 0
    batch_texts = deque()
    batch_size = 100

    with gzip.open(wet_file, 'rb') as gz:
        for record in warcio.ArchiveIterator(gz, no_record_parse=False):
            if record.rec_type == 'conversion':
                total += 1
                content_bytes = record.content_stream().read()

                if not (500 < len(content_bytes) < 20000):
                    continue

                text = content_bytes.decode('utf-8', errors='ignore')

                # Clean website boilerplate
                text = remove_web_boilerplate(text)

                # Document check
                if is_good(text, english_words) and quality_check(text):
                    batch_texts.append(text + '\n\n---\n\n')
                    kept += 1

                    # Write batch
                    if len(batch_texts) >= batch_size:
                        out.write(''.join(batch_texts))
                        batch_texts.clear()

        if batch_texts:
            out.write(''.join(batch_texts))

    return {'total': total, 'kept': kept}


def process_file_worker(args):
    """Multiprocessing worker"""
    wet_file, english_words = args

    # Write to temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, buffering=131072)

    try:
        stats = process_file(wet_file, temp_file, english_words)
        temp_file.close()
        return {'total': stats['total'], 'kept': stats['kept'], 'temp_file': temp_file.name}
    except Exception as e:
        temp_file.close()
        os.unlink(temp_file.name)
        raise e


def preprocess(input_dir, output_file, num_files=None):
    """Process all WET files in the folder"""

    wet_files = glob.glob(os.path.join(input_dir, "*.warc.wet.gz"))
    if num_files is not None and num_files > 0:
        wet_files = wet_files[:num_files]
    print(f"Found {len(wet_files)} WET files (processing {'all' if num_files is None else num_files})")

    english_words = load_english_words()
    total = 0
    kept = 0
    temp_files = []

    # Set worker
    num_workers = min(cpu_count(), len(wet_files))
    print(f"Using {num_workers} workers")

    # Parallel processing
    with Pool(num_workers) as pool:
        # Arguments for workers
        worker_args = [(wet_file, english_words) for wet_file in wet_files]

        chunksize = max(1, len(wet_files) // (num_workers * 4))

        # Process bar
        with tqdm(total=len(wet_files), desc="Files completed") as pbar:
            for result in pool.imap_unordered(process_file_worker, worker_args, chunksize=chunksize):
                temp_files.append(result['temp_file'])
                total += result['total']
                kept += result['kept']

                # Update progress bar
                pbar.update(1)
                pbar.set_postfix({
                    'Total docs': f"{total:,}",
                    'Kept': f"{kept:,}",
                    'Rate': f"{kept / total * 100:.1f}%" if total > 0 else "0%"
                })

    # Merge all temporary files
    print("\nMerging results")
    hasher = xxhash.xxh64()
    exact_hashes = set()
    kept_after_dedup = 0

    with open(output_file, 'w', encoding='utf-8', buffering=262144) as out:
        for temp_file in tqdm(temp_files, desc="Merging"):
            with open(temp_file, 'rb') as f:
                buffer = ""
                chunk_size = 1024 * 1024  # 1MB

                # Process documents from temp file
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    buffer += chunk.decode('utf-8', errors='ignore')

                    while '\n\n---\n\n' in buffer:
                        doc, buffer = buffer.split('\n\n---\n\n', 1)
                        if doc.strip():
                            hasher.reset()
                            hasher.update(doc.encode('utf-8'))
                            doc_hash = hasher.intdigest()

                            if doc_hash not in exact_hashes:
                                exact_hashes.add(doc_hash)
                                out.write(doc + '\n\n---\n\n')
                                kept_after_dedup += 1

                # Handle remaining content
                if buffer.strip():
                    hasher.reset()
                    hasher.update(buffer.encode('utf-8'))
                    doc_hash = hasher.intdigest()

                    if doc_hash not in exact_hashes:
                        exact_hashes.add(doc_hash)
                        out.write(buffer + '\n\n---\n\n')
                        kept_after_dedup += 1

            os.unlink(temp_file)

    print(f"\n=== Preprocessing ===")
    print(f"Total documents: {total:,}")
    print(f"After filtering: {kept:,}")
    print(f"After exact dedup: {kept_after_dedup:,}")
    print(f"Exact duplicates removed: {kept - kept_after_dedup:,}")
    print(f"Overall retention rate: {kept_after_dedup / total * 100:.1f}%")


if __name__ == '__main__':
    preprocess("../data/CC_data", "../processed_data/cleaned_data.txt", 10)