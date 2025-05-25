from .generator import TextGenerator, load_generator, generate_text
from .batch_inference import BatchInference, run_batch_inference
from .flask_web import start_demo

__version__ = "1.0.0"

__all__ = [
    "TextGenerator",
    "load_generator",
    "generate_text",
    "BatchInference",
    "run_batch_inference",
]