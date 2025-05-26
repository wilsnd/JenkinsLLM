from .trainer import SimpleTrainer, train_model, list_saved_models, load_model_by_version
from .data_loader import TextDataset, create_data_loader, collate_fn
from .metrics import calculate_accuracy, calculate_perplexity
from .optimizer import create_optimizer, create_scheduler
from .memory_optimizer import clear_cache, get_memory_usage, print_memory

__version__ = "1.0.0"


def get_version():
    return __version__