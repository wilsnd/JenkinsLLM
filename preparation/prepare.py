import os
from tokenization import tokenize
from vocabularize import build_vocabulary
from convert_id import convert_to_id
from data_split import split_data
from data_validator import validate_all


def prepare_data(input_file, output_dir="../processed_data", min_freq=250):
    """Run complete preparation pipeline"""
    print("Process Start")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Tokenization
    tokenized_file = f"{output_dir}/tokenized.json"
    tokenize(input_file, tokenized_file)

    # Step 2: Split data
    split_data(tokenized_file, output_dir)

    # Step 3: Build vocabulary
    train_file = f"{output_dir}/train.json"
    vocab_file = f"{output_dir}/vocabulary.json"
    build_vocabulary(train_file, vocab_file, min_freq)

    # Step 4: Convert to IDs
    convert_to_id(f"{output_dir}/train.json", vocab_file, f"{output_dir}/train_ids.json")
    convert_to_id(f"{output_dir}/val.json", vocab_file, f"{output_dir}/val_ids.json")
    convert_to_id(f"{output_dir}/test.json", vocab_file, f"{output_dir}/test_ids.json")

    # Step 5: Validation
    success = validate_all()

    return success


if __name__ == "__main__":
    prepare_data("../processed_data/cleaned_data.txt", "../processed_data", 250)
