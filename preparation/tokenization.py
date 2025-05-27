from tqdm import tqdm
import json


def tokenize(input_file, output_file):
    """Simple Word Tokenizer"""

    print("=== Tokenizer ===")

    # Load the file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    documents = [doc.strip() for doc in content.split('\n---\n') if doc.strip()]
    print(f"Loaded {len(documents)} documents")

    # Word tokenizer
    tokenized_docs = []

    total_words = 0

    for doc in tqdm(documents, desc="Tokenize"):
        # Split whitespace then lowercase
        words = doc.lower().split()
        tokenized_docs.append(words)
        total_words += len(words)

    # Save as JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tokenized_docs, f)

    print(f"Documents: {len(documents):,}")
    print(f"Total words: {total_words:,}")
    if len(documents) > 0:
        print(f"Average words per doc: {total_words / len(documents):.1f}")
    else:
        print("Average words per doc: 0.0")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    tokenize("../processed_data/cleaned_data.txt", "../processed_data/tokenized.json")