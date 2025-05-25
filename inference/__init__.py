from .generator import TextGenerator, load_generator, generate_text
from .api_server import create_app
from .batch_inference import BatchInference, run_batch_inference

__version__ = "1.0.0"

__all__ = [
    "TextGenerator",
    "load_generator",
    "generate_text",
    "create_app",
    "BatchInference",
    "run_batch_inference"
]

def quick_generate(prompt="hello world", max_length=30):
    """Text generation for testing"""
    generator = load_generator()
    return generator.generate(prompt, max_length)

def start_api_server():
    """Start the API server"""
    app = create_app()
    if app:
        app.run(host='0.0.0.0', port=5000)
    else:
        print("Failed to start API server")
