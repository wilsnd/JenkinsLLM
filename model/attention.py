import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        self.w_qkv = nn.Linear(d_model, 3 * d_model, bias=False)
        self.w_o = nn.Linear(d_model, d_model, bias=False)

        self.dropout = nn.Dropout(0.1)
        self.scale = 1.0 / math.sqrt(self.d_k)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        # Linear projections
        qkv = self.w_qkv(query)
        q, k, v = qkv.chunk(3, dim=-1)
        Q = q.view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = k.view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = v.view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)

        # Attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale

        if mask is not None:
            scores.masked_fill_(mask == 0, -1e9)

        attention = F.softmax(scores, dim=-1)
        attention = self.dropout(attention)

        # Apply attention to values
        context = torch.matmul(attention, V)

        # Concat the heads
        context = context.transpose(1, 2).contiguous().view(
            batch_size, -1, self.d_model)

        return self.w_o(context)


def create_causal_mask(seq_len):
    """Create causal mask for decoder"""
    mask = torch.tril(torch.ones(seq_len, seq_len))
    return mask.unsqueeze(0).unsqueeze(0)