import re
from tqdm import tqdm
from multiprocessing import Pool

# Pre-compile regex patterns
SENTENCE_PATTERN = re.compile(r'[.!?]+')

def quality_check(text):
    """Combine every check"""
    if len(text) < 500:
        return False

    # Split text
    lines = text.split('\n')
    stripped_lines = [line.strip() for line in lines if line.strip()]

    # Check line diversity
    if len(stripped_lines) >= 5:
        if len(set(stripped_lines)) / len(stripped_lines) <= 0.5:
            return False  # Exit early

    # Check content ratio
    content_lines = sum(1 for line in stripped_lines
                        if len(line) > 40 and ' ' in line and not line.isupper())
    if content_lines / len(lines) <= 0.2:
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


def process_batch_worker(batch_docs):
    """Process batch and then return the results"""
    kept_docs = []
    for doc in batch_docs:
        if quality_check(doc):
            kept_docs.append(doc)
    return kept_docs


def stage_2(input_file, output_file, batch_size=500):
    """Stage 2: Advanced Filtering """

    print("=== STAGE 2: ADVANCED FILTERING ===")

    # Set worker as total CPU - 1
    num_workers = 3

    # Stream processing
    with Pool(num_workers) as pool:
        with open(output_file, 'w', encoding='utf-8', buffering=1024 * 1024) as out:

            buffer = ""
            chunk_size = 1024 * 1024 * 50  # 50MB chunks
            batch_queue = []
            total_docs = 0
            kept_docs = 0
            pending_futures = []

            print("Starting process")

            with open(input_file, 'r', encoding='utf-8') as f:
                with tqdm(desc="Processing documents") as pbar:

                    while True:
                        # Read chunk
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break

                        buffer += chunk

                        # Extract the documents
                        while '\n---\n' in buffer:
                            doc, buffer = buffer.split('\n---\n', 1)
                            if doc.strip():
                                batch_queue.append(doc.strip())
                                total_docs += 1

                                # Send to the worker if the batch is full
                                if len(batch_queue) >= batch_size:
                                    future = pool.apply_async(process_batch_worker, (batch_queue,))
                                    pending_futures.append(future)
                                    batch_queue = []

                                    # Collect the completed results
                                    if len(pending_futures) >= num_workers * 2:
                                        completed_future = pending_futures.pop(0)
                                        kept_batch = completed_future.get()

                                        # Write the results
                                        for kept_doc in kept_batch:
                                            out.write(kept_doc + '\n\n---\n\n')
                                            kept_docs += 1

                                        # Update progress
                                        pbar.update(len(kept_batch))
                                        pbar.set_postfix({
                                            'Processed': f"{total_docs:,}",
                                            'Kept': f"{kept_docs:,}",
                                            'Rate': f"{kept_docs / total_docs * 100:.1f}%" if total_docs > 0 else "0%"
                                        })

                    # Process the remaining buffer
                    if buffer.strip():
                        batch_queue.append(buffer.strip())
                        total_docs += 1

                    # Process final batch
                    if batch_queue:
                        future = pool.apply_async(process_batch_worker, (batch_queue,))
                        pending_futures.append(future)

                    # Collect all remaining results
                    for future in pending_futures:
                        kept_batch = future.get()
                        for kept_doc in kept_batch:
                            out.write(kept_doc + '\n\n---\n\n')
                            kept_docs += 1
                        pbar.update(len(kept_batch))

    print(f"\n=== STAGE 2 FINAL SUMMARY ===")
    print(f"Total documents: {total_docs:,}")
    print(f"Kept documents: {kept_docs:,}")
    print(f"Overall retention rate: {kept_docs / total_docs * 100:.1f}%")


if __name__ == "__main__":
    stage_2("stage_1_output.txt", "stage_2_output.txt")
