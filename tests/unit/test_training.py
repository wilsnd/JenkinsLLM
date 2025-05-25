import sys
import os
import json

# Rood project so can import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from model import create_model
from training import train_model


def test_model_creation():
    """Test model creation works"""
    print("Testing model creation")
    model = create_model(vocab_size=1000)
    assert model is not None
    assert model.count_parameters() > 0
    print(f"Model created with {model.count_parameters():,} parameters")


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
        "../../processed_data/train_ids.json",
        "../../processed_data/val_ids.json",
        epochs=5
    )

    print("Training test complete!")


if __name__ == "__main__":
    test_model_creation()
    test_training_pipeline()