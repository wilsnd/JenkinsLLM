import torch

def calculate_accuracy(predictions, targets):
    """Calculate token-level accuracy"""
    # Get predicted tokens (highest probability)
    pred_tokens = torch.argmax(predictions, dim=-1)
    # Calculate percentage of correct predictions
    correct = (pred_tokens == targets).float()
    return correct.mean().item()

def calculate_perplexity(loss):
    """Calculate perplexity from loss (lower is better)"""
    return torch.exp(torch.tensor(loss)).item()