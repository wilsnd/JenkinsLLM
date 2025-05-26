class ModelConfig:
    def __init__(self):
        # Model size
        self.vocab_size = 10000
        self.d_model = 512
        self.n_heads = 4
        self.n_layers = 3
        self.d_ff = int(self.d_model * 2.7)  # Swiglu is 2.7x, if use ReLU 4x
        self.max_seq_len = 32

        # Training
        self.dropout = 0.005
        self.learning_rate = 0.0004
        self.batch_size = 128

        # Tokens
        self.pad_token = 0
        self.unk_token = 1
        self.start_token = 2
        self.end_token = 3


# Default config
DEFAULT_CONFIG = ModelConfig()
