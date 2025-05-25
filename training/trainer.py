import torch
import torch.nn as nn
import os
from tqdm import tqdm
from .data_loader import create_data_loader

class SimpleTrainer:
    """EZ and simple trainer, no time to implement complex one"""

    def __init__(self, model):
        self.model = model
        # GPU if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        self.loss_fn = nn.CrossEntropyLoss()

        print(f"Using device: {self.device}")

    def train_epoch(self, train_loader):
        """Train model for one epoch"""
        self.model.train()  # Set to train mode
        total_loss = 0

        for batch in tqdm(train_loader, desc="Training"):
            batch = batch.to(self.device)

            # Prepare input and target sequences
            input_ids = batch[:, :-1]  # All tokens but not the last one
            targets = batch[:, 1:]  # All tokens but not the first one

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(input_ids)

            # Calculate loss
            loss = self.loss_fn(outputs.reshape(-1, outputs.size(-1)), targets.reshape(-1))

            # Backward pass and optimization
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / len(train_loader)

    def evaluate(self, val_loader):
        """Evaluate model on val set"""
        self.model.eval()  # Set to eval mode
        total_loss = 0

        # No grad computation
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(self.device)
                input_ids = batch[:, :-1]
                targets = batch[:, 1:]

                outputs = self.model(input_ids)
                loss = self.loss_fn(outputs.reshape(-1, outputs.size(-1)), targets.reshape(-1))
                total_loss += loss.item()

        return total_loss / len(val_loader)

    def train(self, train_file, val_file, epochs=5):
        """Main training loop"""
        print("=== STARTING TRAINING ===")

        # Create data loaders
        train_loader = create_data_loader(train_file)
        val_loader = create_data_loader(val_file)

        # Training loop
        for epoch in range(1, epochs + 1):
            print(f"\nEpoch {epoch}/{epochs}")

            # Train and evaluate
            train_loss = self.train_epoch(train_loader)
            val_loss = self.evaluate(val_loader)

            print(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

        # Save trained model with version
        self._save_model()

    def _save_model(self):
        """Save model with version from __init__.py"""
        from . import __version__

        # Create directory if it doesn't exist
        save_dir = '../models/all_models'
        os.makedirs(save_dir, exist_ok=True)

        # Use version from __init__.py
        filename = f"model_v{__version__}.pt"
        filepath = os.path.join(save_dir, filename)

        # Save model
        torch.save(self.model.state_dict(), filepath)
        print(f"Model saved: {filename}")

        # Also save as 'latest.pt'
        latest_path = os.path.join(save_dir, 'latest.pt')
        torch.save(self.model.state_dict(), latest_path)
        print("Latest model saved as: latest.pt")

def train_model(model, train_file, val_file, epochs=5):
    """Train the model"""
    trainer = SimpleTrainer(model)
    trainer.train(train_file, val_file, epochs)


def list_saved_models():
    """List all saved models"""
    save_dir = '../models/all_models'
    if not os.path.exists(save_dir):
        print("No models directory found")
        return []

    # Get all model files
    models = [f for f in os.listdir(save_dir) if f.startswith('model_v') and f.endswith('.pt')]
    models.sort()

    print(f"Found {len(models)} saved models:")
    for i, model in enumerate(models):
        print(f"  {i + 1}. {model}")

    return models


def load_model_by_version(model, version):
    """Load a specific model by version"""
    save_dir = '../models/all_models'
    filename = f"model_v{version}.pt"
    filepath = os.path.join(save_dir, filename)

    if os.path.exists(filepath):
        model.load_state_dict(torch.load(filepath))
        print(f"Model loaded: {filename}")
    else:
        print(f"Model not found: {filename}")
        list_saved_models()