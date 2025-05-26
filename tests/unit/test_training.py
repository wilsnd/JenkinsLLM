import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from training import train_model
from model import create_model

def test_training_pipeline():
    """Test the training pipeline"""

    # Load the vocab
    print("Load Vocab")
    with open("../../processed_data/vocabulary.json", 'r') as f:
        vocab = json.load(f)

    print(f"Vocabulary size: {len(vocab)}")

    # Create the model
    print("Creating model")
    model = create_model(vocab_size=len(vocab))

    print("Training model")
    # Train the model
    train_model(
        model,
        "mock_data/test_train.json",
        "mock_data/test_val.json",
        epochs=1
    )

    print("Training test complete!")


if __name__ == "__main__":
    test_training_pipeline()