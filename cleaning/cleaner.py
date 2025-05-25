import gzip
import warcio
from tqdm import tqdm
import glob
import os
from multiprocessing import Pool, cpu_count
import tempfile
from collections import deque

from content_validation import load_english_words, is_good, quality_check
from web_cleaner import remove_web_boilerplate
from deduplicator import ContentDeduplicator


def process_file(wet_file, out, english_words, config=None):
    """Process single WET file"""
    if config is None:
        from config import get_cleaning_config
        config = get_cleaning_config()

    total = kept = 0
    batch_texts = deque()
    batch_size = config["batch_size"]

    with gzip.open(wet_file, 'rb') as gz:
        for record in warcio.ArchiveIterator(gz, no_record_parse=False):
            if record.rec_type == 'conversion':
                total += 1
                content_bytes = record.content_stream().read()

                if not (config["min_text_length"] < len(content_bytes) < config["max_text_length"]):
                    continue

                text = content_bytes.decode('utf-8', errors='ignore')

                # Clean website boilerplate
                text = remove_web_boilerplate(text)

                # Document check
                if is_good(text, english_words, config) and quality_check(text, config):
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
    wet_file, english_words, config = args

    # Write to temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, buffering=131072)

    try:
        stats = process_file(wet_file, temp_file, english_words, config)
        temp_file.close()
        return {'total': stats['total'], 'kept': stats['kept'], 'temp_file': temp_file.name}
    except Exception as e:
        temp_file.close()
        os.unlink(temp_file.name)
        raise e


def preprocess(input_dir, output_file, num_files=None, config=None):
    """Process all WET files in the folder"""
    if config is None:
        from config import get_cleaning_config
        config = get_cleaning_config()

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
        worker_args = [(wet_file, english_words, config) for wet_file in wet_files]

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

    # Merge all temporary files and deduplicate
    if config["deduplication_enabled"]:
        deduplicator = ContentDeduplicator()
        deduplicator.merge_and_deduplicate(temp_files, output_file)
        kept_after_dedup = deduplicator.get_duplicates_removed(kept)
        duplicates_removed = deduplicator.get_kept_count()
    else:
        kept_after_dedup = kept
        duplicates_removed = 0
        with open(output_file, 'w', encoding='utf-8') as out:
            for temp_file in temp_files:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    out.write(f.read())

    # Clean up temp files
    for temp_file in temp_files:
        os.unlink(temp_file)

    print(f"\n=== Preprocessing ===")
    print(f"Total documents: {total:,}")
    print(f"After filtering: {kept:,}")
    print(f"After exact dedup: {kept_after_dedup:,}")
    print(f"Exact duplicates removed: {duplicates_removed:,}")
    print(f"Overall retention rate: {kept_after_dedup / total * 100:.1f}%")


if __name__ == '__main__':
    preprocess("../data/CC_data", "../processed_data/cleaned_data.txt", 50)