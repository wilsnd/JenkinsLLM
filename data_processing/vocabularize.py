import json
from collections import Counter
from tqdm import tqdm


def build_vocabulary(tokenized_file, vocab_file, min_freq=5):
    """Make the vocabulary from the tokenized data"""

    print("=== BUILDING VOCABULARY ===")

    # Load tokenized data
    with open(tokenized_file, 'r', encoding='utf-8') as f:
        tokenized_docs = json.load(f)

    # Count total words
    word_counter = Counter()
    for doc in tqdm(tokenized_docs, desc="Counting words"):
        word_counter.update(doc)

    print(f"Total unique words: {len(word_counter):,}")

    # Make the vocab
    vocab = {
        '<PAD>': 0,
        '<UNK>': 1,
        '<START>': 2,
        '<END>': 3
    }

    # Add frequent words
    for word, count in word_counter.most_common():
        if count >= min_freq:
            vocab[word] = len(vocab)

    # Save vocabulary
    with open(vocab_file, 'w', encoding='utf-8') as f:
        json.dump(vocab, f, indent=2)

    print(f"Vocabulary size: {len(vocab):,}")
    print(f"Saved to: {vocab_file}")


build_vocabulary("../old_files/tokenized.json", "extra_files/vocabulary.json")
