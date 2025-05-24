class ModelConfig:
    def __init__(self):
        # Model size
        self.vocab_size = 10000
        self.d_model = 512
        self.n_heads = 8
        self.n_layers = 6
        self.d_ff = 2048
        self.max_seq_len = 1024

        # Training
        self.dropout = 0.1
        self.learning_rate = 0.0001
        self.batch_size = 32

        # Tokens
        self.pad_token = 0
        self.unk_token = 1
        self.start_token = 2
        self.end_token = 3


# Default config
DEFAULT_CONFIG = ModelConfig()