from flask import Flask, request, jsonify
import os
from generator import TextGenerator

app = Flask(__name__)

# Global generator
generator = None


def init_generator():
    """Start the text generator"""
    global generator

    model_path = "../models/all_models/latest.pt"
    vocab_path = "../processed_data/vocabulary.json"

    if os.path.exists(model_path) and os.path.exists(vocab_path):
        generator = TextGenerator(model_path, vocab_path)
        print("Generator initialized successfully")
        return True
    else:
        print("Model or vocab files not found")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": generator is not None
    })


@app.route('/generate', methods=['POST'])
def generate_text():
    """Generate text endpoint"""

    if generator is None:
        return jsonify({"error": "Model not loaded"}), 500

    try:
        # Get request data
        data = request.get_json()
        prompt = data.get('prompt', '')
        max_length = data.get('max_length', 50)
        temperature = data.get('temperature', 0.8)

        # Generate text
        result = generator.generate(prompt, max_length, temperature)

        return jsonify({
            "prompt": prompt,
            "generated_text": result,
            "max_length": max_length,
            "temperature": temperature
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/generate_simple', methods=['GET'])
def generate_simple():
    """GET endpoint"""

    if generator is None:
        return jsonify({"error": "Model not loaded"}), 500

    try:
        prompt = request.args.get('prompt', '')
        max_length = int(request.args.get('max_length', 30))

        result = generator.generate(prompt, max_length)

        return jsonify({
            "prompt": prompt,
            "generated_text": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/info', methods=['GET'])
def model_info():
    """Get model information"""

    if generator is None:
        return jsonify({"error": "Model not loaded"}), 500

    return jsonify({
        "vocab_size": len(generator.vocab),
        "model_device": str(generator.device),
        "available_endpoints": [
            "/health",
            "/generate",
            "/generate_simple",
            "/info"
        ]
    })


def create_app():
    """Create Flask app"""
    if init_generator():
        return app
    else:
        print("Failed to initialize generator")
        return None


if __name__ == "__main__":
    print("=== STARTING API SERVER ===")

    if init_generator():
        print("Starting server on http://localhost:5000")
        print("\nEndpoints:")
        print("  GET  /health - Health check")
        print("  POST /generate - Generate text")
        print("  GET  /generate_simple?prompt=hello - Simple generation")
        print("  GET  /info - Model information")

        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        print("Failed to start server - model files not found")