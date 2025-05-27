import json
from tqdm import tqdm
try:
    from config import get_preparation_config
except ImportError:
    from .config import get_preparation_config


def words_to_ids(words, vocab):
    """Convert list of words to token IDs"""
    doc_ids = [vocab['<START>']]
    unk_count = 0

    for word in words:
        if word in vocab:
            doc_ids.append(vocab[word])
        else:
            doc_ids.append(vocab['<UNK>'])
            unk_count += 1

    doc_ids.append(vocab['<END>'])
    return doc_ids, unk_count


def convert_to_id(tokenized_file, vocab_file, output_file):
    """Convert words to IDs"""

    print("=== CONVERTING TO IDS ===")

    # Load config
    config = get_preparation_config()
    max_length = config["max_sequence_length"]

    # Load the vocab
    with open(vocab_file, 'r', encoding='utf-8') as f:
        vocab = json.load(f)

    # Load tokenized data
    with open(tokenized_file, 'r', encoding='utf-8') as f:
        tokenized_docs = json.load(f)

    # Convert to IDs
    id_docs = []
    total_unk_count = 0
    long_docs = 0

    for doc in tqdm(tokenized_docs, desc="Convert to IDs"):
        if len(doc) > max_length - 2:  # The 2 is for START and END token
            # Long docs
            long_docs += 1
            # Split into chunks
            chunk_size = max_length - 2
            for i in range(0, len(doc), chunk_size):
                chunk = doc[i:i + chunk_size]
                if len(chunk) >= 10:  # Only keep substantial chunks
                    doc_ids, unk_count = words_to_ids(chunk, vocab)
                    id_docs.append(doc_ids)
                    total_unk_count += unk_count
        else:
            # Short docs
            doc_ids, unk_count = words_to_ids(doc, vocab)
            id_docs.append(doc_ids)
            total_unk_count += unk_count

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(id_docs, f)

    print(f"Documents: {len(id_docs):,}")
    print(f"Unknown words: {total_unk_count:,}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    convert_to_id("../processed_data/train.json",
                  "../processed_data/vocabulary.json",
                  "../processed_data/train_ids.json")
    convert_to_id("../processed_data/val.json",
                  "../processed_data/vocabulary.json",
                  "../processed_data/val_ids.json")
    convert_to_id("../processed_data/test.json",
                  "../processed_data/vocabulary.json",
                  "../processed_data/test_ids.json")