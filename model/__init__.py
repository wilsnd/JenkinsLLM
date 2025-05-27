from .attention import MultiHeadAttention, create_causal_mask
from .config import ModelConfig, DEFAULT_CONFIG
from .embedding import Embeddings, TokenEmbedding, PositionalEmbedding
from .llm_model import SimpleLLM, create_model
from .transformer import TransformerBlock, TransformerDecoder, FeedForward

__version__ = "1.0.0"

__all__ = [
    "ModelConfig",
    "DEFAULT_CONFIG", 
    "Embeddings",
    "TokenEmbedding",
    "PositionalEmbedding",
    "MultiHeadAttention",
    "create_causal_mask",
    "TransformerBlock", 
    "TransformerDecoder",
    "FeedForward",
    "SimpleLLM",
    "create_model"
]


def get_version():
    return __version__