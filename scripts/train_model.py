import json
from model import create_model
from training import train_model

# Load vocab
with open("../processed_data/vocabulary.json", 'r') as f:
    vocab = json.load(f)

print(f"Vocab size: {len(vocab)}")

# Create and train model
model = create_model(vocab_size=len(vocab))
train_model(model, "../processed_data/train_ids.json", "../processed_data/val_ids.json", epochs=5)

print("Done!")