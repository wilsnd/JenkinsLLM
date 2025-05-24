import gzip
import warcio
from tqdm import tqdm
import glob
import os
import re
from multiprocessing import Pool, cpu_count
import tempfile

# Compile regex
WORD_PATTERN = re.compile(r'\b[a-zA-Z]+\b')


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

    # Count printable characters
    printable_chars = 0
    total_chars = len(text)

    for char in text:
        if char.isprintable() or char.isspace():
            printable_chars += 1

    # Must be at least 95% printable characters
    printable_ratio = printable_chars / total_chars
    return printable_ratio > 0.95


def is_good(text, english_words):
    """Check the text quality"""

    # Check length
    text_len = len(text)
    if not (500 < text_len < 20000):
        return False

    # Encoding Validation
    if not is_valid_encoding(text):
        return False

    # Check baesd on latin character
    latin_chars = sum(1 for char in text if char.isalpha() and ord(char) < 256)
    total_alpha = sum(1 for char in text if char.isalpha())
    if total_alpha > 0 and (latin_chars / total_alpha) < 0.95:
        return False

    # Limit search
    search_text = text[:min(2000, text_len)]
    words = WORD_PATTERN.findall(search_text.lower())[:100]

    if not words:
        return False

    # Check if English words
    english_count = sum(1 for word in words if word in english_words)

    if english_count < len(words) * 0.50:
        return False

    lines = text.split('\n')
    unique_ratio = len(set(lines)) / len(lines)
    return unique_ratio > 0.5


def process_file(wet_file, out, english_words):
    """Process single WET file"""

    total = kept = 0
    batch_texts = []
    batch_size = 50

    with gzip.open(wet_file, 'rb') as gz:
        for record in warcio.ArchiveIterator(gz):
            if record.rec_type == 'conversion':
                total += 1
                text = record.content_stream().read().decode('utf-8', errors='ignore')

                if is_good(text, english_words):
                    batch_texts.append(text + '\n\n---\n\n')
                    kept += 1

                    # Write batch
                    if len(batch_texts) >= batch_size:
                        out.write(''.join(batch_texts))
                        batch_texts = []

        if batch_texts:
            out.write(''.join(batch_texts))

    return {'total': total, 'kept': kept}


def process_file_worker(args):
    """Multiprocessing worker"""
    wet_file, english_words = args

    # Write to temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, buffering=65536)

    try:
        stats = process_file(wet_file, temp_file, english_words)
        temp_file.close()
        return {'total': stats['total'], 'kept': stats['kept'],
                'temp_file': temp_file.name}
    except Exception as e:
        temp_file.close()
        os.unlink(temp_file.name)
        raise e


def stage_1(input_dir, output_file, num_workers=None):
    """Process all WET files in the folder"""

    wet_files = glob.glob(os.path.join(input_dir, "*.warc.wet.gz"))
    print(f"Found {len(wet_files)} WET files")

    english_words = load_english_words()
    total = 0
    kept = 0
    temp_files = []

    # Set worker
    num_workers = 4

    # Parallel processing
    with Pool(num_workers) as pool:
        # Prepare arguments for workers
        worker_args = [(wet_file, english_words) for wet_file in wet_files]

        # Process bar
        with tqdm(total=len(wet_files), desc="Files completed") as pbar:
            for result in pool.imap_unordered(process_file_worker, worker_args):
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
    with open(output_file, 'w', encoding='utf-8', buffering=65536) as out:
        for temp_file in tqdm(temp_files, desc="Merging files"):
            with open(temp_file, 'r', encoding='utf-8', buffering=65536) as f:
                out.write(f.read())
            os.unlink(temp_file)

    print(f"\n=== STAGE 1 FINAL SUMMARY ===")
    print(f"Total documents: {total:,}")
    print(f"Kept documents: {kept:,}")
    print(f"Overall retention rate: {kept / total * 100:.1f}%")


if __name__ == '__main__':
    stage_1("../data/CC_data", "stage_1_output_v2.txt")