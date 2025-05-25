import xxhash
from tqdm import tqdm


class ContentDeduplicator:
    """Handle content deduplication using exact hashing"""

    def __init__(self):
        self.hasher = xxhash.xxh64()
        self.exact_hashes = set()
        self.kept_after_dedup = 0

    def merge_and_deduplicate(self, temp_files, output_file):
        """Merge all temporary files and remove exact duplicates"""
        print("\nMerging results")

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
                                self.hasher.reset()
                                self.hasher.update(doc.encode('utf-8'))
                                doc_hash = self.hasher.intdigest()

                                if doc_hash not in self.exact_hashes:
                                    self.exact_hashes.add(doc_hash)
                                    out.write(doc + '\n\n---\n\n')
                                    self.kept_after_dedup += 1

                    # Handle remaining content
                    if buffer.strip():
                        self.hasher.reset()
                        self.hasher.update(buffer.encode('utf-8'))
                        doc_hash = self.hasher.intdigest()

                        if doc_hash not in self.exact_hashes:
                            self.exact_hashes.add(doc_hash)
                            out.write(buffer + '\n\n---\n\n')
                            self.kept_after_dedup += 1

    def get_kept_count(self):
        """Return number of documents kept after deduplication"""
        return self.kept_after_dedup

    def get_duplicates_removed(self, original_kept):
        """Return number of duplicates removed"""
        return original_kept - self.kept_after_dedup