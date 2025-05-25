import json
import torch
from torch.utils.data import Dataset, DataLoader


class TextDataset(Dataset):
    """Load the tokenized data"""

    def __init__(self, data_file, max_length=128):
        # Load the JSON file
        with open(data_file, 'r') as f:
            self.data = json.load(f)

        self.max_length = max_length
        print(f"Loaded {len(self.data)} samples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # Get sequence and trunc if too long
        sequence = self.data[idx]
        if len(sequence) > self.max_length:
            sequence = sequence[:self.max_length]

        # Convert token IDs to tensor
        return torch.tensor(sequence, dtype=torch.long)


def collate_fn(batch):
    """Pad sequences to same length in batch"""
    # Find the max length in the batch
    max_len = max(len(seq) for seq in batch)

    # Pad all sequences to max length
    padded_batch = []
    for seq in batch:
        if len(seq) < max_len:
            # Padding with 0
            padding = torch.zeros(max_len - len(seq), dtype=torch.long)
            seq = torch.cat([seq, padding])
        padded_batch.append(seq)

    return torch.stack(padded_batch)


def create_data_loader(data_file, batch_size=32, max_length=128):
    """PyTorch DataLoader from JSON file"""
    dataset = TextDataset(data_file, max_length)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn
    )

