import json
import random


def split_data(input_file, output_dir):
    """Split data into train/val/test"""

    print("=== SPLITTING DATA ===")

    # Load data
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Shuffle
    random.shuffle(data)

    # Split 80/10/10
    total = len(data)
    train_end = int(0.8 * total)
    val_end = int(0.9 * total)

    train_data = data[:train_end]
    val_data = data[train_end:val_end]
    test_data = data[val_end:]

    # Save
    import os
    os.makedirs(output_dir, exist_ok=True)

    with open(f"{output_dir}/train.json", 'w') as f:
        json.dump(train_data, f)

    with open(f"{output_dir}/val.json", 'w') as f:
        json.dump(val_data, f)

    with open(f"{output_dir}/test.json", 'w') as f:
        json.dump(test_data, f)

    print(f"Train: {len(train_data)}")
    print(f"Val: {len(val_data)}")
    print(f"Test: {len(test_data)}")


if __name__ == "__main__":
    split_data("./processed_data/preprocess_output.txt", "./processed_data")