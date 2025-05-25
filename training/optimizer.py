import torch.optim as optim

def create_optimizer(model, lr=0.001):
    """Adam optimizer for model training"""
    return optim.Adam(model.parameters(), lr=lr)

def create_scheduler(optimizer):
    """learning rate scheduler"""
    # Reduce LR every 5 epochs
    return optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)