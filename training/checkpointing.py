import torch
import os


def save_checkpoint(model, optimizer, epoch, loss, filepath):
    """Save complete training checkpoint"""
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss
    }
    torch.save(checkpoint, filepath)
    print(f"Checkpoint saved: {filepath}")


def load_checkpoint(filepath, model, optimizer=None):
    """Load training checkpoint"""
    checkpoint = torch.load(filepath)
    model.load_state_dict(checkpoint['model_state_dict'])

    # Load optimizer state if provided
    if optimizer:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

    print(f"Checkpoint loaded: {filepath}")
    return checkpoint['epoch'], checkpoint['loss']


def save_model(model, filepath):
    """Only save the model weight"""
    torch.save(model.state_dict(), filepath)
    print(f"Model saved: {filepath}")