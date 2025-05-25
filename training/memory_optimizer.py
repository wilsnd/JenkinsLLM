import torch
import gc

def clear_cache():
    """Clear GPU memory cache and start garbage collection"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

def get_memory_usage():
    """Get current memory usage information"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3  # Convert to GB
        return f"GPU Memory: {allocated:.2f}GB"
    return "Using CPU"

def print_memory():
    """Print current memory usage"""
    print(get_memory_usage())