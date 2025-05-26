# Config
PREPARATION_CONFIG = {
    "min_vocab_frequency": 250,
    "max_sequence_length": 32,
    "train_split": 0.8,
    "validation_split": 0.1,
    "test_split": 0.1,
    "special_tokens": ['<PAD>', '<UNK>', '<START>', '<END>'],
    "tokenization_method": "whitespace"
}

def get_preparation_config():
    return PREPARATION_CONFIG.copy()