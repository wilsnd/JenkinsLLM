import json
from tqdm import tqdm


def convert_to_id(tokenized_file, vocab_file, output_file):
    """Convert words to IDs"""

    print("=== CONVERTING TO IDS ===")

    # Load the vocab
    with open(vocab_file, 'r', encoding='utf-8') as f:
        vocab = json.load(f)

    # Load tokenized data
    with open(tokenized_file, 'r', encoding='utf-8') as f:
        tokenized_docs = json.load(f)

    # Convert to IDs
    id_docs = []
    unk_count = 0

    for doc in tqdm(tokenized_docs, desc="Convert to IDs"):
        doc_ids = [vocab['<START>']]

        for word in doc:
            if word in vocab:
                doc_ids.append(vocab[word])
            else:
                doc_ids.append(vocab['<UNK>'])
                unk_count += 1

        doc_ids.append(vocab['<END>'])
        id_docs.append(doc_ids)

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(id_docs, f)

    print(f"Documents: {len(id_docs):,}")
    print(f"Unknown words: {unk_count:,}")
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