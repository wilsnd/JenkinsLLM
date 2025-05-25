import torch
import torch.nn as nn
from .attention import MultiHeadAttention
import torch.nn.functional as F


class FeedForward(nn.Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.w1 = nn.Linear(d_model, d_ff, bias=False)  # Gate
        self.w2 = nn.Linear(d_model, d_ff, bias=False)  # Value
        self.w3 = nn.Linear(d_ff, d_model, bias=False)  # Output
        self.dropout = nn.Dropout(0.1)

    def forward(self, x):
        # SwiGLUU~~~~
        gate = self.w1(x)
        value = self.w2(x)
        return self.w3(self.dropout(F.silu(gate) * value))

class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, d_ff):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, n_heads)
        self.feed_forward = FeedForward(d_model, d_ff)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x, mask=None):
        # Self-attention
        attn_output = self.attention(self.norm1(x), self.norm1(x), self.norm1(x), mask)
        x = x + self.dropout(attn_output)

        # Feed-forward
        ff_output = self.feed_forward(self.norm2(x))
        x = x + self.dropout(ff_output)

        return x


class TransformerDecoder(nn.Module):
    def __init__(self, n_layers, d_model, n_heads, d_ff):
        super().__init__()
        self.layers = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff)
            for _ in range(n_layers)
        ])

    def forward(self, x, mask=None):
        for layer in self.layers:
            x = layer(x, mask)
        return x