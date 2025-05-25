import torch
import torch.nn as nn
from .config import DEFAULT_CONFIG
from .embedding import Embeddings
from .transformer import TransformerDecoder
from .attention import create_causal_mask
import torch.nn.functional as F


class SimpleLLM(nn.Module):
    """EZ model"""
    def __init__(self, config=None):
        super().__init__()
        if config is None:
            config = DEFAULT_CONFIG

        self.config = config

        # Components
        self.embeddings = Embeddings(
            config.vocab_size,
            config.d_model,
            config.max_seq_len
        )

        self.decoder = TransformerDecoder(
            config.n_layers,
            config.d_model,
            config.n_heads,
            config.d_ff
        )

        self.norm_f = nn.LayerNorm(config.d_model)

        # Tied embedding
        self.tie_embeddings = True
        if not self.tie_embeddings:
            self.output_projection = nn.Linear(config.d_model, config.vocab_size, bias=False)

        # Initialize the weights
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, input_ids):
        seq_len = input_ids.size(1)

        # Create causal mask
        mask = create_causal_mask(seq_len)
        if input_ids.is_cuda:
            mask = mask.cuda()

        # Forward pass
        x = self.embeddings(input_ids)
        x = self.decoder(x, mask)
        x = self.norm_f(x)

        # Tied embeddings
        if self.tie_embeddings:
            logits = F.linear(x, self.embeddings.token_emb.embedding.weight)
        else:
            logits = self.output_projection(x)

        return logits

    def generate(self, input_ids, max_length=50, temperature=1.0):
        """Simple text generation"""
        self.eval()

        with torch.no_grad():
            for _ in range(max_length):
                logits = self.forward(input_ids)
                next_token_logits = logits[:, -1, :] / temperature
                next_token = torch.multinomial(
                    torch.softmax(next_token_logits, dim=-1),
                    num_samples=1
                )
                input_ids = torch.cat([input_ids, next_token], dim=1)

                # Stop if we hit end token
                if next_token.item() == self.config.end_token:
                    break

        return input_ids

    def count_parameters(self):
        """Count trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def create_model(vocab_size=None):
    """Factory function to create model"""
    config = DEFAULT_CONFIG
    if vocab_size:
        config.vocab_size = vocab_size

    model = SimpleLLM(config)
    print(f"Model created with {model.count_parameters():,} parameters")
    return model