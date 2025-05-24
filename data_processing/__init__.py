from .preprocessing import preprocess
from .tokenization import tokenize
from .vocabularize import build_vocabulary
from .convert_id import convert_to_id
from .data_split import split_data
from .data_validator import DataValidator

__version__ = "1.0.0"
__author__ = "Wilsnd"

__all__ = [
    "preprocess",
    "tokenize",
    "build_vocabulary",
    "convert_to_id",
    "split_data",
    "DataValidator"
]

# Pipeline config
DEFAULT_CONFIG = {
    "min_vocab_frequency": 5,
    "max_sequence_length": 512,
    "train_split": 0.8,
    "validation_split": 0.1,
    "test_split": 0.1
}

def get_version():
    return __version__

def get_default_config():
    return DEFAULT_CONFIG.copy()