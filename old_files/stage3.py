import hashlib
from tqdm import tqdm


def stream_documents(input_file):
    """Read documents 1 by 1"""
    buffer = ""
    chunk_size = 1024 * 1024 * 50  # 50MB chunks

    with open(input_file, 'r', encoding='utf-8') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            buffer += chunk

            while '\n---\n' in buffer:
                doc, buffer = buffer.split('\n---\n', 1)
                if doc.strip():
                    yield doc.strip()

        # Handle the remaining buffer
        if buffer.strip():
            yield buffer.strip()


def stage_3(input_file, output_file):
    """Stage 3: Exact Deduplication"""

    print("=== STAGE 3: EXACT DEDUPLICATION ===")

    # Statistics
    total_docs = 0
    kept_docs = 0
    exact_hashes = set()

    print("Removing exact duplicates...")

    with open(output_file, 'w', encoding='utf-8') as out:
        for doc in tqdm(stream_documents(input_file), desc="Exact dedup"):
            total_docs += 1
            doc_hash = hashlib.md5(doc.encode('utf-8')).hexdigest()

            if doc_hash not in exact_hashes:
                exact_hashes.add(doc_hash)
                out.write(doc + '\n\n---\n\n')
                kept_docs += 1

    print(f"\n=== STAGE 3 FINAL SUMMARY ===")
    print(f"Total documents: {total_docs:,}")
    print(f"Kept documents: {kept_docs:,}")
    print(f"Exact duplicates removed: {total_docs - kept_docs:,}")
    print(f"Overall keep rate: {kept_docs/total_docs*100:.1f}%")


if __name__ == "__main__":
    stage_3("stage_1_2_output.txt", "stage_3_output.txt")