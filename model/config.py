class ModelConfig:
    def __init__(self):
        # Model size
        self.vocab_size = 10000
        self.d_model = 256
        self.n_heads = 8
        self.n_layers = 6
        self.d_ff = int(self.d_model * 2.7)  # Swiglu is 2.7x, if use ReLU 4x
        self.max_seq_len = 128

        # Training
        self.dropout = 0.0
        self.learning_rate = 0.0003
        self.batch_size = 4

        # Tokens
        self.pad_token = 0
        self.unk_token = 1
        self.start_token = 2
        self.end_token = 3


# Default config
DEFAULT_CONFIG = ModelConfig()
